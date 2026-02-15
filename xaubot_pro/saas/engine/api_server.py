"""XAUBOT Pro SaaS - Windows VPS Internal API"""
import sys, os, json
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from flask import Flask, request, jsonify
import MetaTrader5 as mt5
import threading

app = Flask(__name__)

API_KEY = os.environ.get('WINDOWS_API_KEY', 'xaubot-engine-key')
ALLOWED_IPS = os.environ.get('ALLOWED_IPS', '74.50.87.77,127.0.0.1').split(',')

@app.before_request
def auth_check():
    # IP whitelist
    client_ip = request.remote_addr
    if client_ip not in ALLOWED_IPS and '0.0.0.0' not in ALLOWED_IPS:
        return jsonify({'error': 'IP not allowed'}), 403
    # API key
    key = request.headers.get('X-API-Key', '')
    if key != API_KEY:
        return jsonify({'error': 'Invalid API key'}), 401

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'xaubot-trading-engine'})

@app.route('/test-connection', methods=['POST'])
def test_connection():
    """Test MT5 connection with user credentials"""
    data = request.json
    login = int(data.get('login', 0))
    password = data.get('password', '')
    server = data.get('server', '')

    if not all([login, password, server]):
        return jsonify({'success': False, 'error': 'Missing credentials'}), 400

    try:
        if not mt5.initialize(login=login, password=password, server=server):
            err = mt5.last_error()
            return jsonify({'success': False, 'error': f'MT5 connection failed: {err}'})

        info = mt5.account_info()
        if info is None:
            mt5.shutdown()
            return jsonify({'success': False, 'error': 'Could not get account info'})

        result = {
            'success': True,
            'account_id': info.login,
            'name': info.name,
            'balance': info.balance,
            'equity': info.equity,
            'server': info.server,
            'currency': info.currency,
            'leverage': info.leverage
        }

        mt5.shutdown()
        return jsonify(result)

    except Exception as e:
        try:
            mt5.shutdown()
        except:
            pass
        return jsonify({'success': False, 'error': str(e)})

@app.route('/user-balance', methods=['POST'])
def user_balance():
    """Get live balance for a user's MT5 account"""
    data = request.json
    login = int(data.get('login', 0))
    password = data.get('password', '')
    server = data.get('server', '')

    try:
        if not mt5.initialize(login=login, password=password, server=server):
            return jsonify({'success': False, 'error': f'MT5 init failed: {mt5.last_error()}'})

        info = mt5.account_info()
        positions = mt5.positions_get(symbol="XAUUSD")
        orders = mt5.orders_get(symbol="XAUUSD")

        xaubot_pos = [p for p in (positions or []) if p.magic == 123456]
        xaubot_ords = [o for o in (orders or []) if o.magic == 123456]

        result = {
            'success': True,
            'balance': info.balance if info else 0,
            'equity': info.equity if info else 0,
            'profit': info.profit if info else 0,
            'positions': [{
                'type': 'BUY' if p.type == 0 else 'SELL',
                'volume': p.volume,
                'price_open': p.price_open,
                'profit': p.profit,
                'sl': p.sl,
                'tp': p.tp
            } for p in xaubot_pos],
            'pending_orders': [{
                'type': 'BUY LIMIT' if o.type == 2 else 'SELL LIMIT',
                'volume': o.volume_current,
                'price': o.price_open,
                'sl': o.sl,
                'tp': o.tp
            } for o in xaubot_ords]
        }

        mt5.shutdown()
        return jsonify(result)

    except Exception as e:
        try:
            mt5.shutdown()
        except:
            pass
        return jsonify({'success': False, 'error': str(e)})

@app.route('/execute-trades', methods=['POST'])
def execute_trades():
    """Trigger trade execution for all active subscribers"""
    from engine import generate_signal, execute_all_trades

    # Run in background thread so API returns immediately
    def run():
        signal = generate_signal()
        if signal:
            execute_all_trades(signal)

    t = threading.Thread(target=run, daemon=True)
    t.start()

    return jsonify({'success': True, 'message': 'Trade execution started in background'})

@app.route('/signal/generate', methods=['POST'])
def gen_signal():
    """Generate signal only"""
    from engine import generate_signal
    signal = generate_signal()
    if signal:
        return jsonify({'success': True, 'signal': signal})
    return jsonify({'success': False, 'error': 'No signal generated'})

@app.route('/signal/latest')
def latest_signal():
    """Get the latest signal"""
    from engine import get_db
    conn = get_db()
    row = conn.execute("SELECT * FROM signals ORDER BY trade_date DESC LIMIT 1").fetchone()
    conn.close()
    if row:
        return jsonify({'success': True, 'signal': dict(row)})
    return jsonify({'success': False, 'error': 'No signals found'})

if __name__ == '__main__':
    print("=" * 50)
    print("XAUBOT Pro - Trading Engine API")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5001, debug=False)
