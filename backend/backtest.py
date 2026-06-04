import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

HISTORY_FILE = os.path.join(DATA_DIR, "hr_results_history.csv")


def safe_num(value, default=0.0):
    try:
        if value is None:
            return default
        if pd.isna(value):
            return default
        if str(value).strip() == "":
            return default
        return float(value)
    except Exception:
        return default


def normalize_result(row):
    profit = safe_num(row.get("Profit"), 0)

    if profit > 0:
        return "WIN"

    if profit < 0:
        return "LOSS"

    raw = str(row.get("Result", "")).strip().upper()
    hr_result = str(row.get("HRResult", "")).strip().upper()

    if raw in ["1", "WIN", "W", "HR", "YES"]:
        return "WIN"

    if raw in ["0", "LOSS", "L", "NO HR", "NO"]:
        return "LOSS"

    if hr_result == "HR":
        return "WIN"

    if hr_result == "NO HR":
        return "LOSS"

    return "PUSH"


def run_backtest():
    if not os.path.exists(HISTORY_FILE):
        print("Missing hr_results_history.csv")
        return

    df = pd.read_csv(HISTORY_FILE)

    if df.empty:
        print("No historical results yet.")
        return

    for col in ["Profit", "Stake", "Edge", "BestOdds", "Player", "Pitcher"]:
        if col not in df.columns:
            df[col] = 0

    df["Profit"] = pd.to_numeric(df["Profit"], errors="coerce").fillna(0)
    df["Stake"] = pd.to_numeric(df["Stake"], errors="coerce").fillna(0)
    df["Edge"] = pd.to_numeric(df["Edge"], errors="coerce").fillna(0)
    df["BestOdds"] = pd.to_numeric(df["BestOdds"], errors="coerce").fillna(0)

    df["BacktestResult"] = df.apply(normalize_result, axis=1)

    graded = df[df["BacktestResult"].isin(["WIN", "LOSS"])].copy()

    total_bets = len(graded)
    wins = int((graded["BacktestResult"] == "WIN").sum())
    losses = int((graded["BacktestResult"] == "LOSS").sum())

    win_rate = round((wins / total_bets) * 100, 2) if total_bets else 0

    total_profit = round(graded["Profit"].sum(), 2)
    total_staked = round(graded["Stake"].sum(), 2)
    roi = round((total_profit / total_staked) * 100, 2) if total_staked else 0
    avg_edge = round(graded["Edge"].mean() * 100, 2) if total_bets else 0

    print()
    print("HR MODEL BACKTEST RESULTS")
    print()
    print(f"Total Graded Bets: {total_bets}")
    print(f"Wins: {wins}")
    print(f"Losses: {losses}")
    print(f"Win Rate: {win_rate}%")
    print(f"Total Units Risked: {total_staked}u")
    print(f"Profit: {total_profit}u")
    print(f"ROI: {roi}%")
    print(f"Average Edge: {avg_edge}%")

    print()
    print("----------------------------")
    print()
    print("PERFORMANCE BY EDGE RANGE")
    print()

    edge_ranges = [
        (0.00, 0.05),
        (0.05, 0.10),
        (0.10, 0.15),
        (0.15, 0.20),
        (0.20, 1.00),
    ]

    for low, high in edge_ranges:
        subset = graded[
            (graded["Edge"] >= low) &
            (graded["Edge"] < high)
        ].copy()

        if subset.empty:
            continue

        subset_stake = subset["Stake"].sum()
        subset_profit = subset["Profit"].sum()
        subset_roi = round((subset_profit / subset_stake) * 100, 2) if subset_stake else 0
        subset_wins = int((subset["BacktestResult"] == "WIN").sum())
        subset_losses = int((subset["BacktestResult"] == "LOSS").sum())
        subset_win_rate = round((subset_wins / len(subset)) * 100, 2) if len(subset) else 0

        print(
            f"{round(low * 100)}%-{round(high * 100)}% Edge | "
            f"Bets: {len(subset)} | "
            f"Wins: {subset_wins} | "
            f"Losses: {subset_losses} | "
            f"Win Rate: {subset_win_rate}% | "
            f"ROI: {subset_roi}%"
        )

    print()
    print("----------------------------")
    print()
    print("TOP WINNING PLAYS")
    print()

    top_wins = graded[graded["Profit"] > 0].sort_values(
        by="Profit",
        ascending=False
    ).head(10)

    if top_wins.empty:
        print("No winning plays found.")
    else:
        show_cols = [
            "Date",
            "Player",
            "Pitcher",
            "BestOdds",
            "Stake",
            "Profit",
            "Edge",
            "BacktestResult",
        ]

        existing = [c for c in show_cols if c in top_wins.columns]

        print(top_wins[existing].to_string(index=False))

    print()
    print("----------------------------")
    print()
    print("TOP LOSING EXPOSURES")
    print()

    top_losses = graded[graded["Profit"] < 0].sort_values(
        by="Profit",
        ascending=True
    ).head(10)

    if top_losses.empty:
        print("No losing plays found.")
    else:
        show_cols = [
            "Date",
            "Player",
            "Pitcher",
            "BestOdds",
            "Stake",
            "Profit",
            "Edge",
            "BacktestResult",
        ]

        existing = [c for c in show_cols if c in top_losses.columns]

        print(top_losses[existing].to_string(index=False))


if __name__ == "__main__":
    run_backtest()