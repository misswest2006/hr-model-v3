import os
import pandas as pd
import requests
from datetime import date, datetime
from zoneinfo import ZoneInfo


TEAM_ABBREVIATIONS = {
    "Arizona Diamondbacks": "ARI",
    "Atlanta Braves": "ATL",
    "Baltimore Orioles": "BAL",
    "Boston Red Sox": "BOS",
    "Chicago Cubs": "CHC",
    "Chicago White Sox": "CWS",
    "Cincinnati Reds": "CIN",
    "Cleveland Guardians": "CLE",
    "Colorado Rockies": "COL",
    "Detroit Tigers": "DET",
    "Houston Astros": "HOU",
    "Kansas City Royals": "KC",
    "Los Angeles Angels": "LAA",
    "Los Angeles Dodgers": "LAD",
    "Miami Marlins": "MIA",
    "Milwaukee Brewers": "MIL",
    "Minnesota Twins": "MIN",
    "New York Mets": "NYM",
    "New York Yankees": "NYY",
    "Athletics": "ATH",
    "Oakland Athletics": "ATH",
    "Philadelphia Phillies": "PHI",
    "Pittsburgh Pirates": "PIT",
    "San Diego Padres": "SD",
    "San Francisco Giants": "SF",
    "Seattle Mariners": "SEA",
    "St. Louis Cardinals": "STL",
    "Tampa Bay Rays": "TB",
    "Texas Rangers": "TEX",
    "Toronto Blue Jays": "TOR",
    "Washington Nationals": "WSH",
}


FALLBACK_LINEUPS = {
    "Pittsburgh Pirates": [
        "Oneil Cruz",
        "Bryan Reynolds",
        "Andrew McCutchen",
        "Ke'Bryan Hayes",
        "Joey Bart",
        "Nick Gonzales",
        "Tommy Pham",
        "Jack Suwinski",
        "Isiah Kiner-Falefa",
    ],
}


POSITION_PRIORITY = {
    "C": 1,
    "1B": 2,
    "2B": 3,
    "3B": 4,
    "SS": 5,
    "LF": 6,
    "CF": 7,
    "RF": 8,
    "OF": 9,
    "DH": 10,
}


def get_json(url, params=None):
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def format_game_time(game_date_utc):
    if not game_date_utc:
        return "", "", ""

    try:
        utc_dt = datetime.fromisoformat(game_date_utc.replace("Z", "+00:00"))
        et_dt = utc_dt.astimezone(ZoneInfo("America/New_York"))

        return (
            utc_dt.isoformat(),
            et_dt.isoformat(),
            et_dt.strftime("%I:%M %p").lstrip("0"),
        )
    except Exception:
        return game_date_utc, "", ""


def get_schedule(game_date=None):
    if game_date is None:
        game_date = date.today().strftime("%Y-%m-%d")

    url = "https://statsapi.mlb.com/api/v1/schedule"
    params = {
        "sportId": 1,
        "date": game_date,
        "hydrate": "probablePitcher",
    }

    data = get_json(url, params=params)
    games = []

    for day in data.get("dates", []):
        for game in day.get("games", []):
            away = game["teams"]["away"]
            home = game["teams"]["home"]

            away_team = away["team"]["name"]
            home_team = home["team"]["name"]

            away_pitcher = away.get("probablePitcher", {}).get("fullName", "TBD")
            home_pitcher = home.get("probablePitcher", {}).get("fullName", "TBD")

            game_time_utc, game_time_et, game_time_display = format_game_time(
                game.get("gameDate", "")
            )

            games.append({
                "gamePk": game["gamePk"],
                "Date": game_date,
                "GameTimeUTC": game_time_utc,
                "GameTimeET": game_time_et,
                "GameTime": game_time_display,
                "Game": f"{away_team} vs {home_team}",
                "AwayTeam": away_team,
                "HomeTeam": home_team,
                "AwayTeamId": away["team"]["id"],
                "HomeTeamId": home["team"]["id"],
                "AwayPitcher": away_pitcher,
                "HomePitcher": home_pitcher,
            })

    games = sorted(games, key=lambda g: g.get("GameTimeET", ""))

    return games


def get_confirmed_lineup(game_pk, side):
    url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"

    try:
        data = get_json(url)
    except Exception:
        return []

    team_data = (
        data.get("liveData", {})
        .get("boxscore", {})
        .get("teams", {})
        .get(side, {})
    )

    players = team_data.get("players", {})
    batters = team_data.get("batters", [])

    lineup = []

    for player_id in batters:
        key = f"ID{player_id}"
        player = players.get(key, {})
        person = player.get("person", {})
        batting_order = player.get("battingOrder")

        if batting_order:
            try:
                spot = int(str(batting_order)[0])
            except Exception:
                continue

            full_name = person.get("fullName", "").strip()

            if full_name:
                lineup.append({
                    "spot": spot,
                    "player": full_name,
                    "player_id": str(player_id),
                    "source": "confirmed",
                })

    lineup = sorted(lineup, key=lambda x: x["spot"])
    return lineup[:9]


