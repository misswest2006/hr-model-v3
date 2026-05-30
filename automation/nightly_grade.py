import sys
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(BACKEND))

from backend.auto_hr_results import save_hr_hits
from backend.grade_results import grade_results


def log(message):
    print(f"[{datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}] {message}")


def run_nightly_grade(game_date=None):
    if game_date is None:
        game_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    log(f"🌙 Nightly grading started for {game_date}")

    save_hr_hits(game_date)
    grade_results(game_date)

    log("✅ Nightly grading complete")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None, help="Date to grade, format YYYY-MM-DD")
    args = parser.parse_args()

    run_nightly_grade(args.date)