def implied_prob(odds):
    if odds > 0:
        return 100 / (odds + 100)

    return abs(odds) / (abs(odds) + 100)