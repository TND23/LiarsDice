import torch
from model import LiarsDiceModel, StateEncoder
from Action import Action
from typing import List, Tuple, no_type_check
import torch.nn.functional as F
from GameState import GameState
from const import MAX_FACE_VALUE

#TODO: Increase epochs
#TODO: If we just play the game N times, once per epoch, there is a good chance that there won't be
# a representative distribution of hands...
def train_model(model: LiarsDiceModel,
                states: List[torch.Tensor],
                actions: List[torch.Tensor],
                rewards: List[float],
                learning_rate: float = 0.001,
                epochs: int = 10) -> None:
    """Train a model on collected game data."""
    policy_optimizer = torch.optim.Adam(model.policy_network.parameters(), lr=learning_rate)
    value_optimizer = torch.optim.Adam(model.value_network.parameters(), lr=learning_rate)

    # Stack all states and actions
    states_tensor = torch.cat(states)
    actions_tensor = torch.cat(actions)
    rewards_tensor = torch.tensor(rewards, dtype=torch.float32).unsqueeze(1)

    for epoch in range(epochs):
        policy_optimizer.zero_grad()
        value_optimizer.zero_grad()

        policy_outputs = model.policy_network(states_tensor)
        policy_loss = F.cross_entropy(policy_outputs, actions_tensor)

        value_outputs = model.value_network(states_tensor)
        value_loss = F.mse_loss(value_outputs, rewards_tensor)

        total_loss = policy_loss + value_loss
        total_loss.backward()

        policy_optimizer.step()
        value_optimizer.step()

        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss.item():.4f}")

@no_type_check
def collect_training_data(game_states: List[GameState],
                         actions: List[Action],
                         rewards: List[float],
                         player_index: int) -> Tuple[List[torch.Tensor], List[torch.Tensor], List[float]]:
    """Convert game data to training tensors."""
    state_tensors = [StateEncoder.encode_state(state, player_index) for state in game_states]

    # Convert actions to one-hot vectors
    action_tensors = []
    for action in actions:
        if action.is_bid():
            # Create a one-hot vector for bid actions
            action_idx = (action.bid.quantity - 1) * MAX_FACE_VALUE + (action.bid.face_value - 1)
            action_tensor = torch.zeros(100)
            action_tensor[action_idx] = 1
        else:
            # Call liar action
            action_tensor = torch.zeros(100)
            action_tensor[-1] = 1  # Last index for call liar

        # Ensure consistent dimensions
        action_tensor = action_tensor.unsqueeze(0)
        action_tensors.append(action_tensor)

    return state_tensors, action_tensors, rewards
