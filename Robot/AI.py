import stat
import numpy as np
from Action import Action, ActionType, Bid
import random
from const import *
from typing import List, Dict, Tuple, Any, Optional
from Managers.ClusterManager import ClusterManager
from Managers.StateManager import StateManager
from Managers.ActionManager import ActionManager
from Robot.qtable_persistence import QTablePersistence
from datetime import datetime

# Fun names for reading debugging output.
names = ['Alex', 'Bob', 'Charlie', 'Denise', 'Ellyn', 'Frank', 'George', 'Hugh', 'InteractivRobot', 'John', 'Kaitlyn', 'Leeroy', 'Marco', 'Nate', 'Orville', 'Parm', 'Quincy', 'Roger', 'Scott', 'TJ', 'Usher', 'Victor', 'Winston', 'Sir Xylophone', 'Yvette', 'Zach']

class AI:
    def __init__(self, p_index: int, cluster_manager: ClusterManager, action_manager: ActionManager):
        self.learning_rate = LEARNING_RATE
        self.discount_factor = DISCOUNT_FACTOR
        self.epsilon = EPSILON # Exploration rate
        self.q_table: Dict[Tuple, Dict[str, float]] = {}  # State-action value table
        self.NUMDICE = MAX_DICE_PER_PLAYER
        self.rolls: List[int] = []  # Player's dice
        self.p_index = p_index
        self.reward = 0
        self.name = self.fun_name() + f"Bot_{p_index}"
        self.cluster_manager = cluster_manager
        self.state_manager = StateManager()
        self.persistence = QTablePersistence()
        self.action_manager = ActionManager()

    def get_action(self, state_manager: StateManager) -> Action:
        """Get the next action based on the current state."""
        # might be uneccessary to update state_manager
        self.state_manager = state_manager
        valid_actions = self.action_manager.get_valid_actions(state_manager)

        action_values = {}
        state_key = self.state_manager.get_state_key()

        # Initialize Q-values for valid actions
        for action in valid_actions:
            assert isinstance(state_key, Tuple)
            assert isinstance(self.q_table, Dict)
            action_str = self.action_manager._action_to_str(action)

            # Only initialize if the state key doesn't exist
            if state_key not in self.q_table:
                # print(f"Initializing new state in Q-table: {state_key}")
                self.q_table[state_key] = {}

            # Only initialize if the action doesn't exist
            if action_str not in self.q_table[state_key]:
                # print(f"Initializing new action in Q-table: {action_str}")
                self.q_table[state_key][action_str] = 0.0

            action_values[action] = self.q_table[state_key][action_str]

        # chance of doing random action decays over time
        if random.random() < self.epsilon:
            chosen_action = random.choice(valid_actions)
        else:
            chosen_action = max(action_values.items(), key=lambda x: x[1])[0]
            print(f"Best action chosen: {chosen_action} with value {action_values[chosen_action]}")

        return chosen_action
    #TODO: this doesn't work without a proper next state.
    def update_q_value(self, state: List[Any], action: Action, reward: float, next_state: List[Any]) -> None:
        """Update Q-value based on the current state, action, reward, and next state."""
        if action is None: # if end of game just return since no next state.
            return

        current_state_key = self.state_manager.get_state_key()
        next_state_key = self.state_manager.get_state_key()
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

    #region helpers

    # Doesn't track liar calls
    def update_opp_bids(self, bid: Tuple[int, int]) -> None:
        """Track opponent bids for learning"""
        if isinstance(bid, tuple) and len(bid) == 2:
            self.epsilon = max(EPSILON, self.epsilon * 0.995)  # Decay exploration rate

    def update_reward(self, reward: float) -> None:
        self.reward = reward

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
