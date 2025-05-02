import torch
import random
import numpy as np
from typing import List, Tuple
from Managers.StateManager import StateManager
from aigame import AIGame
from GameState import GameState
from Action import Action, ActionType, Bid
from Managers.ActionManager import ActionManager
from model import StateEncoder, LiarsDiceModel, ActionDecoder
from const import CUR_MODEL_PATH


def get_human_action(state_manager: StateManager, action_manager: ActionManager) -> Action:
    """Get action from human player."""
    valid_actions = action_manager.get_valid_actions(state_manager)
    choice = input("\nEnter your action: ")
    if choice == "help":
        print("\nEnter a bet of format 'quantity, face_value' or 'liar'")
        print("Example: 3, 5")
        print("Example: liar")
        return get_human_action(state_manager, action_manager)
    if choice == "liar":
        return Action(ActionType.CALL_LIE)
    else:
        try:
            quantity, face_value = choice.split(",")
            action = Action(ActionType.BID, Bid(int(quantity), int(face_value)))
            if action in valid_actions:
                return action
            else:
                print("Invalid bet. Please make sure your bet is larger than your opponent's.")
                return get_human_action(state_manager, action_manager)
        except ValueError:
            print("Invalid input. Please try again.")
            return get_human_action(state_manager, action_manager)

def display_game_state(game: AIGame, player_index: int):
    """Display the current game state to the human player."""
    print("\n=== Game State ===")
    print(f"Your dice: {game.players[player_index].rolls}")
    print(f"Your dice count: {game.players[player_index].NUMDICE}")
    print(f"Opponent dice count: {game.players[1-player_index].rolls}")


def play_human_vs_ai(model_path: str = CUR_MODEL_PATH):
    """Play a game of Liar's Dice against the AI."""
    torch.manual_seed(42)
    random.seed(42)
    np.random.seed(42)

    # Initialize game components
    action_manager = ActionManager()
    game = AIGame(2, 5, action_manager)  # 2 players, 5 dice each

    # Load the AI model
    state_tensor = StateEncoder.encode_state(game.game_state, 0)
    input_size = state_tensor.size(1)
    model = LiarsDiceModel(input_size, 128, 100)
    model.load(model_path)


    # Start the game
    game.start_round()
    human_player_index = 0  # Human is player 0, AI is player 1
    new_round = True
    while not game.check_game_over():
        if new_round:
            display_game_state(game, human_player_index)
            new_round = False

        if game.IDX == human_player_index:
            print(game.round_history)
            print(game.last_bet)
            # Human's turn
            action = get_human_action(game.state_manager, action_manager)
            game.apply_action(action)
            if action.is_call_liar():
                # After liar call, let the player who was called bid first
                if game.IDX == human_player_index:
                    action = get_human_action(game.state_manager, action_manager)
                    game.apply_action(action)
                new_round = True

        elif game.IDX == 1:
            # AI's turn
            print("======================")
            state_tensor = StateEncoder.encode_state(game.game_state, 1)
            policy = model.get_policy(state_tensor)
            action = ActionDecoder.decode_action(policy, game.state_manager, action_manager)
            game.apply_action(action)
            print(f"\nAI's move: {action}")

            if action.is_call_liar():
                # After liar call, let the player who was called bid first
                if game.IDX == 1:
                    state_tensor = StateEncoder.encode_state(game.game_state, 1)
                    policy = model.get_policy(state_tensor)
                    action = ActionDecoder.decode_action(policy, game.state_manager, action_manager)
                    game.apply_action(action)
                new_round = True

    # Game over
    winner = game.players[0] if game.players[0].NUMDICE > 0 else game.players[1]
    if winner.p_index == human_player_index:
        print("\nCongratulations! You won!")
    else:
        print("\nAI won the game!")

def main():
    print("Welcome to Liar's Dice!")
    print("You will be playing against an AI opponent.")
    print("The game will start with 5 dice each.")

    while True:
        play_human_vs_ai()
        play_again = input("\nWould you like to play again? (y/n): ").lower()
        if play_again != 'y':
            break

    print("Thanks for playing!")

if __name__ == "__main__":
    main()
