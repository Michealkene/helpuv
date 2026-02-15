"""XAUBOT Pro SaaS - Trading Engine (Signal Generator + Parallel Executor)"""
import sys, os, time, json, sqlite3, multiprocessing
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta, time as dtime

# Add parent path for shared encryption
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'web'))
from encryption import decrypt

# Config
DATA_LOGIN = int(os.environ.get('MT5_DATA_LOGIN', '5046171682'))
DATA_PASSWORD = os.environ.get('MT5_DATA_PASSWORD', '2i_hYuTw')
DATA_SERVER = os.environ.get('MT5_DATA_SERVER', 'MetaQuotes-Demo')
DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(__file__), '..', 'web', 'xaubot_saas.db'))
NUM_WORKERS = int(os.environ.get('NUM_WORKERS', '8'))
SYMBOL = "XAUUSD"

# Strategy constants (hidden)
_F = 0.45
_R = 4.0
_L = 6  # lookback

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def is_dst(dt):
    y = dt.year
    m3 = datetime(y, 3, 31)
    while m3.weekday() != 6: m3 -= timedelta(days=1)
    o10 = datetime(y, 10, 31)
    while o10.weekday() != 6: o10 -= timedelta(days=1)
    return m3.date() <= dt.date() <= o10.date()

def asian_times(dt):
    if is_dst(dt):
        return dtime(1, 0), dtime(4, 0)
    else:
        return dtime(0, 0), dtime(3, 0)

