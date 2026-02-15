import MetaTrader5 as mt5
import json

with open('config.json') as f:
    cfg = json.load(f)

print("Init:", mt5.initialize())
print("Login:", mt5.login(cfg['mt5_login'], cfg['mt5_password'], cfg['mt5_server']))
acc = mt5.account_info()
if acc:
    print(f"Balance: ${acc.balance}")
    print(f"Equity: ${acc.equity}")
mt5.shutdown()
