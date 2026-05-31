import os
import pandas as pd
import joblib

from core.odds import implied_prob
from save_results import save_results
from player_adjustments import get_player_bonus


FEATURES = [
    "ISO",
    "Pitcher_HR9",
    "HardHit",
    "FlyBall",
    "BarrelRate",
    "ExitVelocity",
    "LaunchAngle",
    "RecentHRRate",
    "ParkFactor",
    "WindFactor",
    "Matchup",
]


MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "models",
    "hr_model.pkl"
)

trained_model = joblib.load(MODEL_PATH)


TEAM_ABBR = {
    "Arizona Diamondbacks": "ari",
    "Atlanta Braves": "atl",
    "Baltimore Orioles": "bal",
    "Boston Red Sox": "bos",
    "Chicago Cubs": "chc",
    "Chicago White Sox": "chw",
    "Cincinnati Reds": "cin",
    "Cleveland Guardians": "cle",
    "Colorado Rockies": "col",
    "Detroit Tigers": "det",
    "Houston Astros": "hou",
    "Kansas City Royals": "kc",
    "Los Angeles Angels": "laa",
    "Los Angeles Dodgers": "lad",
    "Miami Marlins": "mia",
    "Milwaukee Brewers": "mil",
    "Minnesota Twins": "min",
    "New York Mets": "nym",
    "New York Yankees": "nyy",
    "Athletics": "ath",
    "Oakland Athletics": "ath",
    "Philadelphia Phillies": "phi",
    "Pittsburgh Pirates": "pit",
    "San Diego Padres": "sd",
    "San Francisco Giants": "sf",
    "Seattle Mariners": "sea",
    "St. Louis Cardinals": "stl",
    "Tampa Bay Rays": "tb",
    "Texas Rangers": "tex",
    "Toronto Blue Jays": "tor",
    "Washington Nationals": "wsh",
}


def team_abbr(team):
    return TEAM_ABBR.get(str(team).strip(), "")


def headshot_url(player_id):
    if not player_id or str(player_id).lower() in ["nan", "none", "<na>"]:
        return ""

    clean_id = str(player_id).replace(".0", "").strip()

    return (
        "https://img.mlbstatic.com/mlb-photos/image/upload/"
        f"w_180,q_auto:best/v1/people/{clean_id}/headshot/67/current"
    )


def team_logo_url(team):
    abbr = team_abbr(team)
    if not abbr:
        return ""
    return f"https://a.espncdn.com/i/teamlogos/mlb/500/{abbr}.png"


def format_odds(odds):
    odds = int(float(odds))
    return f"+{odds}" if odds > 0 else str(odds)


def is_blank(value):
    return pd.isna(value) or str(value).strip() == ""


def lineup_spot_boost(lineup_spot):
    boosts = {
        1: 1.08,
        2: 1.12,
        3: 1.18,
        4: 1.22,
        5: 1.14,
        6: 1.05,
        7: 0.96,
        8: 0.91,
        9: 0.88,
    }

    try:
        spot = int(float(lineup_spot))
        return boosts.get(spot, 1.00)
    except Exception:
        return 1.00


def calculate_power_score(
    iso,
    hard_hit,
    barrel_rate,
    fly_ball,
    exit_velocity,
    recent_hr_rate
):
    score = (
        (iso * 120)
        + (hard_hit * 0.90)
        + (barrel_rate * 3.20)
        + (fly_ball * 0.55)
        + (exit_velocity * 0.35)
        + (recent_hr_rate * 120)
    )

    return round(score, 2)


def calibrate_probability(raw_model_prob, power_score, lineup_boost):
    model_prob = raw_model_prob

    if power_score >= 115:
        model_prob *= 2.45
    elif power_score >= 100:
        model_prob *= 2.20
    elif power_score >= 85:
        model_prob *= 1.85
    elif power_score >= 70:
        model_prob *= 1.50
    elif power_score <= 55:
        model_prob *= 0.75

    model_prob *= lineup_boost

    return min(max(model_prob, 0.01), 0.42)


def calculate_confidence(
    model_prob,
    edge,
    barrel_rate,
    recent_hr_rate,
    hard_hit,
    power_score,
    lineup_boost
):
    confidence = (
        (model_prob * 75)
        + (edge * 120)
        + (barrel_rate * 0.90)
        + (recent_hr_rate * 55)
        + (hard_hit * 0.12)
        + (power_score * 0.12)
        + ((lineup_boost - 1) * 80)
    )

    return min(max(round(confidence), 0), 99)


