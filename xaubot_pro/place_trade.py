"""Place today's XAUBOT Pro trade on MT5 - $500 risk"""
import sys, os, time
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta, time as dtime

# Config
MT5_LOGIN = 5046171682
MT5_PASSWORD = "2i_hYuTw"
MT5_SERVER = "MetaQuotes-Demo"
SYMBOL = "XAUUSD"
FIBO = 0.45
RR = 4.0
LOOKBACK = 6
TARGET_RISK = 500  # $500 per trade
MIN_LOT = 0.01
MAX_LOT = 5.0
MAGIC = 123456

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

def calc_lot(candle_range):
    risk_per_unit = candle_range * (1 - FIBO)
    if risk_per_unit <= 0:
        return MIN_LOT
    lot = TARGET_RISK / (risk_per_unit * 100)
    return max(MIN_LOT, min(MAX_LOT, round(lot, 2)))

print("=" * 60)
print("XAUBOT Pro - LIVE TRADE PLACEMENT")
print("=" * 60)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Risk: ${TARGET_RISK}/trade")
print()

# Connect to MT5
print("[1] Connecting to MetaTrader 5...")
if not mt5.initialize(login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER):
    print(f"  FAILED: {mt5.last_error()}")
    sys.exit(1)

info = mt5.account_info()
print(f"  Connected! Account: {info.login}")
print(f"  Balance: ${info.balance:,.2f} | Equity: ${info.equity:,.2f}")
print()

# Check for existing XAUBOT orders
existing = mt5.orders_get(symbol=SYMBOL)
xaubot_orders = [o for o in (existing or []) if o.magic == MAGIC]
if xaubot_orders:
    print(f"  [!] Found {len(xaubot_orders)} existing XAUBOT pending order(s):")
    for o in xaubot_orders:
        otype = "BUY LIMIT" if o.type == 2 else "SELL LIMIT" if o.type == 3 else f"Type {o.type}"
        print(f"      {otype} {o.volume_current} lots @ {o.price_order:.2f} SL:{o.sl:.2f} TP:{o.tp:.2f}")
    print()

existing_pos = mt5.positions_get(symbol=SYMBOL)
xaubot_pos = [p for p in (existing_pos or []) if p.magic == MAGIC]
if xaubot_pos:
    print(f"  [!] Found {len(xaubot_pos)} existing XAUBOT position(s):")
    for p in xaubot_pos:
        d = "BUY" if p.type == 0 else "SELL"
        print(f"      {d} {p.volume} lots @ {p.price_open:.2f} P&L: ${p.profit:+,.2f}")
    print()

# Get Asian session data
today = datetime.now()
print(f"[2] Analyzing Asian session for {today.strftime('%Y-%m-%d')}...")
st, et = asian_times(today)
print(f"  Asian session: {st} - {et} (server time)")
print(f"  DST: {'Yes' if is_dst(today) else 'No'}")

# Get M15 candles for today's session
session_start = datetime.combine(today.date(), st)
session_end = datetime.combine(today.date(), et)

# Get candles
rates = mt5.copy_rates_range(SYMBOL, mt5.TIMEFRAME_M15, session_start, session_end)
if rates is None or len(rates) == 0:
    print(f"  No candles found for today's session ({session_start} - {session_end})")
    print(f"  Trying to check if market is open...")
    tick = mt5.symbol_info_tick(SYMBOL)
    if tick:
        print(f"  Current price: {tick.ask:.2f}/{tick.bid:.2f}")
    else:
        print(f"  Cannot get tick data. Market may be closed.")
    mt5.shutdown()
    sys.exit(0)

df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s')
df['range'] = df['high'] - df['low']

print(f"  Found {len(df)} candles in Asian session")
print()

if len(df) < 2:
    print("  [!] Not enough candles (need at least 2). Exiting.")
    mt5.shutdown()
    sys.exit(0)

# Find the candle with highest range in the lookback
lookback_df = df.iloc[-LOOKBACK-1:-1] if len(df) > LOOKBACK else df
if len(lookback_df) == 0:
    print("  [!] No candles in lookback window. Exiting.")
    mt5.shutdown()
    sys.exit(0)

candle = lookback_df.loc[lookback_df['range'].idxmax()]
rng = candle['high'] - candle['low']

