from typing import List, Set, Tuple, Union, Any
from GameState import GameState
from Action import Action, ActionType, Bid
from const import (
    MAX_FACE_VALUE,
    MIN_FACE_VALUE,
    BET_HIST_IDX,
    TOTAL_DICE_IDX,
    LAST_BID_IDX
)

def get_valid_actions(state: Union[GameState, List[Any]]) -> List[Action]:
    """
    Get valid actions for the current game state.
    Works with both GameState objects and public state lists.
    
    Args:
        state: Either a GameState object or a public state list
    Returns:
        List of valid Action objects
    """
    # Convert public state list to GameState if needed
    if isinstance(state, list):
        # Extract previous bid from public state if it exists
        prev_bid = None
        if state[BET_HIST_IDX] > 0:
            prev_bid = (state[-2], state[-1])
            
        state = GameState(
            action_history=[],  # Not needed for valid actions
            player_dice_counts=state[4:],  # Hidden dice counts
            current_player=0,  # Not needed for valid actions
            total_dice=state[TOTAL_DICE_IDX],
            dice_totals={},  # Not needed for valid actions
            bet_history=[prev_bid] if prev_bid else []
        )
    
    actions = []
    total_dice = state.total_dice
    
    # Can only call lie if there's a previous bid
    if state.bet_history:
        actions.append(Action.call_liar())
    
    # Get previous bid if it exists
    prev_bid = state.get_last_bid()
    
    # Add possible bid actions
    if prev_bid:
        # Must increase quantity or face value
        start_quantity = prev_bid[0]
        start_face = prev_bid[1]
        
        # Same quantity, higher face
        for face in range(start_face + 1, MAX_FACE_VALUE + 1):
            actions.append(Action.make_bid(start_quantity, face))
        
        # Higher quantity
        for quantity in range(start_quantity + 1, total_dice + 1):
            for face in range(MIN_FACE_VALUE, MAX_FACE_VALUE + 1):
                actions.append(Action.make_bid(quantity, face))
    else:
        # First bid - any valid combination
        for quantity in range(1, total_dice + 1):
            for face in range(MIN_FACE_VALUE, MAX_FACE_VALUE + 1):
                actions.append(Action.make_bid(quantity, face))
                
    return actions