def is_pitcher_position(position_code, position_name):
    combined = f"{position_code} {position_name}".lower()
    return (
        position_code == "1"
        or "pitcher" in combined
        or "p/" in combined
        or combined.strip() == "p"
    )


def get_active_roster_lineup(team_id, team_name):
    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster"
    params = {"rosterType": "active"}

    try:
        data = get_json(url, params=params)
    except Exception as exc:
        print(f"⚠️ Could not pull active roster for {team_name}: {exc}")
        return []

    hitters = []

    for item in data.get("roster", []):
        person = item.get("person", {})
        position = item.get("position", {})

        player_id = str(person.get("id", "")).strip()
        full_name = str(person.get("fullName", "")).strip()
        position_code = str(position.get("code", "")).strip()
        position_abbrev = str(position.get("abbreviation", "")).strip()
        position_name = str(position.get("name", "")).strip()

        if not full_name or not player_id:
            continue

        if is_pitcher_position(position_code, position_name):
            continue

        priority = POSITION_PRIORITY.get(position_abbrev, 50)

        hitters.append({
            "player": full_name,
            "player_id": player_id,
            "position": position_abbrev,
            "priority": priority,
        })

    hitters = sorted(hitters, key=lambda x: (x["priority"], x["player"]))

    lineup = []

    for idx, hitter in enumerate(hitters[:9]):
        lineup.append({
            "spot": idx + 1,
            "player": hitter["player"],
            "player_id": hitter["player_id"],
            "source": "power_roster",
        })

    return lineup


def get_fallback_lineup(team_name):
    players = FALLBACK_LINEUPS.get(team_name, [])

    if not players:
        return []

    return [
        {
            "spot": idx + 1,
            "player": player,
            "player_id": "",
            "source": "manual_fallback",
        }
        for idx, player in enumerate(players)
    ]


def get_best_available_lineup(game, team_side):
    if team_side == "away":
        team_name = game["AwayTeam"]
        team_id = game["AwayTeamId"]
    else:
        team_name = game["HomeTeam"]
        team_id = game["HomeTeamId"]

    confirmed = get_confirmed_lineup(game["gamePk"], team_side)

    if confirmed:
        print(f"✅ Confirmed lineup found for {team_name}")
        return confirmed

    print(f"⚠️ No confirmed lineup for {team_name}. Using active roster hitters.")
    roster_lineup = get_active_roster_lineup(team_id, team_name)

    if roster_lineup:
        return roster_lineup

    print(f"⚠️ Active roster failed for {team_name}. Using manual fallback.")
    fallback = get_fallback_lineup(team_name)

    if fallback:
        return fallback

    print(f"❌ No lineup available for {team_name}. Skipping team.")
    return []


def add_rows(rows, game, team, opposing_pitcher, lineup):
    for hitter in lineup:
        rows.append({
            "Date": game["Date"],
            "GameTimeUTC": game["GameTimeUTC"],
            "GameTimeET": game["GameTimeET"],
            "GameTime": game["GameTime"],
            "Game": game["Game"],
            "LineupSpot": hitter["spot"],
            "Player": hitter["player"],
            "player_id": hitter.get("player_id", ""),
            "LineupSource": hitter.get("source", ""),
            "Team": team,
            "Pitcher": opposing_pitcher,
            "ISO": "",
            "Pitcher_HR9": "",
            "HardHit": "",
            "FlyBall": "",
            "BarrelRate": "",
            "ExitVelocity": "",
            "LaunchAngle": "",
            "RecentHRRate": "",
            "ParkFactor": "",
            "WindFactor": "",
            "Matchup": "",
            "FanDuel": "",
            "DraftKings": "",
            "BetMGM": "",
        })


def build_daily_slate(game_date=None):
    print("\n🚀 BUILDING DAILY SLATE\n")

    games = get_schedule(game_date)
    rows = []

    for game in games:
        print(f"\n📅 {game['Game']} — {game['GameTime']} ET")

        away_lineup = get_best_available_lineup(game, "away")
        home_lineup = get_best_available_lineup(game, "home")

        add_rows(
            rows,
            game,
            game["AwayTeam"],
            game["HomePitcher"],
            away_lineup,
        )

        add_rows(
            rows,
            game,
            game["HomeTeam"],
            game["AwayPitcher"],
            home_lineup,
        )

    df = pd.DataFrame(rows)

    if not df.empty:
        df = df.sort_values(
            by=["GameTimeET", "Game", "Team", "LineupSpot"],
            ascending=[True, True, True, True]
        )

    output_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "data",
        "sample_slate.csv",
    )

    df.to_csv(output_path, index=False)

    print("\n✅ DAILY SLATE COMPLETE")
    print(f"📊 Total Rows: {len(df)}")
    print(f"📁 Saved to: {output_path}")

    if len(df):
        print("\n📌 Lineup source counts:")
        print(df["LineupSource"].value_counts())

        print("\n📌 Games by start time:")
        print(
            df[["GameTime", "Game"]]
            .drop_duplicates()
            .to_string(index=False)
        )

        print("\n📌 Preview:")
        print(df[["GameTime", "Game", "Team", "LineupSpot", "Player", "LineupSource"]].head(30))


if __name__ == "__main__":
    build_daily_slate()