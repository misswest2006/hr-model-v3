import os
import sys
import pandas as pd

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "..", "data")

HISTORY_PATH = os.path.join(DATA_DIR, "hr_results_history.csv")
RESULTS_PATH = os.path.join(DATA_DIR, "hr_model_results.csv")

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


def safe_float(value, default=0):
    try:
        if value is None:
            return default
        if pd.isna(value):
            return default

        value = str(value).strip()

        if value == "" or value.lower() in ["nan", "none", "<na>"]:
            return default

        return float(value)

    except Exception:
        return default


def safe_str(value, default=""):
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

    try:
        return pd.read_csv(HISTORY_PATH)

    except Exception:
        return pd.DataFrame()


def load_results():
    if not os.path.exists(RESULTS_PATH):
        return pd.DataFrame()

    try:
        df = pd.read_csv(RESULTS_PATH)
        df = df.fillna("")
        return df

    except Exception:
        return pd.DataFrame()


def latest_snapshot_df(df):
    if df.empty or "Date" not in df.columns:
        return pd.DataFrame(), "", ""

    df = df.copy()
    df["Date"] = df["Date"].astype(str).str.strip()

    latest_date = df["Date"].max()
    today_df = df[df["Date"] == latest_date].copy()

    active_snapshot = ""

    if "Snapshot" in today_df.columns:
        today_df["Snapshot"] = today_df["Snapshot"].astype(str).str.upper().str.strip()

        for snap in ["LOCK", "ONE_HOUR", "MORNING", "MANUAL"]:
            if snap in today_df["Snapshot"].values:
                active_snapshot = snap
                today_df = today_df[today_df["Snapshot"] == snap].copy()
                break

    return today_df, latest_date, active_snapshot


def make_json_safe(value):
    if isinstance(value, dict):
        return {k: make_json_safe(v) for k, v in value.items()}

    if isinstance(value, list):
        return [make_json_safe(v) for v in value]

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    return value


def clean_result(value):
    result = str(value).strip()

    if result.lower() == "nan" or result == "":
        return "PENDING"

    if result.upper() == "HR":
        return "💣 HR"

    if result.upper() in ["NO HR", "NO_HR", "MISS"]:
        return "❌ NO HR"

    return result


def headshot_url(player_id):
    if player_id is None:
        return ""

    try:
        if pd.isna(player_id):
            return ""
    except Exception:
        pass

    clean_id = str(player_id).replace(".0", "").strip()

    if clean_id == "" or clean_id.lower() in ["nan", "none", "<na>"]:
        return ""

    return (
        "https://img.mlbstatic.com/mlb-photos/image/upload/"
        f"w_180,q_auto:best/v1/people/{clean_id}/headshot/67/current"
    )


