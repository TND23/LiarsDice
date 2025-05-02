import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Dict, Any, Optional, no_type_check
from GameState import GameState
from Action import Action, ActionType
from const import *
from Managers.StateManager import StateManager
from Managers.ActionManager import ActionManager
from datetime import datetime
import random
#from state_approximation.approximation_utils import StateApproximation
# neural network parameters
hidden = 10
learn_rate = LEARN_RATE
gamma = 0.8

# Q-networks

class LiarsDicePolicyNetwork(nn.Module):
    """Policy network."""

    def __init__(self, input_size: int, hidden_size: int = 128, output_size: int = 100):
        """
        Initialize policy network.
        output_size is fixed at 100:
        - Indices 0-98: Bid actions (quantity-1) * 6 + (face_value-1)
        - Index 99: Call liar action
        """
        super(LiarsDicePolicyNetwork, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, 100)  # Fixed size of 100

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Ensure input is 2D [batch_size, features]
        if len(x.shape) == 1:
            x = x.unsqueeze(0)

        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        logits = self.fc3(x)

        # Ensure output is 2D [batch_size, num_actions]
        if len(logits.shape) == 1:
            logits = logits.unsqueeze(0)

        return F.softmax(logits, dim=1)

class LiarsDiceValueNetwork(nn.Module):
    """Value network that estimates state values."""

    def __init__(self, input_size: int, hidden_size: int = 128):
        super(LiarsDiceValueNetwork, self).__init__()

        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        # values between -1 and 1
        value = torch.tanh(self.fc3(x))
        return value

class LiarsDiceModel:
    """Model for Liars Dice with both networks."""

    def __init__(self, input_size: int, hidden_size: int = 128, output_size: int = 100):
        self.policy_network = LiarsDicePolicyNetwork(input_size, hidden_size, output_size)
        self.value_network = LiarsDiceValueNetwork(input_size, hidden_size)

    def get_policy(self, state: torch.Tensor) -> torch.Tensor:
        """Get action probabilities for a given state."""
        return self.policy_network(state)

    def get_value(self, state: torch.Tensor) -> float:
        """Get value estimate for a given state."""
        return self.value_network(state).item()

    def save(self, path: str) -> None:
        """Save model"""
        if path == "":
            print("No path provided for saving Liars Dice model - creating default.")
            path = f"models/_{datetime.now().strftime('%Y%m%d_%H%M%S')}/"
        torch.save({
            'policy_state_dict': self.policy_network.state_dict(),
            'value_state_dict': self.value_network.state_dict()
        }, path)

    def load(self, path: str) -> None:
        """Load model from path"""
        checkpoint = torch.load(path)
        self.policy_network.load_state_dict(checkpoint['policy_state_dict'])
        self.value_network.load_state_dict(checkpoint['value_state_dict'])

class AveragePolicyNetwork:
    """averages outputs of multiple policy networks."""

    def __init__(self, input_size: int, hidden_size: int = 128, output_size: int = 100):
        self.models: List[LiarsDiceModel] = []
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size

    def add_model(self, model: Optional[LiarsDiceModel] = None) -> None:
        """Add a model"""
        if model is None:
            print("No model provided - creating new one.")
            model = LiarsDiceModel(self.input_size, self.hidden_size, self.output_size)
        self.models.append(model)

    def remove_model(self, index: int) -> None:
        """Remove a model at index"""
        if 0 <= index < len(self.models):
            self.models.pop(index)

    def save_models(self, base_path: str) -> None:
        """Save all models in base_path"""
        for i, model in enumerate(self.models):
            model.save(f"{base_path}_model_{i}.pt")

    def load_models(self, base_path: str, count: int) -> None:
        """Load models"""
        self.models = []
        for i in range(count):
            model = LiarsDiceModel(self.input_size, self.hidden_size, self.output_size)
            model.load(f"{base_path}_model_{i}.pt")
            self.models.append(model)
