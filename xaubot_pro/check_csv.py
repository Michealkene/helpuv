import pandas as pd
import os

csv_dir = os.path.dirname(os.path.abspath(__file__))
for f in sorted(os.listdir(csv_dir)):
    if f.startswith('backtest_results_') and f.endswith('.csv'):
        path = os.path.join(csv_dir, f)
        df = pd.read_csv(path)
        dates = df['date'].unique()
        print(f"\n{f}: {len(df)} trades")
        print(f"  Dates: {dates[0]} to {dates[-1]}")
        print(f"  Outcomes: {df['outcome'].value_counts().to_dict()}")
        print(f"  Total P&L: ${df['profit_dollars'].sum():,.2f}")
