import requests


STADIUM_COORDS = {
    "Los Angeles Angels": {"lat": 33.8003, "lon": -117.8827},
    "Detroit Tigers": {"lat": 42.3390, "lon": -83.0485},
    "New York Yankees": {"lat": 40.8296, "lon": -73.9262},
    "Los Angeles Dodgers": {"lat": 34.0739, "lon": -118.2400},
    "Philadelphia Phillies": {"lat": 39.9061, "lon": -75.1665},
    "Colorado Rockies": {"lat": 39.7561, "lon": -104.9942},
    "Boston Red Sox": {"lat": 42.3467, "lon": -71.0972},
    "Toronto Blue Jays": {"lat": 43.6414, "lon": -79.3894},
    "Texas Rangers": {"lat": 32.7473, "lon": -97.0842},
    "Baltimore Orioles": {"lat": 39.2839, "lon": -76.6217},
}


def get_weather_factor_for_team(team):
    coords = STADIUM_COORDS.get(team)

    if not coords:
        return 1.00

    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={coords['lat']}"
            f"&longitude={coords['lon']}"
            "&current_weather=true"
        )

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()
        weather = data.get("current_weather", {})

        temp = weather.get("temperature", 70)
        wind = weather.get("windspeed", 0)

        factor = 1.00

        if temp >= 80:
            factor += 0.05

        if wind >= 15:
            factor += 0.10
        elif wind >= 10:
            factor += 0.05

        return round(factor, 2)

    except Exception:
        return 1.00