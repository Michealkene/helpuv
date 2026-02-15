"""XAUBOT Pro - Backend API
Handles: Affiliate program, Bitcoin payments, License delivery
Run: python app.py
"""
import os
import json
import uuid
import hashlib
import hmac
import time
import sqlite3
import secrets
import string
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify, redirect, render_template_string, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.secret_key = secrets.token_hex(32)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xaubot.db")
PRODUCT_PRICE_USD = 297
BTC_WALLET = os.environ.get("BTC_WALLET", "YOUR_BTC_ADDRESS_HERE")
ADMIN_KEY = os.environ.get("ADMIN_KEY", "xaubot_admin_2026")
AFFILIATE_COMMISSION = 0.20  # 20% commission
LANDING_URL = "http://74.50.87.77"

# ==================== DATABASE ====================
def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS affiliates (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            ref_code TEXT UNIQUE NOT NULL,
            commission_rate REAL DEFAULT 0.20,
            total_clicks INTEGER DEFAULT 0,
            total_sales INTEGER DEFAULT 0,
            total_earned REAL DEFAULT 0,
            balance REAL DEFAULT 0,
            btc_payout_address TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            active INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            affiliate_id TEXT,
            ip TEXT,
            user_agent TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (affiliate_id) REFERENCES affiliates(id)
        );
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            affiliate_id TEXT DEFAULT NULL,
            ref_code TEXT DEFAULT NULL,
            amount_usd REAL NOT NULL,
            amount_btc REAL DEFAULT 0,
            btc_address TEXT DEFAULT '',
            payment_status TEXT DEFAULT 'pending',
            license_key TEXT DEFAULT NULL,
            download_token TEXT DEFAULT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            paid_at TEXT DEFAULT NULL,
            expires_at TEXT DEFAULT NULL,
            FOREIGN KEY (affiliate_id) REFERENCES affiliates(id)
        );
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT NOT NULL,
            tx_hash TEXT DEFAULT '',
            amount_btc REAL DEFAULT 0,
            confirmations INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        );
    """)
    db.commit()
    db.close()

init_db()

# ==================== HELPERS ====================
def gen_ref_code(name):
    base = ''.join(c for c in name.lower() if c.isalnum())[:8]
    suffix = ''.join(secrets.choice(string.digits) for _ in range(3))
    return f"{base}{suffix}"

def gen_license_key():
    parts = [secrets.token_hex(4).upper() for _ in range(4)]
    return '-'.join(parts)

def gen_download_token():
    return secrets.token_urlsafe(32)

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get('X-Admin-Key') or request.args.get('admin_key')
        if key != ADMIN_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

def get_btc_price():
    """Get current BTC/USD price from CoinGecko (free, no API key)"""
    import urllib.request
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        req = urllib.request.Request(url, headers={'User-Agent': 'XAUBOT/1.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode())
        return data['bitcoin']['usd']
    except Exception:
        return 95000  # fallback estimate

# ==================== AFFILIATE ENDPOINTS ====================

@app.route('/api/affiliate/create', methods=['POST'])
@require_admin
def create_affiliate():
    """Admin: Create a new affiliate/influencer"""
    data = request.json
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    btc_address = data.get('btc_payout_address', '')
    commission = data.get('commission_rate', AFFILIATE_COMMISSION)

    if not name or not email:
        return jsonify({"error": "Name and email required"}), 400

    aff_id = str(uuid.uuid4())[:8]
    ref_code = gen_ref_code(name)

    db = get_db()
    try:
        db.execute("""INSERT INTO affiliates (id, name, email, ref_code, commission_rate, btc_payout_address)
                      VALUES (?, ?, ?, ?, ?, ?)""",
                   (aff_id, name, email, ref_code, commission, btc_address))
        db.commit()
    except sqlite3.IntegrityError:
        ref_code = gen_ref_code(name + secrets.token_hex(2))
        db.execute("""INSERT INTO affiliates (id, name, email, ref_code, commission_rate, btc_payout_address)
                      VALUES (?, ?, ?, ?, ?, ?)""",
                   (aff_id, name, email, ref_code, commission, btc_address))
        db.commit()
    db.close()

    ref_link = f"{LANDING_URL}?ref={ref_code}"
    return jsonify({
        "affiliate_id": aff_id,
        "name": name,
        "ref_code": ref_code,
        "ref_link": ref_link,
        "commission_rate": f"{commission*100:.0f}%"
    })

@app.route('/api/affiliate/list', methods=['GET'])
@require_admin
def list_affiliates():
    """Admin: List all affiliates with stats"""
    db = get_db()
    affs = db.execute("SELECT * FROM affiliates ORDER BY total_earned DESC").fetchall()
    db.close()
    return jsonify([{
        "id": a['id'], "name": a['name'], "email": a['email'],
        "ref_code": a['ref_code'], "ref_link": f"{LANDING_URL}?ref={a['ref_code']}",
        "commission_rate": f"{a['commission_rate']*100:.0f}%",
        "clicks": a['total_clicks'], "sales": a['total_sales'],
        "total_earned": f"${a['total_earned']:.2f}",
        "balance": f"${a['balance']:.2f}",
        "btc_payout": a['btc_payout_address'],
        "active": bool(a['active']), "created": a['created_at']
    } for a in affs])

@app.route('/api/affiliate/<ref_code>/stats', methods=['GET'])
def affiliate_stats(ref_code):
    """Affiliate: View their own stats (public by ref_code)"""
    db = get_db()
    a = db.execute("SELECT * FROM affiliates WHERE ref_code = ?", (ref_code,)).fetchone()
    if not a:
        db.close()
        return jsonify({"error": "Affiliate not found"}), 404

    recent = db.execute("""SELECT created_at, payment_status FROM orders
                          WHERE ref_code = ? ORDER BY created_at DESC LIMIT 10""",
                       (ref_code,)).fetchall()
    db.close()

    return jsonify({
        "name": a['name'],
        "ref_code": a['ref_code'],
        "ref_link": f"{LANDING_URL}?ref={ref_code}",
        "clicks": a['total_clicks'],
        "sales": a['total_sales'],
        "conversion_rate": f"{(a['total_sales']/max(a['total_clicks'],1)*100):.1f}%",
        "total_earned": f"${a['total_earned']:.2f}",
        "balance": f"${a['balance']:.2f}",
        "recent_orders": [{"date": r['created_at'], "status": r['payment_status']} for r in recent]
    })

@app.route('/ref/<ref_code>')
def track_referral(ref_code):
    """Track click and redirect to landing page with ref param"""
    db = get_db()
    a = db.execute("SELECT id FROM affiliates WHERE ref_code = ? AND active = 1",
                   (ref_code,)).fetchone()
    if a:
        db.execute("UPDATE affiliates SET total_clicks = total_clicks + 1 WHERE id = ?", (a['id'],))
        db.execute("INSERT INTO clicks (affiliate_id, ip, user_agent) VALUES (?, ?, ?)",
                   (a['id'], request.remote_addr, request.user_agent.string[:200]))
        db.commit()
    db.close()
    return redirect(f"{LANDING_URL}?ref={ref_code}")

# ==================== PAYMENT ENDPOINTS ====================

@app.route('/api/order/create', methods=['POST'])
def create_order():
    """Create a new order - returns BTC payment details"""
    data = request.json
    email = data.get('email', '').strip()
    ref_code = data.get('ref_code', '').strip() or None

    if not email:
        return jsonify({"error": "Email required"}), 400

    order_id = str(uuid.uuid4())[:12]
    btc_price = get_btc_price()
    amount_btc = round(PRODUCT_PRICE_USD / btc_price, 8)
    license_key = gen_license_key()
    download_token = gen_download_token()

    # Verify affiliate ref_code
    affiliate_id = None
    if ref_code:
        db = get_db()
        a = db.execute("SELECT id FROM affiliates WHERE ref_code = ? AND active = 1",
                       (ref_code,)).fetchone()
        if a:
            affiliate_id = a['id']
        db.close()

    db = get_db()
    db.execute("""INSERT INTO orders (id, email, affiliate_id, ref_code, amount_usd, amount_btc,
                  btc_address, license_key, download_token, expires_at)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
               (order_id, email, affiliate_id, ref_code, PRODUCT_PRICE_USD, amount_btc,
                BTC_WALLET, license_key, download_token,
                (datetime.utcnow() + timedelta(hours=24)).isoformat()))
    db.commit()
    db.close()

    return jsonify({
        "order_id": order_id,
        "amount_usd": PRODUCT_PRICE_USD,
        "amount_btc": amount_btc,
        "btc_address": BTC_WALLET,
        "btc_price": btc_price,
        "expires_in": "24 hours",
        "status_url": f"/api/order/{order_id}/status"
    })

