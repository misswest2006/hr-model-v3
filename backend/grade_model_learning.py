import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

LEARNING_FILE = os.path.join(DATA_DIR, "model_learning.csv")

HR_HITTERS = [
    "Kyle Schwarber",
]


def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        if pd.isna(value):
            return default
        value = str(value).strip()
        if value == "" or value.lower() in ["nan", "none"]:
            return default
        return float(value)
    except Exception:
        return default


def profit_from_odds_and_stake(odds, result, stake):
    odds = safe_float(odds, 0)
    stake = safe_float(stake, 1)

    if stake <= 0:
        stake = 1

    result = str(result).upper().strip()

    if result == "HR":
        if odds > 0:
            return round((odds / 100) * stake, 2)
        return round((100 / abs(odds)) * stake, 2)

    if result == "NO HR":
        return round(-1 * stake, 2)

    return 0


def main():
    if not os.path.exists(LEARNING_FILE):
        raise FileNotFoundError(f"Missing file: {LEARNING_FILE}")

    df = pd.read_csv(LEARNING_FILE)

    if df.empty:
        print("model_learning.csv is empty.")
        return

    for col in ["HRResult", "Profit", "BestOdds", "Player", "Stake"]:
        if col not in df.columns:
            df[col] = ""

    hr_hitters_clean = {p.strip().lower() for p in HR_HITTERS}

    df["HRResult"] = df["Player"].astype(str).str.strip().str.lower().apply(
        lambda p: "HR" if p in hr_hitters_clean else "NO HR"
    )

    df["Stake"] = pd.to_numeric(df["Stake"], errors="coerce").fillna(0.25)

    df["Profit"] = df.apply(
        lambda row: profit_from_odds_and_stake(
            row.get("BestOdds", 0),
            row.get("HRResult", ""),
            row.get("Stake", 0.25)
        ),
        axis=1
    )

    df.to_csv(LEARNING_FILE, index=False)

    total_plays = len(df)
    total_stake = round(pd.to_numeric(df["Stake"], errors="coerce").fillna(0).sum(), 2)
    total_hr = int((df["HRResult"] == "HR").sum())
    total_profit = round(pd.to_numeric(df["Profit"], errors="coerce").fillna(0).sum(), 2)
    hit_rate = round((total_hr / total_plays * 100), 2) if total_plays else 0
    roi = round((total_profit / total_stake * 100), 2) if total_stake else 0

    print()
    print("MODEL LEARNING GRADED")
    print(f"Total plays: {total_plays}")
    print(f"Total stake: {total_stake}u")
    print(f"HR hits: {total_hr}")
    print(f"Hit rate: {hit_rate}%")
    print(f"Profit: {total_profit}u")
    print(f"ROI: {roi}%")
    print()
    print(
        df[["Player", "Play", "BestOdds", "Stake", "HRResult", "Profit"]]
        .head(50)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()