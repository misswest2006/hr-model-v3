from daily_slate_builder import build_daily_slate
from stat_enrichment import enrich_slate
from run_model import run
from grade_results import grade_results
from backtest import run_backtest


def main():

    print("\n===================================")
    print("🚀 HR MODEL DAILY RUNNER STARTED")
    print("===================================\n")

    # -------------------------
    # STEP 1
    # BUILD DAILY SLATE
    # -------------------------

    print("📅 STEP 1 — BUILDING DAILY SLATE\n")

    build_daily_slate()

    # -------------------------
    # STEP 2
    # ENRICH STATS
    # -------------------------

    print("\n📊 STEP 2 — ENRICHING STATS\n")

    enrich_slate()

    # -------------------------
    # STEP 3
    # RUN MODEL
    # -------------------------

    print("\n🤖 STEP 3 — RUNNING ML MODEL\n")

    results = run()

    print(f"\n✅ Total Plays Generated: {len(results)}")

    # -------------------------
    # STEP 4
    # GRADE HISTORICAL RESULTS
    # -------------------------

    print("\n🎯 STEP 4 — GRADING RESULTS\n")

    grade_results()

    # -------------------------
    # STEP 5
    # BACKTEST REPORT
    # -------------------------

    print("\n📈 STEP 5 — BACKTEST REPORT\n")

    run_backtest()

    print("\n===================================")
    print("🔥 DAILY RUN COMPLETE")
    print("===================================\n")


if __name__ == "__main__":

    main()