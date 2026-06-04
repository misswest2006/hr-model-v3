import os
import sys
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
DATA_DIR = os.path.join(BASE_DIR, "data")

sys.path.insert(0, BACKEND_DIR)

INPUT_FILE = os.path.join(DATA_DIR, "sample_slate.csv")
OUTPUT_FILE = os.path.join(DATA_DIR, "today_slate_enriched.csv")

try:
    from sgo_odds_provider import build_sgo_hr_odds_lookup, clean_name
except Exception:
    build_sgo_hr_odds_lookup = None

    def clean_name(name):
        return (
            str(name or "")
            .strip()
            .lower()
            .replace(".", "")
            .replace("’", "'")
            .replace("'", "")
        )


POWER_BATS = {
    "Shohei Ohtani", "Aaron Judge", "Kyle Schwarber", "Pete Alonso",
    "Yordan Alvarez", "Matt Olson", "Bryce Harper", "Mookie Betts",
    "Max Muncy", "Kyle Tucker", "Cody Bellinger", "Brent Rooker",
    "Marcell Ozuna", "Mike Trout", "Jorge Soler", "Riley Greene",
    "Kerry Carpenter", "Coby Mayo", "Daulton Varsho", "Oneil Cruz",
    "Juan Soto", "Nick Kurtz", "Brandon Lowe", "Shea Langeliers",
    "Ben Rice", "JJ Bleday", "Jake Burger", "Matt Chapman",
    "Ian Happ", "Kyle Manzardo", "Salvador Perez", "Seiya Suzuki",
    "Willy Adames"
}

MID_POWER_BATS = {
    "Alec Bohm", "Spencer Steer", "Nathaniel Lowe", "Willson Contreras",
    "William Contreras", "Brandon Marsh", "Bryson Stott", "Ernie Clement"
}


PITCHER_RISK_PROFILES = {
    "Zac Gallen": (1.18, 52),
    "Walker Buehler": (1.32, 58),
    "George Kirby": (1.05, 45),
    "Paul Skenes": (0.78, 32),
    "Colin Rea": (1.42, 62),
    "Payton Tolle": (1.35, 60),
    "Spencer Arrighetti": (1.48, 65),
    "Gavin Williams": (1.26, 55),
    "Michael Lorenzen": (1.31, 57),
    "Andre Pallante": (1.10, 46),
    "Stephen Kolek": (1.38, 61),
    "Robert Gasser": (1.20, 50),
    "Chris Bassitt": (1.15, 49),
    "Gerrit Cole": (0.95, 39),
    "Chase Burns": (1.28, 56),
    "Jeffrey Springs": (1.22, 53),
    "Nick Martinez": (1.45, 63),
    "Erick Fedde": (1.46, 63.7),
    "Logan Webb": (1.53, 66.8),
    "MacKenzie Gore": (1.57, 68.6),
    "Taj Bradley": (1.54, 67.2),
    "Andrew Alvarez": (1.09, 46.2),
    "Grant Holmes": (1.30, 53.5),
}


def safe_num(value, default=np.nan):
    try:
        if value == "" or value is None:
            return default
        return float(value)
    except Exception:
        return default


def player_spread(name):
    name = str(name).strip()
    return (abs(hash(name)) % 100) / 1000


def pitcher_spread(name):
    name = str(name).strip()
    return (abs(hash(name)) % 100) / 100


def safe_price(value):
    try:
        if value is None:
            return np.nan

        value = str(value).strip()

        if value == "" or value.lower() in ["nan", "none", "<na>"]:
            return np.nan

        value = value.replace("+", "")
        return float(value)
    except Exception:
        return np.nan


def apply_hitter_smart_fallback(row):
    player = str(row.get("Player", "")).strip()
    spot = safe_num(row.get("LineupSpot"), 7)

    iso = safe_num(row.get("ISO"))
    hardhit = safe_num(row.get("HardHit"))
    barrel = safe_num(row.get("BarrelRate"))
    recent = safe_num(row.get("RecentHRRate"))

    needs_fix = (
        pd.isna(iso)
        or pd.isna(hardhit)
        or pd.isna(barrel)
        or pd.isna(recent)
        or iso == 0.18
        or hardhit == 38
        or barrel == 8
        or recent == 0.10
    )

    if not needs_fix:
        row["FallbackType"] = row.get("FallbackType", "")
        return row

    if player in POWER_BATS:
        iso = 0.245
        hardhit = 47.5
        barrel = 12.5
        recent = 0.145
        fallback_type = "SMART_POWER_BAT_V2_1"

    elif player in MID_POWER_BATS:
        iso = 0.205
        hardhit = 42.5
        barrel = 9.8
        recent = 0.115
        fallback_type = "SMART_MID_POWER_V2_1"

    else:
        if spot in [3, 4, 5]:
            iso = 0.195
            hardhit = 41.5
            barrel = 9.2
            recent = 0.105
        elif spot in [1, 2, 6]:
            iso = 0.175
            hardhit = 39.5
            barrel = 8.1
            recent = 0.088
        else:
            iso = 0.155
            hardhit = 36.5
            barrel = 6.9
            recent = 0.070

        fallback_type = "SMART_LINEUP_V2_1"

    spread = player_spread(player)

    row["ISO"] = round(iso + spread * 0.08, 3)
    row["HardHit"] = round(hardhit + spread * 8, 1)
    row["BarrelRate"] = round(barrel + spread * 3, 1)
    row["RecentHRRate"] = round(recent + spread * 0.04, 3)
    row["FallbackType"] = fallback_type

    return row


