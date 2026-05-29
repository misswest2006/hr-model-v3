import os
import pandas as pd
from datetime import datetime


HISTORY_COLUMNS = [
    "Date",
    "Player",
    "Team",
    "Pitcher",
    "BestBook",
    "BestOdds",
    "ModelProb",
    "Edge",
    "Stake",
    "Play",
    "Result",
    "Profit"
]


def save_results(results):

    history_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "data",
        "hr_results_history.csv"
    )

    if os.path.exists(history_path):

        history_df = pd.read_csv(history_path)

    else:

        history_df = pd.DataFrame(columns=HISTORY_COLUMNS)

    rows = []

    today = datetime.today().strftime("%Y-%m-%d")

    for play in results:

        if play["play"] != "YES 🔥":
            continue

        rows.append({
            "Date": today,
            "Player": play["player"],
            "Team": play["team"],
            "Pitcher": play["pitcher"],
            "BestBook": play["best_book"],
            "BestOdds": play["best_odds"],
            "ModelProb": play["model_prob"],
            "Edge": play["best_edge"],
            "Stake": play["stake"],
            "Play": play["play"],
            "Result": "",
            "Profit": "",
        })

    if rows:

        new_df = pd.DataFrame(rows)

        history_df = pd.concat(
            [history_df, new_df],
            ignore_index=True
        )

        history_df.to_csv(history_path, index=False)

        print(f"✅ Saved {len(rows)} YES plays to history.")

    else:

        print("⚠️ No YES plays to save.")