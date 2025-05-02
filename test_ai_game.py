from Managers.ActionManager import ActionManager
from aigame import AIGame
from typing import no_type_check

def print_start_of_round_state(game: AIGame) -> None:
    """Print the current game state."""
    print("\nGame State:")

    print("\nPlayers:")
    for player in game.players:
        if player == game.active_player:
            print(f"* {player.name}: {player.NUMDICE} dice - {player.rolls}")
        else:
            print(f"  {player.name}: {player.NUMDICE} dice - {player.rolls}")
@no_type_check
def print_game_state(game: AIGame) -> None:
    """Print the current game state."""
    if game.last_bet():
        print(f"\nLast bid: quantity={game.last_bet()[0]}, face_value={game.last_bet()[1]}")
    print()
@no_type_check
def test_ai_game():
    """Test that AIs can play the game correctly."""
    print("Starting AI game test...")
    action_manager = ActionManager()
    # Create a game with 2 players, 5 dice each
    game = AIGame(2, 5, action_manager)
    #this_table = game.active_player.load_q_table("King")
    #print(f"Loaded Q-table with {len(this_table)} states")
    print(f"Created game with {game.player_ct} players, {game.dice_per} dice each")

    # Start a round
    game.start_round()
    print("\nStarted a new round")

    # Play a few turns
    max_turns = 500
    turn = 0

    while not game.check_game_over() and turn < max_turns:
        print(f"\n=== Turn {turn + 1} ===")
        # Add a method to output the full game state history and actions taken to file
        print_game_state(game)

        try:
            # Get and apply an action
            action = game.step()
            print(f"Action taken: {action}")
            if game.game_over:

                break
            # If it was a call liar, show the outcome and start a new round
            if action.is_call_liar():
                print("\nCall liar detected!")
                if game.last_bet():
                    last_bid = game.last_bet()
                    dt = game._dice_totals()
                    actual_count = dt.get(last_bid[1], 0)
                    print(f"Last bid was: {last_bid[0]} {last_bid[1]}s")
                    print(f"Actual count: {actual_count} {last_bid[1]}s")
                print("\nStarting new round...")
                game.start_round()
            elif action.is_bid():
                print(f"Bid made: quantity={action.bid.quantity}, face_value={action.bid.face_value}")

        except ValueError as e:
            print(f"Error during turn: {e}")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            break

        turn += 1

    # Check game result
    if game.check_game_over():

        print(f"Game completed in {turn} turns")
    else:
        print(f"\nTest completed after {turn} turns")

    return game


if __name__ == "__main__":
    test_ai_game()