def apply_pitcher_smart_fallback(row):
    pitcher = str(row.get("Pitcher", "")).strip()

    hr9 = safe_num(row.get("Pitcher_HR9"))
    vuln = safe_num(row.get("PitcherVulnerability"))

    needs_fix = (
        pd.isna(hr9)
        or pd.isna(vuln)
        or hr9 == 1.25
        or vuln == 48.7
    )

    if not needs_fix:
        row["PitcherFallbackType"] = row.get("PitcherFallbackType", "")
        return row

    if pitcher in PITCHER_RISK_PROFILES:
        hr9, vuln = PITCHER_RISK_PROFILES[pitcher]
    else:
        spread = pitcher_spread(pitcher)
        hr9 = round(0.85 + spread * 0.75, 2)
        vuln = round(35 + spread * 35, 1)

    row["Pitcher_HR9"] = hr9
    row["PitcherVulnerability"] = vuln
    row["PitcherFallbackType"] = "SMART_PITCHER_V2_2"

    return row


def calculate_scores(df):
    for col in [
        "ISO", "HardHit", "BarrelRate", "RecentHRRate",
        "Pitcher_HR9", "PitcherVulnerability", "LineupSpot",
        "ParkFactor", "WindFactor", "Matchup"
    ]:
        if col not in df.columns:
            df[col] = np.nan
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["TruePowerIndex"] = (
        df["ISO"] * 500
        + df["HardHit"] * 2.2
        + df["BarrelRate"] * 5.8
        + df["RecentHRRate"] * 300
    ).round(2)

    df["ContactQualityScore"] = (
        df["HardHit"] * 0.16
        + df["BarrelRate"] * 0.35
    ).clip(1, 10).round(0)

    df["LaunchProfileScore"] = (
        df["BarrelRate"] * 0.45
        + df["ISO"] * 18
    ).clip(1, 10).round(0)

    df["PulledAirScore"] = (
        df["ISO"] * 20
        + df["RecentHRRate"] * 20
    ).clip(1, 10).round(0)

    df["PitcherHRWeaknessScore"] = (
        df["Pitcher_HR9"] * 4.5
    ).clip(1, 10).round(0)

    df["PitcherLineupWeakSpot"] = df["LineupSpot"].apply(
        lambda x: 10 if x in [4, 5, 6] else 0
    )

    raw_enrichment = (
        df["ContactQualityScore"] * 2.2
        + df["LaunchProfileScore"] * 2.0
        + df["PulledAirScore"] * 1.5
        + df["PitcherHRWeaknessScore"] * 1.7
        + df["PitcherLineupWeakSpot"] * 1.2
        + df["PitcherVulnerability"] * 0.45
    )

    if raw_enrichment.nunique() <= 1:
        df["EnrichmentScore"] = 50
    else:
        df["EnrichmentScore"] = (
            raw_enrichment.rank(pct=True) * 100
        ).round(2)

    df["EnrichmentTier"] = np.select(
        [
            df["EnrichmentScore"] >= 90,
            df["EnrichmentScore"] >= 80,
            df["EnrichmentScore"] >= 70,
            df["EnrichmentScore"] >= 60,
        ],
        [
            "V2 ELITE",
            "V2 STRONG",
            "V2 WATCH",
            "V2 LEAN",
        ],
        default="LOW"
    )

    return df


