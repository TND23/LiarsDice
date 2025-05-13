import torch
import random
import numpy as np
from typing import List, Tuple, Optional
from Managers.StateManager import StateManager
from deep_q_learning import DeepQLearningAgent
from aigame import AIGame
from Managers.ActionManager import ActionManager
from model import StateEncoder
from const import CUR_MODEL_NAME, CUR_MODEL_PATH, CUR_Q_TABLE_NAME, LEARN_RATE

from const import EPSILON
def train_deep_q(agent: DeepQLearningAgent, num_episodes: int, opponent: Optional[DeepQLearningAgent] = None, q_table_name=CUR_Q_TABLE_NAME) -> Tuple[List[float], List[float]]:
    """Train the deep Q-learning agent."""
    total_rewards = []
    win_rates = []
    action_manager = ActionManager()

    for episode in range(num_episodes):
        try:
            # Create a new game
            game = AIGame(2, 5, action_manager)
            game.reset_hands()
            episode_rewards = [0.0] * len(game.players)
            done = False
            state_man = game.state_manager
            reward = 0.0

            # Use the agent's cached Q-table
            game.players[0].q_table = agent.q_table_cache
            while not done:
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
                reward = game.players[0].reward
                # Calculate reward
                if game.check_game_over():
                    done = True
                    winner_idx = game.players[0].p_index
                    if current_player_idx == winner_idx:
                        reward = 10 + game.players[winner_idx].reward
                    else:
                        reward = -10 + game.players[winner_idx].reward

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

                # Update episode rewards and replay
                episode_rewards[current_player_idx] += reward
                #action_manager.decay_random_liar_prob()
                agent.replay()
                agent.learning_rate = get_learning_rate(episode, agent.learning_rate)
                agent.epsilon = get_epsilon(episode, agent.epsilon)
                # Update target network periodically
                if game.round_number % 100 == 0:
                    agent.update_target_model()

            # Calculate win rate
            total_rewards.append(sum(episode_rewards))
            win_rate = sum(1 for r in episode_rewards if r > 0) / len(episode_rewards)
            win_rates.append(win_rate)

            # Save progress periodically
            agent.save_if_needed(episode)

            # Print progress
            if (episode + 1) % 100 == 0:
                print(f"Episode {episode+1}/{num_episodes}")
                print(f"Average reward: {sum(total_rewards[-100:])/100:.2f}")
                print(f"Win rate: {sum(win_rates[-100:])/100:.2%}")
                print(f"Memory size: {len(agent.memory)}")
                print(f"Q-table size: {len(agent.q_table_cache)}")

        except Exception as e:
            print(f"Error in episode {episode}: {str(e)}")
            print(game.state_manager.get_game_state())
            breakpoint()
            continue

    # Save final Q-table
    agent.save_qtable(agent.q_table_cache, q_table_name)
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

def get_learning_rate(episode: int, initial_lr: float = 0.01) -> float:
    """Decay learning rate over time"""
    return initial_lr * (1.0 / (1.0 + 0.0001 * episode))

def get_epsilon(episode: int, initial_epsilon: float = 0.3) -> float:
    """Decay epsilon over time"""
    return max(0.01, initial_epsilon * (1.0 / (1.0 + 0.0001 * episode)))


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
        gamma=0.95,
        epsilon=EPSILON
    )

    print("Training deep Q-learning agent...")
    total_rewards, win_rates = train_deep_q(agent, num_episodes=10000)

    # Evaluate final agent
    print("\nEvaluating final agent...")
    win_rate = evaluate_agent(agent)
    print(f"Final win rate against random policy: {win_rate:.2%}")

    # Save final model
    agent.save_qtable(agent.q_table_cache, CUR_MODEL_NAME)
    agent.save(CUR_MODEL_PATH)
    print("\nTraining complete!")

def write_rewards_win_rates(rewards: List[float], model_name: str, win_rates: List[float], file_path: str):
    """Write the rewards and win rates to a file."""
    with open(file_path, "a") as f:
        f.write(f"{model_name},{sum(rewards)/len(rewards)},{sum(win_rates)/len(win_rates)}\n")

if __name__ == "__main__":
    main()
