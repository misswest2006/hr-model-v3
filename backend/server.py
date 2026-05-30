import os
import sys
import pandas as pd

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
HISTORY_PATH = os.path.join(DATA_DIR, "hr_results_history.csv")

sys.path.append(BASE_DIR)

from run_model import run
from model_health import get_model_health

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def empty_tracker():
    return {
        "date": "",
        "snapshot": "",
        "yes_plays": 0,
        "hr_hits": 0,
        "pending": 0,
        "hit_rate": 0,
        "profit": 0,
    }


def load_history():
    if not os.path.exists(HISTORY_PATH):
        return pd.DataFrame()

    return pd.read_csv(HISTORY_PATH)


def latest_snapshot_df(df):
    if df.empty or "Date" not in df.columns:
        return pd.DataFrame(), "", ""

    df = df.copy()
    df["Date"] = df["Date"].astype(str).str.strip()

    latest_date = df["Date"].max()
    today_df = df[df["Date"] == latest_date].copy()

    active_snapshot = ""

    if "Snapshot" in today_df.columns:
        today_df["Snapshot"] = today_df["Snapshot"].astype(str).str.strip()

        for snap in ["LOCK", "ONE_HOUR", "MORNING", "MANUAL"]:
            if snap in today_df["Snapshot"].values:
                active_snapshot = snap
                today_df = today_df[today_df["Snapshot"] == snap].copy()
                break

    return today_df, latest_date, active_snapshot


def clean_result(value):
    result = str(value).strip()

    if result.lower() == "nan" or result == "":
        return "PENDING"

    if result.upper() == "HR":
        return "💣 HR"

    if result.upper() in ["NO HR", "NO_HR", "MISS"]:
        return "❌ NO HR"

    return result


@app.get("/")
def home():
    return {"status": "HR model backend running"}


@app.get("/api/slate")
def get_slate():
    picks = run()
    return {
        "count": len(picks),
        "picks": picks,
    }


@app.get("/api/model-health")
def model_health():
    return get_model_health()


@app.get("/yes-tracker")
def yes_tracker():
    df = load_history()

    if df.empty:
        return empty_tracker()

    today_df, latest_date, active_snapshot = latest_snapshot_df(df)

    if today_df.empty:
        return empty_tracker()

    yes_df = today_df[today_df["Play"] == "YES 🔥"].copy()

    total_yes = len(yes_df)

    if "Result" not in yes_df.columns:
        yes_df["Result"] = ""

    result_col = yes_df["Result"].fillna("").astype(str).str.strip()

    hr_hits = int((result_col.str.upper() == "HR").sum())
    pending = int((result_col == "").sum() + (result_col.str.lower() == "nan").sum())

    if "Profit" not in yes_df.columns:
        yes_df["Profit"] = 0

    profit = pd.to_numeric(
        yes_df["Profit"],
        errors="coerce",
    ).fillna(0).sum()

    hit_rate = round((hr_hits / total_yes * 100), 1) if total_yes else 0

    return {
        "date": latest_date,
        "snapshot": active_snapshot,
        "yes_plays": total_yes,
        "hr_hits": hr_hits,
        "pending": pending,
        "hit_rate": hit_rate,
        "profit": round(profit, 2),
    }


@app.get("/yes-results")
def yes_results():
    df = load_history()

    if df.empty:
        return []

    today_df, latest_date, active_snapshot = latest_snapshot_df(df)

    if today_df.empty:
        return []

    yes_df = today_df[today_df["Play"] == "YES 🔥"].copy()

    if yes_df.empty:
        return []

    for col in ["Result", "Profit", "Stake"]:
        if col not in yes_df.columns:
            yes_df[col] = ""

    yes_df["Profit"] = pd.to_numeric(
        yes_df["Profit"],
        errors="coerce",
    ).fillna(0)

    rows = []

    for _, row in yes_df.iterrows():
        rows.append({
            "date": latest_date,
            "player": row.get("Player", ""),
            "team": row.get("Team", ""),
            "pitcher": row.get("Pitcher", ""),
            "snapshot": row.get("Snapshot", active_snapshot),
            "book": row.get("BestBook", ""),
            "odds": row.get("BestOdds", ""),
            "confidence": row.get("Confidence", ""),
            "edge": row.get("Edge", ""),
            "grade": row.get("Grade", ""),
            "stake": row.get("Stake", ""),
            "result": clean_result(row.get("Result", "")),
            "profit": row.get("Profit", 0),
        })

    return rows


@app.get("/snapshot-health")
def snapshot_health():
    df = load_history()

    if df.empty or "Snapshot" not in df.columns:
        return []

    summary = []

    for snap in ["MORNING", "ONE_HOUR", "LOCK", "MANUAL"]:
        snap_df = df[df["Snapshot"] == snap].copy()
        yes_df = snap_df[snap_df["Play"] == "YES 🔥"].copy()

        yes_count = len(yes_df)

        if "Result" not in yes_df.columns:
            yes_df["Result"] = ""

        if "Profit" not in yes_df.columns:
            yes_df["Profit"] = 0

        if "Stake" not in yes_df.columns:
            yes_df["Stake"] = 0

        result_col = yes_df["Result"].fillna("").astype(str).str.strip()

        hr_hits = int((result_col.str.upper() == "HR").sum())

        profit = pd.to_numeric(
            yes_df["Profit"],
            errors="coerce",
        ).fillna(0).sum()

        stake = pd.to_numeric(
            yes_df["Stake"],
            errors="coerce",
        ).fillna(0).sum()

        hit_rate = round((hr_hits / yes_count * 100), 1) if yes_count else 0
        roi = round((profit / stake * 100), 1) if stake else 0

        summary.append({
            "snapshot": snap,
            "total_plays": len(snap_df),
            "yes_plays": yes_count,
            "hr_hits": hr_hits,
            "hit_rate": hit_rate,
            "profit": round(profit, 2),
            "roi": roi,
        })

    return summary