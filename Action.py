from enum import Enum

class Action(Enum):
    INC_BID = 0
    CALL_LIE = 1

# Add class that defines what a Bid is. The tuple implementation has proven difficult to work with.
class Bid:
    def __init__(self, qty, face_val):
        self.qty = qty
        self.face_val = face_val
        
# Add a second action class that contains action and Bid.
class ActionBid:
    def __init__(self, action, bid):
        self.action = action
        self.bid = bid
    @classmethod
    def make_bid(cls, action, bid):
        return cls(action, bid)

    def call_liar(cls):
        return cls(Action.CALL_LIE, None)

    def __repr__(self):
        return f"ActionBid(action={self.action}, bid={self.bid})"
