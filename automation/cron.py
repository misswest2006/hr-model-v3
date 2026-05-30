import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
DATA = ROOT / "data"
SNAPSHOTS = DATA / "snapshots"

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(BACKEND))

from backend.daily_slate_builder import build_daily_slate
from backend.stat_enrichment import enrich_slate
from backend.run_model import run


def log(message):
    print(f"[{datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}] {message}")


def save_snapshot(label):
    SNAPSHOTS.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    slate = DATA / "sample_slate.csv"
    history = DATA / "hr_results_history.csv"

    if slate.exists():
        shutil.copy(slate, SNAPSHOTS / f"{timestamp}_{label}_sample_slate.csv")

    if history.exists():
        shutil.copy(history, SNAPSHOTS / f"{timestamp}_{label}_hr_results_history.csv")

    log(f"📸 Saved {label} snapshot")


def full_model_refresh(label="MANUAL"):
    label = label.upper().strip()

    os.environ["MODEL_SNAPSHOT_LABEL"] = label

    log(f"🚀 {label} MODEL REFRESH STARTED")

    build_daily_slate()
    enrich_slate()
    results = run()

    save_snapshot(label)

    yes_count = sum(1 for r in results if r.get("play") == "YES 🔥")

    log(f"✅ {label} MODEL REFRESH COMPLETE")
    log(f"🔥 YES Plays: {yes_count}")
    log(f"📊 Total Plays: {len(results)}")

    return results


def morning_run():
    return full_model_refresh("MORNING")


def one_hour_run():
    return full_model_refresh("ONE_HOUR")


def lock_run():
    return full_model_refresh("LOCK")


def manual_run():
    return full_model_refresh("MANUAL")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--snapshot",
        default="MANUAL",
        choices=["MANUAL", "MORNING", "ONE_HOUR", "LOCK"],
        help="Snapshot label for this model run",
    )

    args = parser.parse_args()

    full_model_refresh(args.snapshot)