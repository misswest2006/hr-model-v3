import os
import re
import pandas as pd


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

PITCHER_STATS_FILE = os.path.join(DATA_DIR, "pitcher_stats.csv")

INPUT_CANDIDATES = [
    os.path.join(DATA_DIR, "today_slate_enriched.csv"),
    os.path.join(DATA_DIR, "sample_slate.csv"),
    os.path.join(DATA_DIR, "today_slate.csv"),
    os.path.join(DATA_DIR, "slate.csv"),
]

OUTPUT_FILE = os.path.join(DATA_DIR, "today_slate_enriched.csv")


def safe_float(value, default=0.0):
    try:
        if pd.isna(value):
            return default
        if str(value).strip() == "":
            return default
        return float(value)
    except Exception:
        return default


def safe_text(value, default=""):
    try:
        if pd.isna(value):
            return default
        return str(value).strip()
    except Exception:
        return default


def clean_name(name):
    name = safe_text(name).lower()

    # remove punctuation and suffixes
    name = re.sub(r"[^\w\s]", " ", name)
    name = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", name)
    name = re.sub(r"\s+", " ", name).strip()

    return name


def find_input_file():
    for file in INPUT_CANDIDATES:
        if os.path.exists(file):
            return file

    raise FileNotFoundError("No slate file found in data folder.")


def calculate_pitcher_hr9(row):
    batter_hand = safe_text(row.get("BatterHand", "")).upper()
    pitcher_hand = safe_text(row.get("PitcherHand", row.get("Hand", ""))).upper()

    hr9_lhb = safe_float(row.get("HR9_vs_LHB", 0))
    hr9_rhb = safe_float(row.get("HR9_vs_RHB", 0))

    if batter_hand == "L":
        return hr9_lhb if hr9_lhb > 0 else max(hr9_lhb, hr9_rhb)

    if batter_hand == "R":
        return hr9_rhb if hr9_rhb > 0 else max(hr9_lhb, hr9_rhb)

    if batter_hand == "S":
        if pitcher_hand == "R":
            return hr9_lhb if hr9_lhb > 0 else max(hr9_lhb, hr9_rhb)
        if pitcher_hand == "L":
            return hr9_rhb if hr9_rhb > 0 else max(hr9_lhb, hr9_rhb)

    return max(hr9_lhb, hr9_rhb)


def calculate_pitcher_vulnerability(row):
    hr9 = safe_float(row.get("Pitcher_HR9", 0))
    hard_hit = safe_float(row.get("HardHitAllowed", 0))
    barrel = safe_float(row.get("BarrelAllowed", 0))
    fly = safe_float(row.get("FlyBallAllowed", 0))
    recent = safe_float(row.get("RecentHRAllowed", 0))

    score = 0

    # HR/9
    if hr9 >= 2.20:
        score += 30
    elif hr9 >= 1.80:
        score += 24
    elif hr9 >= 1.40:
        score += 18
    elif hr9 >= 1.00:
        score += 10
    else:
        score += 5

    # Barrel allowed
    if barrel >= 10:
        score += 25
    elif barrel >= 8:
        score += 18
    elif barrel >= 6:
        score += 10
    else:
        score += 5

    # Hard hit allowed
    if hard_hit >= 42:
        score += 20
    elif hard_hit >= 38:
        score += 14
    elif hard_hit >= 34:
        score += 8
    else:
        score += 4

    # Fly ball allowed
    if fly >= 42:
        score += 15
    elif fly >= 38:
        score += 10
    elif fly >= 34:
        score += 6
    else:
        score += 3

    # Recent HR allowed
    if recent >= 0.24:
        score += 15
    elif recent >= 0.18:
        score += 10
    elif recent >= 0.12:
        score += 6
    else:
        score += 2

    return round(min(score, 100), 2)


def guess_pitcher_hr_weak_side(row):
    hr9_lhb = safe_float(row.get("HR9_vs_LHB", 0))
    hr9_rhb = safe_float(row.get("HR9_vs_RHB", 0))

    if hr9_lhb > hr9_rhb:
        return "L"
    if hr9_rhb > hr9_lhb:
        return "R"

    return ""


def guess_pitcher_spot_bucket(row):
    # If you do not have true pitcher HR by lineup bucket yet, this gives a conservative fallback.
    hr9 = safe_float(row.get("Pitcher_HR9", 0))
    barrel = safe_float(row.get("BarrelAllowed", 0))
    fly = safe_float(row.get("FlyBallAllowed", 0))

    if hr9 >= 1.60 and barrel >= 8:
        return "4-6"

    if fly >= 40 and hr9 >= 1.30:
        return "5-9"

    return ""


