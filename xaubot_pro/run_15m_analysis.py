"""Quick 15-month deep analysis for marketing - Nov 2024 to Feb 2026"""
import sys, os
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time

# Config
SYMBOL = "XAUUSD"
MT5_LOGIN = 5046171682
MT5_PASSWORD = "2i_hYuTw"
MT5_SERVER = "MetaQuotes-Demo"
FIBO = 0.45
RR = 4.0
LOOKBACK = 6
TARGET_RISK = 100
MIN_LOT = 0.01
MAX_LOT = 5.0

START = datetime(2024, 11, 1)
END = datetime(2026, 2, 8)

def is_dst(dt):
    y = dt.year
    march = datetime(y, 3, 31)
    while march.weekday() != 6: march -= timedelta(days=1)
    oct = datetime(y, 10, 31)
    while oct.weekday() != 6: oct -= timedelta(days=1)
    return march.date() <= dt <= oct.date()

def asian_times(dt):
    if is_dst(dt): return time(1, 0), time(4, 0)
    return time(0, 0), time(3, 0)

def calc_lot(rng):
    rpu = rng * (1 - FIBO)
    if rpu <= 0: return MIN_LOT
    lot = TARGET_RISK / (rpu * 100)
    return max(MIN_LOT, min(MAX_LOT, round(lot, 2)))

print("="*70)
print("DEEP ANALYSIS: Asian Session XAUUSD - Past 15 Months")
print("="*70)
print(f"Period: {START.date()} to {END.date()}")
print(f"Strategy: {FIBO*100}% Fibo | 1:{RR} R:R | ${TARGET_RISK} risk/trade")
print("="*70)
print()

# Connect
if not mt5.initialize(login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER):
    print(f"MT5 connection failed: {mt5.last_error()}")
    sys.exit(1)

info = mt5.account_info()
print(f"Connected | Account: {info.login} | Balance: ${info.balance:,.2f}")
print()

# Load data
print("Loading data...")
frames = []
cs = START
while cs < END:
    ce = min(datetime(cs.year + 1, 1, 1), END)
    rates = mt5.copy_rates_range(SYMBOL, mt5.TIMEFRAME_M15, cs, ce)
    if rates is not None and len(rates) > 0:
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        frames.append(df)
        print(f"  {cs.year}: {len(df)} candles")
    cs = ce

mt5.shutdown()

if not frames:
    print("No data!")
    sys.exit(1)

all_data = pd.concat(frames, ignore_index=True)
all_data = all_data.drop_duplicates(subset='time').sort_values('time').reset_index(drop=True)
print(f"Total: {len(all_data)} candles")
print()

# Run backtest
trades = []
current = START.date()
end_d = END.date()

while current <= end_d:
    if current.weekday() >= 5:
        current += timedelta(days=1)
        continue

    start_t, end_t = asian_times(current)
    s_dt = datetime.combine(current, start_t)
    e_dt = datetime.combine(current, end_t)
    mask = (all_data['time'] >= s_dt) & (all_data['time'] <= e_dt)
    asian_df = all_data[mask].copy()

    if len(asian_df) < 2:
        current += timedelta(days=1)
        continue

    asian_df['range'] = asian_df['high'] - asian_df['low']
    n = LOOKBACK
    ldf = asian_df.iloc[-n-1:-1] if len(asian_df) > n else asian_df
    if len(ldf) == 0:
        current += timedelta(days=1)
        continue

    candle = ldf.loc[ldf['range'].idxmax()]
    rng = candle['high'] - candle['low']
    if rng == 0:
        current += timedelta(days=1)
        continue

    is_bull = candle['close'] > candle['open']
    if is_bull:
        direction = "BUY"
        entry = candle['high'] - (rng * FIBO)
        sl = candle['low']
        risk = entry - sl
        tp = entry + (risk * RR)
    else:
        direction = "SELL"
        entry = candle['low'] + (rng * FIBO)
        sl = candle['high']
        risk = sl - entry
        tp = entry - (risk * RR)

    lot = calc_lot(rng)
    risk_dollars = risk * lot * 100

    # Simulate fill
    entry_ts = candle['time']
    future = all_data[all_data['time'] >= entry_ts]
    filled = False
    fill_time = None

    for _, bar in future.iterrows():
        if is_bull and bar['low'] <= entry:
            filled, fill_time = True, bar['time']
            break
        elif not is_bull and bar['high'] >= entry:
            filled, fill_time = True, bar['time']
            break

    if not filled:
        trades.append({'date': current, 'direction': direction, 'outcome': 'NO_FILL',
                       'profit_dollars': 0, 'profit_pips': 0, 'lot_size': lot,
                       'risk_dollars': risk_dollars, 'candle_range': rng})
        current += timedelta(days=1)
        continue

    # Track
    after = all_data[all_data['time'] > fill_time]
    outcome = None

    for _, bar in after.iterrows():
        if is_bull:
            if bar['high'] >= tp:
                outcome = "WIN"; break
            if bar['low'] <= sl:
                outcome = "LOSS"; break
        else:
            if bar['low'] <= tp:
                outcome = "WIN"; break
            if bar['high'] >= sl:
                outcome = "LOSS"; break

    if outcome is None:
        outcome = "OPEN"

    if outcome == "WIN":
        pips = abs(tp - entry) / 0.01
        dollars = pips * 0.01 * lot * 100
    elif outcome == "LOSS":
        pips = -abs(entry - sl) / 0.01
        dollars = pips * 0.01 * lot * 100
    else:
        pips = dollars = 0

    trades.append({'date': current, 'direction': direction, 'outcome': outcome,
                   'profit_dollars': round(dollars, 2), 'profit_pips': round(pips, 1),
                   'lot_size': lot, 'risk_dollars': round(risk_dollars, 2),
                   'candle_range': round(rng, 2), 'entry_price': round(entry, 2),
                   'stop_loss': round(sl, 2), 'take_profit': round(tp, 2)})

    current += timedelta(days=1)

