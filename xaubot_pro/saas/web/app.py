"""XAUBOT Pro SaaS - Main Web Application"""
import sys, os, json, time, io, csv
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from flask import Flask, request, jsonify, render_template, redirect, url_for, make_response, Response
from flask_cors import CORS
from datetime import datetime, timedelta
from functools import wraps
import bcrypt, jwt, requests

from models import (
    init_db, get_db, create_user, get_user_by_email, get_user_by_id, update_user,
    create_subscription, get_user_subscriptions, get_user_trades, get_latest_signal,
    get_active_subscribers, check_fingerprint, store_fingerprint,
    get_affiliate_by_ref, credit_affiliate, get_admin_stats, new_id, log_trade
)
from encryption import encrypt, decrypt

app = Flask(__name__)
CORS(app)

SECRET_KEY = os.environ.get('XAUBOT_SECRET', 'xaubot-saas-secret-key-change-me')
ADMIN_KEY = os.environ.get('XAUBOT_ADMIN_KEY', 'xaubot_admin_2026')
WINDOWS_VPS = os.environ.get('WINDOWS_VPS_URL', 'http://3.231.147.217:5001')
WINDOWS_API_KEY = os.environ.get('WINDOWS_API_KEY', 'xaubot-engine-key')
BTC_WALLET = os.environ.get('BTC_WALLET', 'bc1pltrhg52zse0dhr2kxjh4f09j6x8glyxaaxdnt98a9q9zjcydmczqgklj8p')
DOMAIN = os.environ.get('DOMAIN', 'http://74.50.87.77')
SUBSCRIPTION_DAYS = 30  # Monthly billing

# --- Auth helpers ---
def make_token(user_id):
    return jwt.encode(
        {'uid': user_id, 'exp': datetime.utcnow() + timedelta(days=30)},
        SECRET_KEY, algorithm='HS256'
    )

def get_current_user():
    token = request.cookies.get('token')
    if not token:
        return None
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return get_user_by_id(data['uid'])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        user = get_current_user()
        if not user:
            if request.is_json:
                return jsonify({'error': 'Not authenticated'}), 401
            return redirect('/login')
        return f(user, *args, **kwargs)
    return wrap

def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        key = request.args.get('admin_key') or request.headers.get('X-Admin-Key')
        if key != ADMIN_KEY:
            return jsonify({'error': 'Unauthorized'}), 403
        return f(*args, **kwargs)
    return wrap

# ============================================================
# AUTH ROUTES
# ============================================================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html', ref=request.args.get('ref', ''))

    data = request.form if request.form else request.json
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    ref_code = data.get('ref_code') or request.args.get('ref') or ''

    if not email or not password:
        return render_template('register.html', error='Email and password required', ref=ref_code)
    if len(password) < 6:
        return render_template('register.html', error='Password must be at least 6 characters', ref=ref_code)

    existing = get_user_by_email(email)
    if existing:
        return render_template('register.html', error='Email already registered', ref=ref_code)

    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    uid = create_user(email, pw_hash, ref_code if ref_code else None)

    # Credit affiliate click
    if ref_code:
        aff = get_affiliate_by_ref(ref_code)
        if aff:
            conn = get_db()
            conn.execute("UPDATE affiliates SET total_clicks=total_clicks+1 WHERE ref_code=?", (ref_code,))
            conn.commit()
            conn.close()

    resp = make_response(redirect('/dashboard'))
    resp.set_cookie('token', make_token(uid), max_age=30*86400, httponly=True, samesite='Lax')
    return resp

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    data = request.form if request.form else request.json
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    user = get_user_by_email(email)
    if not user or not bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
        return render_template('login.html', error='Invalid email or password')

    resp = make_response(redirect('/dashboard'))
    resp.set_cookie('token', make_token(user['id']), max_age=30*86400, httponly=True, samesite='Lax')
    return resp

@app.route('/logout')
def logout():
    resp = make_response(redirect('/login'))
    resp.delete_cookie('token')
    return resp