@app.route('/api/order/<order_id>/status', methods=['GET'])
def order_status(order_id):
    """Check order payment status"""
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    db.close()

    if not order:
        return jsonify({"error": "Order not found"}), 404

    result = {
        "order_id": order['id'],
        "amount_usd": order['amount_usd'],
        "amount_btc": order['amount_btc'],
        "btc_address": order['btc_address'],
        "status": order['payment_status'],
        "created_at": order['created_at']
    }

    if order['payment_status'] == 'confirmed':
        result['license_key'] = order['license_key']
        result['download_url'] = f"/download/{order['download_token']}"

    return jsonify(result)

@app.route('/api/order/<order_id>/confirm', methods=['POST'])
@require_admin
def confirm_order(order_id):
    """Admin: Manually confirm payment and release license"""
    data = request.json or {}
    tx_hash = data.get('tx_hash', '')

    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        db.close()
        return jsonify({"error": "Order not found"}), 404

    # Update order
    db.execute("""UPDATE orders SET payment_status = 'confirmed', paid_at = ?
                  WHERE id = ?""", (datetime.utcnow().isoformat(), order_id))

    # Record payment
    db.execute("""INSERT INTO payments (order_id, tx_hash, amount_btc, confirmations, status)
                  VALUES (?, ?, ?, ?, 'confirmed')""",
               (order_id, tx_hash, order['amount_btc'], 1))

    # Credit affiliate commission
    if order['affiliate_id']:
        aff = db.execute("SELECT * FROM affiliates WHERE id = ?",
                         (order['affiliate_id'],)).fetchone()
        if aff:
            commission = order['amount_usd'] * aff['commission_rate']
            db.execute("""UPDATE affiliates SET total_sales = total_sales + 1,
                         total_earned = total_earned + ?, balance = balance + ?
                         WHERE id = ?""", (commission, commission, order['affiliate_id']))

    db.commit()
    db.close()

    return jsonify({
        "order_id": order_id,
        "status": "confirmed",
        "license_key": order['license_key'],
        "download_url": f"/download/{order['download_token']}",
        "affiliate_credited": bool(order['affiliate_id'])
    })

