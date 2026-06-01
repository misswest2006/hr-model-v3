import os
import pandas as pd
import unicodedata


def safe(value):
    try:
        return float(value)
    except Exception:
        return 0.0


def clean_name(name):
    if pd.isna(name):
        return ""

    name = str(name).strip().lower()
    name = unicodedata.normalize("NFKD", name)
    name = "".join(ch for ch in name if not unicodedata.combining(ch))
    name = " ".join(name.split())

    return name


def get_hitter_stats():
    file_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "data",
        "hitter_stats.csv"
    )

    df = pd.read_csv(file_path)
    hitters = {}

    for _, row in df.iterrows():
        key = clean_name(row["Player"])

        hitters[key] = {
            "Hand": row["Hand"],
            "ISO_vs_RHP": safe(row["ISO_vs_RHP"]),
            "ISO_vs_LHP": safe(row["ISO_vs_LHP"]),
            "HardHit": safe(row["HardHit"]),
            "FlyBall": safe(row["FlyBall"]),
            "BarrelRate": safe(row["BarrelRate"]),
            "ExitVelocity": safe(row["ExitVelocity"]),
            "LaunchAngle": safe(row["LaunchAngle"]),
            "RecentHRRate": safe(row["RecentHRRate"]),
            "Matchup": safe(row["Matchup"]),
        }

    print(f"✅ Loaded hitter stats: {len(hitters)}")
    return hitters


def get_pitcher_stats():
    file_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "data",
        "pitcher_stats.csv"
    )

    df = pd.read_csv(file_path)
    pitchers = {}

    for _, row in df.iterrows():
        key = clean_name(row["Pitcher"])

        pitchers[key] = {
            "Hand": row["Hand"],
            "HR9_vs_LHB": safe(row["HR9_vs_LHB"]),
            "HR9_vs_RHB": safe(row["HR9_vs_RHB"]),
            "HardHitAllowed": safe(row["HardHitAllowed"]),
            "BarrelAllowed": safe(row["BarrelAllowed"]),
            "FlyBallAllowed": safe(row["FlyBallAllowed"]),
            "RecentHRAllowed": safe(row["RecentHRAllowed"]),
        }

    print(f"✅ Loaded pitcher stats: {len(pitchers)}")
    return pitchers