def result_row(row):
    play_code = safe_str(row.get("PlayCode", ""))
    tier_code = safe_str(row.get("TierCode", ""))

    play_display = safe_str(row.get("Play", ""))
    tier_display = safe_str(row.get("Tier", ""))

    if play_code == "" and play_display:
        if "YES" in play_display.upper():
            play_code = "YES"
        elif "POWER" in play_display.upper():
            play_code = "POWER_BAT"
        elif "VALUE" in play_display.upper():
            play_code = "VALUE_LEAN"
        elif "NO ODDS" in play_display.upper():
            play_code = "NO_ODDS"
        elif "PASS" in play_display.upper():
            play_code = "PASS"

    return {
        "date": safe_str(row.get("Date", "")),
        "game": safe_str(row.get("Game", "")),
        "game_time": safe_str(row.get("GameTime", "")),
        "game_time_et": safe_str(row.get("GameTimeET", "")),
        "snapshot": safe_str(row.get("Snapshot", "MANUAL"), "MANUAL"),

        "player": safe_str(row.get("Player", "")),
        "Player": safe_str(row.get("Player", "")),

        "player_id": safe_str(row.get("player_id", "")),
        "player_headshot": headshot_url(row.get("player_id", "")),

        "team": safe_str(row.get("Team", "")),
        "Team": safe_str(row.get("Team", "")),

        "pitcher": safe_str(row.get("Pitcher", "")),
        "Pitcher": safe_str(row.get("Pitcher", "")),

        "lineup_spot": safe_str(row.get("LineupSpot", "")),
        "LineupSpot": safe_str(row.get("LineupSpot", "")),
        "lineup_source": safe_str(row.get("LineupSource", "")),

        "best_book": safe_str(row.get("BestBook", "")),
        "BestBook": safe_str(row.get("BestBook", "")),

        "best_odds": safe_str(row.get("BestOdds", "")),
        "BestOdds": safe_str(row.get("BestOdds", "")),

        "model_prob": safe_float(row.get("ModelProb")),
        "ModelProb": safe_float(row.get("ModelProb")),

        "raw_model_prob": safe_float(row.get("RawModelProb")),
        "RawModelProb": safe_float(row.get("RawModelProb")),

        "best_edge": safe_float(row.get("Edge")),
        "edge": safe_float(row.get("Edge")),
        "Edge": safe_float(row.get("Edge")),

        "confidence": safe_float(row.get("Confidence")),
        "Confidence": safe_float(row.get("Confidence")),

        "power_score": safe_float(row.get("PowerScore")),
        "PowerScore": safe_float(row.get("PowerScore")),

        "hr_score": safe_float(row.get("HRScore")),
        "HRScore": safe_float(row.get("HRScore")),

        "ev_score": safe_float(row.get("EVScore")),
        "EVScore": safe_float(row.get("EVScore")),

        "decision_score": safe_float(row.get("DecisionScore")),
        "DecisionScore": safe_float(row.get("DecisionScore")),

        "smash_score": safe_float(row.get("SmashScore")),
        "SmashScore": safe_float(row.get("SmashScore")),

        "pitcher_weakness_score": safe_float(
            row.get("PitcherScore", row.get("PitcherHRWeaknessScore", 0))
        ),
        "pitcher_lineup_weak_spot": safe_float(
            row.get("PitcherLineupScore", row.get("PitcherLineupWeakSpot", 0))
        ),

        "grade": safe_str(row.get("Grade", "")),
        "Grade": safe_str(row.get("Grade", "")),

        "tier": tier_display,
        "Tier": tier_display,
        "tier_code": tier_code,
        "TierCode": tier_code,

        "play": play_display,
        "Play": play_display,
        "play_code": play_code,
        "PlayCode": play_code,

        "reason": safe_str(row.get("Reason", "")),
        "Reason": safe_str(row.get("Reason", "")),

        "stake": safe_float(row.get("Stake", 0)),
        "Stake": safe_float(row.get("Stake", 0)),

        "top_hr_rank": safe_str(row.get("TopHRRank", "")),
        "TopHRRank": safe_str(row.get("TopHRRank", "")),

        "top_edge_rank": safe_str(row.get("TopEdgeRank", "")),
        "TopEdgeRank": safe_str(row.get("TopEdgeRank", "")),

        "top_prob_rank": safe_str(row.get("TopProbRank", "")),
        "TopProbRank": safe_str(row.get("TopProbRank", "")),

        "top_smash_rank": safe_str(row.get("TopSmashRank", "")),
        "TopSmashRank": safe_str(row.get("TopSmashRank", "")),
    }


@app.get("/")
def home():
    return {"status": "HR model backend running"}


@app.get("/api/slate")
def get_slate():
    df = load_results()

    if df.empty:
        return {
            "count": 0,
            "date": "",
            "snapshot": "MANUAL",
            "picks": [],
        }

    picks = []

    for _, row in df.iterrows():
        picks.append(result_row(row))

    latest_date = str(df["Date"].iloc[0]) if "Date" in df.columns else ""
    latest_snapshot = "MANUAL"

    if "Snapshot" in df.columns:
        snapshots = df["Snapshot"].astype(str).str.upper().str.strip()
        for snap in ["LOCK", "ONE_HOUR", "MORNING", "MANUAL"]:
            if snap in snapshots.values:
                latest_snapshot = snap
                break

    return {
        "count": len(picks),
        "date": latest_date,
        "snapshot": latest_snapshot,
        "picks": picks,
    }


