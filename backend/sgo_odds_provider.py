import os
import requests


SGO_API_KEY = os.getenv("SGO_API_KEY")

URL = "https://api.sportsgameodds.com/v2/events"

BOOKS = {
    "fanduel": "FanDuel",
    "draftkings": "DraftKings",
    "betmgm": "BetMGM",
}


def clean_name(name):
    return (
        str(name or "")
        .strip()
        .lower()
        .replace(".", "")
        .replace("’", "'")
    )


def fetch_sgo_events():
    if not SGO_API_KEY:
        print("⚠️ Missing SGO_API_KEY")
        return []

    params = {
        "apiKey": SGO_API_KEY,
        "oddsAvailable": "true",
        "leagueID": "MLB",
        "limit": 100,
    }

    response = requests.get(URL, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()

    if not data.get("success"):
        print("⚠️ SportsGameOdds request failed")
        print(data)
        return []

    return data.get("data", [])


def player_name_from_market(market_name):
    # Example: "Pedro Pagés Any Home Runs Yes/No"
    name = str(market_name or "")
    name = name.replace(" Any Home Runs Yes/No", "")
    name = name.replace(" Home Runs Over/Under", "")
    return name.strip()


def build_sgo_hr_odds_lookup():
    lookup = {}

    events = fetch_sgo_events()

    print(f"📡 SportsGameOdds events found: {len(events)}")

    for event in events:
        odds = event.get("odds", {})

        for odd_id, odd in odds.items():
            if odd.get("statID") != "batting_homeRuns":
                continue

            if odd.get("sideID") != "yes":
                continue

            market_name = odd.get("marketName", "")
            player = player_name_from_market(market_name)

            if not player:
                continue

            key = clean_name(player)

            if key not in lookup:
                lookup[key] = {}

            by_book = odd.get("byBookmaker", {})

            for book_key, label in BOOKS.items():
                book_data = by_book.get(book_key)

                if not book_data:
                    continue

                if book_data.get("available") is False:
                    continue

                price = book_data.get("odds")

                if price:
                    lookup[key][label] = price

    print(f"✅ SportsGameOdds HR odds loaded for {len(lookup)} players")
    return lookup


if __name__ == "__main__":
    odds = build_sgo_hr_odds_lookup()

    for player, prices in list(odds.items())[:40]:
        print(player, prices)