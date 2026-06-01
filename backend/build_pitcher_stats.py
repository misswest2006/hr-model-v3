import os
import requests
import pandas as pd


BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "..", "data")

SLATE_PATH = os.path.join(DATA_DIR, "sample_slate.csv")
OUTPUT_PATH = os.path.join(DATA_DIR, "pitcher_stats.csv")


def safe_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def get_json(url, params=None):
    res = requests.get(url, params=params, timeout=30)
    res.raise_for_status()
    return res.json()


def search_player_id(name):
    url = "https://statsapi.mlb.com/api/v1/people/search"
    data = get_json(url, {"names": name})

    people = data.get("people", [])
    if not people:
        return None

    return people[0].get("id")


def get_pitcher_hand(player_id):
    try:
        data = get_json(f"https://statsapi.mlb.com/api/v1/people/{player_id}")
        people = data.get("people", [])
        if not people:
            return "R"

        return people[0].get("pitchHand", {}).get("code", "R")
    except Exception:
        return "R"


def estimate_hr9_splits(hr9, hand):
    hand = str(hand).upper().strip()

    if hand == "R":
        # RHP usually has more HR risk to LHB
        return round(hr9 * 1.12, 2), round(hr9 * 0.92, 2)

    if hand == "L":
        # LHP usually has more HR risk to RHB
        return round(hr9 * 0.92, 2), round(hr9 * 1.12, 2)

    return round(hr9, 2), round(hr9, 2)


def get_pitching_stats(player_id, hand):
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats"

    data = get_json(
        url,
        {
            "stats": "season",
            "group": "pitching",
            "season": 2026,
        },
    )

    splits = (
        data.get("stats", [{}])[0]
        .get("splits", [])
    )

    if not splits:
        return None

    stat = splits[0].get("stat", {})

    innings = safe_float(stat.get("inningsPitched", 0), 0)
    hr = safe_float(stat.get("homeRuns", 0), 0)

    if innings > 0:
        hr9 = round((hr * 9) / innings, 2)
    else:
        hr9 = 1.25

    hr9_vs_lhb, hr9_vs_rhb = estimate_hr9_splits(hr9, hand)

    era = safe_float(stat.get("era", 4.25), 4.25)
    whip = safe_float(stat.get("whip", 1.30), 1.30)

    hard_hit_allowed = round(min(max(34 + (era - 3.5) * 2.4, 30), 52), 1)
    barrel_allowed = round(min(max(6 + (hr9 - 1.0) * 3.5, 5), 16), 1)
    fly_ball_allowed = round(min(max(35 + (hr9 - 1.0) * 5, 30), 48), 1)
    recent_hr_allowed = round(min(max(hr9 / 9, 0.05), 0.30), 3)

    return {
        "HR9": hr9,
        "HR9_vs_LHB": hr9_vs_lhb,
        "HR9_vs_RHB": hr9_vs_rhb,
        "HardHitAllowed": hard_hit_allowed,
        "BarrelAllowed": barrel_allowed,
        "FlyBallAllowed": fly_ball_allowed,
        "RecentHRAllowed": recent_hr_allowed,
        "ERA": era,
        "WHIP": whip,
    }


def build_pitcher_stats():
    if not os.path.exists(SLATE_PATH):
        print("❌ Missing data/sample_slate.csv")
        return

    slate = pd.read_csv(SLATE_PATH)

    if "Pitcher" not in slate.columns:
        print("❌ sample_slate.csv has no Pitcher column")
        return

    pitchers = (
        slate["Pitcher"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    rows = []

    print(f"📥 Building pitcher stats for {len(pitchers)} pitchers...")

    for pitcher in pitchers:
        if not pitcher or pitcher.upper() == "TBD":
            continue

        try:
            player_id = search_player_id(pitcher)

            if not player_id:
                print(f"⚠️ No player id found for {pitcher}")
                continue

            hand = get_pitcher_hand(player_id)
            stats = get_pitching_stats(player_id, hand)

            if not stats:
                print(f"⚠️ No pitching stats found for {pitcher}")
                continue

            rows.append({
                "Pitcher": pitcher,
                "Hand": hand,
                "HR9_vs_LHB": stats["HR9_vs_LHB"],
                "HR9_vs_RHB": stats["HR9_vs_RHB"],
                "HardHitAllowed": stats["HardHitAllowed"],
                "BarrelAllowed": stats["BarrelAllowed"],
                "FlyBallAllowed": stats["FlyBallAllowed"],
                "RecentHRAllowed": stats["RecentHRAllowed"],
            })

            weak_side = "L" if stats["HR9_vs_LHB"] > stats["HR9_vs_RHB"] else "R"

            print(
                f"✅ {pitcher}: "
                f"HR9 {stats['HR9']} | "
                f"LHB {stats['HR9_vs_LHB']} | "
                f"RHB {stats['HR9_vs_RHB']} | "
                f"WeakSide {weak_side} | "
                f"Hand {hand}"
            )

        except Exception as e:
            print(f"⚠️ Failed for {pitcher}: {e}")

    df = pd.DataFrame(rows)

    df.to_csv(OUTPUT_PATH, index=False)

    print(f"✅ Pitcher stats saved: {len(df)}")
    print(f"📁 Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_pitcher_stats()