def grade_play(confidence, barrel_rate, recent_hr_rate, power_score, edge):
    if (
        confidence >= 82
        and barrel_rate >= 14
        and recent_hr_rate >= 0.20
        and power_score >= 105
        and edge >= 0.10
    ):
        return "A+"

    if (
        confidence >= 70
        and barrel_rate >= 12
        and recent_hr_rate >= 0.16
        and power_score >= 90
        and edge >= 0.05
    ):
        return "A"

    if (
        confidence >= 55
        and barrel_rate >= 8
        and recent_hr_rate >= 0.10
        and power_score >= 75
        and edge >= 0.00
    ):
        return "B"

    if confidence >= 40:
        return "C"

    return "D"


def base_yes_rule(model_prob, edge, confidence):
    return (
        model_prob >= 0.195
        and edge >= 0.025
        and confidence >= 63
    )


def signal_tier(model_prob, edge, confidence):
    if model_prob >= 0.21 and edge >= 0.04 and confidence >= 67:
        return "TIER 1 💎"

    if model_prob >= 0.195 and edge >= 0.025 and confidence >= 63:
        return "TIER 2 🔥"

    return "WATCH"


def stake_size(play, tier):
    if play != "YES 🔥":
        return 0

    if tier == "TIER 1 💎":
        return 1.0

    if tier == "TIER 2 🔥":
        return 0.5

    return 0


def get_player_id(row):
    player_id = row.get("player_id", "")
    if pd.isna(player_id):
        return ""
    return str(player_id).replace(".0", "").strip()


def add_team_overlap_yes(results):
    df = pd.DataFrame(results)

    if df.empty:
        return results

    df["top_edge_rank"] = (
        df.groupby("team")["best_edge"]
        .rank(method="first", ascending=False)
        .astype(int)
    )

    df["top_prob_rank"] = (
        df.groupby("team")["model_prob"]
        .rank(method="first", ascending=False)
        .astype(int)
    )

    df["is_top3_edge"] = df["top_edge_rank"] <= 3
    df["is_top4_prob"] = df["top_prob_rank"] <= 4

    df["overlap_candidate"] = (
        df["is_top3_edge"]
        & df["is_top4_prob"]
        & df.apply(
            lambda row: base_yes_rule(
                float(row["model_prob"]),
                float(row["best_edge"]),
                int(row["confidence"])
            ),
            axis=1
        )
    )

    df["play"] = "NO"
    df["tier"] = "WATCH"
    df["stake"] = 0.0

    for team, group in df.groupby("team"):
        overlap = group[group["overlap_candidate"]].copy()

        if overlap.empty:
            continue

        overlap = overlap.sort_values(
            by=["best_edge", "model_prob", "confidence"],
            ascending=[False, False, False]
        )

        best_idx = overlap.index[0]

        model_prob = float(df.loc[best_idx, "model_prob"])
        edge = float(df.loc[best_idx, "best_edge"])
        confidence = int(df.loc[best_idx, "confidence"])

        tier = signal_tier(model_prob, edge, confidence)

        df.loc[best_idx, "play"] = "YES 🔥"
        df.loc[best_idx, "tier"] = tier
        df.loc[best_idx, "stake"] = stake_size("YES 🔥", tier)

    return df.to_dict(orient="records")


