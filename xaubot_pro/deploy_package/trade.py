import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta, time
import pytz
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# ================= CONFIG =================

SYMBOL = "XAUUSD"
TIMEFRAME = mt5.TIMEFRAME_M15

# Asian session in GMT (with DST adjustment)
# Winter (Standard Time): 00:00-03:00 GMT
# Summer (Daylight Saving): 01:00-04:00 GMT
ASIAN_START_WINTER = time(0, 0)
ASIAN_END_WINTER = time(3, 0)
ASIAN_START_SUMMER = time(1, 0)
ASIAN_END_SUMMER = time(4, 0)

LOOKBACK_CANDLES = 6

# No spread
SPREAD_PIPS = 0

# Fibonacci retracement for entry
FIBO_RETRACEMENT = 0.45  # 45% retracement

# Risk/Reward
RR_RATIO = 4.0

# Dynamic lot sizing: target $100 risk per trade ($80-$120 range)
# Formula: lot = TARGET_RISK / (candle_range * (1 - FIBO_RETRACEMENT) * 100)
# Risk per trade = candle_range * 0.55 * lot * 100
DYNAMIC_LOT_SIZING = True
TARGET_RISK_DOLLARS = 100  # Target risk per trade in dollars
MIN_LOT = 0.01
MAX_LOT = 5.0
FIXED_LOT = 0.10  # Used when DYNAMIC_LOT_SIZING = False

# MT5 login (DEMO) - Update these with your credentials
MT5_LOGIN = 5046171682
MT5_PASSWORD = "2i_hYuTw"
MT5_SERVER = "MetaQuotes-Demo"

# Backtest period (maximum available data)
BACKTEST_START = datetime(2022, 1, 1)
BACKTEST_END = datetime(2026, 2, 8)

# =========================================

def is_dst(date):
    """
    Check if date is in Daylight Saving Time (DST) period
    DST in US/Europe typically: March last Sunday to October last Sunday
    """
    year = date.year

    # Find last Sunday of March
    march_last = datetime(year, 3, 31)
    while march_last.weekday() != 6:  # 6 = Sunday
        march_last -= timedelta(days=1)

    # Find last Sunday of October
    oct_last = datetime(year, 10, 31)
    while oct_last.weekday() != 6:
        oct_last -= timedelta(days=1)

    return march_last.date() <= date <= oct_last.date()

def connect_mt5():
    """Initialize MT5 connection"""
    if not mt5.initialize(login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER):
        print("❌ MT5 initialization failed!")
        print(f"Error: {mt5.last_error()}")
        return False

    print("✅ Connected to MT5 successfully")
    print(f"Account: {mt5.account_info().login}")
    print(f"Server: {mt5.account_info().server}")
    print()
    return True

def get_asian_session_data(date):
    """Get candles for Asian session on a specific date (with DST adjustment)"""
    # Check if date is in DST period
    if is_dst(date):
        start_dt = datetime.combine(date, ASIAN_START_SUMMER)
        end_dt = datetime.combine(date, ASIAN_END_SUMMER)
    else:
        start_dt = datetime.combine(date, ASIAN_START_WINTER)
        end_dt = datetime.combine(date, ASIAN_END_WINTER)

    rates = mt5.copy_rates_range(SYMBOL, TIMEFRAME, start_dt, end_dt)

    if rates is None or len(rates) == 0:
        return None, None, None

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')

    asian_high = df['high'].max()
    asian_low = df['low'].min()
    asian_range = asian_high - asian_low

    return asian_range, asian_high, asian_low, df

def get_biggest_candle(df, lookback=6):
    """Find the biggest candle in the lookback period"""
    if df is None or len(df) < 2:
        return None

    df = df.copy()
    df['range'] = df['high'] - df['low']

    # Get last 'lookback' candles (excluding the very last incomplete one)
    if len(df) > lookback:
        lookback_df = df.iloc[-lookback-1:-1]
    else:
        lookback_df = df

    if len(lookback_df) == 0:
        return None

    biggest_idx = lookback_df['range'].idxmax()
    return lookback_df.loc[biggest_idx]

