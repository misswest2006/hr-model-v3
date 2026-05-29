import os
import random
import requests


ODDS_API_KEY = os.getenv("ODDS_API_KEY")

SPORT = "baseball_mlb"
MARKET = "batter_home_runs"


FALLBACK_ODDS = {
    "Aaron Judge": [220, 260],
    "Shohei Ohtani": [240, 290],
    "Juan Soto": [260, 320],
    "Kyle Schwarber": [280, 350],
    "Matt Olson": [300, 380],
    "Pete Alonso": [290, 360],
    "Bryce Harper": [300, 370],
    "Yordan Alvarez": [270, 340],
    "Mike Trout": [450, 600],
    "Taylor Ward": [400, 650],
    "Logan O'Hoppe": [400, 650],
    "Jorge Soler": [350, 600],
}


def randomize(base):
    return base + random.randint(-15, 15)


def fallback_player_odds(player):
    if player in FALLBACK_ODDS:
        low, high = FALLBACK_ODDS[player]
        fd = random.randint(low, high)
    else:
        fd = random.randint(350, 650)

    return {
        "FanDuel": fd,
        "DraftKings": randomize(fd),
        "BetMGM": randomize(fd),
    }


def american_to_int(price):
    try:
        return int(price)
    except Exception:
        return None


def fetch_real_odds():
    if not ODDS_API_KEY:
        return None

    url = (
        f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds"
        f"?apiKey={ODDS_API_KEY}"
        f"&regions=us"
        f"&markets={MARKET}"
        f"&oddsFormat=american"
    )

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        return response.json()

    except Exception as e:
        print("⚠️ Real odds API failed. Using fallback odds.")
        print(e)
        return None


def normalize_book_name(book):
    book = book.lower()

    if "fanduel" in book:
        return "FanDuel"

    if "draftkings" in book:
        return "DraftKings"

    if "betmgm" in book:
        return "BetMGM"

    return None


def build_odds_lookup():
    data = fetch_real_odds()

    if not data:
        return {}

    lookup = {}

    for game in data:
        bookmakers = game.get("bookmakers", [])

        for bookmaker in bookmakers:
            book_name = normalize_book_name(
                bookmaker.get("title", "")
            )

            if not book_name:
                continue

            for market in bookmaker.get("markets", []):
                for outcome in market.get("outcomes", []):
                    player = outcome.get("description") or outcome.get("name")
                    price = american_to_int(outcome.get("price"))

                    if not player or price is None:
                        continue

                    if player not in lookup:
                        lookup[player] = {}

                    lookup[player][book_name] = price

    return lookup


REAL_ODDS_LOOKUP = build_odds_lookup()


def get_player_odds(player):

    real = REAL_ODDS_LOOKUP.get(player)

    if real:

        fallback = fallback_player_odds(player)

        return {
            "FanDuel": real.get("FanDuel") or fallback["FanDuel"],
            "DraftKings": real.get("DraftKings") or fallback["DraftKings"],
            "BetMGM": real.get("BetMGM") or fallback["BetMGM"],
        }

    return fallback_player_odds(player)