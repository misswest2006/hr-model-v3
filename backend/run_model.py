import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

INPUT_FILE = os.path.join(DATA_DIR, "today_slate_enriched.csv")
OUTPUT_FILE = os.path.join(DATA_DIR, "hr_model_results.csv")


def safe_num(value, default=0.0):
    try:
        if value == "" or value is None:
            return default
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def implied_probability(odds):
    odds = safe_num(odds, 0)

    if odds == 0:
        return np.nan

    if odds > 0:
        return 100 / (odds + 100)

    return abs(odds) / (abs(odds) + 100)


def best_odds(row):
    books = {
        "FanDuel": row.get("FanDuel"),
        "DraftKings": row.get("DraftKings"),
        "BetMGM": row.get("BetMGM"),
    }

    clean = {}

    for book, odds in books.items():
        val = safe_num(odds, np.nan)
        if not pd.isna(val) and val != 0:
            clean[book] = val

    if not clean:
        return pd.Series(["NO_ODDS", np.nan, False])

    best_book = max(clean, key=clean.get)
    best_price = clean[best_book]

    return pd.Series([best_book, best_price, True])


def percentile_score(series):
    series = pd.to_numeric(series, errors="coerce").fillna(0)

    if series.nunique() <= 1:
        return pd.Series([50.0] * len(series), index=series.index)

    return (series.rank(pct=True) * 100).round(2)


def lineup_adjustment(spot):
    spot = safe_num(spot, 0)

    if spot == 0:
        return -18

    if spot == 2:
        return -8

    if spot == 3:
        return 10

    if spot == 4:
        return 8

    if spot == 5:
        return 9

    if spot == 6:
        return 2

    return 0


def calculate_raw_scores(df):
    numeric_cols = [
        "TruePowerIndex",
        "ISO",
        "HardHit",
        "BarrelRate",
        "RecentHRRate",
        "Pitcher_HR9",
        "PitcherVulnerability",
        "PitcherHRWeaknessScore",
        "PitcherLineupWeakSpot",
        "ContactQualityScore",
        "LaunchProfileScore",
        "PulledAirScore",
        "EnrichmentScore",
        "LineupSpot",
        "ParkFactor",
        "WindFactor",
        "Matchup",
    ]

    for col in numeric_cols:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["LineupSpotAdj"] = df["LineupSpot"].apply(lineup_adjustment)

    df["RawHRScore"] = (
        df["TruePowerIndex"] * 0.34
        + df["BarrelRate"] * 4.8
        + df["HardHit"] * 1.15
        + df["ISO"] * 250
        + df["RecentHRRate"] * 180
        + df["PitcherHRWeaknessScore"] * 6.5
        + df["PitcherVulnerability"] * 0.85
        + df["PitcherLineupWeakSpot"] * 4.5
        + df["ParkFactor"] * 8
        + df["WindFactor"] * 4
        + df["Matchup"] * 10
        + df["LineupSpotAdj"]
    )

    df["RawDecisionScore"] = (
        df["RawHRScore"] * 0.45
        + df["EnrichmentScore"] * 0.25
        + df["PitcherVulnerability"] * 0.20
        + df["PitcherLineupWeakSpot"] * 1.2
        + df["LineupSpotAdj"] * 1.4
    )

    df["RawSmashScore"] = (
        df["TruePowerIndex"] * 0.25
        + df["RawHRScore"] * 0.35
        + df["PitcherVulnerability"] * 0.75
        + df["PitcherHRWeaknessScore"] * 5.5
        + df["PitcherLineupWeakSpot"] * 5
        + df["LineupSpotAdj"] * 1.2
    )

    return df


def apply_percentile_scores(df):
    df["HRScore"] = percentile_score(df["RawHRScore"])
    df["DecisionScore"] = percentile_score(df["RawDecisionScore"])
    df["SmashScore"] = percentile_score(df["RawSmashScore"])
    df["PowerScore"] = df["TruePowerIndex"].round(2)

    pitcher_pct = percentile_score(df["PitcherVulnerability"])

    df["Confidence"] = (
        df["HRScore"] * 0.40
        + df["DecisionScore"] * 0.30
        + df["SmashScore"] * 0.20
        + pitcher_pct * 0.10
    ).round(2)

    return df


def calculate_model_probability(df):
    df["BestImpliedProb"] = df["BestOdds"].apply(implied_probability)

    hr_pct = df["HRScore"] / 100
    decision_pct = df["DecisionScore"] / 100
    smash_pct = df["SmashScore"] / 100
    pitcher_pct = percentile_score(df["PitcherVulnerability"]) / 100

    raw_prob = (
        0.055
        + hr_pct * 0.055
        + decision_pct * 0.040
        + smash_pct * 0.035
        + pitcher_pct * 0.020
    )

    df["RawModelProb"] = raw_prob.round(4)
    df["ModelProb"] = raw_prob.clip(0.045, 0.235).round(4)

    df["Edge"] = (
        df["ModelProb"] - df["BestImpliedProb"]
    ).round(6)

    df["EVScore"] = np.where(
        df["HasOdds"],
        (df["Edge"] * 100).round(2),
        0
    )

    df["Edge"] = pd.to_numeric(df["Edge"], errors="coerce").fillna(0)
    df["EVScore"] = pd.to_numeric(df["EVScore"], errors="coerce").fillna(0)

    return df