def calculate_dynamic_lot(candle_range):
    """
    Calculate lot size so each trade risks ~$100 ($80-$120 range).
    For XAUUSD: risk_dollars = candle_range * (1 - FIBO) * lot * 100
    So: lot = TARGET_RISK / (candle_range * (1 - FIBO) * 100)
    Small candle ranges get bigger lots, big ranges get smaller lots.
    """
    risk_portion = 1 - FIBO_RETRACEMENT  # 0.55 of candle range is risk
    risk_per_unit = candle_range * risk_portion
    if risk_per_unit <= 0:
        return MIN_LOT
    lot = TARGET_RISK_DOLLARS / (risk_per_unit * 100)
    lot = round(lot, 2)  # Round to 0.01
    lot = max(MIN_LOT, min(MAX_LOT, lot))  # Clamp to MT5 limits
    return lot

def simulate_trade(entry_candle, lot, entry_time, all_data):
    """
    Simulate trade execution and track to TP or SL
    Entry: 45% Fibonacci retracement (no candle limit - waits until filled)
    SL: End of candle (high for SELL, low for BUY)
    TP: 4.5 R:R from entry
    Spread: 5 pips deducted from every trade
    No time exit - trade runs until TP or SL
    """
    # Determine direction
    is_bullish = entry_candle['close'] > entry_candle['open']
    candle_high = entry_candle['high']
    candle_low = entry_candle['low']
    candle_range = candle_high - candle_low

    # Spread adjustment (0.05 = 5 pips on XAUUSD)
    spread = SPREAD_PIPS * 0.01

    if is_bullish:
        direction = "BUY"
        entry_price = candle_high - (candle_range * FIBO_RETRACEMENT)
        entry_price += spread  # BUY fills at ask (higher)
        stop_loss = candle_low
        risk = entry_price - stop_loss
        take_profit = entry_price + (risk * RR_RATIO)
    else:
        direction = "SELL"
        entry_price = candle_low + (candle_range * FIBO_RETRACEMENT)
        entry_price -= spread  # SELL fills at bid (lower)
        stop_loss = candle_high
        risk = stop_loss - entry_price
        take_profit = entry_price - (risk * RR_RATIO)

    # Get all candles from entry signal onward (including signal candle itself)
    entry_timestamp = entry_candle['time']
    future_data = all_data[all_data['time'] >= entry_timestamp].copy()

    # Wait for entry price to be hit (no expiry)
    entry_confirmed = False
    actual_entry_time = None

    for idx, candle in future_data.iterrows():
        if is_bullish and candle['low'] <= entry_price:
            entry_confirmed = True
            actual_entry_time = candle['time']
            break
        elif not is_bullish and candle['high'] >= entry_price:
            entry_confirmed = True
            actual_entry_time = candle['time']
            break

    # Calculate risk in dollars for this trade
    risk_dollars = risk * lot * 100

    if not entry_confirmed:
        return {
            'direction': direction,
            'entry_time': entry_timestamp,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'exit_time': None,
            'exit_price': entry_price,
            'exit_reason': 'NO_FILL',
            'outcome': 'NO_FILL',
            'lot_size': lot,
            'profit_pips': 0,
            'profit_dollars': 0,
            'candle_range': candle_range,
            'risk_dollars': risk_dollars
        }

    # Get candles after actual entry
    future_data_after_entry = all_data[all_data['time'] > actual_entry_time].copy()

    # Track the trade - NO time exit, runs until TP or SL
    exit_time = None
    exit_price = None
    outcome = "OPEN"
    exit_reason = None

    for idx, candle in future_data_after_entry.iterrows():
        if is_bullish:
            if candle['high'] >= take_profit:
                exit_time = candle['time']
                exit_price = take_profit
                outcome = "WIN"
                exit_reason = "TP"
                break
            elif candle['low'] <= stop_loss:
                exit_time = candle['time']
                exit_price = stop_loss
                outcome = "LOSS"
                exit_reason = "SL"
                break
        else:  # SELL
            if candle['low'] <= take_profit:
                exit_time = candle['time']
                exit_price = take_profit
                outcome = "WIN"
                exit_reason = "TP"
                break
            elif candle['high'] >= stop_loss:
                exit_time = candle['time']
                exit_price = stop_loss
                outcome = "LOSS"
                exit_reason = "SL"
                break

    # Calculate profit
    if outcome == "WIN":
        profit_pips = abs(take_profit - entry_price) / 0.01
        profit_dollars = profit_pips * 0.01 * lot * 100
    elif outcome == "LOSS":
        profit_pips = -abs(entry_price - stop_loss) / 0.01
        profit_dollars = profit_pips * 0.01 * lot * 100
    else:
        profit_pips = 0
        profit_dollars = 0

    return {
        'direction': direction,
        'entry_time': actual_entry_time if entry_confirmed else entry_timestamp,
        'entry_price': entry_price,
        'stop_loss': stop_loss,
        'take_profit': take_profit,
        'exit_time': exit_time,
        'exit_price': exit_price,
        'exit_reason': exit_reason,
        'outcome': outcome,
        'lot_size': lot,
        'profit_pips': profit_pips,
        'profit_dollars': profit_dollars,
        'candle_range': candle_range,
        'risk_dollars': risk_dollars
    }

