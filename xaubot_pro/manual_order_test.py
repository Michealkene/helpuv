#!/usr/bin/env python3
"""
Manual Order Test for XauBot Pro
Place a small test order to verify MT5 order execution works
"""
import MetaTrader5 as mt5
import json
from datetime import datetime

print("=" * 60)
print("XAUBOT PRO - MANUAL ORDER TEST")
print("=" * 60)
print()

# Load config
print("[1/8] Loading configuration...")
with open('config.json', 'r') as f:
    config = json.load(f)
print("✅ Config loaded")
print()

# Initialize MT5
print("[2/8] Initializing MT5...")
if not mt5.initialize():
    print(f"❌ ERROR: MT5 initialize failed: {mt5.last_error()}")
    exit(1)
print("✅ MT5 initialized")
print()

# Login
print("[3/8] Logging into MT5 account...")
login = config['mt5_login']
password = config['mt5_password']
server = config['mt5_server']

authorized = mt5.login(login, password, server)
if not authorized:
    print(f"❌ ERROR: Login failed: {mt5.last_error()}")
    mt5.shutdown()
    exit(1)
print(f"✅ Logged in: {login} @ {server}")
print()

# Get account info
print("[4/8] Retrieving account information...")
account_info = mt5.account_info()
if not account_info:
    print("❌ ERROR: Could not get account info")
    mt5.shutdown()
    exit(1)

print(f"✅ Account Details:")
print(f"   Balance: ${account_info.balance:,.2f}")
print(f"   Equity: ${account_info.equity:,.2f}")
print(f"   Leverage: 1:{account_info.leverage}")
print(f"   Free Margin: ${account_info.margin_free:,.2f}")
print()

# Check symbol
print("[5/8] Checking XAUUSD symbol...")
symbol = "XAUUSD"
symbol_info = mt5.symbol_info(symbol)

if symbol_info is None:
    print(f"❌ ERROR: Symbol {symbol} not found")
    mt5.shutdown()
    exit(1)

if not symbol_info.visible:
    print(f"   Symbol not visible. Attempting to enable...")
    if mt5.symbol_select(symbol, True):
        print(f"   ✅ Symbol {symbol} enabled")
        symbol_info = mt5.symbol_info(symbol)
    else:
        print(f"   ❌ ERROR: Could not enable {symbol}")
        mt5.shutdown()
        exit(1)
else:
    print(f"   ✅ Symbol {symbol} is accessible")

# Get current price
tick = mt5.symbol_info_tick(symbol)
if not tick:
    print(f"❌ ERROR: Could not get tick data for {symbol}")
    mt5.shutdown()
    exit(1)

print(f"   Current Price - Bid: {tick.bid:.2f} | Ask: {tick.ask:.2f}")
print(f"   Spread: {(tick.ask - tick.bid):.2f} points")
print()

# Prepare test order
print("[6/8] Preparing test order...")
lot = 0.01  # Minimum lot size for safety
price = tick.ask  # Current ask price

# Place BUY LIMIT order 5 points below current (will fill quickly)
entry_price = price - 5.0
stop_loss = entry_price - 50.0
take_profit = entry_price + 50.0

print(f"   Test Order Details:")
print(f"   Type: BUY LIMIT")
print(f"   Lot Size: {lot}")
print(f"   Entry: {entry_price:.2f}")
print(f"   Stop Loss: {stop_loss:.2f}")
print(f"   Take Profit: {take_profit:.2f}")
print(f"   Risk: ~${50 * lot:.2f}")
print(f"   Expected Profit: ~${50 * lot:.2f}")
print()

# Ask for confirmation
print("=" * 60)
print("READY TO PLACE TEST ORDER")
print("=" * 60)
print()
print("This will place a REAL order on your demo account.")
print("The order will execute if price drops 5 points.")
print()
response = input("Continue? (yes/no): ").strip().lower()

if response != 'yes':
    print()
    print("Test cancelled. No order placed.")
    mt5.shutdown()
    exit(0)

print()
print("[7/8] Placing order...")

request = {
    "action": mt5.TRADE_ACTION_PENDING,
    "symbol": symbol,
    "volume": lot,
    "type": mt5.ORDER_TYPE_BUY_LIMIT,
    "price": entry_price,
    "sl": stop_loss,
    "tp": take_profit,
    "deviation": 20,
    "magic": 123456,
    "comment": "XauBot Test Order",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_IOC,  # CRITICAL: This is the bug fix!
}

result = mt5.order_send(request)

if result is None:
    print(f"❌ ERROR: Order send failed: {mt5.last_error()}")
    mt5.shutdown()
    exit(1)

print()
print("[8/8] Order Result:")
print(f"   Return Code: {result.retcode}")

if result.retcode == mt5.TRADE_RETCODE_DONE:
    print(f"   ✅ ORDER PLACED SUCCESSFULLY!")
    print(f"   Order Ticket: #{result.order}")
    print(f"   Entry Price: {entry_price:.2f}")
    print(f"   Stop Loss: {stop_loss:.2f}")
    print(f"   Take Profit: {take_profit:.2f}")
    print()
    print("=" * 60)
    print("✅ TEST PASSED - MT5 ORDER EXECUTION WORKS!")
    print("=" * 60)
    print()
    print("The order is now pending in MT5.")
    print("It will execute if price drops to the entry level.")
    print()
    print("To cancel the order:")
    print("1. Open MT5 terminal")
    print(f"2. Find order #{result.order} in 'Trade' tab")
    print("3. Right-click → 'Delete Order'")
    print()
elif result.retcode == mt5.TRADE_RETCODE_REQUOTE:
    print(f"   ⚠️  Requote - Price changed")
    print(f"   Comment: {result.comment}")
    print()
    print("This is normal. Market moved. Try again.")
elif result.retcode == mt5.TRADE_RETCODE_INVALID_FILL:
    print(f"   ❌ Invalid filling mode")
    print(f"   Comment: {result.comment}")
    print()
    print("THIS SHOULD NOT HAPPEN - The bug fix should prevent this!")
    print("If you see this, the type_filling parameter may not be working.")
else:
    print(f"   ❌ Order failed: {result.comment}")
    print()
    print("Possible reasons:")
    print("- Insufficient margin")
    print("- Symbol not tradeable")
    print("- Broker restrictions")
    print("- Invalid parameters")

print()
mt5.shutdown()
print("MT5 connection closed.")
print()
print("Test complete.")
