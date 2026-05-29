import os
import pandas as pd
import requests


def get_mlb_player_id(player_name):
    try:
        url = "https://statsapi.mlb.com/api/v1/people/search"
        params = {"names": player_name}

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        people = data.get("people", [])

        if not people:
            return ""

        return str(people[0].get("id", ""))

    except Exception:
        return ""


def enrich_player_ids():
    base_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    slate_path = os.path.join(base_dir, "sample_slate.csv")

    if not os.path.exists(slate_path):
        print("❌ sample_slate.csv not found")
        return

    df = pd.read_csv(slate_path)

    if "player_id" not in df.columns:
        df["player_id"] = ""

    df["player_id"] = df["player_id"].astype("string")

    added = 0

    for idx, row in df.iterrows():
        player = str(row.get("Player", "")).strip()
        current_id = str(row.get("player_id", "")).strip()

        if not player or player.lower() == "nan":
            continue

        if current_id not in ["", "nan", "None", "<NA>"]:
            continue

        player_id = get_mlb_player_id(player)

        if player_id:
            df.at[idx, "player_id"] = str(player_id)
            added += 1
            print(f"✅ {player} -> {player_id}")
        else:
            print(f"⚠️ No ID found for {player}")

    df.to_csv(slate_path, index=False)

    print("\n🔥 PLAYER ID ENRICHMENT COMPLETE 🔥")
    print(f"✅ Player IDs added: {added}")
    print(f"✅ Saved to: {slate_path}")


if __name__ == "__main__":
    enrich_player_ids()