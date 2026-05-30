import os
import sys
import pandas as pd

BASE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(BASE_DIR)

sys.path.insert(0, BASE_DIR)
sys.path.insert(0, PROJECT_ROOT)

from backend.baseball_data import get_hitter_stats, get_pitcher_stats
from backend.odds_provider import get_player_odds
from backend.weather_provider import get_weather_factor_for_team


PARK_FACTORS = {
    "New York Yankees": 1.10,
    "Los Angeles Dodgers": 1.15,
    "Philadelphia Phillies": 1.08,
    "Cincinnati Reds": 1.12,
    "Colorado Rockies": 1.20,
    "Boston Red Sox": 1.08,
    "Toronto Blue Jays": 1.05,
    "Milwaukee Brewers": 1.04,
    "Baltimore Orioles": 1.03,
    "Texas Rangers": 1.06,
    "Los Angeles Angels": 1.00,
    "Detroit Tigers": 0.98,
}

FALLBACK_PITCHER_STATS = {
    "Hand": "R",
    "HR9_vs_LHB": 1.25,
    "HR9_vs_RHB": 1.25,
    "HardHitAllowed": 40.0,
    "BarrelAllowed": 9.0,
    "FlyBallAllowed": 38.0,
    "RecentHRAllowed": 0.12,
}


def is_blank(value):
    return pd.isna(value) or str(value).strip() == ""


def safe_set(df, idx, column, value):
    if value is not None and value != "":
        df.at[idx, column] = value


def choose_hitter_iso(hitter, pitcher_hand):
    if pitcher_hand == "R":
        return hitter["ISO_vs_RHP"]
    if pitcher_hand == "L":
        return hitter["ISO_vs_LHP"]
    return max(hitter["ISO_vs_RHP"], hitter["ISO_vs_LHP"])


def choose_pitcher_hr9(pitcher_stats, hitter_hand):
    if hitter_hand == "L":
        return pitcher_stats["HR9_vs_LHB"]
    if hitter_hand == "R":
        return pitcher_stats["HR9_vs_RHB"]
    return max(pitcher_stats["HR9_vs_LHB"], pitcher_stats["HR9_vs_RHB"])


def calculate_pitcher_vulnerability(pitcher_stats):
    score = (
        pitcher_stats["HardHitAllowed"] * 0.35
        + pitcher_stats["BarrelAllowed"] * 2.0
        + pitcher_stats["FlyBallAllowed"] * 0.25
        + pitcher_stats["RecentHRAllowed"] * 60
    )
    return round(score, 2)


def ensure_columns(df):
    required_columns = {
        "ISO": 0.0,
        "Pitcher_HR9": 0.0,
        "HardHit": 0.0,
        "FlyBall": 0.0,
        "BarrelRate": 0.0,
        "ExitVelocity": 0.0,
        "LaunchAngle": 0.0,
        "RecentHRRate": 0.0,
        "PitcherVulnerability": 0.0,
        "ParkFactor": 1.0,
        "WindFactor": 1.0,
        "Matchup": 0.0,
        "FanDuel": "",
        "DraftKings": "",
        "BetMGM": "",
    }

    for column, default in required_columns.items():
        if column not in df.columns:
            df[column] = default

    return df


def enrich_slate():
    file_path = os.path.join(BASE_DIR, "..", "data", "sample_slate.csv")

    df = pd.read_csv(file_path)
    df = ensure_columns(df)

    print("📥 Loading hitter stats...")
    hitter_data = get_hitter_stats()

    print("📥 Loading pitcher stats...")
    pitcher_data = get_pitcher_stats()

    filled_hitters = 0
    filled_pitchers = 0
    fallback_pitchers = 0
    filled_odds = 0
    filled_weather = 0

    for idx, row in df.iterrows():
        player = str(row.get("Player", "")).strip()
        pitcher = str(row.get("Pitcher", "")).strip()
        team = str(row.get("Team", "")).strip()

        if is_blank(player):
            continue

        hitter = hitter_data.get(player)
        pitcher_stats = pitcher_data.get(pitcher)

        if not pitcher_stats:
            pitcher_stats = FALLBACK_PITCHER_STATS
            fallback_pitchers += 1
        else:
            filled_pitchers += 1

        if hitter:
            hitter_hand = hitter.get("Hand", "R")
            pitcher_hand = pitcher_stats.get("Hand", "R")

            safe_set(df, idx, "ISO", choose_hitter_iso(hitter, pitcher_hand))
            safe_set(df, idx, "Pitcher_HR9", choose_pitcher_hr9(pitcher_stats, hitter_hand))
            safe_set(df, idx, "HardHit", hitter["HardHit"])
            safe_set(df, idx, "FlyBall", hitter["FlyBall"])
            safe_set(df, idx, "BarrelRate", hitter["BarrelRate"])
            safe_set(df, idx, "ExitVelocity", hitter["ExitVelocity"])
            safe_set(df, idx, "LaunchAngle", hitter["LaunchAngle"])
            safe_set(df, idx, "RecentHRRate", hitter["RecentHRRate"])
            safe_set(df, idx, "PitcherVulnerability", calculate_pitcher_vulnerability(pitcher_stats))
            safe_set(df, idx, "Matchup", hitter["Matchup"])

            filled_hitters += 1

        safe_set(df, idx, "ParkFactor", PARK_FACTORS.get(team, 1.00))
        safe_set(df, idx, "WindFactor", get_weather_factor_for_team(team))
        filled_weather += 1

        odds = get_player_odds(player)
        safe_set(df, idx, "FanDuel", odds["FanDuel"])
        safe_set(df, idx, "DraftKings", odds["DraftKings"])
        safe_set(df, idx, "BetMGM", odds["BetMGM"])
        filled_odds += 1

    df.to_csv(file_path, index=False)

    print("✅ Slate enrichment complete")
    print(f"✅ Hitters matched: {filled_hitters}")
    print(f"✅ Pitchers matched: {filled_pitchers}")
    print(f"⚠️ Fallback pitchers used: {fallback_pitchers}")
    print(f"✅ Weather filled: {filled_weather}")
    print(f"✅ Odds filled: {filled_odds}")
    print(f"✅ Saved to: {file_path}")
    print(df.head())


if __name__ == "__main__":
    enrich_slate()