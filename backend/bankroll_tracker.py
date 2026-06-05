import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

TRACKER_PATH = os.path.join(DATA_DIR, "yes_performance_tracker.csv")
BANKROLL_PATH = os.path.join(DATA_DIR, "bankroll_tracker.csv")

STARTING_BANKROLL = 100.0


def safe_num(value, default=0.0):
    try:
        if value is None:
            return default
        if pd.isna(value):
            return default

        value = str(value).replace("+", "").strip()

        if value == "" or value.lower() in ["nan", "none", "<na>"]:
            return default

        return float(value)

    except Exception:
        return default


def safe_text(value, default=""):
    try:
        if value is None:
            return default
        if pd.isna(value):
            return default

        value = str(value).strip()

        if value.lower() in ["nan", "none", "<na>"]:
            return default

        return value

    except Exception:
        return default


def load_csv(path):
    if not os.path.exists(path):
        return pd.DataFrame()

    try:
        return pd.read_csv(path)

    except Exception:
        return pd.DataFrame()


def play_priority(play_code):
    play_code = safe_text(play_code).upper().strip()

    if play_code == "YES":
        return 3

    if play_code == "POWER_BAT":
        return 2

    if play_code == "VALUE_LEAN":
        return 1

    return 0


def result_priority(result):
    result = safe_text(result).upper().strip()

    if result == "WIN":
        return 3

    if result == "LOSS":
        return 2

    return 1


def normalize_tracker():
    df = load_csv(TRACKER_PATH)

    if df.empty:
        return pd.DataFrame()

    needed_cols = [
        "Date", "Snapshot", "Player", "Team", "Pitcher", "PlayCode",
        "BestBook", "BestOdds", "Stake", "Result", "Profit",
        "ModelProb", "Edge", "Confidence", "HRScore", "DecisionScore",
        "SmashScore", "PowerScore", "LineupSpot", "PitcherWeakness",
        "PitcherSpotMatch", "Grade", "TierCode"
    ]

    for col in needed_cols:
        if col not in df.columns:
            df[col] = ""

    rows = []

    for _, row in df.iterrows():
        play_code = safe_text(row.get("PlayCode", "")).upper().strip()
        result = safe_text(row.get("Result", "PENDING")).upper().strip()

        if play_code not in ["YES", "POWER_BAT", "VALUE_LEAN"]:
            continue

        if result not in ["WIN", "LOSS", "PENDING"]:
            result = "PENDING"

        rows.append({
            "Date": safe_text(row.get("Date", "")),
            "Snapshot": safe_text(row.get("Snapshot", "")),
            "Player": safe_text(row.get("Player", "")),
            "Team": safe_text(row.get("Team", "")),
            "Pitcher": safe_text(row.get("Pitcher", "")),
            "PlayCode": play_code,
            "BestBook": safe_text(row.get("BestBook", "")),
            "BestOdds": safe_num(row.get("BestOdds", 0)),
            "Stake": safe_num(row.get("Stake", 0)),
            "Result": result,
            "Profit": safe_num(row.get("Profit", 0)),
            "ModelProb": safe_num(row.get("ModelProb", 0)),
            "Edge": safe_num(row.get("Edge", 0)),
            "Confidence": safe_num(row.get("Confidence", 0)),
            "HRScore": safe_num(row.get("HRScore", 0)),
            "DecisionScore": safe_num(row.get("DecisionScore", 0)),
            "SmashScore": safe_num(row.get("SmashScore", 0)),
            "PowerScore": safe_num(row.get("PowerScore", 0)),
            "LineupSpot": safe_num(row.get("LineupSpot", 0)),
            "PitcherWeakness": safe_num(row.get("PitcherWeakness", 0)),
            "PitcherSpotMatch": safe_num(row.get("PitcherSpotMatch", 0)),
            "Grade": safe_text(row.get("Grade", "")),
            "TierCode": safe_text(row.get("TierCode", "")),
        })

    out = pd.DataFrame(rows)

    if out.empty:
        return out

    out["PlayPriority"] = out["PlayCode"].apply(play_priority)
    out["ResultPriority"] = out["Result"].apply(result_priority)
    out["AbsProfit"] = out["Profit"].abs()

    out = out.sort_values(
        by=[
            "Date",
            "Player",
            "PlayPriority",
            "ResultPriority",
            "AbsProfit",
            "Confidence",
            "Edge",
        ],
        ascending=[True, True, False, False, False, False, False],
    )

    out = out.drop_duplicates(
        subset=["Date", "Player"],
        keep="first",
    )

    out = out.sort_values(
        by=["Date", "PlayPriority", "Confidence", "Edge"],
        ascending=[True, False, False, False],
    )

    out = out.drop(columns=["PlayPriority", "ResultPriority", "AbsProfit"], errors="ignore")

    return out


