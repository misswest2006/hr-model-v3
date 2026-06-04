import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

LEARNING_FILE = os.path.join(DATA_DIR, "model_learning.csv")


def main():

    if not os.path.exists(LEARNING_FILE):
        print("Missing model_learning.csv")
        return

    df = pd.read_csv(LEARNING_FILE)

    if df.empty:
        print("No learning data.")
        return

    if "HRResult" not in df.columns:
        print("No HR results graded yet.")
        return

    graded = df[
        df["HRResult"].isin(["HR", "NO HR"])
    ].copy()

    if graded.empty:
        print("No graded plays yet.")
        return

    print()
    print("=" * 70)
    print("MODEL LEARNING ANALYTICS")
    print("=" * 70)

    print()
    print("PLAY TYPE PERFORMANCE")
    print()

    play_stats = (
        graded.groupby("Play")
        .agg(
            Plays=("Player", "count"),
            HRs=("HRResult", lambda x: (x == "HR").sum())
        )
        .reset_index()
    )

    play_stats["HitRate"] = (
        play_stats["HRs"] /
        play_stats["Plays"] * 100
    ).round(2)

    print(play_stats.to_string(index=False))

    print()
    print("=" * 70)
    print("LINEUP SPOT PERFORMANCE")
    print("=" * 70)

    lineup = (
        graded.groupby("LineupSpot")
        .agg(
            Plays=("Player", "count"),
            HRs=("HRResult", lambda x: (x == "HR").sum())
        )
        .reset_index()
    )

    lineup["HitRate"] = (
        lineup["HRs"] /
        lineup["Plays"] * 100
    ).round(2)

    lineup = lineup.sort_values(
        "HitRate",
        ascending=False
    )

    print(lineup.to_string(index=False))

    print()
    print("=" * 70)
    print("CONFIDENCE BUCKETS")
    print("=" * 70)

    graded["ConfBucket"] = pd.cut(
        graded["Confidence"],
        bins=[0,70,80,90,95,100],
        labels=[
            "0-70",
            "70-80",
            "80-90",
            "90-95",
            "95-100"
        ]
    )

    conf = (
        graded.groupby("ConfBucket")
        .agg(
            Plays=("Player", "count"),
            HRs=("HRResult", lambda x: (x == "HR").sum())
        )
        .reset_index()
    )

    conf["HitRate"] = (
        conf["HRs"] /
        conf["Plays"] * 100
    ).round(2)

    print(conf.to_string(index=False))

    print()
    print("=" * 70)
    print("PITCHER WEAKNESS PERFORMANCE")
    print("=" * 70)

    graded["PitcherBucket"] = pd.cut(
        graded["PitcherHRWeaknessScore"],
        bins=[0,3,5,7,10],
        labels=[
            "0-3",
            "4-5",
            "6-7",
            "8-10"
        ]
    )

    pitcher = (
        graded.groupby("PitcherBucket")
        .agg(
            Plays=("Player", "count"),
            HRs=("HRResult", lambda x: (x == "HR").sum())
        )
        .reset_index()
    )

    pitcher["HitRate"] = (
        pitcher["HRs"] /
        pitcher["Plays"] * 100
    ).round(2)

    print(pitcher.to_string(index=False))

    print()
    print("=" * 70)
    print("TOP PERFORMERS")
    print("=" * 70)

    players = (
        graded.groupby("Player")
        .agg(
            Plays=("Player", "count"),
            HRs=("HRResult", lambda x: (x == "HR").sum())
        )
        .reset_index()
    )

    players = players.sort_values(
        ["HRs", "Plays"],
        ascending=False
    )

    print(players.head(20).to_string(index=False))


if __name__ == "__main__":
    main()