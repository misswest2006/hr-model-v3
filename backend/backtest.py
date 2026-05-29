import os
import pandas as pd


def run_backtest():

    file_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "data",
        "hr_results_history.csv"
    )

    df = pd.read_csv(file_path)

    if len(df) == 0:
        print("⚠️ No historical results yet.")
        return

    total_bets = len(df)

    wins = len(df[df["Result"] == 1])
    losses = len(df[df["Result"] == 0])

    win_rate = round((wins / total_bets) * 100, 2)

    total_profit = round(df["Profit"].sum(), 2)

    total_staked = round(df["Stake"].sum(), 2)

    roi = round((total_profit / total_staked) * 100, 2)

    avg_edge = round(df["Edge"].mean() * 100, 2)

    print("\n🔥 HR MODEL BACKTEST RESULTS 🔥\n")

    print(f"Total Bets: {total_bets}")
    print(f"Wins: {wins}")
    print(f"Losses: {losses}")

    print(f"\nWin Rate: {win_rate}%")

    print(f"Total Units Risked: {total_staked}u")
    print(f"Profit: {total_profit}u")

    print(f"\nROI: {roi}%")

    print(f"Average Edge: {avg_edge}%")

    print("\n----------------------------")

    print("\n📊 PERFORMANCE BY EDGE RANGE\n")

    edge_ranges = [
        (0.00, 0.05),
        (0.05, 0.10),
        (0.10, 0.15),
        (0.15, 0.20),
        (0.20, 1.00),
    ]

    for low, high in edge_ranges:

        subset = df[
            (df["Edge"] >= low) &
            (df["Edge"] < high)
        ]

        if len(subset) == 0:
            continue

        subset_roi = round(
            (subset["Profit"].sum() / subset["Stake"].sum()) * 100,
            2
        )

        print(
            f"{round(low*100)}%-{round(high*100)}% Edge | "
            f"Bets: {len(subset)} | "
            f"ROI: {subset_roi}%"
        )

    print("\n----------------------------")

    print("\n📚 TOP WINNING PLAYS\n")

    top_wins = df.sort_values(
        by="Profit",
        ascending=False
    ).head(10)

    print(
        top_wins[
            [
                "Player",
                "BestOdds",
                "Profit",
                "Edge"
            ]
        ]
    )


if __name__ == "__main__":
    run_backtest()