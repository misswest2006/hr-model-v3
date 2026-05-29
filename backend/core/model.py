import numpy as np

def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def hr_probability(f):
    base = 0.035

    iso = float(f["ISO"])
    hr9 = float(f["Pitcher_HR9"])
    hardhit = float(f["HardHit"]) / 100
    flyball = float(f["FlyBall"]) / 100
    park = float(f["ParkFactor"])
    wind = float(f["WindFactor"])
    matchup = float(f["Matchup"])

    signal = (
        (iso - 0.200) * 5.0 +
        (hr9 - 1.2) * 2.5 +
        (hardhit - 0.35) * 4.0 +
        (flyball - 0.30) * 3.0 +
        (park - 1.0) * 2.0 +
        (wind - 1.0) * 1.5 +
        (matchup - 0.5) * 2.0
    )

    raw = sigmoid(signal)

    prob = base + raw * 0.45

    return float(np.clip(prob, 0.01, 0.60))