import os
import pandas as pd

DATA_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "data"
)

ADJUSTMENTS_FILE = os.path.join(
    DATA_DIR,
    "player_adjustments.csv"
)


def get_player_bonus(player):

    if not os.path.exists(ADJUSTMENTS_FILE):
        return 0

    try:
        df = pd.read_csv(ADJUSTMENTS_FILE)

        row = df[
            df["Player"].astype(str).str.lower().str.strip()
            ==
            str(player).lower().strip()
        ]

        if row.empty:
            return 0

        return float(row.iloc[0]["Bonus"])

    except Exception:
        return 0