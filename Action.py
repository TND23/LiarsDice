from enum import Enum

class Action(Enum):
    INC_BID = 0
    CALL_LIE = 1
    NONE = -1

LIE_TUPLE = (-1,-1)