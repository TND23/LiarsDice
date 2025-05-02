import stat
import torch
import random
import numpy as np
from typing import List, Tuple
from Managers.StateManager import StateManager
from deep_q_learning import DeepQLearningAgent
from aigame import AIGame
from GameState import GameState
from Action import Action
from Managers.ActionManager import ActionManager
from model import StateEncoder
import os
import time
from const import EPSILON, CUR_MODEL_PATH
def main():
    # Set random seeds for reproducibility
    torch.manual_seed(42)
    random.seed(42)
    np.random.seed(42)

    # Create a temporary game to get the correct input size
    action_manager = ActionManager()
    game = AIGame(2, 5, action_manager)
    state_tensor = StateEncoder.encode_state(game.game_state, 0)
    input_size = state_tensor.size(1)

    # Initialize agent with correct input size
    agent = DeepQLearningAgent(
        input_size=input_size,
        hidden_size=128,
        output_size=100,
        learning_rate=0.001,
        gamma=0.99,
        epsilon=EPSILON
    )

    tbl = agent.load(CUR_MODEL_PATH)
    print(tbl)

if __name__ == "__main__":
    main()
