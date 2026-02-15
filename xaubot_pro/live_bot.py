"""
ASIAN SESSION XAUUSD FIBONACCI LIVE TRADING BOT
================================================
Strategy: Find biggest candle in Asian session, enter at 45% Fibo retracement
Direction: Follow the candle direction (bullish = BUY, bearish = SELL)
SL: Opposite end of the biggest candle
TP: 4.0 R:R from entry
Lot Sizing: Dynamic ($80-120 risk per trade, targeting $100)

This bot runs continuously. It:
1. Waits for Asian session to complete
2. Identifies the biggest candle
3. Calculates entry, SL, TP
4. Places a pending order (BUY LIMIT or SELL LIMIT)
5. Monitors the trade until TP or SL

Usage:
  python live_bot.py              # Run normally
  python live_bot.py --dry-run    # Simulate without placing real orders
"""

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta, time
import time as time_module
import json
import os
import sys
import logging

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# ================= CONFIG =================

SYMBOL = "XAUUSD"
TIMEFRAME = mt5.TIMEFRAME_M15

# Asian session in GMT (with DST adjustment)
ASIAN_START_WINTER = time(0, 0)
ASIAN_END_WINTER = time(3, 0)
ASIAN_START_SUMMER = time(1, 0)
ASIAN_END_SUMMER = time(4, 0)

LOOKBACK_CANDLES = 6

FIBO_RETRACEMENT = 0.45  # 45% retracement entry
RR_RATIO = 4.0           # Risk:Reward ratio
SPREAD_PIPS = 0           # Spread adjustment (set to 0 for now)

# Dynamic lot sizing
TARGET_RISK_DOLLARS = 100
MIN_LOT = 0.01
MAX_LOT = 5.0

# MT5 credentials - UPDATE THESE FOR YOUR LIVE/DEMO ACCOUNT
MT5_LOGIN = 5046171682
MT5_PASSWORD = "2i_hYuTw"
MT5_SERVER = "MetaQuotes-Demo"

# Bot settings
CHECK_INTERVAL_SECONDS = 30   # How often to check for fills/exits
LOG_FILE = "live_bot.log"
TRADE_HISTORY_FILE = "live_trades.json"
DRY_RUN = "--dry-run" in sys.argv

# =========================================

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("LiveBot")


def is_dst(date):
    """Check if date is in DST period (US/Europe: last Sunday March to last Sunday October)"""
    year = date.year
    march_last = datetime(year, 3, 31)
    while march_last.weekday() != 6:
        march_last -= timedelta(days=1)
    oct_last = datetime(year, 10, 31)
    while oct_last.weekday() != 6:
        oct_last -= timedelta(days=1)
    return march_last.date() <= date <= oct_last.date()


def get_asian_session_times(date):
    """Get Asian session start/end times for a given date"""
    if is_dst(date):
        return (datetime.combine(date, ASIAN_START_SUMMER),
                datetime.combine(date, ASIAN_END_SUMMER))
    else:
        return (datetime.combine(date, ASIAN_START_WINTER),
                datetime.combine(date, ASIAN_END_WINTER))


def connect_mt5():
    """Initialize MT5 connection"""
    if not mt5.initialize(login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER):
        log.error(f"MT5 initialization failed: {mt5.last_error()}")
        return False
    info = mt5.account_info()
    log.info(f"Connected to MT5 | Account: {info.login} | Server: {info.server} | Balance: ${info.balance:.2f}")
    return True


def calculate_dynamic_lot(candle_range):
    """Calculate lot size so each trade risks ~$100"""
    risk_portion = 1 - FIBO_RETRACEMENT  # 0.55 of candle range is risk
    risk_per_unit = candle_range * risk_portion
    if risk_per_unit <= 0:
        return MIN_LOT
    lot = TARGET_RISK_DOLLARS / (risk_per_unit * 100)
    lot = round(lot, 2)
    lot = max(MIN_LOT, min(MAX_LOT, lot))
    return lot


def get_biggest_candle(df, lookback=6):
    """Find the biggest candle in the lookback period"""
    if df is None or len(df) < 2:
        return None
    df = df.copy()
    df['range'] = df['high'] - df['low']
    if len(df) > lookback:
        lookback_df = df.iloc[-lookback-1:-1]
    else:
        lookback_df = df
    if len(lookback_df) == 0:
        return None
    biggest_idx = lookback_df['range'].idxmax()
    return lookback_df.loc[biggest_idx]


def get_asian_session_data(date):
    """Get candles for Asian session on a specific date"""
    start_dt, end_dt = get_asian_session_times(date)
    rates = mt5.copy_rates_range(SYMBOL, TIMEFRAME, start_dt, end_dt)
    if rates is None or len(rates) == 0:
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df