@app.route('/api/order/<order_id>/check_blockchain', methods=['POST'])
def check_blockchain_payment(order_id):
    """Check blockchain for payment to the BTC address"""
    import urllib.request

    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        db.close()
        return jsonify({"error": "Order not found"}), 404

    if order['payment_status'] == 'confirmed':
        db.close()
        return jsonify({"status": "already_confirmed", "license_key": order['license_key']})

    # Check blockchain.info for received payments
    try:
        url = f"https://blockchain.info/q/getreceivedbyaddress/{order['btc_address']}?confirmations=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'XAUBOT/1.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        received_satoshis = int(resp.read().decode().strip())
        received_btc = received_satoshis / 1e8
        expected_btc = order['amount_btc']

        if received_btc >= expected_btc * 0.98:  # 2% tolerance for fees
            # Payment confirmed!
            db.execute("""UPDATE orders SET payment_status = 'confirmed', paid_at = ?
                         WHERE id = ?""", (datetime.utcnow().isoformat(), order_id))

            if order['affiliate_id']:
                aff = db.execute("SELECT commission_rate FROM affiliates WHERE id = ?",
                                 (order['affiliate_id'],)).fetchone()
                if aff:
                    commission = order['amount_usd'] * aff['commission_rate']
                    db.execute("""UPDATE affiliates SET total_sales = total_sales + 1,
                                 total_earned = total_earned + ?, balance = balance + ?
                                 WHERE id = ?""",
                               (commission, commission, order['affiliate_id']))

            db.commit()
            db.close()
            return jsonify({
                "status": "confirmed",
                "received_btc": received_btc,
                "license_key": order['license_key'],
                "download_url": f"/download/{order['download_token']}"
            })

        db.close()
        return jsonify({
            "status": "pending",
            "received_btc": received_btc,
            "expected_btc": expected_btc,
            "message": "Payment not yet confirmed. Please wait for blockchain confirmation."
        })

    except Exception as e:
        db.close()
        return jsonify({"status": "check_failed", "error": str(e)})