# Analysis
df = pd.DataFrame(trades)
completed = df[df['outcome'].isin(['WIN', 'LOSS'])]
wins = completed[completed['outcome'] == 'WIN']
losses = completed[completed['outcome'] == 'LOSS']

total = len(completed)
n_wins = len(wins)
n_losses = len(losses)
wr = (n_wins / total * 100) if total > 0 else 0
total_pnl = completed['profit_dollars'].sum()
win_sum = wins['profit_dollars'].sum()
loss_sum = abs(losses['profit_dollars'].sum())
pf = win_sum / loss_sum if loss_sum > 0 else 0

avg_win = wins['profit_dollars'].mean() if n_wins > 0 else 0
avg_loss = losses['profit_dollars'].mean() if n_losses > 0 else 0

equity = completed['profit_dollars'].cumsum()
peak = equity.cummax()
dd = equity - peak
max_dd = dd.min() if len(dd) > 0 else 0
rf = abs(total_pnl / max_dd) if max_dd < 0 else 0

avg_win_pips = wins['profit_pips'].mean() if n_wins > 0 else 0
avg_loss_pips = abs(losses['profit_pips'].mean()) if n_losses > 0 else 1
avg_rr = avg_win_pips / avg_loss_pips if avg_loss_pips > 0 else 0

# Monthly
completed_m = completed.copy()
completed_m['month'] = pd.to_datetime(completed_m['date']).dt.to_period('M')
monthly = completed_m.groupby('month').agg(
    trades=('outcome', 'count'),
    wins=('outcome', lambda x: (x == 'WIN').sum()),
    pnl=('profit_dollars', 'sum')
).reset_index()
monthly['wr'] = (monthly['wins'] / monthly['trades'] * 100).round(1)
profitable_months = (monthly['pnl'] > 0).sum()
total_months = len(monthly)

# Direction
buy_trades = completed[completed['direction'] == 'BUY']
sell_trades = completed[completed['direction'] == 'SELL']

# Print results
print()
print("="*70)
print("15-MONTH DEEP ANALYSIS RESULTS")
print("="*70)
print()
print(f"  Total Trades:      {total}")
print(f"  Wins:              {n_wins}")
print(f"  Losses:            {n_losses}")
print(f"  No Fills:          {len(df[df['outcome'] == 'NO_FILL'])}")
print()
print(f"  WIN RATE:          {wr:.1f}%")
print(f"  TOTAL P&L:         ${total_pnl:,.2f}")
print(f"  PROFIT FACTOR:     {pf:.2f}")
print(f"  AVG R:R:           1:{avg_rr:.1f}")
print()
print(f"  Avg Win:           ${avg_win:,.2f}")
print(f"  Avg Loss:          ${avg_loss:,.2f}")
print(f"  Max Drawdown:      ${max_dd:,.2f}")
print(f"  Recovery Factor:   {rf:.1f}")
print()
print(f"  Avg Risk/Trade:    ${completed['risk_dollars'].mean():,.2f}")
print()

# Starting balance scenarios
print("="*70)
print("ACCOUNT GROWTH (Starting $10,000)")
print("="*70)
print()
starting = 10000
final = starting + total_pnl
ret = ((final - starting) / starting) * 100
monthly_avg = total_pnl / max(total_months, 1)
print(f"  Starting Balance:  ${starting:,.2f}")
print(f"  Final Balance:     ${final:,.2f}")
print(f"  Total Return:      {ret:+.1f}%")
print(f"  Avg Monthly P&L:   ${monthly_avg:,.2f}")
print(f"  Profitable Months: {profitable_months}/{total_months} ({profitable_months/max(total_months,1)*100:.0f}%)")
print()

# Monthly breakdown
print("="*70)
print("MONTHLY BREAKDOWN")
print("="*70)
print()
print(f"{'Month':<12} {'Trades':<8} {'Wins':<6} {'WR%':<8} {'P&L':>12}")
print("-"*50)
for _, row in monthly.iterrows():
    pnl_str = f"${row['pnl']:>10,.2f}"
    marker = "+" if row['pnl'] >= 0 else ""
    print(f"{str(row['month']):<12} {int(row['trades']):<8} {int(row['wins']):<6} {row['wr']:<7.1f}% {marker}{pnl_str}")

print()

# Direction analysis
print("="*70)
print("DIRECTION ANALYSIS")
print("="*70)
print()
for name, sub in [("BUY", buy_trades), ("SELL", sell_trades)]:
    if len(sub) > 0:
        sub_wr = (sub['outcome'] == 'WIN').mean() * 100
        sub_pnl = sub['profit_dollars'].sum()
        print(f"  {name:4}: {len(sub)} trades | WR: {sub_wr:.1f}% | P&L: ${sub_pnl:,.2f}")
print()

# Marketing summary
print("="*70)
print("MARKETING SUMMARY")
print("="*70)
print()
print(f"  >>> ${total_pnl:,.0f} profit in {total_months} months <<<")
print(f"  >>> {wr:.0f}% win rate with {pf:.2f} profit factor <<<")
print(f"  >>> {profitable_months}/{total_months} profitable months ({profitable_months/max(total_months,1)*100:.0f}%) <<<")
print(f"  >>> {ret:+.0f}% return on $10,000 starting balance <<<")
print(f"  >>> Average {avg_rr:.1f}:1 reward-to-risk ratio <<<")
print()

# Save
save_name = f"analysis_15m_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
df.to_csv(save_name, index=False)
print(f"Results saved to: {save_name}")
print()
print("Launch the dashboard with: streamlit run app.py")
print("="*70)
