import os
import random
import requests


ODDS_API_KEY = os.getenv("ODDS_API_KEY")

SPORT = "baseball_mlb"
MARKET = "batter_home_runs"

BOOKMAKER_KEYS = {
    "fanduel": "FanDuel",
    "draftkings": "DraftKings",
    "betmgm": "BetMGM",
}


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


_ODDS_CACHE = None


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


def clean_name(name):
    return str(name or "").strip().lower().replace(".", "").replace("’", "'")


def normalize_book_name(book_key, book_title):
    key = str(book_key or "").lower().strip()
    title = str(book_title or "").strip()

    if key in BOOKMAKER_KEYS:
        return BOOKMAKER_KEYS[key]

    if "fanduel" in title.lower():
        return "FanDuel"

    if "draftkings" in title.lower():
        return "DraftKings"

    if "betmgm" in title.lower():
        return "BetMGM"

    return None


def fetch_events():
    if not ODDS_API_KEY:
        return []

    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/events"

    params = {
        "apiKey": ODDS_API_KEY,
        "dateFormat": "iso",
    }

    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print("⚠️ Events API failed. Using fallback odds.")
        print(e)
        return []


def fetch_event_hr_odds(event_id):
    if not ODDS_API_KEY:
        return None

    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/events/{event_id}/odds"

    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": MARKET,
        "oddsFormat": "american",
        "dateFormat": "iso",
        "bookmakers": "fanduel,draftkings,betmgm",
    }

    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"⚠️ Event odds failed for event {event_id}.")
        print(e)
        return None


def build_odds_lookup():
    lookup = {}

    events = fetch_events()

    if not events:
        return lookup

    print(f"📡 Odds API events found: {len(events)}")

    for event in events:
        event_id = event.get("id")

        if not event_id:
            continue

        data = fetch_event_hr_odds(event_id)

        if not data:
            continue

        for bookmaker in data.get("bookmakers", []):
            book = normalize_book_name(
                bookmaker.get("key"),
                bookmaker.get("title")
            )

            if not book:
                continue

            for market in bookmaker.get("markets", []):
                if market.get("key") != MARKET:
                    continue

                for outcome in market.get("outcomes", []):
                    if outcome.get("name") != "Over":
                        continue

                    player = outcome.get("description") or outcome.get("name")
                    price = american_to_int(outcome.get("price"))

                    if not player or price is None:
                        continue

                    key = clean_name(player)

                    if key not in lookup:
                        lookup[key] = {}

                    lookup[key][book] = price

    print(f"✅ Real HR odds loaded for {len(lookup)} players")
    return lookup


def get_odds_cache():
    global _ODDS_CACHE

    if _ODDS_CACHE is None:
        _ODDS_CACHE = build_odds_lookup()

    return _ODDS_CACHE


def get_player_odds(player):
    odds_lookup = get_odds_cache()
    key = clean_name(player)

    if key in odds_lookup:
        real = odds_lookup[key]

        fallback = fallback_player_odds(player)

        return {
            "FanDuel": real.get("FanDuel", fallback["FanDuel"]),
            "DraftKings": real.get("DraftKings", fallback["DraftKings"]),
            "BetMGM": real.get("BetMGM", fallback["BetMGM"]),
        }

    return fallback_player_odds(player)


if __name__ == "__main__":
    odds = build_odds_lookup()
    print(f"Players with real odds: {len(odds)}")
    for name, prices in list(odds.items())[:20]:
        print(name, prices)