@app.route('/download/<token>')
def download_bot(token):
    """Download bot after payment confirmation"""
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE download_token = ? AND payment_status = 'confirmed'",
                       (token,)).fetchone()
    db.close()

    if not order:
        return jsonify({"error": "Invalid or expired download link"}), 403

    # Serve the installer package
    installer_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "releases", "xaubot_pro.zip")
    if os.path.exists(installer_path):
        return send_file(installer_path, as_attachment=True, download_name="XAUBOT_Pro_Installer.zip")

    return jsonify({
        "license_key": order['license_key'],
        "message": "Your license key is above. Download link will be sent to your email.",
        "email": order['email']
    })

# ==================== ADMIN DASHBOARD ====================

@app.route('/admin')
@require_admin
def admin_dashboard():
    db = get_db()
    total_orders = db.execute("SELECT COUNT(*) as c FROM orders").fetchone()['c']
    confirmed_orders = db.execute("SELECT COUNT(*) as c FROM orders WHERE payment_status='confirmed'").fetchone()['c']
    total_revenue = db.execute("SELECT COALESCE(SUM(amount_usd), 0) as s FROM orders WHERE payment_status='confirmed'").fetchone()['s']
    total_affiliates = db.execute("SELECT COUNT(*) as c FROM affiliates").fetchone()['c']
    pending_commissions = db.execute("SELECT COALESCE(SUM(balance), 0) as s FROM affiliates").fetchone()['s']

    affiliates = db.execute("SELECT * FROM affiliates ORDER BY total_earned DESC").fetchall()
    recent_orders = db.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT 20").fetchall()
    db.close()

    return render_template_string(ADMIN_HTML,
        total_orders=total_orders, confirmed_orders=confirmed_orders,
        total_revenue=total_revenue, total_affiliates=total_affiliates,
        pending_commissions=pending_commissions,
        affiliates=affiliates, orders=recent_orders,
        admin_key=ADMIN_KEY, landing_url=LANDING_URL)

