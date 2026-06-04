import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

HISTORY_FILE = os.path.join(DATA_DIR, "hr_results_history.csv")
BACKUP_FILE = os.path.join(DATA_DIR, "hr_results_history_backup_before_deep_dedupe.csv")


def main():
    if not os.path.exists(HISTORY_FILE):
        print("Missing hr_results_history.csv")
        return

    df = pd.read_csv(HISTORY_FILE)

    if df.empty:
        print("History file is empty.")
        return

    original_rows = len(df)
    df.to_csv(BACKUP_FILE, index=False, encoding="utf-8-sig")

    for col in ["Date", "Player", "Pitcher", "BestOdds", "Profit"]:
        if col not in df.columns:
            df[col] = ""

    df["Date"] = df["Date"].astype(str).str.strip()
    df["Player"] = df["Player"].astype(str).str.strip()
    df["Pitcher"] = df["Pitcher"].astype(str).str.strip()
    df["BestOdds"] = df["BestOdds"].astype(str).str.strip()
    df["Profit"] = pd.to_numeric(df["Profit"], errors="coerce").fillna(0)

    df["IsWin"] = df["Profit"] > 0

    df = df.sort_values(
        by=["Date", "Player", "Pitcher", "BestOdds", "IsWin", "Profit"],
        ascending=[True, True, True, True, False, False]
    )

    deduped = df.drop_duplicates(
        subset=["Date", "Player", "Pitcher", "BestOdds"],
        keep="first"
    ).copy()

    deduped = deduped.drop(columns=["IsWin"], errors="ignore")

    deduped.to_csv(HISTORY_FILE, index=False, encoding="utf-8-sig")

    print()
    print("DEEP HISTORY DEDUPE COMPLETE")
    print(f"Original rows: {original_rows}")
    print(f"Clean rows: {len(deduped)}")
    print(f"Removed duplicates: {original_rows - len(deduped)}")
    print(f"Backup saved: {BACKUP_FILE}")


if __name__ == "__main__":
    main()