@app.get("/today-plays")
def today_plays():
    df = load_results()

    if df.empty:
        return {
            "count": 0,
            "date": "",
            "snapshot": "",
            "yes_count": 0,
            "power_bat_count": 0,
            "value_lean_count": 0,
            "total_stake": 0,
            "plays": [],
            "yes": [],
            "power_bats": [],
            "value_leans": [],
        }

    df = df.copy()

    for col in ["PlayCode", "Play", "Stake", "Edge", "Confidence", "HRScore", "DecisionScore", "SmashScore"]:
        if col not in df.columns:
            df[col] = ""

    df["PlayCode"] = df["PlayCode"].fillna("").astype(str).str.upper().str.strip()
    df["Play"] = df["Play"].fillna("").astype(str).str.upper().str.strip()

    official = df[
        (df["PlayCode"].isin(["YES", "POWER_BAT", "VALUE_LEAN"]))
        | (df["Play"].str.contains("YES", na=False))
        | (df["Play"].str.contains("POWER BAT", na=False))
        | (df["Play"].str.contains("VALUE LEAN", na=False))
    ].copy()

    official["Stake"] = pd.to_numeric(official["Stake"], errors="coerce").fillna(0)
    official["Edge"] = pd.to_numeric(official["Edge"], errors="coerce").fillna(0)
    official["Confidence"] = pd.to_numeric(official["Confidence"], errors="coerce").fillna(0)
    official["HRScore"] = pd.to_numeric(official["HRScore"], errors="coerce").fillna(0)
    official["DecisionScore"] = pd.to_numeric(official["DecisionScore"], errors="coerce").fillna(0)
    official["SmashScore"] = pd.to_numeric(official["SmashScore"], errors="coerce").fillna(0)

    official = official.sort_values(
        by=["PlayCode", "HRScore", "DecisionScore", "SmashScore", "Edge"],
        ascending=[True, False, False, False, False],
    )

    plays = [result_row(row) for _, row in official.iterrows()]

    yes = [p for p in plays if p.get("PlayCode") == "YES"]
    power_bats = [p for p in plays if p.get("PlayCode") == "POWER_BAT"]
    value_leans = [p for p in plays if p.get("PlayCode") == "VALUE_LEAN"]

    latest_date = str(df["Date"].iloc[0]) if "Date" in df.columns and not df.empty else ""
    latest_snapshot = "MANUAL"

    if "Snapshot" in df.columns:
        snapshots = df["Snapshot"].astype(str).str.upper().str.strip()
        for snap in ["LOCK", "ONE_HOUR", "MORNING", "MANUAL"]:
            if snap in snapshots.values:
                latest_snapshot = snap
                break

    return {
        "count": len(plays),
        "date": latest_date,
        "snapshot": latest_snapshot,
        "yes_count": len(yes),
        "power_bat_count": len(power_bats),
        "value_lean_count": len(value_leans),
        "total_stake": round(sum(p.get("Stake", 0) for p in plays), 2),
        "plays": plays,
        "yes": yes,
        "power_bats": power_bats,
        "value_leans": value_leans,
    }


@app.get("/api/today-plays")
def api_today_plays():
    return today_plays()


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
            "player": safe_str(row.get("Player", "")),
            "player_id": safe_str(row.get("player_id", "")),
            "player_headshot": headshot_url(row.get("player_id", "")),
            "team": safe_str(row.get("Team", "")),
            "pitcher": safe_str(row.get("Pitcher", "")),
            "snapshot": safe_str(row.get("Snapshot", active_snapshot)),
            "book": safe_str(row.get("BestBook", "")),
            "odds": safe_str(row.get("BestOdds", "")),
            "confidence": safe_float(row.get("Confidence", 0)),
            "edge": safe_float(row.get("Edge", 0)),
            "grade": safe_str(row.get("Grade", "")),
            "stake": safe_float(row.get("Stake", 0)),
            "result": clean_result(row.get("Result", "")),
            "profit": safe_float(row.get("Profit", 0)),
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


