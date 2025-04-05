from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from Action import Action, ActionType

@dataclass
class GameState:
    action_history: List[Action]
    player_dice_counts: List[int]
    current_player: int
    total_dice: int
    dice_totals: Dict[int, int]  # Maps face value to count
    bet_history: List[tuple[int, int]]  # List of (quantity, face_value) tuples
    
    def get_last_action(self) -> Optional[Action]:
        return self.action_history[-1] if self.action_history else None
    
    def get_last_bid(self) -> Optional[tuple[int, int]]:
        return self.bet_history[-1] if self.bet_history else None
    
    def add_action(self, action: Action) -> None:
        self.action_history.append(action)
        if action.is_bid():
            self.bet_history.append((action.bid.quantity, action.bid.face_value))
    
    def to_public_state(self) -> List[Any]:
        """Convert to the public state representation used by AI"""
        return [
            len(self.bet_history),  # BET_HIST_IDX
            len(self.player_dice_counts),  # PLAYER_CT_IDX
            self.get_last_action().type.value if self.get_last_action() else -1,  # LAST_ACTION_IDX
            self.total_dice,  # TOTAL_DICE_IDX
            *self.player_dice_counts  # Hidden dice counts
        ]
    
    @classmethod
    def from_public_state(cls, pub_state: List[Any], current_player: int) -> 'GameState':
        """Create a GameState from the public state representation"""
        return cls(
            action_history=[],  # Would need to be populated from game history
            player_dice_counts=pub_state[4:],  # Hidden dice counts
            current_player=current_player,
            total_dice=pub_state[3],  # TOTAL_DICE_IDX
            dice_totals={},  # Would need to be populated from actual dice
            bet_history=[]  # Would need to be populated from game history
        )