ADMIN_HTML = """<!DOCTYPE html>
<html><head>
<meta charset="UTF-8"><title>XAUBOT Pro Admin</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:#0a0a0f;color:#e0e0e0;padding:20px}
h1{color:#d4af37;margin-bottom:20px}
h2{color:#d4af37;margin:30px 0 15px;font-size:1.2em}
.stats{display:flex;gap:15px;flex-wrap:wrap;margin-bottom:30px}
.stat{background:#12121a;border:1px solid #1e1e2e;border-radius:10px;padding:20px;flex:1;min-width:150px;text-align:center}
.stat .v{font-size:1.8em;font-weight:800;color:#d4af37}
.stat .l{font-size:0.75em;color:#6b6b80;text-transform:uppercase;margin-top:5px}
table{width:100%;border-collapse:collapse;margin:10px 0}
th{background:#1a1a2e;color:#d4af37;padding:10px;text-align:left;font-size:0.85em}
td{padding:10px;border-bottom:1px solid #1e1e2e;font-size:0.85em}
tr:hover{background:#12121a}
.badge{display:inline-block;padding:3px 8px;border-radius:4px;font-size:0.75em;font-weight:600}
.b-confirmed{background:#0a2a1a;color:#00d4aa}
.b-pending{background:#2a2a0a;color:#d4af37}
.copy-btn{background:#1a1a2e;border:1px solid #333;color:#d4af37;padding:4px 10px;border-radius:4px;cursor:pointer;font-size:0.8em}
.copy-btn:hover{background:#2a2a3e}
.form-row{display:flex;gap:10px;margin:10px 0;flex-wrap:wrap}
.form-row input{background:#12121a;border:1px solid #2a2a3e;color:#e0e0e0;padding:8px 12px;border-radius:6px;flex:1}
.form-row button{background:linear-gradient(135deg,#d4af37,#b8962e);color:#000;border:none;padding:8px 20px;border-radius:6px;cursor:pointer;font-weight:600}
</style></head><body>
<h1>XAUBOT Pro - Admin Panel</h1>
<div class="stats">
  <div class="stat"><div class="v">{{ confirmed_orders }}</div><div class="l">Sales</div></div>
  <div class="stat"><div class="v">${{ "%.0f"|format(total_revenue) }}</div><div class="l">Revenue</div></div>
  <div class="stat"><div class="v">{{ total_affiliates }}</div><div class="l">Affiliates</div></div>
  <div class="stat"><div class="v">${{ "%.0f"|format(pending_commissions) }}</div><div class="l">Pending Commissions</div></div>
  <div class="stat"><div class="v">{{ total_orders }}</div><div class="l">Total Orders</div></div>
</div>

<h2>Create New Affiliate</h2>
<div class="form-row">
  <input type="text" id="aff-name" placeholder="Influencer Name">
  <input type="email" id="aff-email" placeholder="Email">
  <input type="text" id="aff-btc" placeholder="BTC Payout Address (optional)">
  <button onclick="createAffiliate()">Create Affiliate</button>
</div>
<div id="aff-result" style="margin:10px 0;color:#00d4aa;font-size:0.9em"></div>

<h2>Affiliates ({{ total_affiliates }})</h2>
<table>
<tr><th>Name</th><th>Ref Code</th><th>Referral Link</th><th>Clicks</th><th>Sales</th><th>Earned</th><th>Balance</th></tr>
{% for a in affiliates %}
<tr>
  <td>{{ a.name }}</td>
  <td>{{ a.ref_code }}</td>
  <td><code style="color:#d4af37;font-size:0.8em">{{ landing_url }}?ref={{ a.ref_code }}</code>
    <button class="copy-btn" onclick="navigator.clipboard.writeText('{{ landing_url }}?ref={{ a.ref_code }}')">Copy</button></td>
  <td>{{ a.total_clicks }}</td>
  <td>{{ a.total_sales }}</td>
  <td>${{ "%.2f"|format(a.total_earned) }}</td>
  <td>${{ "%.2f"|format(a.balance) }}</td>
</tr>
{% endfor %}
</table>

<h2>Recent Orders ({{ total_orders }})</h2>
<table>
<tr><th>Order ID</th><th>Email</th><th>Amount</th><th>Ref</th><th>Status</th><th>License</th><th>Date</th><th>Action</th></tr>
{% for o in orders %}
<tr>
  <td><code>{{ o.id }}</code></td>
  <td>{{ o.email }}</td>
  <td>${{ "%.0f"|format(o.amount_usd) }} / {{ "%.6f"|format(o.amount_btc) }} BTC</td>
  <td>{{ o.ref_code or '-' }}</td>
  <td><span class="badge {{ 'b-confirmed' if o.payment_status == 'confirmed' else 'b-pending' }}">{{ o.payment_status }}</span></td>
  <td><code style="font-size:0.75em">{{ o.license_key or '-' }}</code></td>
  <td style="font-size:0.8em">{{ o.created_at[:16] }}</td>
  <td>{% if o.payment_status != 'confirmed' %}<button class="copy-btn" onclick="confirmOrder('{{ o.id }}')">Confirm</button>{% else %}-{% endif %}</td>
</tr>
{% endfor %}
</table>

<script>
const AK = '{{ admin_key }}';
async function createAffiliate() {
  const name = document.getElementById('aff-name').value;
  const email = document.getElementById('aff-email').value;
  const btc = document.getElementById('aff-btc').value;
  if (!name || !email) { alert('Name and email required'); return; }
  const r = await fetch('/api/affiliate/create', {
    method: 'POST', headers: {'Content-Type':'application/json','X-Admin-Key':AK},
    body: JSON.stringify({name, email, btc_payout_address: btc})
  });
  const d = await r.json();
  if (d.ref_link) {
    document.getElementById('aff-result').innerHTML =
      'Created! Referral link: <strong>' + d.ref_link + '</strong>';
    setTimeout(() => location.reload(), 2000);
  } else { alert(d.error); }
}
async function confirmOrder(id) {
  if (!confirm('Confirm payment for order ' + id + '?')) return;
  const r = await fetch('/api/order/' + id + '/confirm', {
    method: 'POST', headers: {'Content-Type':'application/json','X-Admin-Key':AK},
    body: JSON.stringify({})
  });
  const d = await r.json();
  if (d.status === 'confirmed') { alert('Payment confirmed! License: ' + d.license_key); location.reload(); }
  else { alert(d.error || 'Failed'); }
}
</script>
</body></html>"""

