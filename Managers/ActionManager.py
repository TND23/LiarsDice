from Action import Action
from typing import Union, no_type_check, List, Any
from GameState import GameState
import GameState
from Managers.StateManager import StateManager
from const import MAX_FACE_VALUE, MIN_FACE_VALUE

@no_type_check
class ActionManager:
    def __init__(self):
        self.actions = []

    def get_actions(self):
        return self.actions
    @no_type_check
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


    @no_type_check #stfu
    def get_valid_actions(self, state: StateManager) -> List[Action]:
        """
        Get valid actions for the current game state.
        Works with GameState objects, public state lists, or StateManager.

        Args:
            state: Either a GameState object, public state list, or StateManager
        Returns:
            List of valid Action objects
        """
        # Handle StateManager


        game_state = state.get_game_state()

        actions = []
        total_dice = game_state.total_dice

        # Can only call lie if there's a previous bid
        if game_state.bet_history:
            actions.append(Action.call_liar())

        # Get previous bid if it exists
        prev_bid = game_state.get_last_bid()

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
