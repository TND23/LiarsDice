from enum import Enum
from dataclasses import dataclass
from typing import Optional

class ActionType(Enum):
    BID = 0
    CALL_LIE = 1

# Add class that defines what a Bid is. The tuple implementation has proven difficult to work with.
@dataclass(frozen=True)
class Bid:
    quantity: int
    face_value: int

    def __post_init__(self):
        if not (1 <= self.quantity <= 30):  # Reasonable max for total dice
            raise ValueError(f"Invalid quantity: {self.quantity}")
        if not (1 <= self.face_value <= 6):
            raise ValueError(f"Invalid face value: {self.face_value}")

# Add a second action class that contains action and Bid.
@dataclass(frozen=True)
class Action:
    type: ActionType
    bid: Optional[Bid] = None

    @classmethod
    def make_bid(cls, quantity: int, face_value: int) -> 'Action':
        return cls(ActionType.BID, Bid(quantity, face_value))

    @classmethod
    def call_liar(cls) -> 'Action':
        return cls(ActionType.CALL_LIE)

    def is_bid(self) -> bool:
        return self.type == ActionType.BID

    def is_call_liar(self) -> bool:
        return self.type == ActionType.CALL_LIE
    
    # make readable for debugging / logging
    def __str__(self) -> str:
        if self.is_bid():
            return f"Action.make_bid({self.bid.quantity}, {self.bid.face_value})"
        return "Action.call_liar()"

    def __repr__(self) -> str:
        return self.__str__()
    
    # make hashable for Q-table
    def __hash__(self) -> int:
        if self.is_bid():
            return hash((self.type, self.bid.quantity, self.bid.face_value))
        return hash((self.type,))

    # should I implement less than and greater than?
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Action):
            return NotImplemented
        if self.type != other.type:
            return False
        if self.is_bid():
            return self.bid == other.bid
        return True