def assign_grade(row):
    confidence = safe_num(row.get("Confidence"))
    hr_score = safe_num(row.get("HRScore"))
    smash = safe_num(row.get("SmashScore"))

    if confidence >= 96 and hr_score >= 96 and smash >= 94:
        return "A+"

    if confidence >= 90 and hr_score >= 90:
        return "A"

    if confidence >= 82:
        return "B+"

    if confidence >= 72:
        return "B"

    if confidence >= 60:
        return "C"

    return "D"


def assign_tier(row):
    confidence = safe_num(row.get("Confidence"))
    edge = safe_num(row.get("Edge"))
    hr_score = safe_num(row.get("HRScore"))
    smash = safe_num(row.get("SmashScore"))

    if confidence >= 97 and hr_score >= 97 and smash >= 97 and edge > 0:
        return "GOD_TIER"

    if confidence >= 95 and hr_score >= 95 and smash >= 95:
        return "ELITE"

    if confidence >= 90 and hr_score >= 90:
        return "STRONG"

    if confidence >= 82:
        return "WATCH"

    return "LOW"


def assign_play(row):
    confidence = safe_num(row.get("Confidence"))
    edge = safe_num(row.get("Edge"), -999)
    hr_score = safe_num(row.get("HRScore"))
    decision = safe_num(row.get("DecisionScore"))
    smash = safe_num(row.get("SmashScore"))
    lineup_spot = safe_num(row.get("LineupSpot"))
    has_odds = bool(row.get("HasOdds"))

    if not has_odds:
        return "NO_ODDS"

    # V3.10 extreme edge override
    if (
        edge >= 0.15
        and confidence >= 80
        and hr_score >= 80
        and decision >= 80
    ):
        return "YES"

    if lineup_spot == 0 and edge < 0.12:
        if edge > 0 and confidence >= 78:
            return "VALUE_LEAN"
        return "PASS"

    if lineup_spot == 2 and edge < 0.10:
        if confidence >= 88 and hr_score >= 90 and edge > 0:
            return "POWER_BAT"
        if edge > 0 and confidence >= 78:
            return "VALUE_LEAN"
        return "PASS"

    if (
        confidence >= 95
        and hr_score >= 95
        and decision >= 95
        and smash >= 95
        and edge >= -0.005
    ):
        return "YES"

    if (
        confidence >= 92
        and hr_score >= 95
        and decision >= 95
        and edge > 0
    ):
        return "YES"

    if (
        edge >= 0.10
        and confidence >= 84
        and hr_score >= 84
        and decision >= 84
    ):
        return "YES"

    if (
        edge >= 0.05
        and edge < 0.10
        and confidence >= 90
        and hr_score >= 88
        and decision >= 90
    ):
        return "YES"

    if (
        edge >= 0.03
        and edge < 0.05
        and confidence >= 88
        and hr_score >= 88
        and decision >= 88
    ):
        return "YES"

    if confidence >= 86 and hr_score >= 88:
        return "POWER_BAT"

    if edge > 0 and confidence >= 78:
        return "VALUE_LEAN"

    return "PASS"


def assign_display_labels(df):
    play_map = {
        "YES": "YES 🔥",
        "POWER_BAT": "POWER BAT 💣",
        "VALUE_LEAN": "VALUE LEAN 👀",
        "NO_ODDS": "NO ODDS",
        "PASS": "PASS",
    }

    tier_map = {
        "GOD_TIER": "GOD TIER 👑",
        "ELITE": "ELITE 🔥",
        "STRONG": "STRONG 💣",
        "WATCH": "WATCH 👀",
        "LOW": "LOW",
    }

    df["PlayCode"] = df["Play"]
    df["TierCode"] = df["Tier"]

    df["Play"] = df["PlayCode"].map(play_map).fillna(df["PlayCode"])
    df["Tier"] = df["TierCode"].map(tier_map).fillna(df["TierCode"])

    return df


