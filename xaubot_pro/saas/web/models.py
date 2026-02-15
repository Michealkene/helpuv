"""XAUBOT Pro SaaS - Database Models"""
import sqlite3, os, uuid
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'xaubot_saas.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        mt5_login INTEGER,
        mt5_password_enc TEXT,
        mt5_server TEXT,
        mt5_account_id TEXT,
        risk_per_trade REAL DEFAULT 100,
        min_lot REAL DEFAULT 0.01,
        max_lot REAL DEFAULT 5.0,
        sub_status TEXT DEFAULT 'none',
        sub_expires TEXT,
        free_trial_used INTEGER DEFAULT 0,
        trial_trade_count INTEGER DEFAULT 0,
        ref_code TEXT,
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS mt5_fingerprints (
        mt5_account_id TEXT PRIMARY KEY,
        user_id TEXT,
        ip TEXT,
        used_at TEXT
    );

    CREATE TABLE IF NOT EXISTS subscriptions (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        amount REAL DEFAULT 97.0,
        payment_method TEXT,
        paystack_ref TEXT,
        btc_address TEXT,
        btc_amount REAL,
        btc_tx TEXT,
        start_date TEXT,
        end_date TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_date TEXT UNIQUE,
        direction TEXT,
        entry REAL,
        sl REAL,
        tp REAL,
        candle_range REAL,
        candle_time TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        signal_id INTEGER,
        trade_date TEXT,
        direction TEXT,
        entry REAL,
        sl REAL,
        tp REAL,
        lot REAL,
        risk_usd REAL,
        mt5_ticket INTEGER,
        status TEXT DEFAULT 'pending',
        pnl_usd REAL DEFAULT 0,
        error TEXT,
        created_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (signal_id) REFERENCES signals(id)
    );

    CREATE TABLE IF NOT EXISTS affiliates (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        password_hash TEXT,
        ref_code TEXT UNIQUE,
        commission_rate REAL DEFAULT 0.20,
        total_clicks INTEGER DEFAULT 0,
        total_sales INTEGER DEFAULT 0,
        total_earned REAL DEFAULT 0,
        balance REAL DEFAULT 0,
        btc_payout_address TEXT,
        created_at TEXT,
        active INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS clicks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        affiliate_id TEXT,
        ip TEXT,
        user_agent TEXT,
        timestamp TEXT
    );
    """)
    conn.commit()

    # Migrations for existing databases
    try:
        conn.execute("ALTER TABLE affiliates ADD COLUMN password_hash TEXT")
        conn.commit()
    except Exception:
        pass  # Column already exists

    conn.close()

def new_id():
    return uuid.uuid4().hex[:12]

# --- User helpers ---
def create_user(email, password_hash, ref_code=None):
    uid = new_id()
    conn = get_db()
    conn.execute(
        "INSERT INTO users (id, email, password_hash, ref_code, created_at) VALUES (?,?,?,?,?)",
        (uid, email.lower().strip(), password_hash, ref_code, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()
    return uid

def get_user_by_email(email):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE email=?", (email.lower().strip(),)).fetchone()
    conn.close()
    return row

def get_user_by_id(uid):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    conn.close()
    return row

def update_user(uid, **kwargs):
    conn = get_db()
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [uid]
    conn.execute(f"UPDATE users SET {sets} WHERE id=?", vals)
    conn.commit()
    conn.close()

# --- Subscription helpers ---
def create_subscription(user_id, payment_method, start_date, end_date, **kwargs):
    sid = new_id()
    conn = get_db()
    conn.execute(
        """INSERT INTO subscriptions (id, user_id, payment_method, start_date, end_date, status, created_at,
           paystack_ref, btc_address, btc_amount, btc_tx)
           VALUES (?,?,?,?,?,'active',?,?,?,?,?)""",
        (sid, user_id, payment_method, start_date, end_date, datetime.utcnow().isoformat(),
         kwargs.get('paystack_ref'), kwargs.get('btc_address'), kwargs.get('btc_amount'), kwargs.get('btc_tx'))
    )
    conn.commit()
    conn.close()
    return sid

def get_user_subscriptions(user_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM subscriptions WHERE user_id=? ORDER BY created_at DESC", (user_id,)
    ).fetchall()
    conn.close()
    return rows

# --- Signal helpers ---
def save_signal(trade_date, direction, entry, sl, tp, candle_range, candle_time):
    conn = get_db()
    conn.execute(
        """INSERT OR REPLACE INTO signals (trade_date, direction, entry, sl, tp, candle_range, candle_time, status, created_at)
           VALUES (?,?,?,?,?,?,?,'ready',?)""",
        (trade_date, direction, entry, sl, tp, candle_range, candle_time, datetime.utcnow().isoformat())
    )
    conn.commit()
    sid = conn.execute("SELECT id FROM signals WHERE trade_date=?", (trade_date,)).fetchone()['id']
    conn.close()
    return sid

def get_latest_signal():
    conn = get_db()
    row = conn.execute("SELECT * FROM signals ORDER BY trade_date DESC LIMIT 1").fetchone()
    conn.close()
    return row

# --- Trade helpers ---
def log_trade(user_id, signal_id, trade_date, direction, entry, sl, tp, lot, risk_usd, mt5_ticket=None, status='placed', error=None):
    conn = get_db()
    conn.execute(
        """INSERT INTO trades (user_id, signal_id, trade_date, direction, entry, sl, tp, lot, risk_usd,
           mt5_ticket, status, error, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (user_id, signal_id, trade_date, direction, entry, sl, tp, lot, risk_usd,
         mt5_ticket, status, error, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

def get_user_trades(user_id, limit=50):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM trades WHERE user_id=? ORDER BY trade_date DESC LIMIT ?", (user_id, limit)
    ).fetchall()
    conn.close()
    return rows

def get_active_subscribers():
    conn = get_db()
    rows = conn.execute(
        """SELECT * FROM users WHERE sub_status IN ('active','trial')
           AND mt5_login IS NOT NULL AND mt5_password_enc IS NOT NULL"""
    ).fetchall()
    conn.close()
    return rows

# --- Fingerprint helpers ---
def check_fingerprint(mt5_account_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM mt5_fingerprints WHERE mt5_account_id=?", (str(mt5_account_id),)).fetchone()
    conn.close()
    return row

def store_fingerprint(mt5_account_id, user_id, ip):
    conn = get_db()
    conn.execute(
        "INSERT OR IGNORE INTO mt5_fingerprints (mt5_account_id, user_id, ip, used_at) VALUES (?,?,?,?)",
        (str(mt5_account_id), user_id, ip, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

# --- Affiliate helpers ---
def get_affiliate_by_ref(ref_code):
    conn = get_db()
    row = conn.execute("SELECT * FROM affiliates WHERE ref_code=? AND active=1", (ref_code,)).fetchone()
    conn.close()
    return row

def credit_affiliate(ref_code, amount):
    conn = get_db()
    aff = conn.execute("SELECT * FROM affiliates WHERE ref_code=?", (ref_code,)).fetchone()
    if aff:
        commission = amount * aff['commission_rate']
        conn.execute(
            """UPDATE affiliates SET total_sales=total_sales+1, total_earned=total_earned+?,
               balance=balance+? WHERE ref_code=?""",
            (commission, commission, ref_code)
        )
        conn.commit()
    conn.close()

# --- Stats ---
def get_admin_stats():
    conn = get_db()
    stats = {
        'total_users': conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        'active_subs': conn.execute("SELECT COUNT(*) FROM users WHERE sub_status='active'").fetchone()[0],
        'trial_users': conn.execute("SELECT COUNT(*) FROM users WHERE sub_status='trial'").fetchone()[0],
        'total_trades': conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0],
        'total_revenue': conn.execute("SELECT COALESCE(SUM(amount),0) FROM subscriptions WHERE status='active'").fetchone()[0],
    }
    conn.close()
    return stats