def apply_sgo_odds(df):
    for col in ["FanDuel", "DraftKings", "BetMGM"]:
        if col not in df.columns:
            df[col] = np.nan

    if build_sgo_hr_odds_lookup is None:
        print("WARNING: sgo_odds_provider import failed. Odds skipped.")
        return df

    print("Loading SportsGameOdds HR odds...")

    try:
        odds_lookup = build_sgo_hr_odds_lookup()
    except Exception as e:
        print(f"WARNING: SportsGameOdds failed: {e}")
        odds_lookup = {}

    if not odds_lookup:
        print("WARNING: No SportsGameOdds odds returned.")
        return df

    matched = 0

    for idx, row in df.iterrows():
        player = str(row.get("Player", "")).strip()
        key = clean_name(player)

        odds = odds_lookup.get(key)

        if not odds:
            continue

        fd = safe_price(odds.get("FanDuel"))
        dk = safe_price(odds.get("DraftKings"))
        mgm = safe_price(odds.get("BetMGM"))

        if not pd.isna(fd):
            df.at[idx, "FanDuel"] = fd
        if not pd.isna(dk):
            df.at[idx, "DraftKings"] = dk
        if not pd.isna(mgm):
            df.at[idx, "BetMGM"] = mgm

        if not pd.isna(fd) or not pd.isna(dk) or not pd.isna(mgm):
            matched += 1

    for col in ["FanDuel", "DraftKings", "BetMGM"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    print(f"SportsGameOdds matched slate players: {matched}")
    print("Odds rows with at least one book:", int(df[["FanDuel", "DraftKings", "BetMGM"]].notna().any(axis=1).sum()))

    return df


def main():
    print("DATA ENRICHMENT V2.3 SMART FALLBACK + ODDS STARTED")
    print(f"Loading: {INPUT_FILE}")

    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"Missing input file: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE)

    required_cols = [
        "Player", "Team", "Pitcher", "LineupSpot",
        "ISO", "HardHit", "BarrelRate", "RecentHRRate",
        "Pitcher_HR9", "PitcherVulnerability",
        "FanDuel", "DraftKings", "BetMGM"
    ]

    for col in required_cols:
        if col not in df.columns:
            df[col] = np.nan

    before_hitter_fallback = (
        (pd.to_numeric(df["ISO"], errors="coerce") == 0.18)
        & (pd.to_numeric(df["HardHit"], errors="coerce") == 38)
        & (pd.to_numeric(df["BarrelRate"], errors="coerce") == 8)
        & (pd.to_numeric(df["RecentHRRate"], errors="coerce") == 0.10)
    ).sum()

    before_pitcher_hr9 = (
        pd.to_numeric(df["Pitcher_HR9"], errors="coerce") == 1.25
    ).sum()

    before_pitcher_vuln = (
        pd.to_numeric(df["PitcherVulnerability"], errors="coerce") == 48.7
    ).sum()

    df["FallbackType"] = ""
    df["PitcherFallbackType"] = ""

    df = df.apply(apply_hitter_smart_fallback, axis=1)
    df = df.apply(apply_pitcher_smart_fallback, axis=1)

    df = calculate_scores(df)
    df = apply_sgo_odds(df)

    after_hitter_fallback = (
        (pd.to_numeric(df["ISO"], errors="coerce") == 0.18)
        & (pd.to_numeric(df["HardHit"], errors="coerce") == 38)
        & (pd.to_numeric(df["BarrelRate"], errors="coerce") == 8)
        & (pd.to_numeric(df["RecentHRRate"], errors="coerce") == 0.10)
    ).sum()

    after_pitcher_hr9 = (
        pd.to_numeric(df["Pitcher_HR9"], errors="coerce") == 1.25
    ).sum()

    after_pitcher_vuln = (
        pd.to_numeric(df["PitcherVulnerability"], errors="coerce") == 48.7
    ).sum()

    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    odds_rows = int(df[["FanDuel", "DraftKings", "BetMGM"]].notna().any(axis=1).sum())

    print()
    print("DATA ENRICHMENT V2.3 COMPLETE")
    print(f"Saved: {OUTPUT_FILE}")
    print(f"Rows enriched: {len(df)}")
    print(f"Rows with odds: {odds_rows}")
    print(f"Default hitter fallback before V2.1: {before_hitter_fallback}")
    print(f"Default hitter fallback after V2.1: {after_hitter_fallback}")
    print(f"Default Pitcher_HR9 before V2.2: {before_pitcher_hr9}")
    print(f"Default Pitcher_HR9 after V2.2: {after_pitcher_hr9}")
    print(f"Default PitcherVulnerability before V2.2: {before_pitcher_vuln}")
    print(f"Default PitcherVulnerability after V2.2: {after_pitcher_vuln}")

    print()
    print("Top V2.3 Enriched HR Spots:")
    show_cols = [
        "Player", "Team", "Pitcher", "LineupSpot",
        "TruePowerIndex", "Pitcher_HR9", "PitcherVulnerability",
        "FanDuel", "DraftKings", "BetMGM",
        "PitcherHRWeaknessScore", "PitcherLineupWeakSpot",
        "ContactQualityScore", "LaunchProfileScore", "PulledAirScore",
        "EnrichmentScore", "EnrichmentTier",
        "FallbackType", "PitcherFallbackType"
    ]

    existing = [c for c in show_cols if c in df.columns]

    print(
        df.sort_values("EnrichmentScore", ascending=False)
        .head(25)[existing]
        .to_string(index=False)
    )


def enrich_slate():
    return main()


if __name__ == "__main__":
    main()