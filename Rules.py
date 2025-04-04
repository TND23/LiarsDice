import torch
# should I specify that the bid qty is not to exceed the number of dice in the game?
def is_valid_bet(new_action, last_action):
    # if this is the first bet, it is valid provided it's not calling someone a liar
    if last_action is None:
        if new_action.is_bid():
            return True
        else:
            return False
    
    if not last_action.is_bid():
        return False # if the last action wasn't a bid, it was a call, so there ought to be nothing to do

    last_bid = last_action.bid
    new_bid = new_action.bid

    if new_bid.quantity < last_bid.quantity:
        return False # if the new bid has less quantity than the last bid, it is invalid
    if new_bid.quantity == last_bid.quantity and new_bid.face_value <= last_bid.face_value:
        return False # if the new bid has the same quantity as the last bid, it must have a higher face value
    return True