def assign_reason(row):
    play_code = str(row.get("PlayCode", row.get("Play", "")))
    confidence = safe_num(row.get("Confidence"))
    edge = safe_num(row.get("Edge"))
    hr_score = safe_num(row.get("HRScore"))
    lineup_spot = safe_num(row.get("LineupSpot"))

    if play_code == "YES":
        if edge >= 0.15:
            return "V3.10 extreme edge official play"
        if edge < 0:
            return "Elite HR profile overrides tiny negative edge"
        if edge >= 0.10:
            return "High-edge official play"
        if edge >= 0.05:
            return "Protected 5-10 edge official play"
        if edge >= 0.03:
            return "Positive low-edge official play"
        return "Strong HR profile with playable edge"

    if lineup_spot == 0 and play_code in ["PASS", "VALUE_LEAN"]:
        return "Lineup spot missing. V3.10 downgrade applied."

    if lineup_spot == 2 and play_code in ["PASS", "VALUE_LEAN", "POWER_BAT"]:
        return "Lineup spot 2 underperformed in tuner. V3.10 protection applied."

    if play_code == "POWER_BAT":
        if confidence >= 90 and hr_score >= 90:
            return "Elite power bat but edge is too negative"
        return "Power bat profile but not enough official-card edge"

    if play_code == "VALUE_LEAN":
        return "Positive edge but not enough elite HR signals"

    if play_code == "NO_ODDS":
        return "No sportsbook odds available"

    if confidence >= 90 and hr_score >= 90:
        return "Strong profile but failed V3.10 official-card threshold"

    return "Not enough confirmed HR signals"


def assign_stake(row):
    play_code = str(row.get("PlayCode", row.get("Play", "")))
    confidence = safe_num(row.get("Confidence"))
    edge = safe_num(row.get("Edge"))
    hr_score = safe_num(row.get("HRScore"))
    decision = safe_num(row.get("DecisionScore"))
    smash = safe_num(row.get("SmashScore"))

    if play_code == "YES":
        if (
            confidence >= 97
            and hr_score >= 97
            and decision >= 97
            and smash >= 97
            and edge >= 0.015
        ):
            return 0.50

        return 0.25

    if play_code == "POWER_BAT":
        return 0.10

    if play_code == "VALUE_LEAN":
        return 0.10

    return 0


def add_rankings(df):
    df["TopHRRank"] = df["HRScore"].rank(method="dense", ascending=False).astype(int)
    df["TopEdgeRank"] = df["Edge"].rank(method="dense", ascending=False).astype(int)
    df["TopProbRank"] = df["ModelProb"].rank(method="dense", ascending=False).astype(int)
    df["TopSmashRank"] = df["SmashScore"].rank(method="dense", ascending=False).astype(int)
    return df


def add_frontend_aliases(df):
    df["PitcherScore"] = df.get("PitcherHRWeaknessScore", 0)
    df["PitcherLineupScore"] = df.get("PitcherLineupWeakSpot", 0)
    df["SmashTier"] = df["Tier"]
    return df


def main():
    print(f"Loading slate: {INPUT_FILE}")

    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"Missing enriched slate: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE)

    for col in ["FanDuel", "DraftKings", "BetMGM"]:
        if col not in df.columns:
            df[col] = np.nan

    df[["BestBook", "BestOdds", "HasOdds"]] = df.apply(best_odds, axis=1)

    df = calculate_raw_scores(df)
    df = apply_percentile_scores(df)
    df = calculate_model_probability(df)

    df["Grade"] = df.apply(assign_grade, axis=1)
    df["Tier"] = df.apply(assign_tier, axis=1)
    df["Play"] = df.apply(assign_play, axis=1)

    df = add_rankings(df)
    df = assign_display_labels(df)

    df["Reason"] = df.apply(assign_reason, axis=1)
    df["Stake"] = df.apply(assign_stake, axis=1)

    df = add_frontend_aliases(df)

    df = df.sort_values(
        by=["Confidence", "HRScore", "SmashScore", "Edge"],
        ascending=[False, False, False, False]
    )

    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    odds_rows = int(df["HasOdds"].sum())
    no_odds_rows = int((~df["HasOdds"].astype(bool)).sum())

    print()
    print("MODEL COMPLETE - V3.10 EXTREME EDGE OVERRIDE")
    print(f"Saved results to: {OUTPUT_FILE}")
    print()
    print(f"Odds rows: {odds_rows}")
    print(f"No odds rows: {no_odds_rows}")
    print()
    print("Play counts:")
    print(df["PlayCode"].value_counts().to_string())
    print()
    print("Tier counts:")
    print(df["TierCode"].value_counts().to_string())
    print()
    print("Stake summary:")
    print(df.groupby("PlayCode")["Stake"].sum().to_string())
    print()
    print("Top HR Plays:")

    show_cols = [
        "Player", "Team", "Pitcher", "LineupSpot",
        "LineupSpotAdj",
        "BestBook", "BestOdds", "HasOdds",
        "PowerScore", "HRScore", "EVScore",
        "ModelProb", "Edge", "Confidence",
        "DecisionScore", "SmashScore",
        "Grade", "TierCode", "PlayCode", "Reason", "Stake"
    ]

    existing = [c for c in show_cols if c in df.columns]

    print(df.head(30)[existing].to_string(index=False))

    return df.to_dict("records")


def run():
    return main()


if __name__ == "__main__":
    main()