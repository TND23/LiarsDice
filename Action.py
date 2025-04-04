from enum import Enum

class ActionType(Enum):
    INC_BID = 0
    CALL_LIE = 1

# Add class that defines what a Bid is. The tuple implementation has proven difficult to work with.
@dataclass(frozen=True)
class Bid:
    def __init__(self, qty, face_val):
        self.qty = qty
        self.face_val = face_val
        
# Add a second action class that contains action and Bid.
@dataclass(frozen=True)
class Action:
    type: ActionType
    bid: Optional[Bid] = None


    @classmethod
    def make_bid(cls, quantity: int, face_val: int):
        return cls(ActionType.INC_BID, Bid(quantity, face_val))

    @classmethod
    def call_liar(cls):
        return cls(ActionType.CALL_LIE)

    def is_bid(self):
        return self.type == ActionType.INC_BID

    def is_call_liar(self):
        return self.type == ActionType.CALL_LIE

    def __str__(self):
        if self.is_bid():
            return f"Action: Bid({self.bid.quantity}, {self.bid.face_val})"
        else:
            return "Action: Call Liar"

