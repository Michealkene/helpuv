import pandas as pd
from datetime import datetime

# Read the CSV file from the original backtest
df = pd.read_csv('../backtest_results_20260206_091418.csv')

print("=" * 100)
print("COMPREHENSIVE STRATEGY ANALYSIS - ASIAN SESSION FIBONACCI STRATEGY")
print("=" * 100)
print()

# Convert date column to datetime
df['date'] = pd.to_datetime(df['date'])
df['month'] = df['date'].dt.to_period('M')

# Overall Statistics
print("OVERALL PERFORMANCE (Jan 2024 - Feb 2026)")
print("-" * 100)
total_trades = len(df)
wins = len(df[df['outcome'] == 'WIN'])
losses = len(df[df['outcome'] == 'LOSS'])
win_rate = (wins / (wins + losses) * 100)
total_profit = df['profit_dollars'].sum()
total_pips = df['profit_pips'].sum()

print(f"Total Trades: {total_trades}")
print(f"Wins: {wins} | Losses: {losses}")
print(f"Win Rate: {win_rate:.2f}%")
print(f"Total Profit: ${total_profit:,.2f} ({total_pips:,.1f} pips)")
print(f"Average Win: ${df[df['outcome']=='WIN']['profit_dollars'].mean():.2f}")
print(f"Average Loss: ${df[df['outcome']=='LOSS']['profit_dollars'].mean():.2f}")
print()

# Monthly Breakdown
print("=" * 100)
print("DETAILED MONTHLY BREAKDOWN")
print("=" * 100)
monthly = df.groupby('month').agg({
    'outcome': lambda x: (x == 'WIN').sum(),
    'profit_dollars': 'sum',
    'profit_pips': 'sum',
    'date': 'count'
}).rename(columns={'outcome': 'wins', 'profit_dollars': 'profit_usd', 'profit_pips': 'profit_pips', 'date': 'total_trades'})

monthly['losses'] = df.groupby('month')['outcome'].apply(lambda x: (x == 'LOSS').sum())
monthly['win_rate'] = (monthly['wins'] / monthly['total_trades'] * 100).round(1)

print(f"\n{'Month':<12} {'Trades':>7} {'Wins':>5} {'Losses':>7} {'Win%':>7} {'Profit $':>12} {'Pips':>12}")
print("-" * 100)
for month, row in monthly.iterrows():
    profit_symbol = "+" if row['profit_usd'] >= 0 else ""
    print(f"{str(month):<12} {int(row['total_trades']):>7} {int(row['wins']):>5} {int(row['losses']):>7} "
          f"{row['win_rate']:>6.1f}% {profit_symbol}${row['profit_usd']:>10,.2f} {profit_symbol}{row['profit_pips']:>10,.0f}")

# Best and Worst Months
print()
print("=" * 100)
print("BEST & WORST MONTHS")
print("=" * 100)
best_month = monthly['profit_usd'].idxmax()
worst_month = monthly['profit_usd'].idxmin()
best_wr_month = monthly['win_rate'].idxmax()

print(f"\nBEST PROFIT MONTH: {best_month}")
print(f"   Profit: ${monthly.loc[best_month, 'profit_usd']:,.2f} ({monthly.loc[best_month, 'profit_pips']:,.0f} pips)")
print(f"   Trades: {int(monthly.loc[best_month, 'total_trades'])} | Wins: {int(monthly.loc[best_month, 'wins'])} | Win Rate: {monthly.loc[best_month, 'win_rate']:.1f}%")

print(f"\nWORST LOSS MONTH: {worst_month}")
print(f"   Loss: ${monthly.loc[worst_month, 'profit_usd']:,.2f} ({monthly.loc[worst_month, 'profit_pips']:,.0f} pips)")
print(f"   Trades: {int(monthly.loc[worst_month, 'total_trades'])} | Wins: {int(monthly.loc[worst_month, 'wins'])} | Win Rate: {monthly.loc[worst_month, 'win_rate']:.1f}%")

print(f"\nBEST WIN RATE MONTH: {best_wr_month}")
print(f"   Win Rate: {monthly.loc[best_wr_month, 'win_rate']:.1f}%")
print(f"   Profit: ${monthly.loc[best_wr_month, 'profit_usd']:,.2f}")
print(f"   Trades: {int(monthly.loc[best_wr_month, 'total_trades'])} | Wins: {int(monthly.loc[best_wr_month, 'wins'])}")

# Winning and Losing Streaks
print()
print("=" * 100)
print("WINNING & LOSING STREAKS")
print("=" * 100)

# Calculate streaks
streaks = []
current_streak = 0
streak_start_idx = 0
last_outcome = None