def build_bankroll():
    df = normalize_tracker()

    if df.empty:
        empty = pd.DataFrame()
        empty.to_csv(BANKROLL_PATH, index=False, encoding="utf-8-sig")
        return empty

    running_bankroll = STARTING_BANKROLL
    rows = []

    for _, row in df.iterrows():
        result = safe_text(row.get("Result", "PENDING")).upper().strip()
        stake = safe_num(row.get("Stake", 0))
        profit = safe_num(row.get("Profit", 0))

        graded_stake = stake if result in ["WIN", "LOSS"] else 0
        running_bankroll = round(running_bankroll + profit, 2)

        rows.append({
            **row.to_dict(),
            "StartingBankroll": STARTING_BANKROLL,
            "GradedStake": graded_stake,
            "RunningBankroll": running_bankroll,
            "RunningProfit": round(running_bankroll - STARTING_BANKROLL, 2),
        })

    bankroll = pd.DataFrame(rows)

    bankroll.to_csv(BANKROLL_PATH, index=False, encoding="utf-8-sig")

    return bankroll


def summary(df):
    if df.empty:
        return {
            "starting_bankroll": STARTING_BANKROLL,
            "current_bankroll": STARTING_BANKROLL,
            "profit": 0,
            "roi": 0,
            "total_plays": 0,
            "graded_plays": 0,
            "pending": 0,
            "wins": 0,
            "losses": 0,
            "stake": 0,
            "hit_rate": 0,
        }

    graded = df[df["Result"].isin(["WIN", "LOSS"])].copy()

    wins = int((graded["Result"] == "WIN").sum())
    losses = int((graded["Result"] == "LOSS").sum())
    pending = int((df["Result"] == "PENDING").sum())

    stake = round(pd.to_numeric(graded["Stake"], errors="coerce").fillna(0).sum(), 2)
    profit = round(pd.to_numeric(graded["Profit"], errors="coerce").fillna(0).sum(), 2)
    current_bankroll = round(STARTING_BANKROLL + profit, 2)

    roi = round((profit / stake * 100), 2) if stake else 0
    hit_rate = round((wins / (wins + losses) * 100), 2) if (wins + losses) else 0

    return {
        "starting_bankroll": STARTING_BANKROLL,
        "current_bankroll": current_bankroll,
        "profit": profit,
        "roi": roi,
        "total_plays": int(len(df)),
        "graded_plays": int(len(graded)),
        "pending": pending,
        "wins": wins,
        "losses": losses,
        "stake": stake,
        "hit_rate": hit_rate,
    }


def group_summary(df, column):
    if df.empty or column not in df.columns:
        return []

    rows = []

    for bucket, g in df.groupby(column):
        s = summary(g)
        s["bucket"] = str(bucket)
        rows.append(s)

    return sorted(rows, key=lambda x: (x["roi"], x["profit"], x["wins"]), reverse=True)


def daily_summary(df):
    if df.empty or "Date" not in df.columns:
        return []

    rows = []

    for date, g in df.groupby("Date"):
        s = summary(g)
        s["date"] = str(date)
        rows.append(s)

    return sorted(rows, key=lambda x: x["date"], reverse=True)


def bankroll_report():
    # Always rebuild from yes_performance_tracker.csv so signal fields do not go stale.
    df = build_bankroll()

    if df.empty:
        return {
            "summary": summary(df),
            "by_play_type": [],
            "by_snapshot": [],
            "daily": [],
            "latest": [],
            "top_winners": [],
            "top_losses": [],
        }

    df["Profit"] = pd.to_numeric(df["Profit"], errors="coerce").fillna(0)
    df["Stake"] = pd.to_numeric(df["Stake"], errors="coerce").fillna(0)

    latest = df.sort_values(
        by=["Date", "Confidence", "Edge"],
        ascending=[False, False, False],
    ).head(75)

    winners = (
        df[df["Profit"] > 0]
        .sort_values(by=["Profit", "Confidence", "Edge"], ascending=[False, False, False])
        .drop_duplicates(subset=["Player"], keep="first")
        .head(15)
    )

    losses = (
        df[df["Profit"] < 0]
        .sort_values(by=["Profit", "Confidence", "Edge"], ascending=[True, False, False])
        .drop_duplicates(subset=["Player"], keep="first")
        .head(15)
    )

    return {
        "summary": summary(df),
        "by_play_type": group_summary(df, "PlayCode"),
        "by_snapshot": group_summary(df, "Snapshot"),
        "daily": daily_summary(df),
        "latest": latest.fillna("").to_dict("records"),
        "top_winners": winners.fillna("").to_dict("records"),
        "top_losses": losses.fillna("").to_dict("records"),
    }


def main():
    df = build_bankroll()
    report = bankroll_report()
    s = report["summary"]

    print()
    print("BANKROLL TRACKER V3.15.1 SIGNAL FIELD FIX COMPLETE")
    print(f"Saved: {BANKROLL_PATH}")
    print(f"Rows: {len(df)}")
    print()
    print("Signal field preview:")
    if not df.empty:
        cols = ["Player", "HRScore", "DecisionScore", "PitcherWeakness", "PitcherSpotMatch", "LineupSpot"]
        print(df[cols].head(10).to_string(index=False))
    print()
    print("Summary:")
    print(f"Starting Bankroll: {s['starting_bankroll']}u")
    print(f"Current Bankroll: {s['current_bankroll']}u")
    print(f"Profit: {s['profit']}u")
    print(f"ROI: {s['roi']}%")
    print(f"Total Plays: {s['total_plays']}")
    print(f"Graded Plays: {s['graded_plays']}")
    print(f"Pending: {s['pending']}")

    return df


if __name__ == "__main__":
    main()