def run():
    print("🚀 SCRIPT LOADED")
    print("🤖 TRAINED HR MODEL STARTED")
    print("🔥 YES rule:")
    print("ModelProb >= 19.5%")
    print("Edge >= +2.5%")
    print("Confidence >= 63")
    print("Player appears in Top 3 Edge AND Top 4 Model Prob")
    print("Only strongest overlap player per team becomes YES")

    file_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "data",
        "sample_slate.csv"
    )

    df = pd.read_csv(file_path)

    books = ["FanDuel", "DraftKings", "BetMGM"]

    results = []

    for _, row in df.iterrows():
        required = [
            "Player",
            "ISO",
            "Pitcher_HR9",
            "HardHit",
            "FlyBall",
            "BarrelRate",
            "ExitVelocity",
            "LaunchAngle",
            "RecentHRRate",
            "ParkFactor",
            "WindFactor",
            "Matchup",
        ]

        if any(is_blank(row[col]) for col in required):
            continue

        try:
            features = {
                "ISO": float(row["ISO"]),
                "Pitcher_HR9": float(row["Pitcher_HR9"]),
                "HardHit": float(row["HardHit"]),
                "FlyBall": float(row["FlyBall"]),
                "BarrelRate": float(row["BarrelRate"]),
                "ExitVelocity": float(row["ExitVelocity"]),
                "LaunchAngle": float(row["LaunchAngle"]),
                "RecentHRRate": float(row["RecentHRRate"]),
                "ParkFactor": float(row["ParkFactor"]),
                "WindFactor": float(row["WindFactor"]),
                "Matchup": float(row["Matchup"]),
            }

            feature_vector = [[
                features["ISO"],
                features["Pitcher_HR9"],
                features["HardHit"],
                features["FlyBall"],
                features["BarrelRate"],
                features["ExitVelocity"],
                features["LaunchAngle"],
                features["RecentHRRate"],
                features["ParkFactor"],
                features["WindFactor"],
                features["Matchup"],
            ]]

            raw_model_prob = float(
                trained_model.predict_proba(feature_vector)[0][1]
            )

            power_score = calculate_power_score(
                features["ISO"],
                features["HardHit"],
                features["BarrelRate"],
                features["FlyBall"],
                features["ExitVelocity"],
                features["RecentHRRate"],
            )

            lineup_boost = lineup_spot_boost(row.get("LineupSpot", 0))

            model_prob = calibrate_probability(
                raw_model_prob,
                power_score,
                lineup_boost
            )

        except Exception as e:
            print(f"⚠️ Failed processing {row.get('Player', 'Unknown')}")
            print(e)
            continue

        book_results = []

        for book in books:
            if book not in row or is_blank(row[book]):
                continue

            try:
                odds = float(row[book])
                implied = implied_prob(odds)
                edge = model_prob - implied

                book_results.append({
                    "book": book,
                    "odds": format_odds(odds),
                    "implied_prob": round(float(implied), 4),
                    "edge": round(float(edge), 4),
                })

            except Exception as e:
                print(f"⚠️ Odds processing failed for {row['Player']} | {book}")
                print(e)
                continue

        if not book_results:
            continue

        best_book = sorted(
            book_results,
            key=lambda x: x["edge"],
            reverse=True
        )[0]

        edge = float(best_book["edge"])

        barrel_rate = features["BarrelRate"]
        recent_hr_rate = features["RecentHRRate"]
        hard_hit = features["HardHit"]

        confidence = calculate_confidence(
            model_prob,
            edge,
            barrel_rate,
            recent_hr_rate,
            hard_hit,
            power_score,
            lineup_boost
        )

        player_bonus = get_player_bonus(row["Player"])

        confidence += player_bonus
        confidence = min(max(round(confidence), 0), 99)

        grade = grade_play(
            confidence,
            barrel_rate,
            recent_hr_rate,
            power_score,
            edge
        )

        player_id = get_player_id(row)
        team = row["Team"]

        results.append({
            "date": row["Date"],
            "game_time": row.get("GameTime", ""),
            "game_time_et": row.get("GameTimeET", ""),
            "snapshot": os.getenv("MODEL_SNAPSHOT_LABEL", "MANUAL"), 
            "game": row["Game"],
            "lineup_spot": row.get("LineupSpot", ""),
            "player": row["Player"],
            "player_id": player_id,
            "player_headshot": headshot_url(player_id),
            "team": team,
            "team_logo": team_logo_url(team),
            "team_abbr": team_abbr(team),
            "pitcher": row["Pitcher"],
            "model_prob": round(float(model_prob), 4),
            "raw_model_prob": round(float(raw_model_prob), 4),
            "power_score": power_score,
            "lineup_boost": round(float(lineup_boost), 2),
            "best_book": best_book["book"],
            "best_odds": best_book["odds"],
            "best_edge": round(float(edge), 4),
            "confidence": confidence,
            "stake": 0,
            "grade": grade,
            "tier": "WATCH",
            "top_edge_rank": 999,
            "top_prob_rank": 999,
            "is_top3_edge": False,
            "is_top4_prob": False,
            "overlap_candidate": False,
            "play": "NO",
            "all_books": book_results,
        })

    results = add_team_overlap_yes(results)

    results = sorted(
        results,
        key=lambda x: (
            x["play"] == "YES 🔥",
            x["tier"] == "TIER 1 💎",
            x["best_edge"],
            x["confidence"],
        ),
        reverse=True
    )

    yes_count = sum(1 for r in results if r["play"] == "YES 🔥")

    print("\n🔥 ALL TRAINED MODEL HR PLAYS 🔥\n")

    if not results:
        print("⚠️ No completed player rows found.")
    else:
        for r in results:
            print(r)

    print(f"\n🔥 YES PLAYS FOUND: {yes_count}\n")

    save_results(results)

    return results


if __name__ == "__main__":
    run()