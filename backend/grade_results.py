import os
import argparse
import pandas as pd
import unicodedata


SNAPSHOT_PRIORITY = ["LOCK", "ONE_HOUR", "MORNING", "MANUAL"]


def clean_name(name):
    if pd.isna(name):
        return ""

    name = str(name).strip().lower()
    name = unicodedata.normalize("NFKD", name)
    name = "".join(ch for ch in name if not unicodedata.combining(ch))

    return name


def american_profit(odds, stake):
    try:
        odds = float(str(odds).replace("+", "").strip())
        stake = float(stake)
    except Exception:
        return 0.0

    if stake <= 0:
        return 0.0

    if odds > 0:
        return round((odds / 100) * stake, 2)

    return round((100 / abs(odds)) * stake, 2)


def active_snapshot_for_date(df, game_date):
    day_df = df[df["Date"] == game_date].copy()

    if "Snapshot" not in day_df.columns:
        return "", day_df

    day_df["Snapshot"] = day_df["Snapshot"].astype(str).str.strip()

    for snap in SNAPSHOT_PRIORITY:
        if snap in day_df["Snapshot"].values:
            return snap, day_df[day_df["Snapshot"] == snap].copy()

    return "", day_df


def grade_results(game_date=None):
    base_dir = os.path.join(os.path.dirname(__file__), "..", "data")

    history_path = os.path.join(base_dir, "hr_results_history.csv")
    hits_path = os.path.join(base_dir, "yesterday_hr_hits.csv")

    if not os.path.exists(history_path):
        print("❌ Missing data/hr_results_history.csv")
        return

    if not os.path.exists(hits_path):
        print("❌ Missing data/yesterday_hr_hits.csv")
        return

    history = pd.read_csv(history_path)
    hits = pd.read_csv(hits_path)

    if history.empty:
        print("⚠️ History file is empty.")
        return

    if hits.empty:
        print("⚠️ Hits file is empty.")
        return

    history["Date"] = history["Date"].astype(str).str.strip()
    hits["Date"] = hits["Date"].astype(str).str.strip()

    if game_date is None:
        game_date = history["Date"].max()

    game_date = str(game_date).strip()

    active_snapshot, active_df = active_snapshot_for_date(history, game_date)

    hits = hits[hits["Date"] == game_date].copy()
    hits["clean_player"] = hits["Player"].apply(clean_name)

    hit_lookup = set(hits["clean_player"])

    if "Result" not in history.columns:
        history["Result"] = ""

    if "Profit" not in history.columns:
        history["Profit"] = 0.0

    history["Result"] = history["Result"].fillna("").astype(str)
    history["Profit"] = pd.to_numeric(history["Profit"], errors="coerce").fillna(0.0)

    graded_count = 0
    hr_count = 0

    active_indexes = active_df.index.tolist()

    for idx in active_indexes:
        row = history.loc[idx]

        if row.get("Play", "") != "YES 🔥":
            continue

        player = clean_name(row.get("Player", ""))
        stake = float(row.get("Stake", 0) or 0)
        odds = row.get("BestOdds", 0)

        is_hr = player in hit_lookup

        if is_hr:
            history.at[idx, "Result"] = "HR"
            history.at[idx, "Profit"] = american_profit(odds, stake)
            hr_count += 1
        else:
            history.at[idx, "Result"] = "NO HR"
            history.at[idx, "Profit"] = round(-stake, 2) if stake > 0 else 0.0

        graded_count += 1

    history.to_csv(history_path, index=False)

    print(f"📅 Date graded: {game_date}")
    print(f"📸 Snapshot graded: {active_snapshot or 'ALL'}")
    print(f"✅ Graded {graded_count} YES plays.")
    print(f"🔥 HR hits matched: {hr_count}")
    print("✅ Results saved to data/hr_results_history.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None, help="Date to grade, format YYYY-MM-DD")
    args = parser.parse_args()

    grade_results(args.date)