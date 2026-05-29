import os
import pandas as pd
from datetime import datetime

from pybaseball import statcast_batter


# -------------------------
# HELPERS
# -------------------------

def american_to_profit(odds, stake):

    odds = int(str(odds).replace("+", ""))

    if odds > 0:
        return round((odds / 100) * stake, 2)

    return round((100 / abs(odds)) * stake, 2)


# -------------------------
# CHECK HR RESULT
# -------------------------

def player_hit_hr(player_name, game_date):

    try:

        start_date = game_date
        end_date = game_date

        data = statcast_batter(
            start_dt=start_date,
            end_dt=end_date,
            player_id_lookup=None
        )

        if data is None or len(data) == 0:
            return False

        hr_events = data[
            (data["events"] == "home_run")
        ]

        for _, row in hr_events.iterrows():

            batter_name = str(row.get("player_name", "")).strip()

            if batter_name.lower() == player_name.lower():
                return True

        return False

    except Exception as e:

        print(f"⚠️ Failed HR lookup for {player_name}")
        print(e)

        return False


# -------------------------
# MAIN GRADING ENGINE
# -------------------------

def grade_results():

    history_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "data",
        "hr_results_history.csv"
    )

    df = pd.read_csv(history_path)

    if len(df) == 0:

        print("⚠️ No saved history.")

        return

    updated = 0

    for idx, row in df.iterrows():

        result = str(row["Result"]).strip()

        if result in ["0", "1"]:
            continue

        player = str(row["Player"]).strip()
        date = str(row["Date"]).strip()

        print(f"🔍 Checking {player} | {date}")

        hit_hr = player_hit_hr(player, date)

        stake = float(row["Stake"])

        odds = row["BestOdds"]

        if hit_hr:

            profit = american_to_profit(odds, stake)

            df.at[idx, "Result"] = 1
            df.at[idx, "Profit"] = profit

            print(f"✅ WIN | +{profit}u")

        else:

            df.at[idx, "Result"] = 0
            df.at[idx, "Profit"] = -stake

            print(f"❌ LOSS | -{stake}u")

        updated += 1

    df.to_csv(history_path, index=False)

    print("\n🔥 GRADING COMPLETE 🔥")
    print(f"Updated Plays: {updated}")


if __name__ == "__main__":

    grade_results()