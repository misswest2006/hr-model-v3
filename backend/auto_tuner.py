import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

HISTORY_FILE = os.path.join(DATA_DIR, "hr_results_history.csv")
REPORT_FILE = os.path.join(DATA_DIR, "auto_tuner_report.csv")


def safe_num(value, default=0.0):
    try:
        if value is None:
            return default
        if pd.isna(value):
            return default
        value = str(value).strip()
        if value == "":
            return default
        return float(value)
    except Exception:
        return default


def summarize_group(df, category, group_col):
    rows = []

    if group_col not in df.columns:
        return rows

    for bucket, group in df.groupby(group_col):
        plays = len(group)
        wins = int((group["Profit"] > 0).sum())
        losses = int((group["Profit"] < 0).sum())
        stake = group["Stake"].sum()
        profit = group["Profit"].sum()

        win_rate = round((wins / plays) * 100, 2) if plays else 0
        roi = round((profit / stake) * 100, 2) if stake else 0

        rows.append({
            "Category": category,
            "Bucket": bucket,
            "Plays": plays,
            "Wins": wins,
            "Losses": losses,
            "Stake": round(stake, 2),
            "Profit": round(profit, 2),
            "WinRate": win_rate,
            "ROI": roi,
        })

    return rows


def recommendation(row):
    category = row["Category"]
    bucket = row["Bucket"]
    plays = int(row["Plays"])
    roi = float(row["ROI"])
    win_rate = float(row["WinRate"])

    if plays < 5:
        return "Sample too small. Track more before changing weight."

    if roi >= 25 and win_rate >= 15:
        return f"Increase weight on {category} = {bucket}"

    if roi <= -20:
        return f"Decrease weight on {category} = {bucket}"

    return "Hold steady"


def main():
    if not os.path.exists(HISTORY_FILE):
        print("Missing hr_results_history.csv")
        return

    df = pd.read_csv(HISTORY_FILE)

    if df.empty:
        print("No historical results yet.")
        return

    for col in [
        "Profit",
        "Stake",
        "Edge",
        "Confidence",
        "HRScore",
        "LineupSpot",
        "PitcherHRWeaknessScore",
        "Snapshot",
        "Play",
        "Tier",
    ]:
        if col not in df.columns:
            df[col] = ""

    df["Profit"] = pd.to_numeric(df["Profit"], errors="coerce").fillna(0)
    df["Stake"] = pd.to_numeric(df["Stake"], errors="coerce").fillna(0)
    df["Edge"] = pd.to_numeric(df["Edge"], errors="coerce").fillna(0)
    df["Confidence"] = pd.to_numeric(df["Confidence"], errors="coerce").fillna(0)
    df["HRScore"] = pd.to_numeric(df["HRScore"], errors="coerce").fillna(0)
    df["LineupSpot"] = pd.to_numeric(df["LineupSpot"], errors="coerce").fillna(0)
    df["PitcherHRWeaknessScore"] = pd.to_numeric(
        df["PitcherHRWeaknessScore"],
        errors="coerce"
    ).fillna(0)

    # Only use actually graded betting results.
    graded = df[df["Profit"] != 0].copy()

    if graded.empty:
        print("No graded betting results found.")
        return

    graded["Snapshot"] = graded["Snapshot"].fillna("").astype(str).str.strip()
    graded["Snapshot"] = graded["Snapshot"].replace("", "UNKNOWN")

    graded["EdgeBucket"] = pd.cut(
        graded["Edge"],
        bins=[-1, 0, 0.03, 0.05, 0.10, 0.15, 0.20, 1],
        labels=[
            "Negative",
            "0-3%",
            "3-5%",
            "5-10%",
            "10-15%",
            "15-20%",
            "20%+",
        ]
    )

    graded["ConfidenceBucket"] = pd.cut(
        graded["Confidence"],
        bins=[0, 70, 80, 85, 90, 95, 100],
        labels=[
            "0-70",
            "70-80",
            "80-85",
            "85-90",
            "90-95",
            "95-100",
        ]
    )

    graded["HRScoreBucket"] = pd.cut(
        graded["HRScore"],
        bins=[0, 70, 80, 85, 90, 95, 100],
        labels=[
            "0-70",
            "70-80",
            "80-85",
            "85-90",
            "90-95",
            "95-100",
        ]
    )

    graded["PitcherWeaknessBucket"] = pd.cut(
        graded["PitcherHRWeaknessScore"],
        bins=[0, 3, 5, 7, 10],
        labels=[
            "0-3",
            "4-5",
            "6-7",
            "8-10",
        ]
    )

    rows = []

    rows += summarize_group(graded, "Snapshot", "Snapshot")
    rows += summarize_group(graded, "EdgeBucket", "EdgeBucket")
    rows += summarize_group(graded, "ConfidenceBucket", "ConfidenceBucket")
    rows += summarize_group(graded, "HRScoreBucket", "HRScoreBucket")
    rows += summarize_group(graded, "LineupSpot", "LineupSpot")
    rows += summarize_group(graded, "PitcherWeakness", "PitcherWeaknessBucket")
    rows += summarize_group(graded, "Play", "Play")
    rows += summarize_group(graded, "Tier", "Tier")

    report = pd.DataFrame(rows)

    if report.empty:
        print("No auto tuner report rows generated.")
        return

    report["Recommendation"] = report.apply(recommendation, axis=1)

    report = report.sort_values(
        by=["ROI", "WinRate", "Profit"],
        ascending=[False, False, False]
    )

    report.to_csv(REPORT_FILE, index=False, encoding="utf-8-sig")

    total_plays = len(graded)
    wins = int((graded["Profit"] > 0).sum())
    losses = int((graded["Profit"] < 0).sum())
    total_stake = round(graded["Stake"].sum(), 2)
    total_profit = round(graded["Profit"].sum(), 2)
    total_roi = round((total_profit / total_stake) * 100, 2) if total_stake else 0
    win_rate = round((wins / total_plays) * 100, 2) if total_plays else 0

    print()
    print("=" * 70)
    print("AUTO TUNER REPORT V3.8")
    print("=" * 70)
    print()
    print(f"Graded Bets: {total_plays}")
    print(f"Wins: {wins}")
    print(f"Losses: {losses}")
    print(f"Win Rate: {win_rate}%")
    print(f"Stake: {total_stake}u")
    print(f"Profit: {total_profit}u")
    print(f"ROI: {total_roi}%")
    print()

    print("TOP POSITIVE SIGNALS")
    print("-" * 70)
    positive = report[
        (report["Plays"] >= 5) &
        (report["ROI"] > 0)
    ].head(12)

    if positive.empty:
        print("No strong positive signals yet.")
    else:
        print(positive.to_string(index=False))

    print()
    print("TOP NEGATIVE SIGNALS")
    print("-" * 70)
    negative = report[
        (report["Plays"] >= 5) &
        (report["ROI"] < 0)
    ].sort_values("ROI", ascending=True).head(12)

    if negative.empty:
        print("No strong negative signals yet.")
    else:
        print(negative.to_string(index=False))

    print()
    print("SNAPSHOT PERFORMANCE")
    print("-" * 70)
    snapshot = report[report["Category"] == "Snapshot"].sort_values(
        "ROI",
        ascending=False
    )

    print(snapshot.to_string(index=False))

    print()
    print("EDGE BUCKET PERFORMANCE")
    print("-" * 70)
    edge_report = report[report["Category"] == "EdgeBucket"].sort_values(
        "Bucket"
    )

    print(edge_report.to_string(index=False))

    print()
    print(f"Saved: {REPORT_FILE}")


if __name__ == "__main__":
    main()