from typing import Optional
from Action import Action

def is_valid_bet(new_action: Action, last_action: Optional[Action], total_dice: int) -> bool:
    """Validate if a bet is legal given the current game state.
    
    Args:
        new_action: The bet action to validate
        last_action: The previous action in the game
        total_dice: Total number of dice in play
        
    Returns:
        bool: True if the bet is valid, False otherwise
    """
    if not new_action.is_bid():
        return False
        
    if last_action is None:
        return True  # First bid of the round
        
    if not last_action.is_bid():
        return False  # Can't bid after a call
        
    last_bid = last_action.bid
    new_bid = new_action.bid
    
    # Must increase quantity or face value
    if new_bid.quantity < last_bid.quantity:
        return False
    if new_bid.quantity == last_bid.quantity and new_bid.face_value <= last_bid.face_value:
        return False
    if new_bid.quantity > total_dice:
        return False
        
    return True