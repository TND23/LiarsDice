import torch
def is_valid_bet(qty, last_qty, face_val, last_face_val):
    if (qty < last_qty):
        return False
    if (qty == last_qty and last_face_val <= last_face_val):
        return False
    if (qty == last_qty and face_val > last_face_val):
        return True
    if (qty > last_qty):
        return True
    return True   