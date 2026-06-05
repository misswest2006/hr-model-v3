import argparse
import os
import shutil
import subprocess
import sys
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
    print(f"[{datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}] {message}", flush=True)


def run_cmd(label, command, required=True):
    log(f"{label} started")

    result = subprocess.run(
        command,
        cwd=str(ROOT),
        shell=True,
        text=True
    )

    if result.returncode != 0:
        log(f"{label} failed")

        if required:
            raise RuntimeError(f"{label} failed")

        return False

    log(f"{label} complete")
    return True


def save_snapshot(label):
    label = str(label or "MANUAL").upper().strip()
    SNAPSHOTS.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    files_to_save = [
        DATA / "sample_slate.csv",
        DATA / "today_slate_enriched.csv",
        DATA / "hr_model_results.csv",
        DATA / "hr_results_history.csv",
        DATA / "yes_performance_tracker.csv",
        DATA / "bankroll_tracker.csv",
        DATA / "model_learning.csv",
        DATA / "auto_tuner_report.csv",
    ]

    for file_path in files_to_save:
        if file_path.exists():
            shutil.copy(
                file_path,
                SNAPSHOTS / f"{timestamp}_{label}_{file_path.name}"
            )

    log(f"Saved {label} snapshot")


def stamp_snapshot_label(label):
    label = str(label or "MANUAL").upper().strip()
    today = datetime.now().strftime("%Y-%m-%d")

    files_to_stamp = [
        DATA / "hr_model_results.csv",
        DATA / "hr_results_history.csv",
        DATA / "yes_performance_tracker.csv",
        DATA / "bankroll_tracker.csv",
    ]

    for path in files_to_stamp:
        if not path.exists():
            continue

        try:
            df = pd.read_csv(path)
        except Exception as e:
            log(f"Could not read {path.name} to stamp snapshot: {e}")
            continue

        if df.empty:
            continue

        if "Snapshot" not in df.columns:
            df["Snapshot"] = label
        else:
            df["Snapshot"] = df["Snapshot"].fillna("").astype(str).str.strip()

            if path.name == "hr_model_results.csv":
                df["Snapshot"] = label
            elif "Date" in df.columns:
                mask = df["Date"].astype(str).str.strip() == today
                if mask.any():
                    df.loc[mask, "Snapshot"] = label
                else:
                    df.loc[df["Snapshot"] == "", "Snapshot"] = label
            else:
                df.loc[df["Snapshot"] == "", "Snapshot"] = label

        try:
            df.to_csv(path, index=False)
            log(f"Stamped {path.name} with Snapshot={label}")
        except Exception as e:
            log(f"Could not write {path.name} snapshot stamp: {e}")


def cleanup_blank_snapshots():
    files_to_clean = [
        DATA / "hr_results_history.csv",
        DATA / "yes_performance_tracker.csv",
        DATA / "bankroll_tracker.csv",
    ]

    for path in files_to_clean:
        if not path.exists():
            continue

        try:
            df = pd.read_csv(path)
        except Exception:
            continue

        if df.empty or "Snapshot" not in df.columns:
            continue

        df["Snapshot"] = df["Snapshot"].fillna("").astype(str).str.strip()
        df.loc[df["Snapshot"] == "", "Snapshot"] = "UNKNOWN"

        df.to_csv(path, index=False)
        log(f"Cleaned blank snapshots in {path.name}")


def summarize_results():
    results_path = DATA / "hr_model_results.csv"

    empty_summary = {
        "total": 0,
        "yes": 0,
        "power_bat": 0,
        "value_lean": 0,
        "no_odds": 0,
        "stake": 0,
    }

    if not results_path.exists():
        return empty_summary

    try:
        df = pd.read_csv(results_path)
    except Exception:
        return empty_summary

    if df.empty:
        return empty_summary

    play_col = "PlayCode" if "PlayCode" in df.columns else "Play"

    stake = 0
    if "Stake" in df.columns:
        stake = pd.to_numeric(df["Stake"], errors="coerce").fillna(0).sum()

    plays = df[play_col].fillna("").astype(str).str.upper().str.strip()

    return {
        "total": len(df),
        "yes": int((plays == "YES").sum()) if play_col == "PlayCode" else int(plays.str.contains("YES").sum()),
        "power_bat": int((plays == "POWER_BAT").sum()) if play_col == "PlayCode" else int(plays.str.contains("POWER").sum()),
        "value_lean": int((plays == "VALUE_LEAN").sum()) if play_col == "PlayCode" else int(plays.str.contains("VALUE").sum()),
        "no_odds": int((plays == "NO_ODDS").sum()) if play_col == "PlayCode" else int(plays.str.contains("NO ODDS").sum()),
        "stake": round(float(stake), 2),
    }


def full_model_refresh(label="MANUAL"):
    label = str(label or "MANUAL").upper().strip()
    os.environ["MODEL_SNAPSHOT_LABEL"] = label

    log(f"{label} MODEL REFRESH STARTED")

    # 1. Build slate
    run_cmd(
        "Step 1 - Build daily slate",
        "py backend\\daily_slate_builder.py"
    )

    # 2. Enrich stats + odds
    run_cmd(
        "Step 2 - Enrichment V2",
        "py backend\\stat_enrichment_v2.py"
    )

    # 3. Run model
    run_cmd(
        "Step 3 - Run Model V3.11",
        "py backend\\run_model.py"
    )

    # 4. Stamp snapshot immediately after model writes results
    stamp_snapshot_label(label)

    # 5. Build performance tracker
    run_cmd(
        "Step 4 - YES Performance Tracker",
        "py backend\\yes_performance_tracker.py",
        required=False
    )

    # 6. Stamp tracker rows after performance tracker rebuild
    stamp_snapshot_label(label)

    # 7. Build bankroll tracker
    run_cmd(
        "Step 5 - Bankroll Tracker",
        "py backend\\bankroll_tracker.py",
        required=False
    )

    # 8. Stamp bankroll rows after bankroll rebuild
    stamp_snapshot_label(label)

    # 9. Clean old blank snapshots
    cleanup_blank_snapshots()

    # 10. Build Signal Lab
    run_cmd(
        "Step 6 - Signal Performance Lab",
        "py backend\\signal_performance_lab.py",
        required=False
    )

    # 11. Build model learning
    run_cmd(
        "Step 7 - Build Model Learning",
        "py backend\\build_model_learning.py",
        required=False
    )

    # 12. Auto Tuner
    run_cmd(
        "Step 8 - Auto Tuner",
        "py backend\\auto_tuner.py",
        required=False
    )

    # 13. Save backup snapshot
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", default="MANUAL")
    args = parser.parse_args()

    full_model_refresh(args.snapshot)


if __name__ == "__main__":
    main()