# ============================================================
# DASHBOARD
# ============================================================
@app.route('/dashboard')
@login_required
def dashboard(user):
    # Check subscription expiry
    if user['sub_status'] in ('active', 'trial') and user['sub_expires']:
        if datetime.fromisoformat(user['sub_expires']) < datetime.utcnow():
            update_user(user['id'], sub_status='expired')
            user = get_user_by_id(user['id'])

    trades = get_user_trades(user['id'], 100)
    signal = get_latest_signal()
    subs = get_user_subscriptions(user['id'])

    # Stats
    total_trades = len(trades)
    wins = sum(1 for t in trades if t['status'] == 'win')
    losses = sum(1 for t in trades if t['status'] == 'loss')
    total_pnl = sum(t['pnl_usd'] for t in trades)
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

    return render_template('dashboard.html',
        user=user, trades=trades, signal=signal, subs=subs,
        stats={'total': total_trades, 'wins': wins, 'losses': losses,
               'pnl': total_pnl, 'win_rate': win_rate}
    )

# ============================================================
# SETTINGS API
# ============================================================
@app.route('/api/settings/mt5', methods=['POST'])
@login_required
def save_mt5_settings(user):
    data = request.json
    mt5_login = data.get('mt5_login')
    mt5_password = data.get('mt5_password')
    mt5_server = data.get('mt5_server')

    if not all([mt5_login, mt5_password, mt5_server]):
        return jsonify({'error': 'All MT5 fields required'}), 400

    update_user(user['id'],
        mt5_login=int(mt5_login),
        mt5_password_enc=encrypt(mt5_password),
        mt5_server=mt5_server
    )
    return jsonify({'success': True, 'message': 'MT5 settings saved'})

@app.route('/api/settings/mt5/test', methods=['POST'])
@login_required
def test_mt5_connection(user):
    data = request.json
    mt5_login = data.get('mt5_login') or user['mt5_login']
    mt5_password = data.get('mt5_password')
    mt5_server = data.get('mt5_server') or user['mt5_server']

    if not mt5_password and user['mt5_password_enc']:
        mt5_password = decrypt(user['mt5_password_enc'])

    if not all([mt5_login, mt5_password, mt5_server]):
        return jsonify({'error': 'MT5 credentials incomplete'}), 400

    try:
        r = requests.post(f"{WINDOWS_VPS}/test-connection", json={
            'login': int(mt5_login), 'password': mt5_password, 'server': mt5_server
        }, headers={'X-API-Key': WINDOWS_API_KEY}, timeout=30)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({'error': f'Could not reach trading server: {e}'}), 503

@app.route('/api/settings/risk', methods=['POST'])
@login_required
def save_risk_settings(user):
    data = request.json
    update_user(user['id'],
        risk_per_trade=float(data.get('risk_per_trade', 100)),
        min_lot=float(data.get('min_lot', 0.01)),
        max_lot=float(data.get('max_lot', 5.0))
    )
    return jsonify({'success': True, 'message': 'Risk settings saved'})

# ============================================================
# FREE TRIAL
# ============================================================
@app.route('/api/trial/activate', methods=['POST'])
@login_required
def activate_trial(user):
    if user['free_trial_used']:
        return jsonify({'error': 'Free trial already used on this account'}), 400

    if user['sub_status'] == 'active':
        return jsonify({'error': 'You already have an active subscription'}), 400

    if not user['mt5_login'] or not user['mt5_password_enc']:
        return jsonify({'error': 'Please save your MT5 credentials first'}), 400

    # Get MT5 account ID via Windows VPS
    mt5_password = decrypt(user['mt5_password_enc'])
    try:
        r = requests.post(f"{WINDOWS_VPS}/test-connection", json={
            'login': user['mt5_login'], 'password': mt5_password, 'server': user['mt5_server']
        }, headers={'X-API-Key': WINDOWS_API_KEY}, timeout=30)
        result = r.json()
        if not result.get('success'):
            return jsonify({'error': f"MT5 connection failed: {result.get('error', 'Unknown')}"}), 400
        account_id = str(result.get('account_id', user['mt5_login']))
    except Exception as e:
        return jsonify({'error': f'Trading server unavailable: {e}'}), 503

    # Check fingerprint
    existing = check_fingerprint(account_id)
    if existing:
        return jsonify({'error': 'This MT5 account has already been used for a free trial'}), 400

    # Activate trial
    store_fingerprint(account_id, user['id'], request.remote_addr)
    expires = (datetime.utcnow() + timedelta(days=7)).isoformat()
    update_user(user['id'],
        sub_status='trial',
        sub_expires=expires,
        free_trial_used=1,
        mt5_account_id=account_id
    )

    return jsonify({
        'success': True,
        'message': 'Free trial activated! You get 3 free trades placed automatically.',
        'expires': expires
    })