@app.get("/confidence-analytics")
def confidence_analytics():
    df = load_history()

    empty = {
        "total_yes_plays": 0,
        "total_hr_hits": 0,
        "total_roi": 0,
        "recommended_min_confidence": "",
        "best_bucket": {},
        "buckets": [],
    }

    if df.empty:
        return empty

    yes_df = df[df["Play"] == "YES 🔥"].copy()

    if yes_df.empty:
        return empty

    for col in ["Confidence", "Result", "Profit", "Stake"]:
        if col not in yes_df.columns:
            yes_df[col] = 0

    yes_df["Confidence"] = pd.to_numeric(
        yes_df["Confidence"],
        errors="coerce",
    ).fillna(0)

    yes_df["Profit"] = pd.to_numeric(
        yes_df["Profit"],
        errors="coerce",
    ).fillna(0)

    yes_df["Stake"] = pd.to_numeric(
        yes_df["Stake"],
        errors="coerce",
    ).fillna(0)

    yes_df["Result"] = (
        yes_df["Result"]
        .fillna("")
        .astype(str)
        .str.upper()
        .str.strip()
    )

    bucket_ranges = [
        ("0-59", 0, 59),
        ("60-64", 60, 64),
        ("65-69", 65, 69),
        ("70-74", 70, 74),
        ("75-79", 75, 79),
        ("80+", 80, 999),
    ]

    buckets = []

    for label, low, high in bucket_ranges:
        bdf = yes_df[
            (yes_df["Confidence"] >= low)
            & (yes_df["Confidence"] <= high)
        ].copy()

        plays = len(bdf)
        hr_hits = int((bdf["Result"] == "HR").sum())
        profit = round(bdf["Profit"].sum(), 2)
        stake = round(bdf["Stake"].sum(), 2)

        hit_rate = round((hr_hits / plays * 100), 1) if plays else 0
        roi = round((profit / stake * 100), 1) if stake else 0

        if plays == 0:
            signal = "No Data"
        elif roi > 25 and hit_rate > 10:
            signal = "🔥 Strong"
        elif roi > 0:
            signal = "✅ Positive"
        elif hit_rate > 0:
            signal = "⚠️ Watch"
        else:
            signal = "❌ Weak"

        buckets.append({
            "bucket": label,
            "plays": plays,
            "hr_hits": hr_hits,
            "hit_rate": hit_rate,
            "profit": profit,
            "stake": stake,
            "roi": roi,
            "signal": signal,
        })

    usable = [b for b in buckets if b["plays"] > 0]

    best_bucket = {}
    recommended = ""

    if usable:
        best_bucket = sorted(
            usable,
            key=lambda x: (x["roi"], x["hit_rate"], x["hr_hits"]),
            reverse=True,
        )[0]

        recommended = best_bucket["bucket"].split("-")[0].replace("+", "")

    total_yes = len(yes_df)
    total_hr = int((yes_df["Result"] == "HR").sum())
    total_profit = yes_df["Profit"].sum()
    total_stake = yes_df["Stake"].sum()
    total_roi = round((total_profit / total_stake * 100), 1) if total_stake else 0

    return {
        "total_yes_plays": total_yes,
        "total_hr_hits": total_hr,
        "total_roi": total_roi,
        "recommended_min_confidence": recommended,
        "best_bucket": best_bucket,
        "buckets": buckets,
    }