if rng == 0:
    print("  [!] Zero range candle. No trade today.")
    mt5.shutdown()
    sys.exit(0)

bullish = candle['close'] > candle['open']

print("[3] Trade Setup:")
print(f"  Signal Candle: {pd.to_datetime(candle['time']).strftime('%H:%M')}")
print(f"  High: {candle['high']:.2f} | Low: {candle['low']:.2f}")
print(f"  Range: {rng:.2f}")
print(f"  Direction: {'BULLISH' if bullish else 'BEARISH'}")
print()

# Calculate levels
if bullish:
    direction = "BUY"
    entry = round(candle['high'] - rng * FIBO, 2)
    sl = round(candle['low'], 2)
    risk = entry - sl
    tp = round(entry + risk * RR, 2)
    order_type = mt5.ORDER_TYPE_BUY_LIMIT
else:
    direction = "SELL"
    entry = round(candle['low'] + rng * FIBO, 2)
    sl = round(candle['high'], 2)
    risk = sl - entry
    tp = round(entry - risk * RR, 2)
    order_type = mt5.ORDER_TYPE_SELL_LIMIT

lot = calc_lot(rng)
risk_dollars = risk * lot * 100

print(f"  Direction:  {direction}")
print(f"  Entry:      {entry:.2f}")
print(f"  Stop Loss:  {sl:.2f}")
print(f"  Take Profit:{tp:.2f}")
print(f"  Risk (pips): {risk/0.01:.0f}")
print(f"  Lot Size:   {lot}")
print(f"  Risk ($):   ${risk_dollars:,.2f}")
print()

# Check current price to see if entry makes sense
tick = mt5.symbol_info_tick(SYMBOL)
if tick:
    current = tick.ask if direction == "BUY" else tick.bid
    print(f"  Current Price: {current:.2f}")
    if direction == "BUY" and current <= entry:
        print(f"  [!] Price already at/below entry. Using BUY LIMIT.")
    elif direction == "SELL" and current >= entry:
        print(f"  [!] Price already at/above entry. Using SELL LIMIT.")
    print()

# Place the order
print("[4] Placing pending order...")
request = {
    "action": mt5.TRADE_ACTION_PENDING,
    "symbol": SYMBOL,
    "volume": lot,
    "type": order_type,
    "price": entry,
    "sl": sl,
    "tp": tp,
    "deviation": 20,
    "magic": MAGIC,
    "comment": f"XAUBOT ${TARGET_RISK}",
    "type_time": mt5.ORDER_TIME_DAY,
    "type_filling": mt5.ORDER_FILLING_IOC,
}

result = mt5.order_send(request)
print()

if result is None:
    print(f"  [ERROR] order_send returned None: {mt5.last_error()}")
elif result.retcode != mt5.TRADE_RETCODE_DONE:
    print(f"  [ERROR] Order failed: {result.retcode} - {result.comment}")
    print(f"  Trying with ORDER_FILLING_RETURN...")
    request["type_filling"] = mt5.ORDER_FILLING_RETURN
    result = mt5.order_send(request)
    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f"  [OK] Order placed! Ticket: {result.order}")
    elif result:
        print(f"  [ERROR] Still failed: {result.retcode} - {result.comment}")
        print(f"  Trying with ORDER_FILLING_FOK...")
        request["type_filling"] = mt5.ORDER_FILLING_FOK
        result = mt5.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"  [OK] Order placed! Ticket: {result.order}")
        elif result:
            print(f"  [ERROR] All fill types failed: {result.retcode} - {result.comment}")
else:
    print(f"  [OK] ORDER PLACED SUCCESSFULLY!")
    print(f"  Ticket: {result.order}")

print()
print("=" * 60)
print("TRADE SUMMARY")
print("=" * 60)
print(f"  {direction} LIMIT @ {entry:.2f}")
print(f"  SL: {sl:.2f} | TP: {tp:.2f}")
print(f"  Lot: {lot} | Risk: ${risk_dollars:,.2f}")
print(f"  R:R = 1:{RR}")
if result and result.retcode == mt5.TRADE_RETCODE_DONE:
    print(f"  Status: PLACED (Ticket #{result.order})")
else:
    print(f"  Status: REVIEW ERRORS ABOVE")
print("=" * 60)

mt5.shutdown()