# ============================================================
# BITCOIN PAYMENTS (Crypto-only)
# ============================================================
@app.route('/api/pay/btc/init', methods=['POST'])
@login_required
def btc_init(user):
    # Get BTC price
    try:
        r = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd', timeout=10)
        btc_price = r.json()['bitcoin']['usd']
    except Exception:
        return jsonify({'error': 'Could not fetch BTC price'}), 503

    # Add unique micro-offset (1-999 satoshis) so each payment amount is unique and trackable
    import hashlib
    order_id = new_id()
    offset_hash = int(hashlib.sha256(order_id.encode()).hexdigest()[:6], 16) % 999 + 1
    micro_offset = offset_hash / 1e8  # 1-999 satoshis
    btc_amount = round(97.0 / btc_price + micro_offset, 8)

    # Store pending subscription
    conn = get_db()
    conn.execute(
        """INSERT INTO subscriptions (id, user_id, amount, payment_method, btc_address, btc_amount,
           start_date, end_date, status, created_at)
           VALUES (?,?,97.0,'bitcoin',?,?,?,?,'pending',?)""",
        (order_id, user['id'], BTC_WALLET, btc_amount,
         datetime.utcnow().isoformat(), (datetime.utcnow() + timedelta(days=SUBSCRIPTION_DAYS)).isoformat(),
         datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'order_id': order_id,
        'btc_address': BTC_WALLET,
        'btc_amount': btc_amount,
        'btc_price': btc_price,
        'usd_amount': 97.0
    })

@app.route('/api/pay/btc/check', methods=['POST'])
@login_required
def btc_check(user):
    data = request.json
    order_id = data.get('order_id')

    conn = get_db()
    sub = conn.execute("SELECT * FROM subscriptions WHERE id=? AND user_id=?", (order_id, user['id'])).fetchone()
    if not sub:
        conn.close()
        return jsonify({'error': 'Order not found'}), 404

    if sub['status'] == 'active':
        conn.close()
        return jsonify({'success': True, 'status': 'already_confirmed'})

    # Check blockchain
    try:
        r = requests.get(f"https://blockchain.info/q/getreceivedbyaddress/{BTC_WALLET}", timeout=15)
        received_satoshi = int(r.text)
        received_btc = received_satoshi / 1e8
    except Exception:
        conn.close()
        return jsonify({'error': 'Could not check blockchain'}), 503

    expected = sub['btc_amount']
    if received_btc >= expected * 0.98:  # 2% tolerance
        now = datetime.utcnow()
        end_date = now + timedelta(days=SUBSCRIPTION_DAYS)
        conn.execute("UPDATE subscriptions SET status='active' WHERE id=?", (order_id,))
        conn.execute(
            "UPDATE users SET sub_status='active', sub_expires=? WHERE id=?",
            (end_date.isoformat(), user['id'])
        )
        conn.commit()
        conn.close()

        if user['ref_code']:
            credit_affiliate(user['ref_code'], 97.0)

        return jsonify({'success': True, 'status': 'confirmed'})

    conn.close()
    return jsonify({'success': False, 'status': 'pending', 'received': received_btc, 'expected': expected})

# ============================================================
# TRADE HISTORY API
# ============================================================
@app.route('/api/trades')
@login_required
def api_trades(user):
    trades = get_user_trades(user['id'], 200)
    return jsonify([dict(t) for t in trades])