# ============================================================
# SIGNAL GENERATOR
# ============================================================
def generate_signal():
    """Analyze Asian session and generate today's trading signal"""
    print("=" * 60)
    print(f"SIGNAL GENERATOR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Connect to MT5 data account
    if not mt5.initialize(login=DATA_LOGIN, password=DATA_PASSWORD, server=DATA_SERVER):
        print(f"[ERROR] MT5 init failed: {mt5.last_error()}")
        return None

    today = datetime.now()

    # Skip weekends
    if today.weekday() >= 5:
        print("[SKIP] Weekend - no signal")
        mt5.shutdown()
        return None

    st, et = asian_times(today)
    print(f"Asian session: {st} - {et} ({'DST' if is_dst(today) else 'Standard'})")

    session_start = datetime.combine(today.date(), st)
    session_end = datetime.combine(today.date(), et)

    # Get M15 candles
    rates = mt5.copy_rates_range(SYMBOL, mt5.TIMEFRAME_M15, session_start, session_end)
    mt5.shutdown()

    if rates is None or len(rates) == 0:
        print("[SKIP] No Asian session candles found")
        return None

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df['range'] = df['high'] - df['low']

    print(f"Found {len(df)} candles")

    if len(df) < 2:
        print("[SKIP] Not enough candles (need >= 2)")
        return None

    # Find biggest candle in lookback
    lookback_df = df.iloc[-_L-1:-1] if len(df) > _L else df
    if len(lookback_df) == 0:
        print("[SKIP] No candles in lookback")
        return None

    candle = lookback_df.loc[lookback_df['range'].idxmax()]
    rng = candle['high'] - candle['low']

    if rng == 0:
        print("[SKIP] Zero range candle")
        return None

    bullish = candle['close'] > candle['open']

    # Calculate levels
    if bullish:
        direction = "BUY"
        entry = round(candle['high'] - rng * _F, 2)
        sl = round(candle['low'], 2)
        risk = entry - sl
        tp = round(entry + risk * _R, 2)
    else:
        direction = "SELL"
        entry = round(candle['low'] + rng * _F, 2)
        sl = round(candle['high'], 2)
        risk = sl - entry
        tp = round(entry - risk * _R, 2)

    signal = {
        'trade_date': today.strftime('%Y-%m-%d'),
        'direction': direction,
        'entry': entry,
        'sl': sl,
        'tp': tp,
        'candle_range': round(rng, 2),
        'candle_time': pd.to_datetime(candle['time']).strftime('%H:%M')
    }

    print(f"\nSIGNAL: {direction}")
    print(f"  Entry: {entry:.2f} | SL: {sl:.2f} | TP: {tp:.2f}")
    print(f"  Range: {rng:.2f} | Candle: {signal['candle_time']}")

    # Save to database
    conn = get_db()
    conn.execute(
        """INSERT OR REPLACE INTO signals (trade_date, direction, entry, sl, tp, candle_range, candle_time, status, created_at)
           VALUES (?,?,?,?,?,?,?,'ready',?)""",
        (signal['trade_date'], direction, entry, sl, tp, rng, signal['candle_time'], datetime.utcnow().isoformat())
    )
    conn.commit()
    signal_id = conn.execute("SELECT id FROM signals WHERE trade_date=?", (signal['trade_date'],)).fetchone()['id']
    conn.close()

    signal['id'] = signal_id
    print(f"\nSignal saved (ID: {signal_id})")
    return signal

# ============================================================
# PARALLEL TRADE EXECUTOR
# ============================================================
def execute_all_trades(signal=None):
    """Execute trades for all active subscribers in parallel"""
    from worker import process_batch

    if signal is None:
        conn = get_db()
        row = conn.execute("SELECT * FROM signals WHERE trade_date=? AND status='ready'",
                          (datetime.now().strftime('%Y-%m-%d'),)).fetchone()
        conn.close()
        if not row:
            print("[ERROR] No signal for today")
            return {'error': 'No signal', 'results': []}
        signal = dict(row)

    print("\n" + "=" * 60)
    print("TRADE EXECUTOR - PARALLEL MODE")
    print("=" * 60)

    # Get active subscribers
    conn = get_db()
    users = conn.execute(
        """SELECT id, mt5_login, mt5_password_enc, mt5_server, risk_per_trade, min_lot, max_lot,
                  sub_status, trial_trade_count
           FROM users
           WHERE sub_status IN ('active','trial')
           AND mt5_login IS NOT NULL AND mt5_password_enc IS NOT NULL"""
    ).fetchall()
    conn.close()

    if not users:
        print("[SKIP] No active subscribers with MT5 credentials")
        return {'results': [], 'total': 0}

    print(f"Active subscribers: {len(users)}")

    # Prepare user credentials (decrypt passwords)
    user_list = []
    for u in users:
        # Skip trial users who already got their trade
        if u['sub_status'] == 'trial' and u['trial_trade_count'] >= 3:
            continue

        try:
            password = decrypt(u['mt5_password_enc'])
        except Exception as e:
            print(f"  [WARN] Cannot decrypt password for user {u['id']}: {e}")
            continue

        user_list.append({
            'user_id': u['id'],
            'login': u['mt5_login'],
            'password': password,
            'server': u['mt5_server'],
            'risk_per_trade': u['risk_per_trade'] or 100,
            'min_lot': u['min_lot'] or 0.01,
            'max_lot': u['max_lot'] or 5.0,
            'is_trial': u['sub_status'] == 'trial'
        })

    if not user_list:
        print("[SKIP] No eligible users after filtering")
        return {'results': [], 'total': 0}

    print(f"Eligible users: {len(user_list)}")

    # Split into batches for parallel workers
    workers = min(NUM_WORKERS, len(user_list))
    batch_size = max(1, len(user_list) // workers)
    batches = []
    for i in range(workers):
        start = i * batch_size
        end = start + batch_size if i < workers - 1 else len(user_list)
        if start < len(user_list):
            batches.append((user_list[start:end], signal, i + 1))

    print(f"Workers: {workers} | Batch sizes: {[len(b[0]) for b in batches]}")
    print(f"Starting parallel execution...")

    start_time = time.time()

    # Execute in parallel
    if workers > 1:
        with multiprocessing.Pool(workers) as pool:
            batch_results = pool.map(process_batch, batches)
    else:
        batch_results = [process_batch(batches[0])]

    # Flatten results
    all_results = []
    for batch in batch_results:
        all_results.extend(batch)

    elapsed = time.time() - start_time

    # Save results to database
    conn = get_db()
    placed = 0
    errors = 0
    for r in all_results:
        conn.execute(
            """INSERT INTO trades (user_id, signal_id, trade_date, direction, entry, sl, tp,
               lot, risk_usd, mt5_ticket, status, error, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (r['user_id'], signal.get('id'), signal['trade_date'], signal['direction'],
             signal['entry'], signal['sl'], signal['tp'], r['lot'], r['risk_usd'],
             r['mt5_ticket'], r['status'], r['error'], datetime.utcnow().isoformat())
        )

        if r['status'] == 'placed':
            placed += 1
            # Increment trial trade count if trial user
            user_data = next((u for u in user_list if u['user_id'] == r['user_id']), None)
            if user_data and user_data.get('is_trial'):
                conn.execute("UPDATE users SET trial_trade_count=trial_trade_count+1 WHERE id=?", (r['user_id'],))
        else:
            errors += 1

    conn.commit()
    conn.close()

    print(f"\n{'=' * 60}")
    print(f"EXECUTION COMPLETE in {elapsed:.1f}s")
    print(f"  Placed: {placed} | Errors: {errors} | Total: {len(all_results)}")
    print(f"{'=' * 60}")

    return {
        'total': len(all_results),
        'placed': placed,
        'errors': errors,
        'elapsed': round(elapsed, 1),
        'results': [{'user_id': r['user_id'], 'status': r['status'], 'ticket': r['mt5_ticket'], 'error': r['error']} for r in all_results]
    }

# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='XAUBOT Pro Trading Engine')
    parser.add_argument('--signal-only', action='store_true', help='Only generate signal')
    parser.add_argument('--execute-only', action='store_true', help='Only execute trades (signal must exist)')
    args = parser.parse_args()

    if args.signal_only:
        generate_signal()
    elif args.execute_only:
        execute_all_trades()
    else:
        # Full flow: generate signal then execute
        signal = generate_signal()
        if signal:
            execute_all_trades(signal)
        else:
            print("\nNo signal generated - no trades to place")