# ==================== CHECKOUT PAGE ====================

@app.route('/checkout')
def checkout_page():
    ref = request.args.get('ref', '')
    return render_template_string(CHECKOUT_HTML, ref=ref, price=PRODUCT_PRICE_USD, btc_wallet=BTC_WALLET)

CHECKOUT_HTML = """<!DOCTYPE html>
<html><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>XAUBOT Pro - Checkout</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:#0a0a0f;color:#e0e0e0;min-height:100vh;display:flex;align-items:center;justify-content:center}
.checkout{background:#12121a;border:1px solid #1e1e2e;border-radius:16px;padding:40px;max-width:500px;width:90%}
h1{color:#d4af37;font-size:1.5em;text-align:center;margin-bottom:5px}
.sub{text-align:center;color:#6b6b80;margin-bottom:30px;font-size:0.9em}
.price{text-align:center;font-size:2.5em;font-weight:800;color:#d4af37;margin:20px 0}
.field{margin:15px 0}
.field label{display:block;color:#8b8b9e;font-size:0.85em;margin-bottom:5px}
.field input{width:100%;background:#0a0a0f;border:1px solid #2a2a3e;color:#e0e0e0;padding:12px;border-radius:8px;font-size:1em}
.field input:focus{outline:none;border-color:#d4af37}
.btn{width:100%;background:linear-gradient(135deg,#d4af37,#b8962e);color:#000;border:none;padding:14px;border-radius:8px;font-size:1.1em;font-weight:700;cursor:pointer;margin-top:20px}
.btn:hover{background:linear-gradient(135deg,#f0d060,#d4af37)}
.payment-info{background:#0a0a0f;border:1px solid #2a2a3e;border-radius:10px;padding:20px;margin:20px 0;display:none}
.btc-addr{word-break:break-all;color:#d4af37;font-family:monospace;font-size:0.9em;background:#1a1a2e;padding:10px;border-radius:6px;margin:10px 0}
.amount{color:#00d4aa;font-size:1.2em;font-weight:700}
.status{text-align:center;padding:15px;margin:15px 0;border-radius:8px;display:none}
.s-pending{background:#2a2a0a;border:1px solid #d4af37;color:#d4af37}
.s-confirmed{background:#0a2a1a;border:1px solid #00d4aa;color:#00d4aa}
.qr{text-align:center;margin:15px 0}
.qr img{border-radius:8px}
.spinner{display:inline-block;width:16px;height:16px;border:2px solid #d4af37;border-top-color:transparent;border-radius:50%;animation:spin 1s linear infinite;margin-right:8px}
@keyframes spin{to{transform:rotate(360deg)}}
.disclaimer{text-align:center;color:#4a4a5e;font-size:0.75em;margin-top:20px}
</style></head><body>
<div class="checkout">
  <h1>XAUBOT Pro</h1>
  <p class="sub">Professional Gold Trading Bot</p>
  <div class="price">${{ price }}</div>

  <div id="step1">
    <div class="field">
      <label>Email Address (for license delivery)</label>
      <input type="email" id="email" placeholder="your@email.com">
    </div>
    <input type="hidden" id="ref" value="{{ ref }}">
    <button class="btn" onclick="createOrder()">Pay with Bitcoin</button>
  </div>

  <div id="payment-info" class="payment-info">
    <p style="text-align:center;font-weight:600;margin-bottom:15px">Send exactly:</p>
    <p class="amount" style="text-align:center" id="btc-amount"></p>
    <p style="text-align:center;color:#6b6b80;font-size:0.85em;margin:5px 0">to this Bitcoin address:</p>
    <div class="btc-addr" id="btc-address"></div>
    <div class="qr" id="qr-code"></div>
    <button class="btn" onclick="checkPayment()" id="check-btn">
      <span class="spinner" id="spinner" style="display:none"></span>
      Check Payment Status
    </button>
  </div>

  <div id="status-pending" class="status s-pending" style="display:none">
    <span class="spinner"></span> Waiting for blockchain confirmation...
  </div>

  <div id="status-confirmed" class="status s-confirmed" style="display:none">
    Payment Confirmed! Your license key and download link are below.
  </div>

  <div id="license-info" style="display:none;margin-top:20px">
    <div class="field">
      <label>Your License Key</label>
      <input type="text" id="license-key" readonly style="color:#00d4aa;font-weight:700;font-size:1.1em;text-align:center">
    </div>
    <a id="download-link" href="#" class="btn" style="display:block;text-align:center;text-decoration:none;color:#000;margin-top:10px">
      Download XAUBOT Pro
    </a>
  </div>

  <p class="disclaimer">Payments are processed on the Bitcoin blockchain. Please allow 10-30 minutes for confirmation.</p>
</div>

<script>
let orderId = null;
async function createOrder() {
  const email = document.getElementById('email').value.trim();
  const ref = document.getElementById('ref').value;
  if (!email || !email.includes('@')) { alert('Please enter a valid email'); return; }

  const r = await fetch('/api/order/create', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({email, ref_code: ref})
  });
  const d = await r.json();
  if (d.error) { alert(d.error); return; }

  orderId = d.order_id;
  document.getElementById('btc-amount').textContent = d.amount_btc + ' BTC';
  document.getElementById('btc-address').textContent = d.btc_address;
  document.getElementById('qr-code').innerHTML =
    '<img src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=bitcoin:' +
    d.btc_address + '?amount=' + d.amount_btc + '" alt="QR">';

  document.getElementById('step1').style.display = 'none';
  document.getElementById('payment-info').style.display = 'block';
}

async function checkPayment() {
  if (!orderId) return;
  document.getElementById('spinner').style.display = 'inline-block';
  document.getElementById('status-pending').style.display = 'block';

  const r = await fetch('/api/order/' + orderId + '/check_blockchain', {method: 'POST'});
  const d = await r.json();
  document.getElementById('spinner').style.display = 'none';

  if (d.status === 'confirmed' || d.status === 'already_confirmed') {
    document.getElementById('status-pending').style.display = 'none';
    document.getElementById('status-confirmed').style.display = 'block';
    document.getElementById('license-info').style.display = 'block';
    document.getElementById('license-key').value = d.license_key;
    document.getElementById('download-link').href = d.download_url;
  } else {
    document.getElementById('status-pending').innerHTML =
      '<span class="spinner"></span> Payment not confirmed yet. Received: ' +
      (d.received_btc || 0) + ' / ' + (d.expected_btc || '?') + ' BTC. Please wait...';
  }
}

// Auto-check every 30 seconds
setInterval(() => { if (orderId) checkPayment(); }, 30000);
</script>
</body></html>"""

# ==================== RUN ====================
if __name__ == '__main__':
    print("=" * 50)
    print("XAUBOT Pro Backend")
    print("=" * 50)
    print(f"Admin panel: http://0.0.0.0:5000/admin?admin_key={ADMIN_KEY}")
    print(f"Checkout:    http://0.0.0.0:5000/checkout")
    print(f"BTC Wallet:  {BTC_WALLET}")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=False)
