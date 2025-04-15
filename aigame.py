from Robot.AI import AI
from Action import Action
from const import *
from typing import List, Dict, Optional, Tuple, Any, no_type_check
from GameState import GameState
from Managers.ClusterManager import ClusterManager
from Managers.StateManager import StateManager
from Managers.ActionManager import ActionManager

# TODO: Cluster manager should be be based of scikit-learn's KMeans or something analogous.
class AIGame:
    """Game for AI player training."""
    def __init__(self, player_ct: int, dice_per: int, cluster_manager: ClusterManager, action_manager: ActionManager):
        assert dice_per <= MAX_DICE_PER_PLAYER
        assert player_ct >= MIN_PLAYERS
        assert isinstance(cluster_manager, ClusterManager)
        self.player_ct = player_ct
        self.dice_per = dice_per
        self.players: List[AI] = []
        self.IDX = 0
        self.active_player: Optional[AI] = None
        self.game_over = 0
        self.action_manager = ActionManager()
        self.round_number = 0

        self.game_state = GameState(
            action_history=[],
            player_dice_counts=[dice_per] * player_ct,
            current_player=0,
            total_dice=player_ct * dice_per,
            dice_totals={}, # It might be better to use a list?
            bet_history=[],
            cluster_manager=cluster_manager
        )

        self.state_manager = StateManager()
        self.state_manager.initialize_from_game_state(self.game_state)
        self.initialize_game()

    def initialize_game(self):
        self.make_players()
        self.state_manager.get_public_state()
        #self.cluster_centers = calculate_cluster_center(self.game_state.bet_history, self.game_state.total_dice, self.game_state.cluster_manager.method)

    def make_players(self):
        for p in range(self.player_ct):
            self.players.append(AI(p, self.game_state.cluster_manager, self.action_manager))
        self.active_player = self.players[0]

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
        self.state_manager.initialize_from_game_state(self.game_state)
        self.round_number += 1
        return self.state_manager.get_public_state()

    def step(self) -> Action:
        """Execute one step of the game."""
        if self.game_over:
            return None
        if(self.active_player is None):
            self.active_player = self.players[0]
        action = self.active_player.get_action(self.state_manager)
        if action.is_bid():
            return self.apply_bid(action)
        elif action.is_call_liar():
            return self.apply_liar_call(action)
        raise ValueError(f"Invalid action type: {action.type}")

    # apply bid action to the game state
    @no_type_check
    def apply_bid(self, action: Action) -> Action:
        """Apply a bid action to the game state."""
        assert isinstance(action, Action)
        assert action.is_bid()
        current_state = self.state_manager.get_public_state()

        self.game_state.add_action(action)
        self.update_opp_hist((action.bid.quantity, action.bid.face_value))

        prev_player = self.active_player
        self.active_player = self.players[self.next()]
        self.game_state.current_player = self.IDX
        self.state_manager.update_from_action(action)
        prev_player.update_q_value(
            current_state,
            action,
            prev_player.reward,
            self.state_manager.get_public_state()
        )

        return action
    @no_type_check
    # apply liar call action to the game state
    def apply_liar_call(self, action: Action) -> Action:
        current_state = self.state_manager.get_public_state()
        last_bid = self.game_state.get_last_bid()
        if not last_bid:
            raise ValueError("Cannot call liar when there are no bids")

        caller = self.active_player
        previous_player = self.players[self.look_prev()]

        actual_count = self.game_state.dice_totals.get(last_bid[1], 0)
        bid_difference = last_bid[0] - actual_count

        # If neither player had any of the faces bid upon, the caller receives a large reward.
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
        #If the caller was correct by a bit, reward based on how closely they called it.
        else:
            reward = 5 + (10 / bid_difference + 1)
            caller.update_reward(reward)
            previous_player.update_reward(-reward)
            previous_player.remove_die()
            self.game_state.player_dice_counts[self.look_prev()] -= 1
            self.game_state.total_dice -= 1
            self.active_player = previous_player
        # If the previous player or caller have no dice, remove them from the game.
        if previous_player.NUMDICE == 0:
            previous_player.update_reward(-10)
        if caller.NUMDICE == 0:
            caller.update_reward(-10)
        if self.game_over:
            return None
        self.game_state.add_action(action)

        self.state_manager.update_from_action(action)
        #TODO: the current state and next state are the same state.
        #want this to be implementation of Bellman equation.
        caller.update_q_value(
            current_state,
            action,
            caller.reward,
            self.state_manager.get_public_state()
        )
        if previous_player in self.players:
            previous_player.update_q_value(
                current_state,
                Action.make_bid(*last_bid),
                previous_player.reward,
                self.state_manager.get_public_state()
            )

        return action

    #region unlikely to change methods
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
        """Move to the previous player and return index."""
        self.IDX = (self.IDX - 1)
        if self.IDX < 0:
            self.IDX = self.player_ct - 1
        return self.IDX

    # format {face_value: count}
    def _sum_dice(self):
        """Sum up all dice in play."""
        self.game_state.dice_totals = {}
        for p in range(self.player_ct):
            for d in self.players[p].rolls:
                if self.game_state.dice_totals.get(d) is None:
                    self.game_state.dice_totals[d] = 1
                else:
                    self.game_state.dice_totals[d] += 1

    # Update opponent bid history (updates epsilon).
    # TODO: This should be made consistent with the game state implementation.
    def update_opp_hist(self, qf: Tuple[int, int]):
        """Update opponent bid history for learning."""
        for p in self.players:
            if p != self.active_player:
                p.update_opp_bids(qf)

    def reset_bet_history(self):
        self.game_state.bet_history = []

    def reset_dice_totals(self):
        self.game_state.dice_totals = {}

    # Get the last bet made in the game. Convenience function.
    def last_bet(self) -> Optional[Tuple[int, int]]:
        if len(self.game_state.bet_history) > 0:
            return self.game_state.bet_history[-1]
        return None

    # We don't remove players for training purposes, so instead check if only one player has dice.
    def check_game_over(self) -> bool:
        players_with_dice = 0
        for p in self.players:
            if p.NUMDICE > 0:
                players_with_dice += 1
        return players_with_dice == 1

    def end_game(self):
        self.game_over = 1
        print(f'{self.players[0].name} wins!')

    # Get opponents dice counts
    def hidden_dice(self) -> List[int]:
        return [p.NUMDICE for p in self.players if p != self.active_player]
    #endregion
