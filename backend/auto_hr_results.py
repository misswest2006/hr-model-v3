import os
import requests
import pandas as pd
from datetime import date


def get_json(url, params=None):
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_hr_hitters(game_date=None):
    if game_date is None:
        game_date = date.today().strftime("%Y-%m-%d")

    schedule_url = "https://statsapi.mlb.com/api/v1/schedule"
    schedule = get_json(
        schedule_url,
        {
            "sportId": 1,
            "date": game_date,
        },
    )

    rows = []

    for day in schedule.get("dates", []):
        for game in day.get("games", []):
            game_pk = game.get("gamePk")
            if not game_pk:
                continue

            feed_url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"

            try:
                feed = get_json(feed_url)
            except Exception as e:
                print(f"⚠️ Could not load game {game_pk}: {e}")
                continue

            plays = (
                feed.get("liveData", {})
                .get("plays", {})
                .get("allPlays", [])
            )

            for play in plays:
                result = play.get("result", {})
                event_type = str(result.get("eventType", "")).lower()

                if event_type != "home_run":
                    continue

                batter = (
                    play.get("matchup", {})
                    .get("batter", {})
                    .get("fullName", "")
                )

                if batter:
                    rows.append({
                        "Date": game_date,
                        "Player": batter,
                    })

    return rows


def save_hr_hits(game_date=None):
    if game_date is None:
        game_date = date.today().strftime("%Y-%m-%d")

    rows = fetch_hr_hitters(game_date)

    base_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    output_path = os.path.join(base_dir, "yesterday_hr_hits.csv")

    df = pd.DataFrame(rows, columns=["Date", "Player"])

    df = df.drop_duplicates()

    df.to_csv(output_path, index=False)

    print(f"✅ Saved HR hitters for {game_date}")
    print(f"🔥 HR hitters found: {len(df)}")
    print(f"📁 Saved to: {output_path}")

    if not df.empty:
        print(df.to_string(index=False))

    return df


if __name__ == "__main__":
    save_hr_hits()