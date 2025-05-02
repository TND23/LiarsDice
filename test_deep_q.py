import torch
import random
import numpy as np
from deep_q_learning import DeepQLearningAgent
from aigame import AIGame
from Managers.ActionManager import ActionManager
from model import StateEncoder
import os
from typing import no_type_check
from const import EPSILON, LEARN_RATE
@no_type_check
def test_agent_initialization():
    """Test that the agent can be initialized and basic functions work."""
    print("Testing agent initialization...")

    # Create cluster manager
    action_manager = ActionManager()
    # Test basic game interaction
    game = AIGame(2, 5, action_manager)
    state = game.game_state
    state_manager = game.state_manager
    player_index = game.IDX

    # Print state tensor size
    state_tensor = StateEncoder.encode_state(state, player_index)
    input_size = state_tensor.size(1)
    print(f"State vs input size: {state_tensor.size() == input_size}")

    # Initialize agent with correct input size
    agent = DeepQLearningAgent(
        input_size=input_size,
        hidden_size=128,
        output_size=100,
        learning_rate=LEARN_RATE,
        gamma=0.99,
        epsilon=EPSILON
    )

    # Test action selection
    action = agent.nnget_action(state_manager, player_index, action_manager)
    # Test memory storage
    agent.remember(state, action, 0.0, state, False, player_index)

    # Test replay
    agent.replay()
    print("Replay completed successfully")

    # Test model saving/loading
    os.makedirs("models/deep_q", exist_ok=True)
    agent.save("models/deep_q/test_model.pt")
    agent.load("models/deep_q/test_model.pt")
    print("Model save/load completed successfully")

    print("All tests passed!")

if __name__ == "__main__":
    # Set random seeds for reproducibility
    torch.manual_seed(42)
    random.seed(42)
    np.random.seed(42)

    test_agent_initialization()