@app.get("/snapshot-analytics")
def snapshot_analytics():
    df = load_history()

    empty = {
        "best_snapshot": {},
        "total_yes_plays": 0,
        "total_hr_hits": 0,
        "total_roi": 0,
        "snapshots": [],
    }

    if df.empty or "Snapshot" not in df.columns:
        return empty

    yes_df = df[df["Play"] == "YES 🔥"].copy()

    if yes_df.empty:
        return empty

    for col in ["Snapshot", "Result", "Profit", "Stake"]:
        if col not in yes_df.columns:
            yes_df[col] = 0

    yes_df["Snapshot"] = yes_df["Snapshot"].fillna("").astype(str).str.strip()
    yes_df["Result"] = yes_df["Result"].fillna("").astype(str).str.upper().str.strip()
    yes_df["Profit"] = pd.to_numeric(yes_df["Profit"], errors="coerce").fillna(0)
    yes_df["Stake"] = pd.to_numeric(yes_df["Stake"], errors="coerce").fillna(0)

    snapshots = []

    for snap in ["MORNING", "ONE_HOUR", "LOCK", "MANUAL"]:
        sdf = yes_df[yes_df["Snapshot"] == snap].copy()

        plays = len(sdf)
        hr_hits = int((sdf["Result"] == "HR").sum())
        profit = round(sdf["Profit"].sum(), 2)
        stake = round(sdf["Stake"].sum(), 2)

        hit_rate = round((hr_hits / plays * 100), 1) if plays else 0
        roi = round((profit / stake * 100), 1) if stake else 0

        if plays == 0:
            signal = "No Data"
        elif roi > 25:
            signal = "🔥 Strong"
        elif roi > 0:
            signal = "✅ Positive"
        elif hr_hits > 0:
            signal = "⚠️ Watch"
        else:
            signal = "❌ Weak"

        snapshots.append({
            "snapshot": snap,
            "plays": plays,
            "hr_hits": hr_hits,
            "hit_rate": hit_rate,
            "profit": profit,
            "stake": stake,
            "roi": roi,
            "signal": signal,
        })

    usable = [s for s in snapshots if s["plays"] > 0]

    best_snapshot = {}

    if usable:
        best_snapshot = sorted(
            usable,
            key=lambda x: (x["roi"], x["roi"], x["hr_hits"]),
            reverse=True,
        )[0]

    total_yes = len(yes_df)
    total_hr = int((yes_df["Result"] == "HR").sum())
    total_profit = yes_df["Profit"].sum()
    total_stake = yes_df["Stake"].sum()
    total_roi = round((total_profit / total_stake * 100), 1) if total_stake else 0

    return {
        "best_snapshot": best_snapshot,
        "total_yes_plays": total_yes,
        "total_hr_hits": total_hr,
        "total_roi": total_roi,
        "snapshots": snapshots,
    }


@app.get("/top-performer-analytics")
def top_performer_analytics():
    df = load_history()

    empty = {
        "best_player": {},
        "worst_player": {},
        "players": [],
    }

    if df.empty:
        return empty

    yes_df = df[df["Play"] == "YES 🔥"].copy()

    if yes_df.empty:
        return empty

    for col in ["Player", "Team", "Result", "Profit", "Stake"]:
        if col not in yes_df.columns:
            yes_df[col] = ""

    yes_df["Player"] = yes_df["Player"].fillna("").astype(str).str.strip()
    yes_df["Team"] = yes_df["Team"].fillna("").astype(str).str.strip()
    yes_df["Result"] = yes_df["Result"].fillna("").astype(str).str.upper().str.strip()
    yes_df["Profit"] = pd.to_numeric(yes_df["Profit"], errors="coerce").fillna(0)
    yes_df["Stake"] = pd.to_numeric(yes_df["Stake"], errors="coerce").fillna(0)

    rows = []

    for player, pdf in yes_df.groupby("Player"):
        if not player:
            continue

        plays = len(pdf)
        hr_hits = int((pdf["Result"] == "HR").sum())
        profit = round(pdf["Profit"].sum(), 2)
        stake = round(pdf["Stake"].sum(), 2)

        hit_rate = round((hr_hits / plays * 100), 1) if plays else 0
        roi = round((profit / stake * 100), 1) if stake else 0

        team = pdf["Team"].mode().iloc[0] if not pdf["Team"].mode().empty else ""

        if plays < 2:
            signal = "Small Sample"
        elif roi > 25:
            signal = "🔥 Strong"
        elif roi > 0:
            signal = "✅ Positive"
        elif hr_hits > 0:
            signal = "⚠️ Watch"
        else:
            signal = "❌ Weak"

        rows.append({
            "player": player,
            "team": team,
            "plays": plays,
            "hr_hits": hr_hits,
            "hit_rate": hit_rate,
            "profit": profit,
            "stake": stake,
            "roi": roi,
            "signal": signal,
        })

    rows = sorted(rows, key=lambda x: (x["roi"], x["hr_hits"], x["plays"]), reverse=True)

    return {
        "best_player": rows[0] if rows else {},
        "worst_player": sorted(rows, key=lambda x: x["roi"])[0] if rows else {},
        "players": rows[:50],
    }


