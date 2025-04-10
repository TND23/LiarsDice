from const import *
def calculate_bet_history_distance(bet_history_a, bet_history_b, total_dice):
    """ Calculate the distance between two bet histories for clustering.
    """
    # assert that bet_history_a and bet_history_b are lists of tuples
    assert isinstance(bet_history_a, list) and all(isinstance(item, tuple) for item in bet_history_a), "bet_history_a must be a list of tuples"
    assert isinstance(bet_history_b, list) and all(isinstance(item, tuple) for item in bet_history_b), "bet_history_b must be a list of tuples"

    if total_dice == 0:
        raise ValueError("total_dice cannot be 0")

    if bet_history_a == bet_history_b:
        return 0.0

    last_bid_a = bet_history_a[-1] if bet_history_a else None
    last_bid_b = bet_history_b[-1] if bet_history_b else None

    if (last_bid_a is None) != (last_bid_b is None):
        return 1.0

    if last_bid_a is None and last_bid_b is None:
        return 0.0

    qty_diff = abs(last_bid_a[0] - last_bid_b[0]) / total_dice
    face_diff = abs(last_bid_a[1] - last_bid_b[1]) / 5  # Assuming face values 1-6

    qty_ratio_a = last_bid_a[0] / total_dice
    qty_ratio_b = last_bid_b[0] / total_dice
    qty_ratio_diff = abs(qty_ratio_a - qty_ratio_b)

    # Calculate distance based on history length difference
    len_diff = abs(len(bet_history_a) - len(bet_history_b)) / 4  # Assuming max 4 rounds

    # Combine the different distance components with weights
    distance = (QTY_DISTANCE_WEIGHT * qty_diff + FACE_DISTANCE_WEIGHT * face_diff + QTY_RATIO_DISTANCE_WEIGHT * qty_ratio_diff + HISTORY_LENGTH_DISTANCE_WEIGHT * len_diff)

    return min(1.0, distance)  # Ensure distance is between 0 and 1