def main():
    print("🚀 PITCHER MATCH FIX STARTED")

    input_file = find_input_file()
    print(f"📥 Slate file: {input_file}")

    if not os.path.exists(PITCHER_STATS_FILE):
        raise FileNotFoundError(f"Missing pitcher stats file: {PITCHER_STATS_FILE}")

    slate = pd.read_csv(input_file)
    pitchers = pd.read_csv(PITCHER_STATS_FILE)

    if slate.empty:
        print("⚠️ Slate is empty.")
        return

    if pitchers.empty:
        print("⚠️ pitcher_stats.csv is empty.")
        return

    if "Pitcher" not in slate.columns:
        raise ValueError("Slate file is missing Pitcher column.")

    if "Pitcher" not in pitchers.columns:
        raise ValueError("pitcher_stats.csv is missing Pitcher column.")

    slate["PitcherClean"] = slate["Pitcher"].apply(clean_name)
    pitchers["PitcherClean"] = pitchers["Pitcher"].apply(clean_name)

    # Avoid duplicate pitcher stat rows
    pitchers = pitchers.drop_duplicates(subset=["PitcherClean"], keep="last")

    pitcher_cols = [
        "PitcherClean",
        "Hand",
        "HR9_vs_LHB",
        "HR9_vs_RHB",
        "HardHitAllowed",
        "BarrelAllowed",
        "FlyBallAllowed",
        "RecentHRAllowed",
    ]

    available_pitcher_cols = [c for c in pitcher_cols if c in pitchers.columns]

    merged = slate.merge(
        pitchers[available_pitcher_cols],
        on="PitcherClean",
        how="left",
        suffixes=("", "_pitcher")
    )

    matched_mask = merged["Hand"].notna() if "Hand" in merged.columns else pd.Series(False, index=merged.index)
    matched = int(matched_mask.sum())
    total = len(merged)
    fallback = total - matched

    print(f"✅ Pitchers matched: {matched}")
    print(f"⚠️ Fallback pitchers used: {fallback}")

    # Fill missing pitcher stat columns
    defaults = {
        "Hand": "",
        "HR9_vs_LHB": 1.10,
        "HR9_vs_RHB": 1.10,
        "HardHitAllowed": 36.0,
        "BarrelAllowed": 7.0,
        "FlyBallAllowed": 36.0,
        "RecentHRAllowed": 0.10,
    }

    for col, default in defaults.items():
        if col not in merged.columns:
            merged[col] = default
        merged[col] = merged[col].fillna(default)

    merged["PitcherHand"] = merged["Hand"]

    merged["Pitcher_HR9"] = merged.apply(calculate_pitcher_hr9, axis=1)
    merged["PitcherVulnerability"] = merged.apply(calculate_pitcher_vulnerability, axis=1)
    merged["PitcherHRWeakSide"] = merged.apply(guess_pitcher_hr_weak_side, axis=1)

    # Only set PitcherHRSpotWeakness if it is missing or blank
    if "PitcherHRSpotWeakness" not in merged.columns:
        merged["PitcherHRSpotWeakness"] = ""

    blank_spot = merged["PitcherHRSpotWeakness"].isna() | (merged["PitcherHRSpotWeakness"].astype(str).str.strip() == "")
    merged.loc[blank_spot, "PitcherHRSpotWeakness"] = merged[blank_spot].apply(guess_pitcher_spot_bucket, axis=1)

    # Remove helper
    merged = merged.drop(columns=["PitcherClean"], errors="ignore")

    os.makedirs(DATA_DIR, exist_ok=True)
    merged.to_csv(OUTPUT_FILE, index=False)

    print(f"✅ Saved fixed enriched slate: {OUTPUT_FILE}")

    print("")
    print("🔎 Sample matched pitcher rows:")
    show_cols = [
        "Pitcher",
        "PitcherHand",
        "Pitcher_HR9",
        "PitcherVulnerability",
        "PitcherHRWeakSide",
        "PitcherHRSpotWeakness",
    ]
    show_cols = [c for c in show_cols if c in merged.columns]
    print(merged[show_cols].drop_duplicates().head(20).to_string(index=False))


if __name__ == "__main__":
    main()