def run_backtest():
    """Main backtest function"""

    print("="*70)
    print("🚀 ASIAN SESSION XAUUSD BACKTEST - FIBONACCI STRATEGY")
    print("="*70)
    print(f"Symbol: {SYMBOL}")
    print(f"Timeframe: M15")
    print(f"Period: {BACKTEST_START.date()} to {BACKTEST_END.date()}")
    print(f"Asian Session (Winter): {ASIAN_START_WINTER} - {ASIAN_END_WINTER} GMT")
    print(f"Asian Session (Summer/DST): {ASIAN_START_SUMMER} - {ASIAN_END_SUMMER} GMT")
    print(f"Entry: {FIBO_RETRACEMENT*100}% Fibonacci Retracement")
    print(f"Stop Loss: Candle High/Low")
    print(f"Risk:Reward: 1:{RR_RATIO}")
    print(f"Spread: None")
    if DYNAMIC_LOT_SIZING:
        print(f"Lot Sizing: DYNAMIC (~${TARGET_RISK_DOLLARS} risk/trade, lot {MIN_LOT}-{MAX_LOT})")
    else:
        print(f"Lot Sizing: FIXED {FIXED_LOT}")
    print(f"Entry Expiry: None (waits until filled)")
    print(f"Time Exit: None (TP or SL only)")
    print("="*70)
    print()

    # Connect to MT5
    if not connect_mt5():
        return

    # Verify symbol
    symbol_info = mt5.symbol_info(SYMBOL)
    if symbol_info is None:
        print(f"❌ Symbol {SYMBOL} not found!")
        mt5.shutdown()
        return

    print(f"📊 Loading historical data...")
    print()

    # Load data in yearly chunks to avoid MT5 limits
    all_frames = []
    chunk_start = BACKTEST_START
    while chunk_start < BACKTEST_END:
        chunk_end = min(datetime(chunk_start.year + 1, 1, 1), BACKTEST_END)
        rates = mt5.copy_rates_range(SYMBOL, TIMEFRAME, chunk_start, chunk_end)
        if rates is not None and len(rates) > 0:
            df_chunk = pd.DataFrame(rates)
            df_chunk['time'] = pd.to_datetime(df_chunk['time'], unit='s')
            all_frames.append(df_chunk)
            print(f"  Loaded {len(df_chunk)} candles for {chunk_start.year}")
        else:
            print(f"  No data for {chunk_start.year}")
        chunk_start = chunk_end

    if len(all_frames) == 0:
        print("❌ No data retrieved! Check your date range and symbol.")
        mt5.shutdown()
        return

    all_data = pd.concat(all_frames, ignore_index=True)
    all_data = all_data.drop_duplicates(subset='time').sort_values('time').reset_index(drop=True)

    print(f"\n✅ Loaded {len(all_data)} total candles ({all_data['time'].iloc[0].date()} to {all_data['time'].iloc[-1].date()})")
    print()

    # Track results
    trades = []
    current_date = BACKTEST_START.date()
    end_date = BACKTEST_END.date()

    days_checked = 0
    days_with_setup = 0

    print("🔍 Scanning for trade setups...")
    print()

    # Main backtest loop
    while current_date <= end_date:
        # Skip weekends
        if current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            continue

        days_checked += 1

        # Get Asian session data for this day
        result = get_asian_session_data(current_date)

        if result[0] is None:
            current_date += timedelta(days=1)
            continue

        asian_range, asian_high, asian_low, asian_df = result

        if asian_range == 0:
            current_date += timedelta(days=1)
            continue

        # Get biggest candle during Asian session
        biggest_candle = get_biggest_candle(asian_df, LOOKBACK_CANDLES)

        if biggest_candle is None:
            current_date += timedelta(days=1)
            continue

        # Calculate candle percentage
        candle_range = biggest_candle['high'] - biggest_candle['low']
        candle_pct = (candle_range / asian_range) * 100

        # Calculate lot size
        if DYNAMIC_LOT_SIZING:
            lot = calculate_dynamic_lot(candle_range)
        else:
            lot = FIXED_LOT

        days_with_setup += 1

        # Simulate the trade
        trade_result = simulate_trade(biggest_candle, lot, biggest_candle['time'], all_data)

        # Add date and candle info
        trade_result['date'] = current_date
        trade_result['candle_pct'] = candle_pct
        trade_result['asian_range'] = asian_range

        trades.append(trade_result)

        # Print trade info
        if trade_result['outcome'] == "WIN":
            symbol = "🟢"
        elif trade_result['outcome'] == "LOSS":
            symbol = "🔴"
        elif trade_result['outcome'] == "NO_FILL":
            symbol = "⏰"
        else:
            symbol = "⚪"

        exit_info = f" [{trade_result['exit_reason']}]" if trade_result['exit_reason'] else ""
        risk_info = f" | Risk: ${trade_result.get('risk_dollars', 0):.0f}" if DYNAMIC_LOT_SIZING else ""
        print(f"{symbol} {current_date} | {trade_result['direction']:4} | "
              f"Range: {candle_range:6.2f} | Lot: {lot:.2f}{risk_info} | "
              f"{trade_result['outcome']:7}{exit_info:12} | {trade_result['profit_pips']:+6.1f} pips | "
              f"${trade_result['profit_dollars']:+8.2f}")

        current_date += timedelta(days=1)

    mt5.shutdown()

    # ================= RESULTS ANALYSIS =================

    print()
    print("="*70)
    print("📊 BACKTEST RESULTS")
    print("="*70)
    print()

    if len(trades) == 0:
        print("❌ No trades found!")
        print(f"   Days checked: {days_checked}")
        print(f"   Days with potential setup: {days_with_setup}")
        print()
        print("💡 Suggestions:")
        print("   - Widen candle % range (e.g., 4-35%)")
        print("   - Extend backtest period")
        print("   - Check if Asian session has data")
        return

    df_trades = pd.DataFrame(trades)

    # Calculate metrics
    total_trades = len(df_trades)
    wins = len(df_trades[df_trades['outcome'] == 'WIN'])
    losses = len(df_trades[df_trades['outcome'] == 'LOSS'])
    expired_trades = len(df_trades[df_trades['outcome'] == 'NO_FILL'])
    open_trades = len(df_trades[df_trades['outcome'] == 'OPEN'])

    # Win rate excludes expired trades
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

    total_profit_pips = df_trades['profit_pips'].sum()
    total_profit_dollars = df_trades['profit_dollars'].sum()

    avg_win_pips = df_trades[df_trades['outcome'] == 'WIN']['profit_pips'].mean() if wins > 0 else 0
    avg_loss_pips = df_trades[df_trades['outcome'] == 'LOSS']['profit_pips'].mean() if losses > 0 else 0

    avg_win_dollars = df_trades[df_trades['outcome'] == 'WIN']['profit_dollars'].mean() if wins > 0 else 0
    avg_loss_dollars = df_trades[df_trades['outcome'] == 'LOSS']['profit_dollars'].mean() if losses > 0 else 0

    # Print summary
    print(f"📅 Period: {days_checked} trading days")
    print(f"🎯 Setups Found: {days_with_setup} days")
    print()
    print(f"📈 TOTAL TRADES: {total_trades}")
    print(f"   ✅ Wins: {wins}")
    print(f"   ❌ Losses: {losses}")
    print(f"   ⏰ No Fill: {expired_trades}")
    print(f"   ⚪ Open: {open_trades}")
    print()
    print("="*70)
    print(f"🎯 WIN RATE: {win_rate:.2f}%")
    print("="*70)
    print()

    # Profit metrics
    print(f"💰 PROFIT/LOSS:")
    print(f"   Total P&L: {total_profit_pips:+.1f} pips (${total_profit_dollars:+,.2f})")
    print(f"   Average Win: {avg_win_pips:.1f} pips (${avg_win_dollars:.2f})")
    print(f"   Average Loss: {avg_loss_pips:.1f} pips (${avg_loss_dollars:.2f})")
    print()

    # Risk stats (dynamic lot sizing)
    if DYNAMIC_LOT_SIZING and 'risk_dollars' in df_trades.columns:
        completed = df_trades[df_trades['outcome'].isin(['WIN', 'LOSS'])]
        print(f"🎲 RISK PER TRADE:")
        print(f"   Avg Risk: ${completed['risk_dollars'].mean():.2f}")
        print(f"   Min Risk: ${completed['risk_dollars'].min():.2f}")
        print(f"   Max Risk: ${completed['risk_dollars'].max():.2f}")
        print(f"   Avg Lot: {completed['lot_size'].mean():.2f}")
        print(f"   Lot Range: {completed['lot_size'].min():.2f} - {completed['lot_size'].max():.2f}")
        print()

    # Profit Factor
    if wins > 0 and losses > 0:
        total_wins = df_trades[df_trades['outcome'] == 'WIN']['profit_dollars'].sum()
        total_losses = abs(df_trades[df_trades['outcome'] == 'LOSS']['profit_dollars'].sum())
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        print(f"📊 Profit Factor: {profit_factor:.2f}")
    print()

    # Risk/Reward achieved
    if wins > 0:
        avg_rr = abs(avg_win_pips / avg_loss_pips) if avg_loss_pips != 0 else 0
        print(f"⚖️  Average R:R Achieved: 1:{avg_rr:.2f}")
        print()

    # Win/Loss streaks
    streaks = []
    current_streak = 0
    last_outcome = None

    for outcome in df_trades['outcome']:
        if outcome == 'OPEN':
            continue
        if outcome == last_outcome:
            current_streak += 1
        else:
            if last_outcome is not None:
                streaks.append((last_outcome, current_streak))
            current_streak = 1
            last_outcome = outcome

    if last_outcome is not None:
        streaks.append((last_outcome, current_streak))

    win_streaks = [s[1] for s in streaks if s[0] == 'WIN']
    loss_streaks = [s[1] for s in streaks if s[0] == 'LOSS']

    if win_streaks:
        print(f"🔥 Max Win Streak: {max(win_streaks)}")
    if loss_streaks:
        print(f"❄️  Max Loss Streak: {max(loss_streaks)}")
    print()

    # Monthly breakdown
    df_trades['month'] = pd.to_datetime(df_trades['date']).dt.to_period('M')
    monthly = df_trades.groupby('month').agg({
        'outcome': lambda x: (x == 'WIN').sum(),
        'profit_dollars': 'sum',
        'date': 'count'
    }).rename(columns={'outcome': 'wins', 'profit_dollars': 'profit', 'date': 'total_trades'})

    monthly['win_rate'] = (monthly['wins'] / monthly['total_trades'] * 100).round(1)

    print("="*70)
    print("📅 MONTHLY BREAKDOWN")
    print("="*70)
    print()
    print(f"{'Month':<12} {'Trades':<8} {'Wins':<6} {'Win%':<8} {'Profit':<12}")
    print("-"*70)

    for month, row in monthly.iterrows():
        print(f"{str(month):<12} {int(row['total_trades']):<8} {int(row['wins']):<6} "
              f"{row['win_rate']:<7.1f}% ${row['profit']:>10,.2f}")

    print()

    # Save to CSV
    output_file = f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df_trades.to_csv(output_file, index=False)
    print(f"💾 Detailed results saved to: {output_file}")
    print()

    # Summary verdict
    print("="*70)
    print("📋 SUMMARY")
    print("="*70)

    if win_rate >= 60:
        verdict = "🌟 EXCELLENT - Strong strategy!"
    elif win_rate >= 55:
        verdict = "✅ VERY GOOD - Solid performance"
    elif win_rate >= 50:
        verdict = "✅ GOOD - Profitable with 2:1 RR"
    elif win_rate >= 45:
        verdict = "⚠️  MARGINAL - Needs improvement"
    else:
        verdict = "❌ POOR - Consider revising strategy"

    print(verdict)
    print()

    if total_trades < 20:
        print("⚠️  Note: Limited sample size. Test longer period for more confidence.")

    print()
    print("="*70)

if __name__ == "__main__":
    try:
        run_backtest()
    except KeyboardInterrupt:
        print("\n\n⚠️  Backtest interrupted by user")
        mt5.shutdown()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        mt5.shutdown()
