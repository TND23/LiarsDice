from aigame import AIGame
from Action import Action
import time

def test_ai_game():
    """Test that AIs can play the game correctly."""
    print("Starting AI game test...")
    
    # Create a game with 2 players, 5 dice each
    game = AIGame(2, 5)
    print(f"Created game with {game.player_ct} players, {game.dice_per} dice each")
    
    # Start a round
    game.start_round()
    print("Started a new round")
    
    # Play a few turns
    max_turns = 10
    turn = 0
    
    while not game.check_game_over() and turn < max_turns:
        print(f"\nTurn {turn + 1}")
        print(f"Active player: {game.active_player.name}")
        
        # Get and apply an action
        action = game.step()
        print(f"Action: {action}")
        
        # If it was a call liar, start a new round
        if action.is_call_liar():
            print("Call liar detected, starting new round")
            game.start_round()
        
        turn += 1
    
    # Check game result
    if game.check_game_over():
        print(f"\nGame over! Winner: {game.players[0].name}")
    else:
        print(f"\nTest completed after {turn} turns")
    
    return game

if __name__ == "__main__":
    test_ai_game() 