import os
import random
import pandas as pd
from datetime import datetime, timedelta


PLAYERS = [
    "Aaron Judge",
    "Juan Soto",
    "Shohei Ohtani",
    "Mookie Betts",
    "Kyle Schwarber",
    "Bryce Harper",
    "Yordan Alvarez",
    "Matt Olson",
    "Pete Alonso",
    "Fernando Tatis Jr"
]

PITCHERS = [
    "Cole Ragans",
    "Kyle Freeland",
    "Joe Musgrove",
    "Chris Sale",
    "Corbin Burnes",
    "Tarik Skubal",
    "Zac Gallen",
    "Blake Snell",
]

TEAMS = [
    "New York Yankees",
    "Los Angeles Dodgers",
    "Philadelphia Phillies",
    "Atlanta Braves",
    "Houston Astros",
    "San Diego Padres",
]

BOOKS = [
    "+180",
    "+200",
    "+220",
    "+250",
    "+275",
    "+300",
    "+350",
]


def random_float(low, high):

    return round(random.uniform(low, high), 3)


def generate_hr_result(iso, hard_hit, fly_ball, pitcher_hr9):

    score = (
        iso * 100
        + hard_hit * 0.4
        + fly_ball * 0.3
        + pitcher_hr9 * 10
    )

    probability = min(max(score / 100, 0.05), 0.45)

    return 1 if random.random() < probability else 0


def build_dataset(rows=5000):

    print("\n🚀 BUILDING HISTORICAL DATASET\n")

    data = []

    start_date = datetime(2024, 3, 28)

    for i in range(rows):

        player = random.choice(PLAYERS)

        pitcher = random.choice(PITCHERS)

        team = random.choice(TEAMS)

        game_date = (
            start_date + timedelta(days=random.randint(0, 365))
        ).strftime("%Y-%m-%d")

        iso = random_float(0.120, 0.350)

        pitcher_hr9 = random_float(0.7, 2.2)

        hard_hit = random_float(25, 60)

        fly_ball = random_float(20, 50)

        park_factor = random_float(0.90, 1.20)

        wind_factor = random_float(0.90, 1.20)

        matchup = random_float(0.50, 1.00)

        best_odds = random.choice(BOOKS)

        hr_result = generate_hr_result(
            iso,
            hard_hit,
            fly_ball,
            pitcher_hr9
        )

        data.append({
            "Player": player,
            "Date": game_date,
            "Pitcher": pitcher,
            "Team": team,
            "BestOdds": best_odds,
            "ISO": iso,
            "Pitcher_HR9": pitcher_hr9,
            "HardHit": hard_hit,
            "FlyBall": fly_ball,
            "ParkFactor": park_factor,
            "WindFactor": wind_factor,
            "Matchup": matchup,
            "HR_Result": hr_result,
        })

        if i % 1000 == 0 and i > 0:
            print(f"📊 Generated {i} rows...")

    df = pd.DataFrame(data)

    output_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "data",
        "historical_hr_training.csv"
    )

    df.to_csv(output_path, index=False)

    print("\n✅ HISTORICAL DATASET COMPLETE")
    print(f"📁 Saved to: {output_path}")
    print(f"📊 Total Rows: {len(df)}")

    print("\n🔥 SAMPLE DATA 🔥\n")

    print(df.head())


if __name__ == "__main__":

    build_dataset(rows=10000)