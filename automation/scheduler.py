import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
SLATE_PATH = ROOT / "data" / "sample_slate.csv"
HISTORY_PATH = ROOT / "data" / "hr_results_history.csv"

ran_today = set()


def log(message):
    print(f"[{datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}] {message}", flush=True)


def run_command(command):
    subprocess.run(command, cwd=str(ROOT), check=False)


def has_snapshot_run_today(label):
    if not HISTORY_PATH.exists():
        return False

    try:
        df = pd.read_csv(HISTORY_PATH)
    except Exception:
        return False

    if df.empty or "Date" not in df.columns or "Snapshot" not in df.columns:
        return False

    today = datetime.now().strftime("%Y-%m-%d")

    df["Date"] = df["Date"].astype(str).str.strip()
    df["Snapshot"] = df["Snapshot"].astype(str).str.upper().str.strip()

    return not df[
        (df["Date"] == today)
        & (df["Snapshot"] == label.upper())
    ].empty


def run_snapshot(label):
    today = datetime.now().date()
    key = f"{today}_{label}"

    if key in ran_today:
        return

    if has_snapshot_run_today(label):
        ran_today.add(key)
        log(f"✅ {label} snapshot already exists today. Skipping.")
        return

    ran_today.add(key)

    log(f"🚀 Running {label} snapshot")

    run_command([
        "py",
        str(ROOT / "automation" / "cron.py"),
        "--snapshot",
        label,
    ])

    log(f"✅ Finished {label} snapshot")


def run_nightly_grade():
    today = datetime.now().date()
    key = f"{today}_NIGHTLY_GRADE"

    if key in ran_today:
        return

    ran_today.add(key)

    game_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    log(f"🌙 Running nightly grading for {game_date}")

    run_command([
        "py",
        str(ROOT / "automation" / "nightly_grade.py"),
        "--date",
        game_date,
    ])

    log("✅ Finished nightly grading")


def get_first_game_time():
    if not SLATE_PATH.exists():
        return None

    try:
        df = pd.read_csv(SLATE_PATH)
    except Exception:
        return None

    if df.empty or "GameTimeET" not in df.columns:
        return None

    times = pd.to_datetime(df["GameTimeET"], errors="coerce").dropna()

    if times.empty:
        return None

    return times.min().to_pydatetime().replace(tzinfo=None)


def main():
    log("⏰ HR Model Scheduler Started")
    log("✅ MORNING run window: 9:00 AM")
    log("✅ MORNING catch-up: runs after 9:00 AM if missed")
    log("✅ ONE_HOUR run window: 1 hour before first pitch")
    log("✅ LOCK run window: 15 minutes before first pitch")
    log("✅ NIGHTLY GRADE window: 1:30 AM")

    while True:
        now = datetime.now()
        first_pitch = get_first_game_time()

        # MORNING normal window: 9:00 - 9:05 AM
        if now.hour == 9 and now.minute < 5:
            run_snapshot("MORNING")

        # MORNING catch-up: if scheduler starts after 9:05 and MORNING did not run
        if now.hour >= 9 and not has_snapshot_run_today("MORNING"):
            run_snapshot("MORNING")

        if first_pitch:
            one_hour_time = first_pitch - timedelta(hours=1)
            lock_time = first_pitch - timedelta(minutes=15)

            # ONE_HOUR run: 1 hour before first pitch
            if 0 <= (now - one_hour_time).total_seconds() < 300:
                run_snapshot("ONE_HOUR")

            # LOCK run: 15 minutes before first pitch
            if 0 <= (now - lock_time).total_seconds() < 300:
                run_snapshot("LOCK")

        # Nightly grade around 1:30 AM
        if now.hour == 1 and 30 <= now.minute < 35:
            run_nightly_grade()

        # Reset memory after 3 AM
        if now.hour == 3 and now.minute < 5:
            ran_today.clear()

        time.sleep(60)


if __name__ == "__main__":
    main()