@app.get("/feature-analytics")
def feature_analytics():
    df = load_history()

    empty = {
        "best_feature": {},
        "total_yes_plays": 0,
        "total_hr_hits": 0,
        "features": [],
    }

    if df.empty:
        return empty

    yes_df = df[df["Play"] == "YES 🔥"].copy()

    if yes_df.empty:
        return empty

    for col in [
        "Result",
        "Profit",
        "Stake",
        "Confidence",
        "Edge",
        "ModelProb",
        "TopEdgeRank",
        "TopProbRank",
        "LineupSpot",
        "Tier",
        "Grade",
        "Snapshot",
    ]:
        if col not in yes_df.columns:
            yes_df[col] = ""

    yes_df["Result"] = yes_df["Result"].fillna("").astype(str).str.upper().str.strip()
    yes_df["Profit"] = pd.to_numeric(yes_df["Profit"], errors="coerce").fillna(0)
    yes_df["Stake"] = pd.to_numeric(yes_df["Stake"], errors="coerce").fillna(0)
    yes_df["Confidence"] = pd.to_numeric(yes_df["Confidence"], errors="coerce").fillna(0)
    yes_df["Edge"] = pd.to_numeric(yes_df["Edge"], errors="coerce").fillna(0)
    yes_df["ModelProb"] = pd.to_numeric(yes_df["ModelProb"], errors="coerce").fillna(0)
    yes_df["TopEdgeRank"] = pd.to_numeric(yes_df["TopEdgeRank"], errors="coerce").fillna(999)
    yes_df["TopProbRank"] = pd.to_numeric(yes_df["TopProbRank"], errors="coerce").fillna(999)
    yes_df["LineupSpot"] = pd.to_numeric(yes_df["LineupSpot"], errors="coerce").fillna(0)

    feature_tests = [
        ("Snapshot LOCK", yes_df["Snapshot"].astype(str).str.upper() == "LOCK"),
        ("Snapshot ONE_HOUR", yes_df["Snapshot"].astype(str).str.upper() == "ONE_HOUR"),
        ("Snapshot MORNING", yes_df["Snapshot"].astype(str).str.upper() == "MORNING"),
        ("Confidence 70+", yes_df["Confidence"] >= 70),
        ("Confidence 75+", yes_df["Confidence"] >= 75),
        ("Edge 5%+", yes_df["Edge"] >= 0.05),
        ("Edge 7%+", yes_df["Edge"] >= 0.07),
        ("Model Prob 20%+", yes_df["ModelProb"] >= 0.20),
        ("Top Edge #1", yes_df["TopEdgeRank"] == 1),
        ("Top Edge Top 3", yes_df["TopEdgeRank"] <= 3),
        ("Top Prob #1", yes_df["TopProbRank"] == 1),
        ("Top Prob Top 4", yes_df["TopProbRank"] <= 4),
        ("Lineup Spot 1-4", yes_df["LineupSpot"].between(1, 4)),
        ("Lineup Spot 5-9", yes_df["LineupSpot"].between(5, 9)),
        ("Grade A/A+", yes_df["Grade"].astype(str).isin(["A", "A+"])),
        ("Grade B", yes_df["Grade"].astype(str) == "B"),
        ("Tier GOD", yes_df["Tier"].astype(str).str.contains("GOD", case=False, na=False)),
        ("Tier ELITE", yes_df["Tier"].astype(str).str.contains("ELITE", case=False, na=False)),
    ]

    features = []

    for label, mask in feature_tests:
        fdf = yes_df[mask].copy()

        plays = len(fdf)
        hr_hits = int((fdf["Result"] == "HR").sum())
        profit = round(fdf["Profit"].sum(), 2)
        stake = round(fdf["Stake"].sum(), 2)

        hit_rate = round((hr_hits / plays * 100), 1) if plays else 0
        roi = round((profit / stake * 100), 1) if stake else 0

        if plays == 0:
            signal = "No Data"
        elif plays < 5:
            signal = "Small Sample"
        elif roi > 25:
            signal = "🔥 Strong"
        elif roi > 0:
            signal = "✅ Positive"
        elif hr_hits > 0:
            signal = "⚠️ Watch"
        else:
            signal = "❌ Weak"

        features.append({
            "feature": label,
            "plays": plays,
            "hr_hits": hr_hits,
            "hit_rate": hit_rate,
            "profit": profit,
            "stake": stake,
            "roi": roi,
            "signal": signal,
        })

    usable = [f for f in features if f["plays"] >= 5]

    best_feature = {}

    if usable:
        best_feature = sorted(
            usable,
            key=lambda x: (x["roi"], x["hit_rate"], x["hr_hits"]),
            reverse=True,
        )[0]

    total_yes = len(yes_df)
    total_hr = int((yes_df["Result"] == "HR").sum())

    features = sorted(
        features,
        key=lambda x: (x["roi"], x["hit_rate"], x["hr_hits"]),
        reverse=True,
    )

    return {
        "best_feature": best_feature,
        "total_yes_plays": total_yes,
        "total_hr_hits": total_hr,
        "features": features,
    }


