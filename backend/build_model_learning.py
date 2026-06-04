import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

RESULTS_FILE = os.path.join(DATA_DIR, "hr_model_results.csv")
LEARNING_FILE = os.path.join(DATA_DIR, "model_learning.csv")


OFFICIAL_ONLY = True

OFFICIAL_PLAYS = [
    "YES 🔥",
]

WATCH_PLAYS = [
    "POWER BAT 💣",
    "VALUE LEAN 👀",
]


def create_learning_file():
    columns = [
        "Date",
        "Player",
        "Team",
        "Pitcher",
        "LineupSpot",
        "Play",
        "Tier",
        "Grade",
        "Confidence",
        "HRScore",
        "DecisionScore",
        "SmashScore",
        "PowerScore",
        "ModelProb",
        "Edge",
        "BestOdds",
        "Stake",
        "PitcherHRWeaknessScore",
        "PitcherLineupWeakSpot",
        "TrackingGroup",
        "HRResult",
        "Profit"
    ]

    pd.DataFrame(columns=columns).to_csv(
        LEARNING_FILE,
        index=False,
        encoding="utf-8-sig"
    )


def main():
    if not os.path.exists(RESULTS_FILE):
        raise FileNotFoundError(f"Missing file: {RESULTS_FILE}")

    if not os.path.exists(LEARNING_FILE):
        create_learning_file()

    results = pd.read_csv(RESULTS_FILE)
    learning = pd.read_csv(LEARNING_FILE)

    if OFFICIAL_ONLY:
        plays = results[results["Play"].isin(OFFICIAL_PLAYS)].copy()
    else:
        plays = results[
            results["Play"].isin(OFFICIAL_PLAYS + WATCH_PLAYS)
        ].copy()

    if plays.empty:
        print("No plays found.")
        return

    keep_cols = [
        "Date",
        "Player",
        "Team",
        "Pitcher",
        "LineupSpot",
        "Play",
        "Tier",
        "Grade",
        "Confidence",
        "HRScore",
        "DecisionScore",
        "SmashScore",
        "PowerScore",
        "ModelProb",
        "Edge",
        "BestOdds",
        "Stake",
        "PitcherHRWeaknessScore",
        "PitcherLineupWeakSpot",
    ]

    for col in keep_cols:
        if col not in plays.columns:
            plays[col] = ""

    plays = plays[keep_cols]

    plays["TrackingGroup"] = plays["Play"].apply(
        lambda x: "OFFICIAL" if x in OFFICIAL_PLAYS else "WATCH"
    )

    plays["HRResult"] = ""
    plays["Profit"] = 0

    combined = pd.concat(
        [learning, plays],
        ignore_index=True
    )

    combined = combined.drop_duplicates(
        subset=[
            "Date",
            "Player",
            "Play",
            "TrackingGroup",
        ],
        keep="last"
    )

    combined.to_csv(
        LEARNING_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print()
    print("MODEL LEARNING UPDATED")
    print(f"Official only: {OFFICIAL_ONLY}")
    print(f"Rows: {len(combined)}")
    print(f"Today's plays added: {len(plays)}")
    print()
    print(
        plays[
            [
                "Player",
                "Play",
                "TrackingGroup",
                "Stake",
                "Confidence",
                "HRScore",
                "Edge"
            ]
        ].head(50).to_string(index=False)
    )


if __name__ == "__main__":
    main()