#TODO: incorporate this into StateManager (?)
class StateEncoder:
    """Encodes game state into a tensor for neural network input."""
    @staticmethod
    def encode_state(game_state: GameState, player_index: int) -> torch.Tensor:
        """Convert game state to tensor representation."""
        pub_state = game_state.to_public_state()

        input_vector = []
        vector_PLAYERS = 1
        vector_MOST_FREQ_OPP_BID = 1
        vector_LAST_BID = 2
        vector_HANDS = MAX_DICE_COUNTS * MAX_PLAYERS # Maximum possible dice across all players

        # Calculate total size needed
        total_size = (
            vector_PLAYERS +
            vector_MOST_FREQ_OPP_BID + vector_LAST_BID + vector_HANDS# Player index and dice count
        )

        # ensure component is expected size
        def pad_component(component, max_size, component_descr=""):
            padded = []
            if not isinstance(component, list):
                component = [component]
            if len(component) > max_size:
                padded.extend(component)
            while len(padded) < max_size:
                padded.append(0)
            return padded

        # Add current player index and dice count
        input_vector.append(player_index)

        # Encode hands
        hands = game_state.hands if game_state.hands else []
        flat_hands = []
        for hand in hands:
            flat_hands.extend(hand)
        weight = FEATURE_WEIGHTS['HANDS']
        weighted_data = [val * weight for val in flat_hands]
        input_vector.extend(pad_component(weighted_data, vector_HANDS, "HANDS"))


        # Encode most frequent opponent bid
        MOST_FREQ_OPP_BID = pub_state[STATE_COMPONENTS['MOST_FREQ_OPP_BID']]
        weight = FEATURE_WEIGHTS['MOST_FREQ_OPP_BID']
        weighted_data = weight * MOST_FREQ_OPP_BID
        input_vector.extend(pad_component(weighted_data, vector_MOST_FREQ_OPP_BID, "MOST FREQ OPP BID"))

        # Encode last bid
        if pub_state[STATE_COMPONENTS['LAST_BID']] is not None:
            if pub_state[STATE_COMPONENTS['LAST_BID']][0] is not None:
                last_bid = pub_state[STATE_COMPONENTS['LAST_BID']]
                weight = FEATURE_WEIGHTS['LAST_BID']
                quantity, face_val = last_bid
                weighted_data = [quantity * weight, face_val * weight]
        else:
            weighted_data = [0] * vector_LAST_BID
        input_vector.extend(pad_component(weighted_data, vector_LAST_BID, "LAST BID"))


        assert len(input_vector) == total_size, f"Expected size {total_size}, got {len(input_vector)}"

        return torch.tensor(input_vector, dtype=torch.float32).unsqueeze(0)

class ActionDecoder:
    """Decodes neural network outputs into game actions."""
    @no_type_check
    @staticmethod
    def decode_action(action_probs: torch.Tensor, state_manager: StateManager, action_manager: ActionManager) -> Action:
        """Convert action probabilities to a game action."""
        valid_actions = action_manager.get_valid_actions(state_manager)

        if not valid_actions:
            return Action.call_liar()
        if random.random() < action_manager.random_liar_prob and len(valid_actions) > 1:
            return Action.call_liar()
        # Get the model's hand from the state
        game_state = state_manager.get_game_state()
        model_hand = game_state.get_model_hand() if game_state else tuple()

        # Create action mapping and filter based on model's hand
        action_map = {}
        for i, action in enumerate(valid_actions):
            # For bid actions, check if the model has the face value in their hand
            if action.type == ActionType.BID:
                bid = action.bid
                face_value = bid.face_value
                if face_value in model_hand:
                    # Map the action to a valid index within the policy network's output size
                    action_idx = (bid.quantity - 1) * 6 + (bid.face_value - 1)
                    if action_idx < 99:  # Reserve index 99 for "call liar"
                        action_map[action_idx] = action
            else:  # For non-bid actions (like calling liar), use last index
                action_map[99] = action  # Use last index for "call liar"

        if not action_map:
            return Action.call_liar()

        # Get probabilities for valid actions only
        valid_indices = list(action_map.keys())

        # Ensure action_probs is 2D [batch_size, num_actions]
        if len(action_probs.shape) == 1:
            action_probs = action_probs.unsqueeze(0)

        # Get probabilities for valid actions
        valid_probs = action_probs[0, valid_indices]

        # Select action with highest probability among valid actions
        best_idx = valid_indices[torch.argmax(valid_probs).item()]
        return action_map[best_idx]