for idx, row in df.iterrows():
    if row['outcome'] == 'OPEN':
        continue

    if row['outcome'] == last_outcome:
        current_streak += 1
    else:
        if last_outcome is not None:
            streaks.append({
                'type': last_outcome,
                'length': current_streak,
                'start_date': df.loc[streak_start_idx, 'date'],
                'end_date': df.loc[idx-1, 'date']
            })
        current_streak = 1
        streak_start_idx = idx
        last_outcome = row['outcome']

# Add final streak
if last_outcome is not None:
    streaks.append({
        'type': last_outcome,
        'length': current_streak,
        'start_date': df.loc[streak_start_idx, 'date'],
        'end_date': df.iloc[-1]['date']
    })

# Find longest streaks
win_streaks = [s for s in streaks if s['type'] == 'WIN']
loss_streaks = [s for s in streaks if s['type'] == 'LOSS']

longest_win = max(win_streaks, key=lambda x: x['length']) if win_streaks else None
longest_loss = max(loss_streaks, key=lambda x: x['length']) if loss_streaks else None

if longest_win:
    print(f"\nLONGEST WINNING STREAK: {longest_win['length']} consecutive wins")
    print(f"   Period: {longest_win['start_date'].strftime('%Y-%m-%d')} to {longest_win['end_date'].strftime('%Y-%m-%d')}")
    print(f"   Month: {longest_win['start_date'].strftime('%B %Y')}")

    # Calculate profit during winning streak
    win_streak_df = df[(df['date'] >= longest_win['start_date']) &
                       (df['date'] <= longest_win['end_date']) &
                       (df['outcome'] == 'WIN')]
    win_streak_profit = win_streak_df['profit_dollars'].sum()
    print(f"   Profit during streak: ${win_streak_profit:,.2f}")

if longest_loss:
    print(f"\nLONGEST LOSING STREAK: {longest_loss['length']} consecutive losses")
    print(f"   Period: {longest_loss['start_date'].strftime('%Y-%m-%d')} to {longest_loss['end_date'].strftime('%Y-%m-%d')}")
    print(f"   Month: {longest_loss['start_date'].strftime('%B %Y')}")

    # Calculate loss during losing streak
    loss_streak_df = df[(df['date'] >= longest_loss['start_date']) &
                        (df['date'] <= longest_loss['end_date']) &
                        (df['outcome'] == 'LOSS')]
    loss_streak_loss = loss_streak_df['profit_dollars'].sum()
    print(f"   Loss during streak: ${loss_streak_loss:,.2f}")

# Biggest Single Trades
print()
print("=" * 100)
print("BIGGEST INDIVIDUAL TRADES")
print("=" * 100)

biggest_win = df[df['outcome'] == 'WIN'].nlargest(5, 'profit_dollars')
biggest_loss = df[df['outcome'] == 'LOSS'].nsmallest(5, 'profit_dollars')

print(f"\nTOP 5 BIGGEST WINS:")
print(f"{'Date':<12} {'Direction':<8} {'Profit':>12} {'Pips':>10}")
print("-" * 50)
for idx, row in biggest_win.iterrows():
    print(f"{row['date'].strftime('%Y-%m-%d'):<12} {row['direction']:<8} ${row['profit_dollars']:>10,.2f} {row['profit_pips']:>9,.0f}")

print(f"\nTOP 5 BIGGEST LOSSES:")
print(f"{'Date':<12} {'Direction':<8} {'Loss':>12} {'Pips':>10}")
print("-" * 50)
for idx, row in biggest_loss.iterrows():
    print(f"{row['date'].strftime('%Y-%m-%d'):<12} {row['direction']:<8} ${row['profit_dollars']:>10,.2f} {row['profit_pips']:>9,.0f}")

# Yearly Summary
print()
print("=" * 100)
print("YEARLY SUMMARY")
print("=" * 100)
df['year'] = df['date'].dt.year
yearly = df.groupby('year').agg({
    'outcome': lambda x: (x == 'WIN').sum(),
    'profit_dollars': 'sum',
    'date': 'count'
}).rename(columns={'outcome': 'wins', 'profit_dollars': 'profit', 'date': 'total_trades'})

yearly['win_rate'] = (yearly['wins'] / yearly['total_trades'] * 100).round(1)

print(f"\n{'Year':<8} {'Trades':>7} {'Wins':>5} {'Win%':>7} {'Profit':>12}")
print("-" * 50)
for year, row in yearly.iterrows():
    profit_symbol = "+" if row['profit'] >= 0 else ""
    print(f"{year:<8} {int(row['total_trades']):>7} {int(row['wins']):>5} {row['win_rate']:>6.1f}% {profit_symbol}${row['profit']:>10,.2f}")

print()
print("=" * 100)
print("ANALYSIS COMPLETE")
print("=" * 100)
