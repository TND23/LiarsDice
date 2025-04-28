import torch
from typing import List, Tuple, Dict, Any
from collections import deque
import random
import os
from Managers.StateManager import StateManager
from model import LiarsDiceModel, StateEncoder, ActionDecoder
from Robot.qtable_persistence import QTablePersistence
from GameState import GameState
from Action import Action
from const import EPSILON, CUR_Q_TABLE_NAME, LEARN_RATE, MEMORY_SIZE, STATE_COMPONENTS
from Managers.ActionManager import ActionManager
class DeepQLearningAgent:
    """Agent that combines Q-learning with neural networks for deep Q-learning."""
    # TODO: consider adding parameters to constants.
    def __init__(self,
                 input_size: int = 20,
                 hidden_size: int = 128,
                 output_size: int = 100,
                 learning_rate: float = LEARN_RATE,
                 gamma: float = 0.99,
                 epsilon: float = EPSILON,
                 memory_size: int = MEMORY_SIZE,
                 batch_size: int = 64,
                 q_table_path: str = "./data/q_tables"):

        os.makedirs(q_table_path, exist_ok=True)
        os.makedirs("models/deep_q", exist_ok=True)

        self.model = LiarsDiceModel(input_size, hidden_size, output_size)
        self.target_model = LiarsDiceModel(input_size, hidden_size, output_size)
        # Initialize target model with same weights
        self.target_model.policy_network.load_state_dict(self.model.policy_network.state_dict())
        self.target_model.value_network.load_state_dict(self.model.value_network.state_dict())

        self.q_table_persistence = QTablePersistence(q_table_path)
        self.memory = deque(maxlen=memory_size)
        self.batch_size = batch_size
        self.gamma = gamma
        self.epsilon = epsilon
        self.learning_rate = learning_rate
        self.action_manager = ActionManager()

        self.optimizer = torch.optim.Adam(
            list(self.model.policy_network.parameters()) +
            list(self.model.value_network.parameters()),
            lr=learning_rate
        )
        self.criterion = torch.nn.MSELoss() # Mean Squared Error Loss

    # named to avoid confusion with AI.get_action
    def nnget_action(self, state_man: StateManager, player_index: int, action_manager: ActionManager) -> Action:
        """Get action using epsilon-greedy policy."""
        state = state_man.get_game_state()
        if random.random() < self.epsilon:
            valid_actions = action_manager.get_valid_actions(state_man)
            return random.choice(valid_actions)

        # Get Q-values from both neural network and Q-table
        state_tensor = StateEncoder.encode_state(state, player_index)
        nn_q_values = self.model.get_policy(state_tensor)

        state_key = self._state_to_key(state, player_index)
        try:
            table_q_values = self.q_table_persistence.load_q_table(CUR_Q_TABLE_NAME)
        except FileNotFoundError:
            table_q_values = {}
            print("Couldn't find q-table: using empty values.")
        # pass in sstate_key
        # TODO: improve validation for q_values tensor-ability, consider updating weights.
        if state_key in table_q_values:
            table_values = torch.tensor(list(table_q_values[state_key].values()))
            combined_q_values = (nn_q_values + table_values) / 2
        else:
            # Otherwise, find the closest cluster (the state in the q_table with a known value)
            #
            combined_q_values = nn_q_values

        return ActionDecoder.decode_action(combined_q_values, state_man, action_manager)
    # see https://deeplizard.com/learn/video/Bcuj2fTH4_4 for definition of experience / memory
    # TODO: implement next_state (this isn't called until then)
    def remember(self, state: GameState, action: Action, reward: float,
                next_state: GameState, done: bool, player_index: int, hand: Tuple[int] = (0,)):
        """Store experience in replay memory."""

        self.memory.append((
            state,
            action,
            reward,
            next_state,
            done,
            player_index,
            hand
        ))

    # TODO: implement next_state
    def replay(self):
        """Train on a batch of experiences."""
        if len(self.memory) < self.batch_size:
            return

        batch = random.sample(self.memory, self.batch_size)
        states, actions, rewards, next_states, dones, player_indices, hands = zip(*batch)

        state_tensors = []
        next_state_tensors = []
        for state, next_state, player_idx in zip(states, next_states, player_indices):
            state_tensors.append(StateEncoder.encode_state(state, player_idx))
            next_state_tensors.append(StateEncoder.encode_state(next_state, player_idx))

        states = torch.stack(state_tensors, dim=0) # add current state tensors
        next_states = torch.stack(next_state_tensors, dim=0) # add next_state_tensors
        rewards = torch.tensor(rewards, dtype=torch.float32, requires_grad=True).unsqueeze(dim=1)
        dones = torch.tensor(dones, dtype=torch.float32, requires_grad=True).unsqueeze(dim=1) # These are always False/0 right now
        current_q_values = self.model.get_policy(states)

        with torch.no_grad():
            next_q_values = self.target_model.get_policy(next_states)
            max_next_q_values = torch.max(next_q_values, dim=1)[0].unsqueeze(dim=1)
            target_q_values = rewards.unsqueeze(dim=1) + (1+dones.unsqueeze(dim=1)) * self.gamma * max_next_q_values

        self.optimizer.zero_grad()
        loss = self.criterion(current_q_values, target_q_values) # Mean Squared Error Loss
        loss.backward()
        self.optimizer.step()
    # add model as params?
    def update_target_model(self):
        """Update target network weights."""
        self.target_model.policy_network.load_state_dict(self.model.policy_network.state_dict())
        self.target_model.value_network.load_state_dict(self.model.value_network.state_dict())

    def save(self, path: str):
        """Save model and Q-table."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.model.save(path)
        try:
            q_table = self.q_table_persistence.load_q_table(CUR_Q_TABLE_NAME)
            self.q_table_persistence.save_q_table(q_table, CUR_Q_TABLE_NAME)
        except FileNotFoundError:
            pass

    def save_qtable(self, q_table: Dict[Tuple, Dict[str, float]], name: str):
        """Save Q-table to disk."""
        if not q_table:
            print("Warning: Attempting to save empty Q-table")
            return

        # Convert state keys to proper format
        formatted_q_table = {}
        for state_key, actions in q_table.items():
            if not isinstance(state_key, tuple) or len(state_key) != 4: #len(STATE_COMPONENTS)-1
                print(f"Warning: Invalid state key format: {state_key}")
                continue
            formatted_q_table[state_key] = actions

        self.q_table_persistence.save_q_table(formatted_q_table, name)

    def load(self, path: str):
        """Load model and Q-table."""
        self.model.load(path)
        try:
            self.q_table_persistence.load_q_table(CUR_Q_TABLE_NAME)
        except FileNotFoundError:
            pass
    #TODO: move to StateManager? Need to improve cluster centers.
    #This is about the only fnc that still uses GameState instead of StateManager.
    def _state_to_key(self, state: GameState, player_index: int) -> Tuple:
        """Convert game state to Q-table key format."""
        pub_state = state.to_public_state()

        current_player = player_index
        hands = tuple(tuple(hand) for hand in state.hands) if state.hands else tuple()
        most_freq_opp_face = pub_state[STATE_COMPONENTS['MOST_FREQ_OPP_BID']]
        last_bid = pub_state[STATE_COMPONENTS['LAST_BID']]

        state_key = (current_player, hands, most_freq_opp_face, last_bid)
        if len(state_key) != 4:
            raise ValueError(f"Invalid state key length: {len(state_key)}")
        return state_key
