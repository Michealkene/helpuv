"""20-Month Deep Analysis: June 2024 - Feb 2026"""
import sys, os
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time

SYMBOL = "XAUUSD"
MT5_LOGIN = 5046171682
MT5_PASSWORD = "2i_hYuTw"
MT5_SERVER = "MetaQuotes-Demo"
FIBO = 0.45
RR = 4.0
LOOKBACK = 6
TARGET_RISK = 100
MIN_LOT, MAX_LOT = 0.01, 5.0
START = datetime(2024, 6, 1)
END = datetime(2026, 2, 8)

def is_dst(dt):
    y = dt.year
    m3 = datetime(y, 3, 31)
    while m3.weekday() != 6: m3 -= timedelta(days=1)
    o10 = datetime(y, 10, 31)
    while o10.weekday() != 6: o10 -= timedelta(days=1)
    return m3.date() <= dt <= o10.date()

def at(dt):
    return (time(1,0), time(4,0)) if is_dst(dt) else (time(0,0), time(3,0))

def clot(rng):
    rpu = rng * (1 - FIBO)
    if rpu <= 0: return MIN_LOT
    return max(MIN_LOT, min(MAX_LOT, round(TARGET_RISK / (rpu * 100), 2)))

print("=" * 70)
print("XAUBOT Pro - 20 MONTH DEEP ANALYSIS")
print("=" * 70)
print(f"Period: {START.date()} to {END.date()}")
print(f"Risk: ${TARGET_RISK}/trade | Dynamic lots")
print("=" * 70)

if not mt5.initialize(login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER):
    print(f"MT5 failed: {mt5.last_error()}")
    sys.exit(1)
info = mt5.account_info()
print(f"Connected | Account: {info.login}")

frames = []
cs = START
while cs < END:
    ce = min(datetime(cs.year + 1, 1, 1), END)
    r = mt5.copy_rates_range(SYMBOL, mt5.TIMEFRAME_M15, cs, ce)
    if r is not None and len(r) > 0:
        df = pd.DataFrame(r)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        frames.append(df)
        print(f"  {cs.year}: {len(df)} candles")
    cs = ce
mt5.shutdown()

if not frames:
    print("No data!"); sys.exit(1)
ad = pd.concat(frames, ignore_index=True).drop_duplicates(subset='time').sort_values('time').reset_index(drop=True)
print(f"Total: {len(ad)} candles\n")

trades = []
cur = START.date()
while cur <= END.date():
    if cur.weekday() >= 5:
        cur += timedelta(days=1); continue
    st_t, et_t = at(cur)
    adf = ad[(ad['time'] >= datetime.combine(cur, st_t)) & (ad['time'] <= datetime.combine(cur, et_t))].copy()
    if len(adf) < 2:
        cur += timedelta(days=1); continue
    adf['range'] = adf['high'] - adf['low']
    ldf = adf.iloc[-LOOKBACK-1:-1] if len(adf) > LOOKBACK else adf
    if len(ldf) == 0:
        cur += timedelta(days=1); continue
    c = ldf.loc[ldf['range'].idxmax()]
    rng = c['high'] - c['low']
    if rng == 0:
        cur += timedelta(days=1); continue
    bull = c['close'] > c['open']
    if bull:
        d, entry, sl = "BUY", c['high'] - rng * FIBO, c['low']
        risk = entry - sl; tp = entry + risk * RR
    else:
        d, entry, sl = "SELL", c['low'] + rng * FIBO, c['high']
        risk = sl - entry; tp = entry - risk * RR
    lot = clot(rng)
    rd = risk * lot * 100
    ets = c['time']
    fut = ad[ad['time'] >= ets]
    filled, ft = False, None
    for _, b in fut.iterrows():
        if bull and b['low'] <= entry: filled, ft = True, b['time']; break
        elif not bull and b['high'] >= entry: filled, ft = True, b['time']; break
    if not filled:
        trades.append({'date': cur, 'direction': d, 'outcome': 'NO_FILL', 'profit_dollars': 0,
                       'profit_pips': 0, 'lot_size': lot, 'risk_dollars': round(rd, 2),
                       'candle_range': round(rng, 2), 'entry_price': round(entry, 2),
                       'stop_loss': round(sl, 2), 'take_profit': round(tp, 2)})
        cur += timedelta(days=1); continue
    aft = ad[ad['time'] > ft]
    outcome = None
    for _, b in aft.iterrows():
        if bull:
            if b['high'] >= tp: outcome = "WIN"; break
            if b['low'] <= sl: outcome = "LOSS"; break
        else:
            if b['low'] <= tp: outcome = "WIN"; break
            if b['high'] >= sl: outcome = "LOSS"; break
    if outcome is None: outcome = "OPEN"
    if outcome == "WIN":
        pips = abs(tp - entry) / 0.01; dol = pips * 0.01 * lot * 100
    elif outcome == "LOSS":
        pips = -abs(entry - sl) / 0.01; dol = pips * 0.01 * lot * 100
    else:
        pips = dol = 0
    trades.append({'date': cur, 'direction': d, 'outcome': outcome,
                   'profit_dollars': round(dol, 2), 'profit_pips': round(pips, 1),
                   'lot_size': lot, 'risk_dollars': round(rd, 2),
                   'candle_range': round(rng, 2), 'entry_price': round(entry, 2),
                   'stop_loss': round(sl, 2), 'take_profit': round(tp, 2)})
    cur += timedelta(days=1)