@app.get("/auto-tuner")
def auto_tuner():
    try:
        confidence = confidence_analytics()
        snapshots = snapshot_analytics()
        features = feature_analytics()

        recommendations = []

        best_snapshot = snapshots.get("best_snapshot", {})
        best_feature = features.get("best_feature", {})
        best_bucket = confidence.get("best_bucket", {})

        if best_snapshot:
            recommendations.append(
                f"Increase weight on {best_snapshot.get('snapshot')} snapshot"
            )

        if best_feature:
            recommendations.append(
                f"Increase weight on {best_feature.get('feature')}"
            )

        if best_bucket:
            recommendations.append(
                f"Target confidence bucket {best_bucket.get('bucket')}"
            )

        return {
            "best_snapshot": best_snapshot,
            "best_feature": best_feature,
            "best_confidence_bucket": best_bucket,
            "recommendations": recommendations,
        }

    except Exception as e:
        return {
            "error": str(e)
        }


@app.get("/ev-analytics")
def ev_analytics():
    df = load_history()

    empty = {
        "best_ev_play": {},
        "average_edge": 0,
        "total_yes_plays": 0,
        "plays": [],
    }

    if df.empty:
        return empty

    yes_df = df[df["Play"] == "YES 🔥"].copy()

    yes_df = yes_df.sort_values(
        by=["Date", "Snapshot", "Player", "Edge"],
        ascending=[True, True, True, False],
    )

    yes_df = yes_df.drop_duplicates(
        subset=["Date", "Player"],
        keep="last",
    )

    if yes_df.empty:
        return empty

    for col in ["Player", "Team", "BestBook", "BestOdds", "ModelProb", "Edge", "Confidence", "SmashScore", "SmashTier", "Result", "Profit"]:
        if col not in yes_df.columns:
            yes_df[col] = ""

    yes_df["ModelProb"] = pd.to_numeric(yes_df["ModelProb"], errors="coerce").fillna(0)
    yes_df["Edge"] = pd.to_numeric(yes_df["Edge"], errors="coerce").fillna(0)
    yes_df["Confidence"] = pd.to_numeric(yes_df["Confidence"], errors="coerce").fillna(0)
    yes_df["Profit"] = pd.to_numeric(yes_df["Profit"], errors="coerce").fillna(0)
    yes_df["SmashScore"] = pd.to_numeric(yes_df.get("SmashScore", 0), errors="coerce").fillna(0)
    yes_df["SmashTier"] = yes_df["SmashTier"].fillna("").replace("nan", "").astype(str).str.strip()

    def implied_prob(odds):
        try:
            odds = float(str(odds).replace("+", "").strip())
            if odds > 0:
                return 100 / (odds + 100)
            return abs(odds) / (abs(odds) + 100)
        except Exception:
            return 0

    plays = []

    for _, row in yes_df.iterrows():
        model_prob = float(row.get("ModelProb", 0))
        odds = row.get("BestOdds", "")
        implied = implied_prob(odds)
        edge = model_prob - implied

        plays.append({
            "player": safe_str(row.get("Player", "")),
            "team": safe_str(row.get("Team", "")),
            "book": safe_str(row.get("BestBook", "")),
            "odds": safe_str(odds),
            "model_prob": round(model_prob * 100, 1),
            "implied_prob": round(implied * 100, 1),
            "ev_edge": round(edge * 100, 1),
            "confidence": safe_float(row.get("Confidence", 0)),
            "smash_score": safe_float(row.get("SmashScore", 0)),
            "smash_tier": safe_str(row.get("SmashTier", "")),
            "result": clean_result(row.get("Result", "")),
            "profit": round(safe_float(row.get("Profit", 0)), 2),
        })

    plays = sorted(plays, key=lambda x: x["ev_edge"], reverse=True)

    avg_edge = round(
        sum(p["ev_edge"] for p in plays) / len(plays),
        1
    ) if plays else 0

    return {
        "best_ev_play": plays[0] if plays else {},
        "average_edge": avg_edge,
        "total_yes_plays": len(plays),
        "plays": plays[:75],
    }


