import os
import pandas as pd


def get_hitter_defaults(player_name):

    slugger_keywords = [
        "Judge",
        "Soler",
        "Trout",
        "Torkelson",
        "Buxton",
        "Burger",
        "Pederson",
        "Greene",
        "Guerrero",
        "Adell",
        "Ward",
        "Rooker",
        "Alonso",
        "Olson",
        "Ozuna",
        "Ohtani",
        "Betts",
        "Riley",
        "Harper"
    ]

    contact_keywords = [
        "Frazier",
        "Lopez",
        "Kiner",
        "Swanson",
        "Meidroth",
        "Hill",
        "Gimenez"
    ]

    player_lower = player_name.lower()

    for word in slugger_keywords:
        if word.lower() in player_lower:

            return {
                "Hand": "R",
                "ISO_vs_RHP": 0.260,
                "ISO_vs_LHP": 0.240,
                "HardHit": 47.0,
                "FlyBall": 42.0,
                "BarrelRate": 14.0,
                "ExitVelocity": 92.5,
                "LaunchAngle": 18.0,
                "RecentHRRate": 0.22,
                "Matchup": 0.78,
            }

    for word in contact_keywords:
        if word.lower() in player_lower:

            return {
                "Hand": "L",
                "ISO_vs_RHP": 0.120,
                "ISO_vs_LHP": 0.105,
                "HardHit": 31.0,
                "FlyBall": 24.0,
                "BarrelRate": 4.0,
                "ExitVelocity": 86.0,
                "LaunchAngle": 9.0,
                "RecentHRRate": 0.04,
                "Matchup": 0.52,
            }

    return {
        "Hand": "R",
        "ISO_vs_RHP": 0.180,
        "ISO_vs_LHP": 0.160,
        "HardHit": 38.0,
        "FlyBall": 34.0,
        "BarrelRate": 8.0,
        "ExitVelocity": 89.0,
        "LaunchAngle": 14.0,
        "RecentHRRate": 0.10,
        "Matchup": 0.65,
    }


DEFAULT_PITCHER = {
    "Hand": "R",
    "HR9_vs_LHB": 1.30,
    "HR9_vs_RHB": 1.20,
    "HardHitAllowed": 40.0,
    "BarrelAllowed": 9.5,
    "FlyBallAllowed": 37.0,
    "RecentHRAllowed": 0.15,
}


HITTER_COLUMNS = [
    "Player",
    "Hand",
    "ISO_vs_RHP",
    "ISO_vs_LHP",
    "HardHit",
    "FlyBall",
    "BarrelRate",
    "ExitVelocity",
    "LaunchAngle",
    "RecentHRRate",
    "Matchup",
]


PITCHER_COLUMNS = [
    "Pitcher",
    "Hand",
    "HR9_vs_LHB",
    "HR9_vs_RHB",
    "HardHitAllowed",
    "BarrelAllowed",
    "FlyBallAllowed",
    "RecentHRAllowed",
]


def load_or_create(path, columns):
    if os.path.exists(path):
        df = pd.read_csv(path)

        for col in columns:
            if col not in df.columns:
                df[col] = ""

        return df[columns]

    return pd.DataFrame(columns=columns)


def main():
    print("\n🚀 AUTO UPDATE STATS STARTED\n")

    base_dir = os.path.join(
        os.path.dirname(__file__),
        "..",
        "data"
    )

    slate_path = os.path.join(base_dir, "sample_slate.csv")
    hitter_path = os.path.join(base_dir, "hitter_stats.csv")
    pitcher_path = os.path.join(base_dir, "pitcher_stats.csv")

    if not os.path.exists(slate_path):
        print("❌ sample_slate.csv not found.")
        return

    slate = pd.read_csv(slate_path)

    hitters = load_or_create(hitter_path, HITTER_COLUMNS)
    pitchers = load_or_create(pitcher_path, PITCHER_COLUMNS)

    existing_hitters = set(
        hitters["Player"].dropna().astype(str).str.strip()
    )

    existing_pitchers = set(
        pitchers["Pitcher"].dropna().astype(str).str.strip()
    )

    new_hitter_rows = []
    new_pitcher_rows = []

    for _, row in slate.iterrows():
        player = str(row.get("Player", "")).strip()
        pitcher = str(row.get("Pitcher", "")).strip()

        if player and player.lower() != "nan" and player not in existing_hitters:
            new_row = {"Player": player}
            new_row.update(get_hitter_defaults(player))
            new_hitter_rows.append(new_row)
            existing_hitters.add(player)

        if pitcher and pitcher.lower() != "nan" and pitcher not in existing_pitchers:
            new_row = {"Pitcher": pitcher}
            new_row.update(DEFAULT_PITCHER)
            new_pitcher_rows.append(new_row)
            existing_pitchers.add(pitcher)

    if new_hitter_rows:
        hitters = pd.concat(
            [hitters, pd.DataFrame(new_hitter_rows)],
            ignore_index=True
        )

    if new_pitcher_rows:
        pitchers = pd.concat(
            [pitchers, pd.DataFrame(new_pitcher_rows)],
            ignore_index=True
        )

    hitters = hitters[HITTER_COLUMNS]
    pitchers = pitchers[PITCHER_COLUMNS]

    hitters.to_csv(hitter_path, index=False)
    pitchers.to_csv(pitcher_path, index=False)

    print(f"✅ New hitters added: {len(new_hitter_rows)}")
    print(f"✅ New pitchers added: {len(new_pitcher_rows)}")
    print(f"✅ Total hitters now: {len(hitters)}")
    print(f"✅ Total pitchers now: {len(pitchers)}")

    if new_hitter_rows:
        print("\n🧢 Added hitters:")
        for row in new_hitter_rows[:20]:
            print("-", row["Player"])

    if new_pitcher_rows:
        print("\n⚾ Added pitchers:")
        for row in new_pitcher_rows[:20]:
            print("-", row["Pitcher"])

    print("\n🔥 AUTO UPDATE COMPLETE 🔥\n")


if __name__ == "__main__":
    main()