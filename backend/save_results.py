import os
import pandas as pd


HISTORY_COLUMNS = [
    "Date",
    "Snapshot",
    "Player",
    "Team",
    "Pitcher",
    "BestBook",
    "BestOdds",
    "ModelProb",
    "RawModelProb",
    "Edge",
    "Confidence",
    "Grade",
    "Tier",
    "TopEdgeRank",
    "TopProbRank",
    "Stake",
    "Play",
    "Result",
    "Profit",
]


def safe_float(value, default=0.0):
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def safe_int(value, default=0):
    try:
        if value is None or pd.isna(value):
            return default
        return int(float(value))
    except Exception:
        return default


def safe_text(value):
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def clean_history_columns(df):
    for col in HISTORY_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    return df[HISTORY_COLUMNS]


def save_results(results):
    history_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "data",
        "hr_results_history.csv"
    )

    snapshot = os.getenv("MODEL_SNAPSHOT_LABEL", "MANUAL")

    if os.path.exists(history_path):
        history_df = pd.read_csv(history_path)
        history_df = clean_history_columns(history_df)
    else:
        history_df = pd.DataFrame(columns=HISTORY_COLUMNS)

    rows = []

    for play in results:
        rows.append({
            "Date": safe_text(play.get("date", "")),
            "Snapshot": snapshot,
            "Player": safe_text(play.get("player", "")),
            "Team": safe_text(play.get("team", "")),
            "Pitcher": safe_text(play.get("pitcher", "")),
            "BestBook": safe_text(play.get("best_book", "")),
            "BestOdds": safe_text(play.get("best_odds", "")),
            "ModelProb": round(safe_float(play.get("model_prob", 0)), 4),
            "RawModelProb": round(safe_float(play.get("raw_model_prob", 0)), 4),
            "Edge": round(safe_float(play.get("best_edge", 0)), 4),
            "Confidence": safe_int(play.get("confidence", 0)),
            "Grade": safe_text(play.get("grade", "")),
            "Tier": safe_text(play.get("tier", "")),
            "TopEdgeRank": safe_int(play.get("top_edge_rank", 999)),
            "TopProbRank": safe_int(play.get("top_prob_rank", 999)),
            "Stake": round(safe_float(play.get("stake", 0)), 2),
            "Play": safe_text(play.get("play", "")),
            "Result": "",
            "Profit": "",
        })

    if not rows:
        print("⚠️ No graded plays to save.")
        return

    new_df = pd.DataFrame(rows)
    new_df = clean_history_columns(new_df)

    combined = pd.concat([history_df, new_df], ignore_index=True)

    combined["Date"] = combined["Date"].astype(str).str.strip()
    combined["Snapshot"] = combined["Snapshot"].astype(str).str.strip()
    combined["Player"] = combined["Player"].astype(str).str.strip()
    combined["Team"] = combined["Team"].astype(str).str.strip()
    combined["Pitcher"] = combined["Pitcher"].astype(str).str.strip()
    combined["BestBook"] = combined["BestBook"].astype(str).str.strip()

    combined = combined.drop_duplicates(
        subset=[
            "Date",
            "Snapshot",
            "Player",
            "Team",
            "Pitcher",
            "BestBook",
        ],
        keep="last"
    )

    combined = combined.sort_values(
        by=["Date", "Snapshot", "Play", "Edge", "Confidence"],
        ascending=[False, True, False, False, False]
    )

    combined.to_csv(history_path, index=False)

    print(f"✅ Saved {len(new_df)} graded plays to history.")
    print("✅ Duplicate history rows removed.")
    print(f"✅ History total rows: {len(combined)}")