#!/usr/bin/env python3
"""Quick MT5 Connection Test"""
import MetaTrader5 as mt5
import json

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

# Initialize MT5
print("Connecting to MT5...")
if not mt5.initialize():
    print(f"ERROR: MT5 initialize failed: {mt5.last_error()}")
    exit(1)

# Login
login = config['mt5_login']
password = config['mt5_password']
server = config['mt5_server']

print(f"Logging in: {login} @ {server}")
authorized = mt5.login(login, password, server)

if not authorized:
    print(f"ERROR: Login failed: {mt5.last_error()}")
    mt5.shutdown()
    exit(1)

# Get account info
account_info = mt5.account_info()
if account_info:
    print(f"\n✅ MT5 CONNECTION SUCCESSFUL!")
    print(f"Account: {account_info.login}")
    print(f"Balance: ${account_info.balance:,.2f}")
    print(f"Equity: ${account_info.equity:,.2f}")
    print(f"Server: {account_info.server}")
    print(f"Leverage: 1:{account_info.leverage}")
    print(f"Currency: {account_info.currency}")
    
    # Test symbol access
    symbol = "XAUUSD"
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info:
        print(f"\n✅ Symbol {symbol} accessible")
        tick = mt5.symbol_info_tick(symbol)
        if tick:
            print(f"Current Price - Bid: {tick.bid:.2f} | Ask: {tick.ask:.2f}")
        else:
            print(f"WARNING: Could not get tick data for {symbol}")
    else:
        print(f"WARNING: Symbol {symbol} not found")
        # Try to enable it
        if mt5.symbol_select(symbol, True):
            print(f"✅ Symbol {symbol} enabled successfully")
        else:
            print(f"ERROR: Could not enable {symbol}")
else:
    print(f"ERROR: Could not get account info")

mt5.shutdown()
print("\nConnection test complete.")
