import torch
import random
import numpy as np
from typing import List, Tuple, Optional
from Managers.StateManager import StateManager
from deep_q_learning import DeepQLearningAgent
from aigame import AIGame
from Managers.ActionManager import ActionManager
from model import StateEncoder
from const import CUR_Q_TABLE_NAME, LEARN_RATE

from const import EPSILON
def train_deep_q(agent: DeepQLearningAgent, num_episodes: int, opponent: Optional[DeepQLearningAgent] = None, q_table_name=CUR_Q_TABLE_NAME) -> Tuple[List[float], List[float]]:
    """Train the deep Q-learning agent."""
    total_rewards = []
    win_rates = []
    action_manager = ActionManager()
    last_qtable = {}
    for episode in range(num_episodes):
        try:
            # Create a new game
            game = AIGame(2, 5, action_manager)  # 2 players, 5 dice each
            # Initialize hands before starting the episode
            game.reset_hands()
            episode_rewards = [0.0] * len(game.players)
            done = False
            state_man = game.state_manager
            if last_qtable:
                game.players[0].q_table = last_qtable
            while not done:
                # train on batch
                current_state = game.state_manager.get_game_state()
                if not current_state.hands:
                    print("Warning: No hands in current state!")
                    game.reset_hands()
                    current_state = game.state_manager.get_game_state()

                hand = current_state.hands[current_state.current_player]
                current_player_idx = game.IDX
                action = agent.nnget_action(state_man, current_player_idx, action_manager)
                prev_state = current_state
                game.step()
                next_state = game.state_manager.get_next_state(action)

                # Calculate reward
                reward = 0.0
                if game.check_game_over():
                    last_qtable = game.players[0].q_table
                    done = True
                    winner_idx = game.players[0].p_index
                    if current_player_idx == winner_idx:
                        reward = 1.0
                    else:
                        reward = -1.0

                # Store experience
                agent.remember(
                    prev_state,
                    action,
                    reward,
                    next_state,
                    done,
                    current_player_idx,
                    hand
                )

                # Update episode rewards
                episode_rewards[current_player_idx] += reward
                agent.replay()

                # Update target network periodically
                if game.round_number % 100 == 0:
                    agent.update_target_model()
            # Calculate win rate
            total_rewards.append(sum(episode_rewards))
            win_rate = sum(1 for r in episode_rewards if r > 0) / len(episode_rewards)
            win_rates.append(win_rate)

            # Print progress and save Q-table
            if (episode + 1) % 10 == 0:
                agent.save_qtable(last_qtable, q_table_name)
                print(f"Episode {episode+1}/{num_episodes}")
                print(f"Average reward: {sum(total_rewards[-10:])/10:.2f}")
                print(f"Win rate: {sum(win_rates[-10:])/10:.2%}")
                print(f"Memory size: {len(agent.memory)}")

        except Exception as e:
            print(f"Error in episode {episode}: {str(e)}")
            continue

    # Save final Q-table
    agent.save_qtable(last_qtable, q_table_name)
    return total_rewards, win_rates


def evaluate_against_agent(agent: DeepQLearningAgent, opponent: Optional[DeepQLearningAgent] = None, num_games: int = 2) -> float:
    """Evaluate the agent against another agent."""
    if opponent is None:
        return 0.0
    # TODO: Implement evaluation against another agent
    return 0.0

def evaluate_agent(agent: DeepQLearningAgent, num_games: int = 5) -> float:
    """Evaluate the agent against a random policy."""
    wins = 0
    action_manager = ActionManager()
    last_q_table = {}
    for _ in range(num_games):
        game = AIGame(2, 5, action_manager)  # 2 players, 5 dice each
        game.start_round()
        if last_q_table != {}:
            # utilize the last q table if available
            game.players[0].q_table = last_q_table
        done = False
        state_manager = game.state_manager
        assert isinstance(state_manager, StateManager)
        while not done:
            if game.IDX == 0:  # Agent's turn
                action = agent.nnget_action(state_manager, 0, action_manager)
                if action:
                    game.apply_action(action)
                else:
                    game.step()
            else:  # Random policy's turn
                valid_actions = action_manager.get_valid_actions(state_manager)
                action = random.choice(valid_actions)
                game.step()

            done = game.check_game_over()
        last_q_table = game.players[0].q_table
        if game.players[0].p_index == 0:  # Agent won
            wins += 1

    return wins / num_games

def main():
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
        learning_rate=LEARN_RATE,
        gamma=0.99,
        epsilon=EPSILON
    )

    print("Training deep Q-learning agent...")
    total_rewards, win_rates = train_deep_q(agent, num_episodes=500)

    # Evaluate final agent
    print("\nEvaluating final agent...")
    win_rate = evaluate_agent(agent)
    print(f"Final win rate against random policy: {win_rate:.2%}")

    # Save final model
    agent.save("models/deep_q/final_model.pt")
    print("\nTraining complete!")

if __name__ == "__main__":
    main()
