import os
import pandas as pd

from daily_slate_builder import build_daily_slate
from stat_enrichment_v2 import enrich_slate
from run_model import run
from grade_results import grade_results
from backtest import run_backtest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RESULTS_FILE = os.path.join(DATA_DIR, "hr_model_results.csv")


def load_results_fallback():
    if not os.path.exists(RESULTS_FILE):
        return []

    try:
        df = pd.read_csv(RESULTS_FILE)
        return df.to_dict("records")
    except Exception:
        return []


def summarize_results(results):
    if not results:
        return {
            "total": 0,
            "yes": 0,
            "power_bat": 0,
            "value_lean": 0,
            "no_odds": 0,
            "stake": 0,
        }

    df = pd.DataFrame(results)

    play_col = "PlayCode" if "PlayCode" in df.columns else "Play"

    stake = 0
    if "Stake" in df.columns:
        stake = pd.to_numeric(df["Stake"], errors="coerce").fillna(0).sum()

    if play_col == "PlayCode":
        yes = int((df[play_col] == "YES").sum())
        power_bat = int((df[play_col] == "POWER_BAT").sum())
        value_lean = int((df[play_col] == "VALUE_LEAN").sum())
        no_odds = int((df[play_col] == "NO_ODDS").sum())
    else:
        yes = int((df[play_col] == "YES 🔥").sum())
        power_bat = int((df[play_col] == "POWER BAT 💣").sum())
        value_lean = int((df[play_col] == "VALUE LEAN 👀").sum())
        no_odds = int((df[play_col] == "NO ODDS").sum())

    return {
        "total": len(df),
        "yes": yes,
        "power_bat": power_bat,
        "value_lean": value_lean,
        "no_odds": no_odds,
        "stake": round(float(stake), 2),
    }


def main():
    print("\n===================================")
    print("HR MODEL DAILY RUNNER STARTED")
    print("===================================\n")

    print("STEP 1 - BUILDING DAILY SLATE\n")
    build_daily_slate()

    print("\nSTEP 2 - ENRICHING STATS\n")
    enrich_slate()

    print("\nSTEP 3 - RUNNING MODEL\n")
    results = run()

    if results is None:
        results = load_results_fallback()

    summary = summarize_results(results)

    print(f"\nTotal Rows Generated: {summary['total']}")
    print(f"YES Plays: {summary['yes']}")
    print(f"POWER BAT Plays: {summary['power_bat']}")
    print(f"VALUE LEAN Plays: {summary['value_lean']}")
    print(f"NO ODDS Rows: {summary['no_odds']}")
    print(f"Total Stake: {summary['stake']}u")

    print("\nSTEP 4 - GRADING RESULTS\n")

    try:
        grade_results()
    except Exception as e:
        print(f"Grade results skipped or failed: {e}")

    print("\nSTEP 5 - BACKTEST REPORT\n")

    try:
        run_backtest()
    except Exception as e:
        print(f"Backtest skipped or failed: {e}")

    print("\n===================================")
    print("DAILY RUN COMPLETE")
    print("===================================\n")


if __name__ == "__main__":
    main()