@app.get("/team-analytics")
def team_analytics():
    df = load_history()

    empty = {
        "best_team": {},
        "worst_team": {},
        "teams": [],
    }

    if df.empty:
        return empty

    yes_df = df[df["Play"] == "YES 🔥"].copy()

    if yes_df.empty:
        return empty

    for col in ["Team", "Result", "Profit", "Stake"]:
        if col not in yes_df.columns:
            yes_df[col] = ""

    yes_df["Team"] = yes_df["Team"].fillna("").astype(str).str.strip()
    yes_df["Result"] = yes_df["Result"].fillna("").astype(str).str.upper().str.strip()
    yes_df["Profit"] = pd.to_numeric(yes_df["Profit"], errors="coerce").fillna(0)
    yes_df["Stake"] = pd.to_numeric(yes_df["Stake"], errors="coerce").fillna(0)

    rows = []

    for team, tdf in yes_df.groupby("Team"):
        if not team:
            continue

        plays = len(tdf)
        hr_hits = int((tdf["Result"] == "HR").sum())
        profit = round(tdf["Profit"].sum(), 2)
        stake = round(tdf["Stake"].sum(), 2)

        hit_rate = round((hr_hits / plays * 100), 1) if plays else 0
        roi = round((profit / stake * 100), 1) if stake else 0

        if plays < 3:
            signal = "Small Sample"
        elif roi > 25:
            signal = "🔥 Strong"
        elif roi > 0:
            signal = "✅ Positive"
        elif hr_hits > 0:
            signal = "⚠️ Watch"
        else:
            signal = "❌ Weak"

        rows.append({
            "team": team,
            "plays": plays,
            "hr_hits": hr_hits,
            "hit_rate": hit_rate,
            "profit": profit,
            "stake": stake,
            "roi": roi,
            "signal": signal,
        })

    rows = sorted(
        rows,
        key=lambda x: (x["roi"], x["hit_rate"], x["hr_hits"]),
        reverse=True,
    )

    qualified = [r for r in rows if r["plays"] >= 3]

    best_team = qualified[0] if qualified else (rows[0] if rows else {})
    worst_team = sorted(qualified, key=lambda x: x["roi"])[0] if qualified else {}

    return {
        "best_team": best_team,
        "worst_team": worst_team,
        "teams": rows,
    }


@app.get("/generate-player-adjustments")
def generate_player_adjustments():
    df = load_history()

    if df.empty:
        return {"status": "no data"}

    yes_df = df[df["Play"] == "YES 🔥"].copy()

    rows = []

    for player, pdf in yes_df.groupby("Player"):
        plays = len(pdf)

        if plays < 3:
            continue

        hr_hits = int(
            (pdf["Result"] == "HR").sum()
        )

        hit_rate = hr_hits / plays

        bonus = 0

        if hit_rate >= 0.30:
            bonus = 3
        elif hit_rate >= 0.20:
            bonus = 2
        elif hit_rate >= 0.15:
            bonus = 1
        elif hit_rate <= 0.05:
            bonus = -2

        rows.append({
            "Player": player,
            "Bonus": bonus
        })

    adj = pd.DataFrame(rows)

    adj.to_csv(
        os.path.join(
            DATA_DIR,
            "player_adjustments.csv"
        ),
        index=False
    )

    return {
        "players": len(adj),
        "saved": True
    }