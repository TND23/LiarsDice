import torch
from typing import List, Tuple, Dict, Any, Optional
from collections import deque
import random
import os
from Managers.StateManager import StateManager
from model import LiarsDiceModel, StateEncoder, ActionDecoder
from Robot.qtable_persistence import QTablePersistence
from GameState import GameState
from Action import Action
from const import EPSILON, CUR_Q_TABLE_NAME, LEARN_RATE, MAX_DICE_COUNTS, MAX_PLAYERS, MEMORY_SIZE, STATE_COMPONENTS, BATCH_SIZE
from Managers.ActionManager import ActionManager

class DeepQLearningAgent:
    """Agent that combines Q-learning with neural networks for deep Q-learning."""
    def __init__(self,
                 input_size: int = 20,
                 hidden_size: int = 128,
                 output_size: int = 100,
                 learning_rate: float = LEARN_RATE,
                 gamma: float = 0.99,
                 epsilon: float = EPSILON,
                 memory_size: int = MEMORY_SIZE,
                 batch_size: int = BATCH_SIZE,
                 q_table_path: str = "./data/q_tables",
                 model_name: Optional[str] = None):

        os.makedirs(q_table_path, exist_ok=True)
        os.makedirs("models/deep_q", exist_ok=True)

        self.model = LiarsDiceModel(input_size, hidden_size, output_size)
        self.target_model = LiarsDiceModel(input_size, hidden_size, output_size)
        # Initialize target model with same weights
        self.target_model.policy_network.load_state_dict(self.model.policy_network.state_dict())
        self.target_model.value_network.load_state_dict(self.model.value_network.state_dict())

        self.q_table_persistence = QTablePersistence(q_table_path)
        self.model_name = model_name if model_name is not None else f"model_{int(random.random() * 10000)}"

        # Add Q-table caching
        self.q_table_cache = {}  # In-memory cache
        self.q_table_dirty = False  # Track if cache has unsaved changes
        self.last_save_episode = 0  # Track when we last saved
        self.save_frequency = 50

        # Try to load existing Q-table into cache
        # Remove this for the factor effectiveness tests
        self.q_table_cache = {}
        try:
            self.q_table_cache = self.q_table_persistence.load_q_table(CUR_Q_TABLE_NAME)
            print(f"Loaded Q-table with {len(self.q_table_cache)} states")
        except FileNotFoundError:
            print("No existing Q-table found, starting fresh")

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
        self.criterion = torch.nn.MSELoss()

    def save(self, path: Optional[str] = None) -> None:
        """Save the model to disk."""
        save_path = path if path is not None else f"models/deep_q/{self.model_name}.pt"
        self.model.save(save_path)
        print(f"Saved model to {save_path}")

    def load(self, path: Optional[str] = None) -> None:
        """Load the model from disk."""
        load_path = path if path is not None else f"models/deep_q/{self.model_name}.pt"
        self.model.load(load_path)
        print(f"Loaded model from {load_path}")

    def save_qtable(self, q_table: Dict, table_id: str) -> None:
        """Save Q-table to disk."""
        self.q_table_persistence.save_q_table(q_table, table_id)
        self.q_table_dirty = False

    def load_qtable(self, table_id: str) -> Dict:
        """Load Q-table from disk."""
        return self.q_table_persistence.load_q_table(table_id)

    # named to avoid confusion with AI.get_action
    # now with more cacheing
    def nnget_action(self, state_man: StateManager, player_index: int, action_manager: ActionManager) -> Action:
        """Get action using epsilon-greedy policy."""
        assert isinstance(state_man, StateManager)
        state = state_man.get_game_state()
        if random.random() < self.epsilon:
            valid_actions = action_manager.get_valid_actions(state_man)
            return random.choice(valid_actions)
        # Get Q-values from both neural network and Q-table
        state_tensor = StateEncoder.encode_state(state, player_index)
        nn_q_values = self.model.get_policy(state_tensor)

        state_key = self._state_to_key(state, player_index)

        # Use cached Q-table values instead of loading from disk
        table_values = None
        if state_key in self.q_table_cache:
            table_values = torch.tensor(list(self.q_table_cache[state_key].values()))

            # Pad table_values to match nn_q_values shape if needed
            if table_values.shape != nn_q_values.shape:
                fill_value = 0
                if nn_q_values.shape[1] > table_values.shape[0]:
                    padded_list = [fill_value] * (nn_q_values.shape[1] - table_values.shape[0])
                    table_values = torch.tensor(table_values.tolist() + padded_list)

            combined_q_values = (nn_q_values + table_values) / 2
        else:
            combined_q_values = nn_q_values
        return ActionDecoder.decode_action(combined_q_values, state_man, action_manager)

    # see https://deeplizard.com/learn/video/Bcuj2fTH4_4 for definition of experience / memory
    # TODO: implement next_state (this isn't called until then)
    def remember(self, state: GameState, action: Action, reward: float,
                next_state: GameState, done: bool, player_index: int, hand: Tuple[int] = (0,)):
        """Store experience in replay memory."""
        try:
            state_tensor = StateEncoder.encode_state(state, player_index)
            next_state_tensor = StateEncoder.encode_state(next_state, player_index)
            if  state_tensor.size(1) != next_state_tensor.size(1):
                print(f"State tensor size: {state_tensor.size(1)}, Next state tensor size: {next_state_tensor.size(1)}")
                return
            self.memory.append((
                state,
                action,
                reward,
                next_state,
                done,
                player_index,
                hand
            ))

        except Exception as e:
            print(f"Error encoding state: {e}")
            return


    # TODO: implement next_state
    def replay(self):

        """Train on a batch of experiences."""
        if len(self.memory) < 1000:
            return
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

    def update_q_value(self, state_key: Tuple, action: Action, value: float) -> None:
        """Update a Q-value in the cache."""
        if state_key not in self.q_table_cache:
            self.q_table_cache[state_key] = {}

        action_str = self.action_manager._action_to_str(action)
        self.q_table_cache[state_key][action_str] = value
        self.q_table_dirty = True

    def save_if_needed(self, current_episode: int) -> None:
        """Save Q-table to disk if enough episodes have passed since last save."""
        if not self.q_table_dirty:
            return

        if current_episode - self.last_save_episode >= self.save_frequency:
            self.save_qtable(self.q_table_cache, CUR_Q_TABLE_NAME)
            self.last_save_episode = current_episode
            self.q_table_dirty = False
            print(f"Saved Q-table with {len(self.q_table_cache)} states")

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
