import os
import sys
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
DATA = ROOT / "data"
SNAPSHOTS = DATA / "snapshots"

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(BACKEND))


def log(message):
    print(f"[{datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}] {message}")


def run_cmd(label, command):
    log(f"{label} started")

    result = subprocess.run(
        command,
        cwd=ROOT,
        shell=True,
        text=True
    )

    if result.returncode != 0:
        log(f"{label} failed")
        raise RuntimeError(f"{label} failed")

    log(f"{label} complete")


def save_snapshot(label):
    SNAPSHOTS.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    files_to_save = [
        DATA / "sample_slate.csv",
        DATA / "today_slate_enriched.csv",
        DATA / "hr_model_results.csv",
        DATA / "model_learning.csv",
        DATA / "auto_tuner_report.csv",
        DATA / "hr_results_history.csv",
    ]

    for file_path in files_to_save:
        if file_path.exists():
            shutil.copy(
                file_path,
                SNAPSHOTS / f"{timestamp}_{label}_{file_path.name}"
            )

    log(f"Saved {label} snapshot")


def summarize_results():
    results_path = DATA / "hr_model_results.csv"

    if not results_path.exists():
        return {
            "total": 0,
            "yes": 0,
            "power_bat": 0,
            "value_lean": 0,
            "no_odds": 0,
            "stake": 0,
        }

    df = pd.read_csv(results_path)

    if df.empty:
        return {
            "total": 0,
            "yes": 0,
            "power_bat": 0,
            "value_lean": 0,
            "no_odds": 0,
            "stake": 0,
        }

    play_col = "PlayCode" if "PlayCode" in df.columns else "Play"

    stake = 0
    if "Stake" in df.columns:
        stake = pd.to_numeric(df["Stake"], errors="coerce").fillna(0).sum()

    return {
        "total": len(df),
        "yes": int((df[play_col] == "YES").sum()) if play_col == "PlayCode" else int((df[play_col] == "YES 🔥").sum()),
        "power_bat": int((df[play_col] == "POWER_BAT").sum()) if play_col == "PlayCode" else int((df[play_col] == "POWER BAT 💣").sum()),
        "value_lean": int((df[play_col] == "VALUE_LEAN").sum()) if play_col == "PlayCode" else int((df[play_col] == "VALUE LEAN 👀").sum()),
        "no_odds": int((df[play_col] == "NO_ODDS").sum()) if play_col == "PlayCode" else int((df[play_col] == "NO ODDS").sum()),
        "stake": round(float(stake), 2),
    }


def full_model_refresh(label="MANUAL"):
    label = label.upper().strip()
    os.environ["MODEL_SNAPSHOT_LABEL"] = label

    log(f"{label} MODEL REFRESH STARTED")

    run_cmd(
        "Step 1 - Build daily slate",
        "py backend\\daily_slate_builder.py"
    )

    run_cmd(
        "Step 2 - Enrichment V2",
        "py backend\\stat_enrichment_v2.py"
    )

    run_cmd(
        "Step 3 - Run Model V3.6",
        "py backend\\run_model.py"
    )

    run_cmd(
        "Step 4 - Build Model Learning",
        "py backend\\build_model_learning.py"
    )

    run_cmd(
        "Step 5 - Auto Tuner",
        "py backend\\auto_tuner.py"
    )

    save_snapshot(label)

    summary = summarize_results()

    log(f"{label} MODEL REFRESH COMPLETE")
    log(f"YES Plays: {summary['yes']}")
    log(f"POWER BAT Plays: {summary['power_bat']}")
    log(f"VALUE LEAN Plays: {summary['value_lean']}")
    log(f"NO ODDS Rows: {summary['no_odds']}")
    log(f"Total Rows: {summary['total']}")
    log(f"Total Stake: {summary['stake']}u")

    return summary


if __name__ == "__main__":
    full_model_refresh("MANUAL")