df = pd.DataFrame(trades)
comp = df[df['outcome'].isin(['WIN', 'LOSS'])]
w = comp[comp['outcome'] == 'WIN']
l = comp[comp['outcome'] == 'LOSS']
nt, nw, nl = len(comp), len(w), len(l)
wr = nw / nt * 100 if nt > 0 else 0
pnl = comp['profit_dollars'].sum()
ws = w['profit_dollars'].sum() if nw > 0 else 0
ls = abs(l['profit_dollars'].sum()) if nl > 0 else 0
pf = ws / ls if ls > 0 else 0
aw = w['profit_dollars'].mean() if nw > 0 else 0
al = l['profit_dollars'].mean() if nl > 0 else 0
eq = comp['profit_dollars'].cumsum()
mdd = (eq - eq.cummax()).min() if len(eq) > 0 else 0
rf = abs(pnl / mdd) if mdd < 0 else 0
awp = w['profit_pips'].mean() if nw > 0 else 0
alp = abs(l['profit_pips'].mean()) if nl > 0 else 1
arr = awp / alp if alp > 0 else 0

cm = comp.copy()
cm['month'] = pd.to_datetime(cm['date']).dt.to_period('M')
mp = cm.groupby('month').agg(trades=('outcome', 'count'), wins=('outcome', lambda x: (x == 'WIN').sum()),
                              pnl=('profit_dollars', 'sum')).reset_index()
mp['wr'] = (mp['wins'] / mp['trades'] * 100).round(1)
pm = (mp['pnl'] > 0).sum()
tm = len(mp)

buy_t = comp[comp['direction'] == 'BUY']
sell_t = comp[comp['direction'] == 'SELL']

print("\n" + "=" * 70)
print("20-MONTH RESULTS")
print("=" * 70)
print(f"  Trades:          {nt}")
print(f"  Wins:            {nw}")
print(f"  Losses:          {nl}")
print(f"  Win Rate:        {wr:.1f}%")
print(f"  Total P&L:       ${pnl:,.2f}")
print(f"  Profit Factor:   {pf:.2f}")
print(f"  Avg R:R:         {arr:.1f}:1")
print(f"  Avg Win:         ${aw:,.2f}")
print(f"  Avg Loss:        ${al:,.2f}")
print(f"  Max Drawdown:    ${mdd:,.2f}")
print(f"  Recovery Factor: {rf:.1f}")
print(f"  Avg Risk/Trade:  ${comp['risk_dollars'].mean():,.2f}")
print()
print(f"  RETURN ON $10K:  {((10000+pnl)/10000 - 1)*100:+.0f}%")
print(f"  Monthly Avg:     ${pnl/max(tm,1):,.2f}")
print(f"  Profitable Mo:   {pm}/{tm} ({pm/max(tm,1)*100:.0f}%)")
print()
print("MONTHLY:")
print(f"{'Month':<10} {'Trades':<8} {'Wins':<6} {'WR%':<8} {'P&L':>12}")
print("-" * 48)
for _, r in mp.iterrows():
    print(f"{str(r['month']):<10} {int(r['trades']):<8} {int(r['wins']):<6} {r['wr']:<7.1f}% ${r['pnl']:>10,.2f}")
print()
print(f"BUY:  {len(buy_t)} trades | WR: {(buy_t['outcome']=='WIN').mean()*100:.1f}% | ${buy_t['profit_dollars'].sum():,.2f}")
print(f"SELL: {len(sell_t)} trades | WR: {(sell_t['outcome']=='WIN').mean()*100:.1f}% | ${sell_t['profit_dollars'].sum():,.2f}")

fn = f"backtest_20m_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
df.to_csv(fn, index=False)
print(f"\nSaved: {fn}")
print("=" * 70)
