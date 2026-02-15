"""MT5 Trade Worker - Handles a batch of users on a dedicated MT5 terminal"""
import time, os, sys
import MetaTrader5 as mt5

# Strategy constants (hidden)
_F = 0.45
_R = 4.0

def calc_lot(candle_range, risk_per_trade, min_lot=0.01, max_lot=5.0):
    """Dynamic lot sizing based on candle range and user risk setting"""
    risk_per_unit = candle_range * (1 - _F)
    if risk_per_unit <= 0:
        return min_lot
    lot = risk_per_trade / (risk_per_unit * 100)
    return max(min_lot, min(max_lot, round(lot, 2)))

def place_trade_for_user(user_creds, signal, worker_id=0):
    """
    Connect to a user's MT5 account and place the pending order.

    Args:
        user_creds: dict with keys: login, password, server, risk_per_trade, min_lot, max_lot, user_id
        signal: dict with keys: direction, entry, sl, tp, candle_range
        worker_id: which MT5 terminal to use

    Returns:
        dict with result info
    """
    result = {
        'user_id': user_creds['user_id'],
        'status': 'error',
        'mt5_ticket': None,
        'lot': 0,
        'risk_usd': 0,
        'error': None
    }

    # Determine MT5 terminal path
    mt5_path = f"C:\\MT5_Worker_{worker_id}\\terminal64.exe"
    if not os.path.exists(mt5_path):
        # Fallback to default MT5 install
        mt5_path = None

    try:
        # Initialize MT5 connection
        init_kwargs = {
            'login': int(user_creds['login']),
            'password': user_creds['password'],
            'server': user_creds['server']
        }
        if mt5_path:
            init_kwargs['path'] = mt5_path

        if not mt5.initialize(**init_kwargs):
            result['error'] = f"MT5 init failed: {mt5.last_error()}"
            return result

        # Verify account
        info = mt5.account_info()
        if info is None:
            result['error'] = "Could not get account info"
            mt5.shutdown()
            return result

        # Calculate lot size
        lot = calc_lot(
            signal['candle_range'],
            user_creds.get('risk_per_trade', 100),
            user_creds.get('min_lot', 0.01),
            user_creds.get('max_lot', 5.0)
        )

        risk = abs(signal['entry'] - signal['sl'])
        risk_usd = risk * lot * 100

        result['lot'] = lot
        result['risk_usd'] = round(risk_usd, 2)

        # Determine order type
        if signal['direction'] == 'BUY':
            order_type = mt5.ORDER_TYPE_BUY_LIMIT
        else:
            order_type = mt5.ORDER_TYPE_SELL_LIMIT

        # Place pending order
        request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": "XAUUSD",
            "volume": lot,
            "type": order_type,
            "price": signal['entry'],
            "sl": signal['sl'],
            "tp": signal['tp'],
            "deviation": 20,
            "magic": 123456,
            "comment": f"XAUBOT SaaS",
            "type_time": mt5.ORDER_TIME_DAY,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        order_result = mt5.order_send(request)

        if order_result is None:
            result['error'] = f"order_send None: {mt5.last_error()}"
        elif order_result.retcode != mt5.TRADE_RETCODE_DONE:
            # Try alternative fill types
            for fill in [mt5.ORDER_FILLING_RETURN, mt5.ORDER_FILLING_FOK]:
                request["type_filling"] = fill
                order_result = mt5.order_send(request)
                if order_result and order_result.retcode == mt5.TRADE_RETCODE_DONE:
                    break

            if order_result is None or order_result.retcode != mt5.TRADE_RETCODE_DONE:
                result['error'] = f"Order failed: {order_result.retcode if order_result else 'None'} - {order_result.comment if order_result else ''}"
            else:
                result['status'] = 'placed'
                result['mt5_ticket'] = order_result.order
        else:
            result['status'] = 'placed'
            result['mt5_ticket'] = order_result.order

    except Exception as e:
        result['error'] = str(e)
    finally:
        try:
            mt5.shutdown()
        except:
            pass

    return result

def process_batch(args):
    """
    Process a batch of users. Called by multiprocessing.Pool.

    Args:
        args: tuple of (user_list, signal_dict, worker_id)

    Returns:
        list of result dicts
    """
    user_batch, signal, worker_id = args
    results = []

    for user in user_batch:
        result = place_trade_for_user(user, signal, worker_id)
        results.append(result)
        time.sleep(2)  # Brief pause between users

    return results
