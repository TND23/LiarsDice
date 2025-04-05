import numpy as np
from Action import Action, ActionType, Bid
import random
from GameState import GameState
from const import *
from itertools import combinations_with_replacement
from typing import List, Dict, Tuple, Any, Optional

class AI:
    def __init__(self, p_index: int):
        self.learning_rate = 0.1
        self.discount_factor = 0.9
        self.epsilon = 0.2  # Exploration rate
        self.q_table: Dict[Tuple, Dict[str, float]] = {}  # State-action value table
        self.NUMDICE = MAX_DICE_PER_PLAYER  # Starting number of dice
        self.rolls: List[int] = []  # Current dice
        self.p_index = p_index
        self.reward = 0
        self.name = f"AI_{p_index}"
        
    def _get_state_key(self, pub_state: List[Any]) -> Tuple:
        """Convert game state to a hashable key for Q-table"""
        state_key = (
            tuple(sorted(self.rolls)),  # Current dice
            tuple(pub_state[-2:]) if pub_state[BET_HIST_IDX] > 0 else None,  # Previous bid
            pub_state[TOTAL_DICE_IDX],  # Total dice in game
            tuple(pub_state[HIDDEN_DICE_START_IDX:])  # Other players' dice counts
        )
        return state_key

    def _get_valid_actions(self, pub_state: List[Any]) -> List[Action]:
        """Get list of valid actions given the current state"""
        actions: List[Action] = []
        total_dice = pub_state[TOTAL_DICE_IDX]
        
        # Can only call lie if there's a previous bid
        if pub_state[BET_HIST_IDX] > 0:
            actions.append(Action.call_liar())
        
        # Get previous bid if it exists
        prev_bid = None
        if pub_state[BET_HIST_IDX] > 0:
            prev_bid = (pub_state[-2], pub_state[-1])
        
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

    def _action_to_str(self, action: Action) -> str:
        """Convert an action to its string representation for Q-table lookup."""
        if action.is_bid():
            return f"bid_{action.bid.quantity}_{action.bid.face_value}"
        return "call_liar"

    def _str_to_action(self, action_str: str) -> Action:
        """Convert a string representation back to an Action object."""
        if action_str == "call_liar":
            return Action.call_liar()
        parts = action_str.split("_")
        if len(parts) == 3 and parts[0] == "bid":
            return Action.make_bid(int(parts[1]), int(parts[2]))
        raise ValueError(f"Invalid action string: {action_str}")

    def get_action(self, pub_state: List[Any]) -> Action:
        """Choose action using epsilon-greedy policy"""
        state_key = self._get_state_key(pub_state)
        valid_actions = self._get_valid_actions(pub_state)
        
        if not valid_actions:
            raise ValueError("No valid actions available")
        
        # Exploration
        if random.random() < self.epsilon:
            return random.choice(valid_actions)
            
        # Exploitation
        if state_key not in self.q_table:
            # Initialize Q-values for all valid actions
            self.q_table[state_key] = {self._action_to_str(action): 0.0 for action in valid_actions}
            return random.choice(valid_actions)
            
        # Get action with highest Q-value among valid actions
        valid_action_strs = {self._action_to_str(action): action for action in valid_actions}
        q_values = {action_str: self.q_table[state_key].get(action_str, 0.0) 
                   for action_str in valid_action_strs.keys()}
        
        max_q = max(q_values.values())
        best_action_strs = [action_str for action_str, q in q_values.items() if q == max_q]
        best_action_str = random.choice(best_action_strs)
        
        return valid_action_strs[best_action_str]

    def update_q_value(self, state: List[Any], action: Action, reward: float, next_state: List[Any]) -> None:
        """Update Q-value for state-action pair"""
        state_key = self._get_state_key(state)
        next_state_key = self._get_state_key(next_state)
        action_str = self._action_to_str(action)
        
        # Initialize Q-values if not exists
        if state_key not in self.q_table:
            valid_actions = self._get_valid_actions(state)
            self.q_table[state_key] = {self._action_to_str(a): 0.0 for a in valid_actions}
            
        if next_state_key not in self.q_table:
            valid_actions = self._get_valid_actions(next_state)
            self.q_table[next_state_key] = {self._action_to_str(a): 0.0 for a in valid_actions}
        
        # Ensure the action exists in the Q-table
        if action_str not in self.q_table[state_key]:
            self.q_table[state_key][action_str] = 0.0
        
        # Get max Q-value for next state
        next_max_q = max(self.q_table[next_state_key].values()) if self.q_table[next_state_key] else 0
        
        # Update Q-value
        current_q = self.q_table[state_key][action_str]
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * next_max_q - current_q)
        self.q_table[state_key][action_str] = new_q

    def roll(self) -> None:
        """Roll dice for new round"""
        self.rolls = []
        for _ in range(self.NUMDICE):
            self.rolls.append(random.randrange(MIN_FACE_VALUE, MAX_FACE_VALUE + 1))

    def remove_die(self) -> None:
        """Remove one die when losing"""
        self.NUMDICE = max(0, self.NUMDICE - 1)
        if self.rolls:
            self.rolls.pop()

    def update_reward(self, reward: float) -> None:
        """Update the agent's reward"""
        self.reward = reward
        
    def update_opp_bids(self, bid: Tuple[int, int]) -> None:
        """Track opponent bids for learning"""
        if isinstance(bid, tuple) and len(bid) == 2:
            # Only track valid bids (quantity, face)
            self.epsilon = max(0.01, self.epsilon * 0.995)  # Decay exploration rate
