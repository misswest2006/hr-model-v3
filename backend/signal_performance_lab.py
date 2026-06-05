import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

BANKROLL_PATH = os.path.join(DATA_DIR, "bankroll_tracker.csv")
YES_TRACKER_PATH = os.path.join(DATA_DIR, "yes_performance_tracker.csv")


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


def load_source():
    if os.path.exists(BANKROLL_PATH):
        try:
            df = pd.read_csv(BANKROLL_PATH)
            if not df.empty:
                return df
        except Exception:
            pass

    if os.path.exists(YES_TRACKER_PATH):
        try:
            return pd.read_csv(YES_TRACKER_PATH)
        except Exception:
            return pd.DataFrame()

    return pd.DataFrame()


def prep_df():
    df = load_source()

    if df.empty:
        return df

    needed = [
        "Date", "Snapshot", "Player", "Team", "Pitcher", "PlayCode",
        "BestOdds", "Stake", "Result", "Profit", "ModelProb", "Edge",
        "Confidence", "HRScore", "DecisionScore", "SmashScore", "PowerScore",
        "LineupSpot", "PitcherWeakness", "PitcherSpotMatch", "Grade", "TierCode"
    ]

    for col in needed:
        if col not in df.columns:
            df[col] = ""

    numeric_cols = [
        "BestOdds", "Stake", "Profit", "ModelProb", "Edge", "Confidence",
        "HRScore", "DecisionScore", "SmashScore", "PowerScore", "LineupSpot",
        "PitcherWeakness", "PitcherSpotMatch"
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["Result"] = df["Result"].fillna("PENDING").astype(str).str.upper().str.strip()
    df["PlayCode"] = df["PlayCode"].fillna("").astype(str).str.upper().str.strip()
    df["Snapshot"] = df["Snapshot"].fillna("").astype(str).str.upper().str.strip()
    df["Grade"] = df["Grade"].fillna("").astype(str).str.upper().str.strip()
    df["TierCode"] = df["TierCode"].fillna("").astype(str).str.upper().str.strip()

    return df


def summarize(frame):
    if frame.empty:
        return {
            "plays": 0,
            "graded": 0,
            "wins": 0,
            "losses": 0,
            "pending": 0,
            "stake": 0,
            "profit": 0,
            "roi": 0,
            "hit_rate": 0,
            "avg_confidence": 0,
            "avg_edge": 0,
        }

    graded = frame[frame["Result"].isin(["WIN", "LOSS"])].copy()

    wins = int((graded["Result"] == "WIN").sum())
    losses = int((graded["Result"] == "LOSS").sum())
    pending = int((frame["Result"] == "PENDING").sum())

    stake = round(pd.to_numeric(graded["Stake"], errors="coerce").fillna(0).sum(), 2)
    profit = round(pd.to_numeric(graded["Profit"], errors="coerce").fillna(0).sum(), 2)

    roi = round((profit / stake * 100), 2) if stake else 0
    hit_rate = round((wins / (wins + losses) * 100), 2) if (wins + losses) else 0

    return {
        "plays": int(len(frame)),
        "graded": int(len(graded)),
        "wins": wins,
        "losses": losses,
        "pending": pending,
        "stake": stake,
        "profit": profit,
        "roi": roi,
        "hit_rate": hit_rate,
        "avg_confidence": round(float(frame["Confidence"].mean()), 2) if "Confidence" in frame else 0,
        "avg_edge": round(float(frame["Edge"].mean() * 100), 2) if "Edge" in frame else 0,
    }


def bucket_confidence(value):
    value = safe_num(value, 0)

    if value >= 95:
        return "95-100"
    if value >= 90:
        return "90-95"
    if value >= 85:
        return "85-90"
    if value >= 80:
        return "80-85"
    if value >= 70:
        return "70-80"

    return "0-70"


def bucket_edge(value):
    value = safe_num(value, 0)

    if value < 0:
        return "Negative"
    if value < 0.03:
        return "0-3%"
    if value < 0.05:
        return "3-5%"
    if value < 0.10:
        return "5-10%"
    if value < 0.15:
        return "10-15%"
    if value < 0.20:
        return "15-20%"

    return "20%+"


def bucket_score(value):
    value = safe_num(value, 0)

    if value >= 95:
        return "95-100"
    if value >= 90:
        return "90-95"
    if value >= 85:
        return "85-90"
    if value >= 80:
        return "80-85"
    if value >= 70:
        return "70-80"
    if value >= 50:
        return "50-70"

    return "0-50"


def bucket_lineup(value):
    value = int(safe_num(value, 0))

    if value <= 0:
        return "Unknown"

    return str(value)


def bucket_pitcher(value):
    value = int(round(safe_num(value, 0)))

    if value <= 0:
        return "0"
    if value >= 10:
        return "10"

    return str(value)


def with_signal_buckets(df):
    if df.empty:
        return df

    df = df.copy()

    df["ConfidenceBucket"] = df["Confidence"].apply(bucket_confidence)
    df["EdgeBucket"] = df["Edge"].apply(bucket_edge)
    df["HRScoreBucket"] = df["HRScore"].apply(bucket_score)
    df["DecisionScoreBucket"] = df["DecisionScore"].apply(bucket_score)
    df["SmashScoreBucket"] = df["SmashScore"].apply(bucket_score)
    df["PowerScoreBucket"] = df["PowerScore"].apply(bucket_score)
    df["LineupSpotBucket"] = df["LineupSpot"].apply(bucket_lineup)
    df["PitcherWeaknessBucket"] = df["PitcherWeakness"].apply(bucket_pitcher)
    df["PitcherSpotMatchBucket"] = df["PitcherSpotMatch"].apply(bucket_pitcher)

    return df


def grouped_signal(df, column, label, min_graded=3):
    if df.empty or column not in df.columns:
        return {
            "label": label,
            "column": column,
            "best": None,
            "worst": None,
            "rows": [],
        }

    rows = []

    for bucket, g in df.groupby(column):
        s = summarize(g)
        s["bucket"] = str(bucket)
        s["signal"] = label
        s["column"] = column

        if s["graded"] < min_graded:
            s["recommendation"] = "Track more"
        elif s["roi"] >= 25:
            s["recommendation"] = "Increase weight"
        elif s["roi"] > 0:
            s["recommendation"] = "Keep / watch"
        elif s["roi"] <= -25:
            s["recommendation"] = "Decrease weight"
        else:
            s["recommendation"] = "Neutral"

        rows.append(s)

    rows = sorted(
        rows,
        key=lambda x: (x["roi"], x["profit"], x["wins"], x["graded"]),
        reverse=True,
    )

    qualified = [r for r in rows if r["graded"] >= min_graded]

    best = qualified[0] if qualified else (rows[0] if rows else None)
    worst = sorted(qualified, key=lambda x: (x["roi"], x["profit"]))[0] if qualified else None

    return {
        "label": label,
        "column": column,
        "best": best,
        "worst": worst,
        "rows": rows,
    }


def all_signal_sections(df):
    df = with_signal_buckets(df)

    sections = [
        grouped_signal(df, "PlayCode", "Play Type", min_graded=2),
        grouped_signal(df, "Snapshot", "Snapshot", min_graded=2),
        grouped_signal(df, "ConfidenceBucket", "Confidence Bucket", min_graded=3),
        grouped_signal(df, "EdgeBucket", "Edge Bucket", min_graded=3),
        grouped_signal(df, "LineupSpotBucket", "Lineup Spot", min_graded=3),
        grouped_signal(df, "PitcherWeaknessBucket", "Pitcher Weakness", min_graded=3),
        grouped_signal(df, "PitcherSpotMatchBucket", "Pitcher Spot Match", min_graded=3),
        grouped_signal(df, "HRScoreBucket", "HR Score", min_graded=3),
        grouped_signal(df, "DecisionScoreBucket", "Decision Score", min_graded=3),
        grouped_signal(df, "SmashScoreBucket", "Smash Score", min_graded=3),
        grouped_signal(df, "Grade", "Grade", min_graded=2),
        grouped_signal(df, "TierCode", "Tier", min_graded=2),
        grouped_signal(df, "Team", "Team", min_graded=2),
    ]

    return sections


def build_recommendations(sections):
    recommendations = []

    for section in sections:
        best = section.get("best")
        worst = section.get("worst")

        if best and best.get("graded", 0) >= 3 and best.get("roi", 0) >= 25:
            recommendations.append({
                "type": "increase",
                "signal": section["label"],
                "bucket": best["bucket"],
                "roi": best["roi"],
                "profit": best["profit"],
                "graded": best["graded"],
                "message": f"Increase weight on {section['label']} = {best['bucket']}",
            })

        if worst and worst.get("graded", 0) >= 3 and worst.get("roi", 0) <= -25:
            recommendations.append({
                "type": "decrease",
                "signal": section["label"],
                "bucket": worst["bucket"],
                "roi": worst["roi"],
                "profit": worst["profit"],
                "graded": worst["graded"],
                "message": f"Decrease weight on {section['label']} = {worst['bucket']}",
            })

    recommendations = sorted(
        recommendations,
        key=lambda x: (abs(x["roi"]), abs(x["profit"]), x["graded"]),
        reverse=True,
    )

    return recommendations[:20]


def signal_lab_report():
    df = prep_df()

    if df.empty:
        return {
            "summary": summarize(df),
            "recommendations": [],
            "sections": [],
            "top_positive": [],
            "top_negative": [],
        }

    sections = all_signal_sections(df)
    recommendations = build_recommendations(sections)

    all_rows = []

    for section in sections:
        for row in section.get("rows", []):
            if row.get("graded", 0) > 0:
                all_rows.append(row)

    qualified = [r for r in all_rows if r.get("graded", 0) >= 3]

    top_positive = sorted(
        qualified,
        key=lambda x: (x["roi"], x["profit"], x["wins"]),
        reverse=True,
    )[:15]

    top_negative = sorted(
        qualified,
        key=lambda x: (x["roi"], x["profit"], x["losses"]),
    )[:15]

    return {
        "summary": summarize(df),
        "recommendations": recommendations,
        "sections": sections,
        "top_positive": top_positive,
        "top_negative": top_negative,
    }


def main():
    report = signal_lab_report()
    s = report["summary"]

    print()
    print("SIGNAL PERFORMANCE LAB V3.15 COMPLETE")
    print()
    print("Summary:")
    print(f"Plays: {s['plays']}")
    print(f"Graded: {s['graded']}")
    print(f"Wins: {s['wins']}")
    print(f"Losses: {s['losses']}")
    print(f"Pending: {s['pending']}")
    print(f"Profit: {s['profit']}u")
    print(f"ROI: {s['roi']}%")
    print()
    print("Top Recommendations:")
    for rec in report["recommendations"][:10]:
        print(f"- {rec['message']} | ROI {rec['roi']}% | Profit {rec['profit']}u")

    return report


if __name__ == "__main__":
    main()
