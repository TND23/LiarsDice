import numpy as np
from Action import Action, ActionType, Bid
import random
from const import *
from typing import List, Dict, Tuple, Any, no_type_check
from Managers.StateManager import StateManager
from Managers.ActionManager import ActionManager
from Robot.qtable_persistence import QTablePersistence
from datetime import datetime

# Fun names for reading debugging output.
names = ['Alex', 'Bob', 'Charlie', 'Denise', 'Ellyn', 'Frank', 'George', 'Hugh', 'InteractivRobot', 'John', 'Kaitlyn', 'Leeroy', 'Marco', 'Nate', 'Orville', 'Parm', 'Quincy', 'Roger', 'Scott', 'TJ', 'Usher', 'Victor', 'Winston', 'Sir Xylophone', 'Yvette', 'Zach']

class AI:
    def __init__(self, p_index: int, action_manager: ActionManager):
        self.learning_rate = LEARN_RATE
        self.discount_factor = DISCOUNT_FACTOR
        self.epsilon = EPSILON # Exploration rate
        self.q_table: Dict[Tuple, Dict[str, float]] = {}  # State-action value table
        self.NUMDICE = MAX_DICE_PER_PLAYER
        self.rolls: List[int] = []  # Player's dice
        self.p_index = p_index
        self.reward = 0
        self.name = self.fun_name() + f"Bot_{p_index}"
        self.state_manager = StateManager()
        self.persistence = QTablePersistence()
        self.action_manager = ActionManager()
        self.spots_could_have_called_liar = []

    def get_action(self, state_manager: StateManager) -> Action:
        """Get the next action based on the current state."""
        # might be uneccessary to update state_manager
        self.state_manager = state_manager
        valid_actions = self.action_manager.get_valid_actions(state_manager)
        if valid_actions.count(Action.call_liar()) > 0:
            self.spots_could_have_called_liar.append(state_manager.get_game_state().last_bid)
        action_values = {}
        state_key = self.state_manager.get_state_key()
        # Initialize Q-values for valid actions
        for action in valid_actions:
            assert isinstance(state_key, Tuple)
            assert isinstance(self.q_table, Dict)
            action_str = self.action_manager._action_to_str(action)
            # Only initialize if the state key doesn't exist
            if state_key not in self.q_table:
                self.q_table[state_key] = {}

            # Only initialize if the action doesn't exist
            if action_str not in self.q_table[state_key]:
                self.q_table[state_key][action_str] = 0.0

            action_values[action] = self.q_table[state_key][action_str]
        # chance of doing random action decays over time
        if random.random() < self.epsilon or not action_values.items():
            chosen_action = random.choice(valid_actions)
        else:
            chosen_action = max(action_values.items(), key=lambda x: x[1])[0]

        return chosen_action
    #TODO: this doesn't work without a proper next state.
    def update_q_value(self, action: Action, reward: float) -> None:
        """Update Q-value based on the current state, action, reward, and next state."""
        if action is None: # if end of game just return since no next state.
            return

        current_state_key = self.state_manager.get_state_key()
        next_state_key = self.state_manager.get_next_state_key(action)
        action_str = self.action_manager._action_to_str(action)

        # Initialize Q-values if needed
        if current_state_key not in self.q_table:
            self.q_table[current_state_key] = {}
        if action_str not in self.q_table[current_state_key]:
            self.q_table[current_state_key][action_str] = 0.0

        max_next_q = 0.0
        if next_state_key in self.q_table:
            max_next_q = max(self.q_table[next_state_key].values()) if self.q_table[next_state_key] else 0.0
        #Bellman equation:
        #Q(s, a) = Q(s, a) + α * (r + γ * max(Q(s', a')) - Q(s, a))
        #Q(s, a) == current_q (q value for state s and action a)
        #α == learning_rate
        #r == reward
        #γ == discount factor
        #s' == next state after taking action a
        #Q(s', a') is the Q-value for the next state s' and action a'.
        #max(Q(s', a')) is the maximum Q-value among all possible actions in the next state s'
        current_q = self.q_table[current_state_key][action_str]
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )
        self.q_table[current_state_key][action_str] = new_q

    def update_reward(self, enforcement_type: str, state_manager: StateManager) -> None:
        """Update the reward based on the enforcement type."""
        game_state = state_manager.get_game_state()

        most_freq_opp_face = game_state.most_freq_opp_face
        last_bid_qty = game_state.get_last_bid()[0]
        last_bid_face = game_state.get_last_bid()[1]
        had_other_actions = self.action_manager.get_valid_actions(state_manager) != [Action.call_liar()]
        opponent_dice_count = sum(len(hand) for hand in [i_hand for i, i_hand in enumerate(game_state.hands) if i != self.p_index])
        """ Trying to prevent really stupid behavior for now."""
        if enforcement_type == "reward_liar_call":
            # if the player can prove the bid is a lie, large reward.
            if last_bid_qty > self.rolls.count(last_bid_face) + opponent_dice_count:
                # The caller was correct - the bid was impossible
                self.reward += 20
            # if the player sees that the bid is possible but that it is not the most frequent opponent bid, reward.
            if last_bid_qty == self.rolls.count(last_bid_face) + opponent_dice_count and most_freq_opp_face != last_bid_face:
                # The caller was correct - the bid was unlikely
                self.reward += 6
            if last_bid_qty == self.rolls.count(last_bid_face) + opponent_dice_count and most_freq_opp_face == last_bid_face:
                # The caller was correct - the bid was possible but risky
                self.reward += 5
            # Base reward for making a correct liar call
            self.reward += 1.5
        elif enforcement_type == "punish_liar_call":
            # if the player called liar but the bid was actually possible, punish harshly.
            if self.rolls.count(last_bid_face) + opponent_dice_count >= last_bid_qty and had_other_actions:
                self.reward -= 30
            # if the player can reason that the bid is probably true and calls a liar, punish
            if self.rolls.count(last_bid_face) + round(opponent_dice_count / 6) >= last_bid_qty and had_other_actions:
                self.reward -= 8
            # if the bid face matches the most frequent opponent face, punish for calling liar
            if most_freq_opp_face == last_bid_face and had_other_actions:
                self.reward -= 2
        elif enforcement_type == "reward_passive":
            # Reward for not making a bad liar call
            self.reward += 5
        elif enforcement_type == "punish_passive":
            # if there was any time the player could have reasoned that the bid was impossible, punish for not calling liar.
            #for bid in self.spots_could_have_called_liar:
            #    if self.rolls.count(bid[1]) + opponent_dice_count < bid[0]: # if the player can reason that the bid is impossible, punish.
            #        self.reward -= 30
            self.reward -= 5
    #region helpers
    def get_expected_number_of_opponent_face(self, opponent_dice_count: int) -> int:
        return round(opponent_dice_count / 6)



    def roll(self) -> None:
        self.rolls = []
        for _ in range(self.NUMDICE):
            self.rolls.append(random.randrange(MIN_FACE_VALUE, MAX_FACE_VALUE + 1))

    def remove_die(self) -> None:
        self.NUMDICE = max(0, self.NUMDICE - 1)
        if self.rolls:
            self.rolls.pop()

    def get_q_table(self):
        return self.q_table

    def fun_name(self):
        return random.choice(names)

    def save_q_table(self, table_id: str = "") -> str:
        """Save the current Q-table with optional table_id."""
        if table_id == "":
            table_id = f"{self.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        # letting an ai agent decide how to encode into binary for now...
        self.persistence.save_q_table(self.q_table, table_id)
        return table_id

    def load_q_table(self, table_id: str) -> None:
        """Load Q-table with table_id."""
        try:
            loaded_table = self.persistence.load_q_table(table_id)
            # Verify the loaded table
            if not loaded_table:
                print("Warning: Loaded Q-table is empty")
            else:
                self.q_table = loaded_table

        except Exception as e:
            print(f"Error loading Q-table: {str(e)}: Keeping existing Q-table")

    def list_saved_tables(self) -> List[str]:
        return self.persistence.list_saved_tables()

    #endregion
