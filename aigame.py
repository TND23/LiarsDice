import random
from Rules import is_valid_bet
from AI import AI
from Action import Action, ActionType, Bid
import itertools
from const import *
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from GameState import GameState

class AIGame:

    def __init__(self, player_ct: int, dice_per: int):
        self.player_ct = player_ct
        self.dice_per = dice_per
        self.players: List[AI] = []
        self.IDX = 0     
        self.active_player: Optional[AI] = None
        self.game_state = GameState(
            action_history=[],
            player_dice_counts=[dice_per] * player_ct,
            current_player=0,
            total_dice=player_ct * dice_per,
            dice_totals={},
            bet_history=[]
        )
        self.game_over = 0
        self.initialize_game()

    def initialize_game(self):
        """Initialize the game state"""
        self.make_players()
        self.set_pub_state()

    def make_players(self):
        """Create AI players for the game"""
        if self.player_ct < 2:
            self.player_ct = 2
        for p in range(self.player_ct):                            
            self.players.append(AI(p))

    def start_round(self):
        """Start a new round of the game"""
        self.game_state.bet_history = []
        self.game_state.dice_totals = {}
        self.game_over = 0        
        for p in range(self.player_ct):
            self.players[p].roll()
        self._sum_dice()
        self.active_player = self.players[0]
        self.IDX = 0
        self.game_state.current_player = 0
        return self.set_pub_state()
        
    def step(self) -> Action:
        """Execute one step of the game.
        """
        action = self.active_player.get_action(self.game_state.to_public_state())
        if action.is_bid():
            return self.apply_bid(action)
        elif action.is_call_liar():
            return self.apply_liar_call(action)
        raise ValueError(f"Invalid action type: {action.type}")

    # apply bid action to the game state
    def apply_bid(self, action: Action) -> Action:

        current_state = self.game_state.to_public_state()
        
        self.game_state.add_action(action)
        self.update_opp_hist((action.bid.quantity, action.bid.face_value))
        
        prev_player = self.active_player
        self.active_player = self.players[self.next()]
        self.game_state.current_player = self.IDX
        
        prev_player.update_q_value(current_state, action, prev_player.reward, self.game_state.to_public_state())
        
        return action

    # apply liar call action to the game state
    def apply_liar_call(self, action: Action) -> Action:
        current_state = self.game_state.to_public_state()
        last_bid = self.game_state.get_last_bid()
        if not last_bid:
            raise ValueError("Cannot call liar when there are no bids")
            
        caller = self.active_player
        previous_player = self.players[self.look_prev()]
        
        actual_count = self.game_state.dice_totals.get(last_bid[1], 0)
        bid_difference = last_bid[0] - actual_count
        # If neither player had any of the faces bid upon, the caller received a large reward.
        if self.game_state.dice_totals.get(last_bid[1]) is None:
            caller.update_reward(15)
            previous_player.update_reward(-15)
            previous_player.remove_die()
            self.game_state.player_dice_counts[self.look_prev()] -= 1
            self.game_state.total_dice -= 1
            self.active_player = previous_player
        # If the caller was incorrect, adjust reward based on how incorrect they were.    
        elif self.game_state.dice_totals[last_bid[1]] >= last_bid[0]:
            reward = -5 - (actual_count - last_bid[0])
            caller.update_reward(reward)
            previous_player.update_reward(-reward)
            caller.remove_die()
            self.game_state.player_dice_counts[self.IDX] -= 1
            self.game_state.total_dice -= 1
            self.active_player = previous_player
        #If the caller was correct, reward based on how closely they called it.
        else:
            reward = 5 + (10 / bid_difference + 1)
            caller.update_reward(reward)
            previous_player.update_reward(-reward)
            previous_player.remove_die()
            self.game_state.player_dice_counts[self.look_prev()] -= 1
            self.game_state.total_dice -= 1
            if previous_player.NUMDICE == 0:
                previous_player.update_reward(-10)
                self.remove_player(previous_player)
            self.active_player = caller
            
        self.game_state.add_action(action)
        caller.update_q_value(current_state, action, caller.reward, self.game_state.to_public_state())
        if previous_player in self.players:
            previous_player.update_q_value(current_state, Action.make_bid(*last_bid), previous_player.reward, self.game_state.to_public_state())
        
        return action
    # Moves to next player and return index
    def next(self) -> int:
            
        self.IDX = (self.IDX + 1) % self.player_ct
        return self.IDX

    # Get the index of the previous player without updating the current index.
    def look_prev(self) -> int:
        tmp = (self.IDX - 1)
        if tmp < 0:
            tmp = self.player_ct - 1 
        return tmp

    # Move to the previous player and return index.
    def prev(self) -> int:
        self.IDX = (self.IDX - 1)

        self.IDX = (self.IDX - 1)
        if self.IDX < 0:
            self.IDX = self.player_ct - 1 
        return self.IDX

    def _all_rolls(self, player):
        assert player in self.players
        n_faces = self.D1 if player == 0 else self.D2
        return [
            tuple(sorted(r))
            for r in itertools.product(range(1, self.SIDES + 1), repeat=n_faces)
        ]

    def _sum_dice(self):
        """Sum up all dice in play."""
        self.game_state.dice_totals = {}
        for p in range(self.player_ct):
            for d in self.players[p].rolls:
                if self.game_state.dice_totals.get(d) is None:
                    self.game_state.dice_totals[d] = 1
                else:
                    self.game_state.dice_totals[d] += 1
    
    # Update opponent bid history for learning.
    # TODO: This should be made consistent with the game state implementation.
    def update_opp_hist(self, qf: Tuple[int, int]):
        """Update opponent bid history for learning.
        
        Args:
            qf: Tuple of (quantity, face_value) for the bid
        """
        for p in self.players:
            if p != self.active_player:
                p.update_opp_bids(qf)

    def reset_bet_history(self):
        """Reset the bet history for a new round."""
        self.game_state.bet_history = []

    def reset_dice_totals(self):
        """Reset the dice totals for a new round."""
        self.game_state.dice_totals = {}

    # Get the last bet made in the game. Convenience function.
    def last_bet(self) -> Optional[Tuple[int, int]]:
        if len(self.game_state.bet_history) > 0:
            return self.game_state.bet_history[-1]
        return None

    # Check if the game is over.
    def check_game_over(self) -> bool:
        return len(self.players) == 1
      
    def remove_player(self, player: AI):
        """Remove a player from the game.
        
        Args:
            player: The player to remove
        """
        player_idx = self.players.index(player)
        self.players.remove(player)
        self.player_ct -= 1
        self.game_state.player_dice_counts.pop(player_idx)
        
        if self.check_game_over():
            self.end_game()
        else:
            # Reset IDX if it's now out of bounds
            if self.IDX >= self.player_ct:
                self.IDX = 0
    # TODO: Update rewards for winner, this should trigger some persistence.
    def end_game(self):
        self.game_over = 1
        print(f'{self.players[0].name} wins!')

    def set_pub_state(self) -> List[Any]:
        """Set the public state of the game.
        
        Returns:
            List[Any]: The public state
        """
        return self.game_state.to_public_state()
    # Get opponents dice counts    
    def hidden_dice(self) -> List[int]:
        return [p.NUMDICE for p in self.players if p != self.active_player]
