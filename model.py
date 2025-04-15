import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import os
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from GameState import GameState
from Action import Action, ActionType, Bid
from const import *
from Managers.StateManager import StateManager
from Managers.ActionManager import ActionManager
from datetime import datetime
# neural network parameters
hidden = 10
learn_rate = 0.001
gamma = 0.99


# f(state) -> {distribution of actions}
class LiarsDicePolicyNetwork(nn.Module):
    """Policy network."""

    def __init__(self, input_size: int, hidden_size: int = 128, output_size: int = 100):
        super(LiarsDicePolicyNetwork, self).__init__()
        # fully connected layers
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, output_size)

    # x = game state
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        logits = self.fc3(x)
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
        #print(checkpoint)
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
        #TODO: refactor this back now that debugging complete
        input_vector = []
        vector_BET = (MAX_BET_HISTORY * 2 + 1)
        vector_PLAYERS = MAX_PLAYERS + 1
        vector_ACTIONS = MAX_ACTIONS + 1
        vector_DICE = MAX_DICE_COUNTS + 1
        vector_CLUSTER = MAX_CLUSTER_INFO + 1
        vector_LAST_BID = MAX_LAST_BID + 1
        # Calculate total size needed
        total_size = (
            vector_BET + vector_PLAYERS + vector_ACTIONS + vector_DICE + vector_CLUSTER + vector_LAST_BID + 2                            # Player index and dice count
        )

        # ensure component is expected size
        def pad_component(component, max_size, component_descr=""):
            if not isinstance(component, list):
                component = [component]
            if len(component) > max_size:
            padded = [len(component)]
            padded.extend(component)
            while len(padded) < max_size:
                padded.append(0)
            return padded


        bet_history = [item for sublist in pub_state[STATE_COMPONENTS['BET_HISTORY']] for item in sublist]
        # handle overly long bet histories if len(bet)
        if len(bet_history) > vector_BET:
            overlong_amt = len(bet_history) - (MAX_BET_HISTORY * 2 + 1)
            bet_history = bet_history[0:-overlong_amt-1]

        input_vector.extend(pad_component(bet_history, MAX_BET_HISTORY * 2 + 1, "BET_HISTORY"))
        # Player info

        player_info = pub_state[STATE_COMPONENTS['PLAYER_INFO']]
        input_vector.extend(pad_component(player_info, MAX_PLAYERS + 1, "PLAYER INFO"))

        # Last action

        last_action = pub_state[STATE_COMPONENTS['LAST_ACTION']]
        input_vector.extend(pad_component(last_action, MAX_ACTIONS + 1, "LAST ACTION"))

        # Dice counts
        dice_counts = pub_state[STATE_COMPONENTS['DICE_COUNTS']]
        input_vector.extend(pad_component(dice_counts, MAX_DICE_COUNTS + 1, "DICE COUNTS"))

        # Cluster info
        cluster_info = pub_state[STATE_COMPONENTS['CLUSTER_INFO']]
        input_vector.extend(pad_component(cluster_info, MAX_CLUSTER_INFO + 1, "CLUSTER INFO"))

        # Last bid
        last_bid = pub_state[STATE_COMPONENTS['LAST_BID']]
        input_vector.extend(pad_component(last_bid, MAX_LAST_BID + 1, "LAST BID"))

        # Add current player index and dice count
        input_vector.append(player_index)
        input_vector.append(game_state.player_dice_counts[player_index])

        # Ensure final size matches expected
        assert len(input_vector) == total_size, f"Expected size {total_size}, got {len(input_vector)}"

        return torch.tensor(input_vector, dtype=torch.float32).unsqueeze(0)

class ActionDecoder:
    """Decodes neural network outputs into game actions."""

    @staticmethod
    def decode_action(action_probs: torch.Tensor, state_manager: StateManager, action_manager: ActionManager) -> Action:
        """Convert action probabilities to a game action."""
        valid_actions = action_manager.get_valid_actions(state_manager)

        if not valid_actions:
            return Action.call_liar()

        action_map = {i: action for i, action in enumerate(valid_actions)}
        action_idx = torch.argmax(action_probs).item()

        # TODO: Should pick next best valid action eventually
        # If the selected action is not valid, choose the first valid action
        if action_idx >= len(valid_actions):
            print(f"Selected action {action_idx} is not valid - choosing first valid action.")
            return valid_actions[0]

        return action_map[action_idx]

