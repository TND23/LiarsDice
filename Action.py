from enum import Enum
from dataclasses import dataclass
from typing import Optional, Tuple, no_type_check
from const import MAX_TOTAL_DICE, MAX_FACE_VALUE

class ActionType(Enum):
    BID = 0
    CALL_LIE = 1

# Add class that defines what a Bid is. The tuple implementation of Bid has proven difficult to work with.
@dataclass(frozen=True)
class Bid:
    quantity: int
    face_value: int


    # ensure in range
    def __post_init__(self):
        if not (1 <= self.quantity <= MAX_TOTAL_DICE):
            raise ValueError(f"Invalid quantity: {self.quantity}")
        if not (1 <= self.face_value <= MAX_FACE_VALUE):
            raise ValueError(f"Invalid face value: {self.face_value}")

    def to_tuple(self) -> Tuple[int, int]:
        return (self.quantity, self.face_value)



# General action
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
    # convert to tuple for Q-table
    def to_tuple(self) -> Tuple[ActionType, Optional[Bid]]:
        if(self.is_bid()):
            return (self.type, self.bid)
        else:
            return (self.type, None)
    @no_type_check
    def __str__(self) -> str:
        if self.is_bid():
            return f"Action.make_bid({self.bid.quantity}, {self.bid.face_value})"
        return "Action.call_liar()"

    def __repr__(self) -> str:
        return self.__str__()

    # make hashable for Q-table
    @no_type_check
    def __hash__(self) -> int:
        if self.is_bid():
            return hash((self.type, self.bid.to_tuple()))
        return hash((self.type,))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Action):
            return NotImplemented
        if self.type != other.type:
            return False
        if self.is_bid():
            return self.bid == other.bid
        return True