def calculate_trade_setup(biggest_candle):
    """Calculate entry, SL, TP from the biggest candle"""
    is_bullish = biggest_candle['close'] > biggest_candle['open']
    candle_high = biggest_candle['high']
    candle_low = biggest_candle['low']
    candle_range = candle_high - candle_low

    spread = SPREAD_PIPS * 0.01

    if is_bullish:
        direction = "BUY"
        entry_price = candle_high - (candle_range * FIBO_RETRACEMENT)
        entry_price += spread
        stop_loss = candle_low
        risk = entry_price - stop_loss
        take_profit = entry_price + (risk * RR_RATIO)
    else:
        direction = "SELL"
        entry_price = candle_low + (candle_range * FIBO_RETRACEMENT)
        entry_price -= spread
        stop_loss = candle_high
        risk = stop_loss - entry_price
        take_profit = entry_price - (risk * RR_RATIO)

    lot = calculate_dynamic_lot(candle_range)
    risk_dollars = risk * lot * 100

    return {
        'direction': direction,
        'entry_price': round(entry_price, 2),
        'stop_loss': round(stop_loss, 2),
        'take_profit': round(take_profit, 2),
        'lot': lot,
        'candle_range': round(candle_range, 2),
        'risk_dollars': round(risk_dollars, 2),
        'risk_pips': round(risk / 0.01, 1),
        'reward_dollars': round(risk_dollars * RR_RATIO, 2),
    }


