import torch
# should I specify that the bid qty is not to exceed the number of dice in the game?
def is_valid_bet(qty, last_qty, face_val, last_face_val):
    # if this is the first bet, it is valid provided it's not calling someone a liar
    if (last_qty == 0):
        return True
    if (qty < last_qty):
        return False
    if (qty == last_qty and face_val <= last_face_val):
        return False
    if (qty == last_qty and face_val > last_face_val):
        return True
    if (qty > last_qty):
        return True
    return True   
