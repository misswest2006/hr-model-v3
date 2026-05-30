import os
import pandas as pd


BUCKETS = [
    ("0-39", 0, 39),
    ("40-49", 40, 49),
    ("50-59", 50, 59),
    ("60-64", 60, 64),
    ("65-69", 65, 69),
    ("70-74", 70, 74),
    ("75+", 75, 999),
]


def safe_float(value, default=0.0):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def load_history():
    path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "data",
        "hr_results_history.csv"
    )

    if not os.path.exists(path):
        return pd.DataFrame()

    return pd.read_csv(path)


def prep_df(df):
    if df.empty:
        return df

    for col in ["Confidence", "Edge", "ModelProb", "Stake", "Profit"]:
        if col not in df.columns:
            df[col] = 0

    for col in ["Result", "Grade", "Play", "Date", "Player", "Team", "Pitcher", "BestBook", "BestOdds"]:
        if col not in df.columns:
            df[col] = ""

    df["Confidence"] = pd.to_numeric(df["Confidence"], errors="coerce").fillna(0)
    df["Edge"] = pd.to_numeric(df["Edge"], errors="coerce").fillna(0)
    df["ModelProb"] = pd.to_numeric(df["ModelProb"], errors="coerce").fillna(0)
    df["Stake"] = pd.to_numeric(df["Stake"], errors="coerce").fillna(0)
    df["Profit"] = pd.to_numeric(df["Profit"], errors="coerce").fillna(0)
    df["Result"] = df["Result"].fillna("").astype(str).str.strip()
    df["Grade"] = df["Grade"].fillna("").astype(str).str.strip()
    df["Play"] = df["Play"].fillna("").astype(str).str.strip()
    df["Date"] = df["Date"].fillna("").astype(str).str.strip()

    return df


def summarize_bucket(df, label, low, high):
    bucket = df[(df["Confidence"] >= low) & (df["Confidence"] <= high)]
    total = len(bucket)

    if total == 0:
        return {
            "bucket": label,
            "plays": 0,
            "hrs": 0,
            "hr_rate": 0,
            "avg_edge": 0,
            "avg_model_prob": 0,
            "profit": 0,
            "roi": 0,
        }

    hrs = int((bucket["Result"] == "HR").sum())
    profit = bucket["Profit"].sum()
    stake = bucket["Stake"].sum()

    return {
        "bucket": label,
        "plays": total,
        "hrs": hrs,
        "hr_rate": round((hrs / total) * 100, 1),
        "avg_edge": round(bucket["Edge"].mean() * 100, 1),
        "avg_model_prob": round(bucket["ModelProb"].mean() * 100, 1),
        "profit": round(profit, 2),
        "roi": round((profit / stake) * 100, 1) if stake > 0 else 0,
    }


def summarize_grade(df, grade):
    group = df[df["Grade"] == grade]
    total = len(group)

    if total == 0:
        return {
            "grade": grade,
            "plays": 0,
            "hrs": 0,
            "hr_rate": 0,
            "profit": 0,
            "roi": 0,
        }

    hrs = int((group["Result"] == "HR").sum())
    profit = group["Profit"].sum()
    stake = group["Stake"].sum()

    return {
        "grade": grade,
        "plays": total,
        "hrs": hrs,
        "hr_rate": round((hrs / total) * 100, 1),
        "profit": round(profit, 2),
        "roi": round((profit / stake) * 100, 1) if stake > 0 else 0,
    }


def get_yesterday_hits(df):
    graded = df[df["Result"].isin(["HR", "NO HR"])]

    if graded.empty:
        return []

    latest_date = graded["Date"].max()
    hits = graded[(graded["Date"] == latest_date) & (graded["Result"] == "HR")]

    hits = hits.sort_values(
        by=["Confidence", "Edge"],
        ascending=[False, False]
    )

    return hits.fillna("").to_dict(orient="records")


def get_model_health():
    df = prep_df(load_history())

    if df.empty:
        return {
            "total_plays": 0,
            "yes_plays": 0,
            "pending_results": 0,
            "graded_results": 0,
            "avg_confidence": 0,
            "avg_edge": 0,
            "avg_model_prob": 0,
            "total_profit": 0,
            "roi": 0,
            "confidence_buckets": [],
            "grade_summary": [],
            "yesterday_hits": [],
            "recent_plays": [],
        }

    total_plays = len(df)
    yes_plays = int((df["Play"] == "YES 🔥").sum())

    pending_results = int((df["Result"] == "").sum())
    graded_results = total_plays - pending_results

    total_profit = round(df["Profit"].sum(), 2)
    total_stake = df["Stake"].sum()

    recent = df.sort_values(
        by=["Date", "Confidence"],
        ascending=[False, False]
    ).head(25)

    return {
        "total_plays": total_plays,
        "yes_plays": yes_plays,
        "pending_results": pending_results,
        "graded_results": graded_results,
        "avg_confidence": round(df["Confidence"].mean(), 1),
        "avg_edge": round(df["Edge"].mean() * 100, 1),
        "avg_model_prob": round(df["ModelProb"].mean() * 100, 1),
        "total_profit": total_profit,
        "roi": round((total_profit / total_stake) * 100, 1) if total_stake > 0 else 0,
        "confidence_buckets": [
            summarize_bucket(df, label, low, high)
            for label, low, high in BUCKETS
        ],
        "grade_summary": [
            summarize_grade(df, grade)
            for grade in ["A+", "A", "B", "C", "D"]
        ],
        "yesterday_hits": get_yesterday_hits(df),
        "recent_plays": recent.fillna("").to_dict(orient="records"),
    }