def place_pending_order(setup):
    """Place a pending order (BUY LIMIT or SELL LIMIT) on MT5"""
    if DRY_RUN:
        log.info(f"[DRY RUN] Would place {setup['direction']} LIMIT @ {setup['entry_price']} | "
                 f"SL: {setup['stop_loss']} | TP: {setup['take_profit']} | Lot: {setup['lot']} | "
                 f"Risk: ${setup['risk_dollars']}")
        return True

    symbol_info = mt5.symbol_info(SYMBOL)
    if symbol_info is None:
        log.error(f"Symbol {SYMBOL} not found")
        return False

    if not symbol_info.visible:
        if not mt5.symbol_select(SYMBOL, True):
            log.error(f"Failed to select {SYMBOL}")
            return False

    point = symbol_info.point
    deviation = 20

    if setup['direction'] == "BUY":
        order_type = mt5.ORDER_TYPE_BUY_LIMIT
    else:
        order_type = mt5.ORDER_TYPE_SELL_LIMIT

    request = {
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": SYMBOL,
        "volume": setup['lot'],
        "type": order_type,
        "price": setup['entry_price'],
        "sl": setup['stop_loss'],
        "tp": setup['take_profit'],
        "deviation": deviation,
        "magic": 123456,
        "comment": "AsianFiboBot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    if result is None:
        log.error(f"Order send failed: {mt5.last_error()}")
        return False

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        log.error(f"Order failed: retcode={result.retcode}, comment={result.comment}")
        return False

    log.info(f"ORDER PLACED: {setup['direction']} LIMIT @ {setup['entry_price']} | "
             f"SL: {setup['stop_loss']} | TP: {setup['take_profit']} | "
             f"Lot: {setup['lot']} | Ticket: {result.order}")
    return True


def cancel_pending_orders():
    """Cancel all pending orders placed by this bot"""
    orders = mt5.orders_get(symbol=SYMBOL)
    if orders is None or len(orders) == 0:
        return 0

    cancelled = 0
    for order in orders:
        if order.magic == 123456:
            request = {
                "action": mt5.TRADE_ACTION_REMOVE,
                "order": order.ticket,
            }
            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                log.info(f"Cancelled pending order #{order.ticket}")
                cancelled += 1
            else:
                log.error(f"Failed to cancel order #{order.ticket}")
    return cancelled


def get_open_positions():
    """Get open positions placed by this bot"""
    positions = mt5.positions_get(symbol=SYMBOL)
    if positions is None:
        return []
    return [p for p in positions if p.magic == 123456]


def save_trade(trade_data):
    """Save trade to JSON history file"""
    history = []
    if os.path.exists(TRADE_HISTORY_FILE):
        with open(TRADE_HISTORY_FILE, 'r') as f:
            history = json.load(f)
    history.append(trade_data)
    with open(TRADE_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2, default=str)


def get_server_time():
    """Get current server time from MT5"""
    tick = mt5.symbol_info_tick(SYMBOL)
    if tick:
        return datetime.fromtimestamp(tick.time)
    return datetime.utcnow()


def wait_for_asian_session_end():
    """Wait until Asian session is complete, then return the date"""
    while True:
        now = get_server_time()
        today = now.date()

        # Skip weekends
        if today.weekday() >= 5:
            next_monday = today + timedelta(days=(7 - today.weekday()))
            wait_until = datetime.combine(next_monday, time(0, 0))
            wait_secs = (wait_until - now).total_seconds()
            log.info(f"Weekend detected. Waiting until Monday {next_monday}... ({wait_secs/3600:.1f}h)")
            time_module.sleep(min(wait_secs + 60, 3600))  # Sleep max 1h at a time
            continue

        _, session_end = get_asian_session_times(today)

        if now >= session_end + timedelta(minutes=1):
            # Session is complete, check if we already traded today
            return today

        # Wait for session to end
        wait_secs = (session_end + timedelta(minutes=1) - now).total_seconds()
        if wait_secs > 0:
            log.info(f"Waiting for Asian session to end at {session_end.strftime('%H:%M')}... "
                     f"({wait_secs/60:.0f} min)")
            time_module.sleep(min(wait_secs + 5, 300))  # Sleep max 5 min at a time

        return today


def run_live_bot():
    """Main live bot loop"""
    mode = "DRY RUN" if DRY_RUN else "LIVE"
    log.info("=" * 70)
    log.info(f"ASIAN SESSION XAUUSD FIBONACCI BOT [{mode}]")
    log.info("=" * 70)
    log.info(f"Symbol: {SYMBOL} | R:R: 1:{RR_RATIO} | Fibo: {FIBO_RETRACEMENT*100}%")
    log.info(f"Target Risk: ${TARGET_RISK_DOLLARS}/trade | Lot Range: {MIN_LOT}-{MAX_LOT}")
    log.info("=" * 70)

    if not connect_mt5():
        return

    last_trade_date = None
    daily_stats = {'wins': 0, 'losses': 0, 'pnl': 0.0}

    try:
        while True:
            # Reconnect if needed
            if mt5.account_info() is None:
                log.warning("MT5 disconnected, reconnecting...")
                if not connect_mt5():
                    time_module.sleep(60)
                    continue

            # Check for open positions first
            positions = get_open_positions()
            if positions:
                pos = positions[0]
                profit = pos.profit
                log.info(f"Open position: {pos.type} | Lot: {pos.volume} | "
                         f"Entry: {pos.price_open} | Current P&L: ${profit:+.2f}")
                time_module.sleep(CHECK_INTERVAL_SECONDS)
                continue

            # Wait for Asian session to end
            trade_date = wait_for_asian_session_end()

            # Skip if already traded today
            if trade_date == last_trade_date:
                # Check if pending order is still active
                orders = mt5.orders_get(symbol=SYMBOL)
                bot_orders = [o for o in (orders or []) if o.magic == 123456]
                if bot_orders:
                    log.debug(f"Pending order active, waiting for fill...")
                    time_module.sleep(CHECK_INTERVAL_SECONDS)
                    continue

                # No pending order, no position - trade was either filled and closed, or cancelled
                # Wait for next day
                now = get_server_time()
                tomorrow = datetime.combine(trade_date + timedelta(days=1), time(0, 0))
                wait_secs = (tomorrow - now).total_seconds()
                if wait_secs > 0:
                    log.info(f"Already traded today. Waiting for next session... ({wait_secs/3600:.1f}h)")
                    time_module.sleep(min(wait_secs + 60, 3600))
                continue

            # Get Asian session data
            asian_df = get_asian_session_data(trade_date)
            if asian_df is None or len(asian_df) == 0:
                log.warning(f"No Asian session data for {trade_date}")
                last_trade_date = trade_date
                continue

            # Find biggest candle
            biggest = get_biggest_candle(asian_df, LOOKBACK_CANDLES)
            if biggest is None:
                log.warning(f"No valid biggest candle for {trade_date}")
                last_trade_date = trade_date
                continue

            # Calculate trade setup
            setup = calculate_trade_setup(biggest)

            log.info("=" * 50)
            log.info(f"TRADE SETUP for {trade_date}")
            log.info(f"  Direction: {setup['direction']}")
            log.info(f"  Candle Range: {setup['candle_range']}")
            log.info(f"  Entry: {setup['entry_price']}")
            log.info(f"  Stop Loss: {setup['stop_loss']}")
            log.info(f"  Take Profit: {setup['take_profit']}")
            log.info(f"  Lot Size: {setup['lot']}")
            log.info(f"  Risk: ${setup['risk_dollars']} ({setup['risk_pips']} pips)")
            log.info(f"  Potential Reward: ${setup['reward_dollars']}")
            log.info("=" * 50)

            # Cancel any old pending orders
            cancel_pending_orders()

            # Place the pending order
            if place_pending_order(setup):
                last_trade_date = trade_date
                save_trade({
                    'date': str(trade_date),
                    'setup': setup,
                    'status': 'PENDING',
                    'placed_at': str(get_server_time()),
                })
                log.info(f"Order placed. Monitoring for fill...")
            else:
                log.error("Failed to place order!")
                last_trade_date = trade_date

            time_module.sleep(CHECK_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        log.info("\nBot stopped by user")
        # Cancel pending orders on shutdown
        cancelled = cancel_pending_orders()
        if cancelled:
            log.info(f"Cancelled {cancelled} pending orders on shutdown")
    finally:
        mt5.shutdown()
        log.info("MT5 disconnected. Bot stopped.")


if __name__ == "__main__":
    run_live_bot()
