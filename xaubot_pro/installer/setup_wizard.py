"""XAUBOT Pro - Setup Wizard
Guides the user through initial configuration.
"""
import json
import os
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(cfg):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(cfg, f, indent=2)

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    clear()
    cfg = load_config()

    print()
    print("  " + "=" * 52)
    print("  =                                                =")
    print("  =         XAUBOT Pro - SETUP WIZARD              =")
    print("  =       Professional Gold Trading Bot            =")
    print("  =                                                =")
    print("  " + "=" * 52)
    print()
    print("  Let's configure your trading bot.")
    print("  You'll need your MetaTrader 5 account details.")
    print()
    print("  " + "-" * 52)
    print()

    # MT5 Login
    current = cfg.get('mt5_login', '')
    print(f"  [1/6] MetaTrader 5 Login (Account Number)")
    if current:
        print(f"        Current: {current}")
    val = input("        Enter login (or press Enter to keep current): ").strip()
    if val:
        try:
            cfg['mt5_login'] = int(val)
        except ValueError:
            print("        [!] Invalid number, keeping current value.")
    print()

    # MT5 Password
    current = cfg.get('mt5_password', '')
    print(f"  [2/6] MetaTrader 5 Password")
    if current:
        masked = current[0] + '*' * (len(current) - 2) + current[-1] if len(current) > 2 else '***'
        print(f"        Current: {masked}")
    val = input("        Enter password (or press Enter to keep current): ").strip()
    if val:
        cfg['mt5_password'] = val
    print()

    # MT5 Server
    current = cfg.get('mt5_server', 'MetaQuotes-Demo')
    print(f"  [3/6] MetaTrader 5 Server")
    print(f"        Current: {current}")
    val = input("        Enter server (or press Enter to keep current): ").strip()
    if val:
        cfg['mt5_server'] = val
    print()

    # Risk per trade
    current = cfg.get('risk_per_trade', 100)
    print(f"  [4/6] Risk Per Trade (USD)")
    print(f"        Current: ${current}")
    print(f"        Recommended: $50 - $200 per trade")
    val = input("        Enter amount (or press Enter to keep current): ").strip()
    if val:
        try:
            risk = float(val)
            if risk < 1 or risk > 10000:
                print("        [!] Value out of range, keeping current.")
            else:
                cfg['risk_per_trade'] = round(risk, 2)
        except ValueError:
            print("        [!] Invalid number, keeping current value.")
    print()

    # Min lot
    current = cfg.get('min_lot', 0.01)
    print(f"  [5/6] Minimum Lot Size")
    print(f"        Current: {current}")
    val = input("        Enter min lot (or press Enter to keep current): ").strip()
    if val:
        try:
            cfg['min_lot'] = max(0.01, round(float(val), 2))
        except ValueError:
            print("        [!] Invalid number, keeping current value.")
    print()

    # Max lot
    current = cfg.get('max_lot', 5.0)
    print(f"  [6/6] Maximum Lot Size")
    print(f"        Current: {current}")
    val = input("        Enter max lot (or press Enter to keep current): ").strip()
    if val:
        try:
            cfg['max_lot'] = max(0.01, round(float(val), 2))
        except ValueError:
            print("        [!] Invalid number, keeping current value.")
    print()

    # Starting balance
    cfg.setdefault('starting_balance', 10000)

    # Save
    print("  " + "-" * 52)
    print()
    print("  Your configuration:")
    print(f"    MT5 Login:      {cfg.get('mt5_login', 'Not set')}")
    pwd = cfg.get('mt5_password', '')
    masked = pwd[0] + '*' * (len(pwd) - 2) + pwd[-1] if len(pwd) > 2 else '***'
    print(f"    MT5 Password:   {masked}")
    print(f"    MT5 Server:     {cfg.get('mt5_server', 'Not set')}")
    print(f"    Risk/Trade:     ${cfg.get('risk_per_trade', 100)}")
    print(f"    Lot Range:      {cfg.get('min_lot', 0.01)} - {cfg.get('max_lot', 5.0)}")
    print()

    confirm = input("  Save this configuration? (Y/n): ").strip().lower()
    if confirm in ('', 'y', 'yes'):
        save_config(cfg)
        print()
        print("  [OK] Configuration saved to config.json")
        print()
        print("  You can change these settings anytime in the Dashboard")
        print("  under the Settings page.")
    else:
        print()
        print("  [!] Configuration NOT saved. You can run setup again or")
        print("      edit settings in the Dashboard.")

    print()
    print("  " + "=" * 52)
    print()

if __name__ == "__main__":
    main()
