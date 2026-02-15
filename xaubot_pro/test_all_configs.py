# Quick summary of already tested configurations:

print("=" * 80)
print("CONFIGURATION COMPARISON - ASIAN SESSION FIBONACCI STRATEGY")
print("=" * 80)
print()

configs = [
    {
        "name": "1. ORIGINAL (No Expiration, No Time Exit)",
        "entry_expiration": "None",
        "time_exit": "None",
        "total_trades": 491,
        "wins": 126,
        "losses": 364,
        "expired": 0,
        "win_rate": 25.71,
        "total_profit": 8567.38,
        "avg_win": 154.66,
        "avg_loss": -30.00,
        "profit_factor": 1.78,
        "rr_achieved": 5.16
    },
    {
        "name": "4. BOTH (45min Expiration + 12hr Time Exit)",
        "entry_expiration": "3 candles (45min)",
        "time_exit": "12 hours",
        "total_trades": 491,
        "wins": 81,
        "losses": 319,
        "expired": 91,
        "win_rate": 20.25,
        "total_profit": 276.48,
        "avg_win": 116.89,
        "avg_loss": -28.81,
        "profit_factor": 1.03,
        "rr_achieved": 4.06
    }
]

print("Configuration #1: ORIGINAL")
print("-" * 80)
print(f"Entry Expiration: None")
print(f"Time Exit: None")
print(f"Total Trades: 491 | Wins: 126 | Losses: 364 | Expired: 0")
print(f"Win Rate: 25.71%")
print(f"Total Profit: ${8567.38:,.2f}")
print(f"Avg Win: ${154.66} | Avg Loss: $-{30.00}")
print(f"Profit Factor: 1.78 | R:R: 1:5.16")
print()

print("Configuration #4: BOTH RULES")
print("-" * 80)
print(f"Entry Expiration: 3 candles (45 minutes)")
print(f"Time Exit: 12 hours")
print(f"Total Trades: 491 | Wins: 81 | Losses: 319 | Expired: 91")
print(f"Win Rate: 20.25%")
print(f"Total Profit: ${276.48:,.2f}")
print(f"Avg Win: ${116.89} | Avg Loss: $-{28.81}")
print(f"Profit Factor: 1.03 | R:R: 1:4.06")
print()

print("=" * 80)
print("RECOMMENDATION")
print("=" * 80)
print()
print("🏆 WINNER: Configuration #1 (ORIGINAL)")
print()
print("Why:")
print("  ✅ 31x higher profit ($8,567 vs $276)")
print("  ✅ Higher win rate (25.71% vs 20.25%)")
print("  ✅ Higher profit factor (1.78 vs 1.03)")
print("  ✅ Better R:R achieved (5.16 vs 4.06)")
print("  ✅ More wins (126 vs 81)")
print()
print("The entry expiration and time exit rules reduced profitability by 96.8%.")
print("The original strategy works best - let trades run to their natural TP/SL.")
print()
print("=" * 80)