@app.route('/api/trades/csv')
@login_required
def export_trades_csv(user):
    trades = get_user_trades(user['id'], 10000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Direction', 'Entry', 'SL', 'TP', 'Lot', 'Risk $', 'Status', 'P&L $'])
    for t in trades:
        writer.writerow([t['trade_date'], t['direction'], t['entry'], t['sl'], t['tp'],
                         t['lot'], t['risk_usd'], t['status'], t['pnl_usd']])
    return Response(output.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=xaubot_trades.csv'})

# ============================================================
# ADMIN
# ============================================================
@app.route('/api/admin/stats')
@admin_required
def admin_stats():
    return jsonify(get_admin_stats())

@app.route('/api/admin/users')
@admin_required
def admin_users():
    conn = get_db()
    users = conn.execute(
        "SELECT id, email, sub_status, sub_expires, mt5_login, mt5_server, risk_per_trade, created_at FROM users ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return jsonify([dict(u) for u in users])

@app.route('/api/admin/payments')
@admin_required
def admin_payments():
    conn = get_db()
    payments = conn.execute(
        """SELECT s.*, u.email FROM subscriptions s
           JOIN users u ON s.user_id = u.id
           ORDER BY s.created_at DESC LIMIT 100"""
    ).fetchall()
    conn.close()
    return jsonify([dict(p) for p in payments])

@app.route('/api/admin/trigger-trades', methods=['POST'])
@admin_required
def admin_trigger_trades():
    try:
        r = requests.post(f"{WINDOWS_VPS}/execute-trades",
                          headers={'X-API-Key': WINDOWS_API_KEY}, timeout=120)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 503

# ============================================================
# PUBLIC RESULTS PAGE
# ============================================================
@app.route('/results')
def public_results():
    conn = get_db()

    # Get all signals
    signals = conn.execute(
        "SELECT * FROM signals ORDER BY trade_date DESC"
    ).fetchall()

    # Aggregate trade stats (across all users, per signal)
    # Use one result per signal_id to avoid counting duplicates from multiple users
    agg = conn.execute("""
        SELECT
            COUNT(DISTINCT signal_id) as total_signals,
            SUM(CASE WHEN status='win' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN status='loss' THEN 1 ELSE 0 END) as losses,
            AVG(CASE WHEN status='win' THEN pnl_usd END) as avg_win,
            AVG(CASE WHEN status='loss' THEN pnl_usd END) as avg_loss
        FROM (
            SELECT signal_id, status, pnl_usd,
                   ROW_NUMBER() OVER (PARTITION BY signal_id ORDER BY id) as rn
            FROM trades WHERE signal_id IS NOT NULL AND status IN ('win','loss')
        ) sub WHERE rn = 1
    """).fetchone()

    # Monthly breakdown
    monthly = conn.execute("""
        SELECT
            strftime('%Y-%m', t.trade_date) as month,
            COUNT(DISTINCT t.signal_id) as trades,
            SUM(CASE WHEN t.status='win' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN t.status='loss' THEN 1 ELSE 0 END) as losses,
            SUM(t.pnl_usd) as pnl
        FROM (
            SELECT signal_id, trade_date, status, pnl_usd,
                   ROW_NUMBER() OVER (PARTITION BY signal_id ORDER BY id) as rn
            FROM trades WHERE signal_id IS NOT NULL AND status IN ('win','loss')
        ) t WHERE t.rn = 1
        GROUP BY month ORDER BY month DESC
    """).fetchall()

    conn.close()

    total_signals = agg['total_signals'] if agg['total_signals'] else 0
    wins = agg['wins'] if agg['wins'] else 0
    losses = agg['losses'] if agg['losses'] else 0
    avg_win = agg['avg_win'] if agg['avg_win'] else 0
    avg_loss = agg['avg_loss'] if agg['avg_loss'] else 0
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    total_pnl = sum(m['pnl'] for m in monthly) if monthly else 0

    return render_template('results.html',
        signals=signals,
        monthly=monthly,
        stats={
            'total_signals': len(signals),
            'total_traded': wins + losses,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'total_pnl': total_pnl
        }
    )

# ============================================================
# LANDING / REFERRAL
# ============================================================
@app.route('/')
def homepage():
    return render_template('landing.html')

@app.route('/ref/<ref_code>')
def track_referral(ref_code):
    aff = get_affiliate_by_ref(ref_code)
    if aff:
        conn = get_db()
        conn.execute(
            "INSERT INTO clicks (affiliate_id, ip, user_agent, timestamp) VALUES (?,?,?,?)",
            (aff['id'], request.remote_addr, request.user_agent.string, datetime.utcnow().isoformat())
        )
        conn.execute("UPDATE affiliates SET total_clicks=total_clicks+1 WHERE id=?", (aff['id'],))
        conn.commit()
        conn.close()
    resp = make_response(redirect(f'/register?ref={ref_code}'))
    resp.set_cookie('xaubot_ref', ref_code, max_age=30*86400)
    return resp

# ============================================================
# BLOG
# ============================================================
@app.route('/blog')
@app.route('/blog/automated-gold-trading-guide-2026')
def blog_post():
    return render_template('blog_post.html')

# ============================================================
# AFFILIATE DASHBOARD
# ============================================================
@app.route('/affiliate', methods=['GET'])
def affiliate_landing():
    return render_template('affiliate.html')

@app.route('/affiliate/register', methods=['GET', 'POST'])
def affiliate_register():
    if request.method == 'GET':
        return render_template('affiliate_register.html')

    data = request.form
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    btc_address = (data.get('btc_address') or '').strip()

    if not name or not email or not password:
        return render_template('affiliate_register.html', error='All fields are required')
    if len(password) < 6:
        return render_template('affiliate_register.html', error='Password must be at least 6 characters')

    conn = get_db()
    existing = conn.execute("SELECT id FROM affiliates WHERE email=?", (email,)).fetchone()
    if existing:
        conn.close()
        return render_template('affiliate_register.html', error='Email already registered as affiliate')

    import secrets, string
    ref_code = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    aff_id = new_id()

    conn.execute(
        """INSERT INTO affiliates (id, name, email, ref_code, password_hash, btc_payout_address, created_at)
           VALUES (?,?,?,?,?,?,?)""",
        (aff_id, name, email, ref_code, pw_hash, btc_address, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

    resp = make_response(redirect('/affiliate/dashboard'))
    aff_token = jwt.encode({'aff_id': aff_id, 'exp': datetime.utcnow() + timedelta(days=30)}, SECRET_KEY, algorithm='HS256')
    resp.set_cookie('aff_token', aff_token, max_age=30*86400, httponly=True, samesite='Lax')
    return resp

@app.route('/affiliate/login', methods=['GET', 'POST'])
def affiliate_login():
    if request.method == 'GET':
        return render_template('affiliate_login.html')

    data = request.form
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    conn = get_db()
    aff = conn.execute("SELECT * FROM affiliates WHERE email=?", (email,)).fetchone()
    conn.close()

    if not aff or not aff['password_hash'] or not bcrypt.checkpw(password.encode(), aff['password_hash'].encode()):
        return render_template('affiliate_login.html', error='Invalid email or password')

    resp = make_response(redirect('/affiliate/dashboard'))
    aff_token = jwt.encode({'aff_id': aff['id'], 'exp': datetime.utcnow() + timedelta(days=30)}, SECRET_KEY, algorithm='HS256')
    resp.set_cookie('aff_token', aff_token, max_age=30*86400, httponly=True, samesite='Lax')
    return resp

def get_current_affiliate():
    token = request.cookies.get('aff_token')
    if not token:
        return None
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        conn = get_db()
        aff = conn.execute("SELECT * FROM affiliates WHERE id=?", (data['aff_id'],)).fetchone()
        conn.close()
        return aff
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

@app.route('/affiliate/dashboard')
def affiliate_dashboard():
    aff = get_current_affiliate()
    if not aff:
        return redirect('/affiliate/login')

    conn = get_db()
    # Get recent clicks
    recent_clicks = conn.execute(
        "SELECT * FROM clicks WHERE affiliate_id=? ORDER BY timestamp DESC LIMIT 20", (aff['id'],)
    ).fetchall()

    # Get referred users (users who signed up with this ref_code)
    referred_users = conn.execute(
        "SELECT id, email, sub_status, created_at FROM users WHERE ref_code=? ORDER BY created_at DESC",
        (aff['ref_code'],)
    ).fetchall()

    conn.close()

    return render_template('affiliate_dashboard.html',
        aff=aff,
        recent_clicks=recent_clicks,
        referred_users=referred_users,
        domain=DOMAIN
    )

@app.route('/affiliate/logout')
def affiliate_logout():
    resp = make_response(redirect('/affiliate/login'))
    resp.delete_cookie('aff_token')
    return resp

# ============================================================
# INIT
# ============================================================
init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
