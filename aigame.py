from Robot.AI import AI
from Action import Action
from const import *
from typing import Dict, List,  Optional, Tuple, Any, no_type_check
from GameState import GameState
from Managers.StateManager import StateManager
from Managers.ActionManager import ActionManager

# TODO: Cluster manager should be be based of scikit-learn's KMeans or something analogous.
class AIGame:
    """Game for AI player training."""
    @no_type_check
    def __init__(self, player_ct: int = STATE_COMPONENTS['PLAYERS'], dice_per: int = MAX_DICE_PER_PLAYER, action_manager: ActionManager = ActionManager()):
        assert dice_per <= MAX_DICE_PER_PLAYER
        assert player_ct >= MIN_PLAYERS
        self.player_ct = player_ct
        self.dice_per = dice_per
        self.players: List[AI] = []
        self.IDX = 0 # active player index
        self.active_player: Optional[AI] = None
        self.game_over = 0
        self.action_manager = action_manager
        self.round_number = 0
        self.face_to_number_of_bids = {}

        self.game_state = GameState(
            current_player=0,
            hands=[],
            most_freq_opp_face=0,
            last_bid=None,
            players=player_ct
        )
        self.round_history = []

        self.state_manager = StateManager()
        self.state_manager.initialize_from_game_state(self.game_state)
        self.initialize_game()

    def initialize_game(self):
        self.make_players()
        self.state_manager.get_public_state()

    def make_players(self):
        for p in range(self.player_ct):
            self.players.append(AI(p, self.action_manager))
        self.active_player = self.players[0]

    def start_round(self):
        """Start a new round of the game"""
        self.game_over = 0
        self.round_history = []
        self.roll()
        self.active_player = self.players[0]
        self.IDX = 0
        self.game_state.current_player = 0
        self.state_manager.initialize_from_game_state(self.game_state)
        self.round_number = 1
        for p in self.players:
            p.spots_could_have_called_liar = []
        return self.state_manager.get_public_state()

    def step(self) -> Action:
        """Execute one step of the game."""
        if self.game_over:
            return Action.call_liar()
        if(self.active_player is None):
            self.active_player = self.players[0]
        action = self.active_player.get_action(self.state_manager)
        if action.is_bid():
            self.round_number += 1
            return self.apply_bid(action)
        elif action.is_call_liar():
            self.round_number += 1
            return self.apply_liar_call(action)
        raise ValueError(f"Invalid action type: {action.type}")

    # for agents with models
    def apply_action(self, action: Action) -> Action:
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
        self.round_history.append(action)
        bid = action.bid.face_value
        if bid not in self.face_to_number_of_bids:
            self.face_to_number_of_bids[bid] = 0
        self.face_to_number_of_bids[bid] += 1

        # update the most frequent opponent bid
        if self.face_to_number_of_bids[bid] > self.game_state.most_freq_opp_face:
            self.game_state.most_freq_opp_face = bid

        prev_player = self.active_player
        # Update game state first
        self.IDX = self.next()
        self.game_state.current_player = self.IDX
        # Then update active player
        self.active_player = self.players[self.IDX]

        self.state_manager.update_from_action(action)
        prev_player.update_q_value(
            action,
            prev_player.reward
        )

        return action
    @no_type_check
    # apply liar call action to the game state
    def apply_liar_call(self, action: Action) -> Action:
        self.round_history.append(action)
        last_bid = self.game_state.get_last_bid()
        if not last_bid:
            raise ValueError("Cannot call liar when there are no bids")
        caller = self.active_player
        previous_player = self.players[self.look_prev()]
        assert isinstance(self.state_manager, StateManager)
        # If the caller was incorrect, adjust reward based on how incorrect they were.
        if self._dice_totals().get(last_bid[1]) >= last_bid[0]:
            caller.update_reward("punish_liar_call", self.state_manager)
            previous_player.update_reward("reward_passive", self.state_manager)
            caller.remove_die()
            self.game_state.hands[self.IDX] = caller.rolls
            # Set active player and index to the caller who lost a die
            self.IDX = caller.p_index
            self.game_state.current_player = self.IDX
            self.active_player = caller

        #If the caller was correct, reward based on how closely they called it.
        else:
            caller.update_reward("reward_liar_call", self.state_manager)
            previous_player.update_reward("punish_passive", self.state_manager)
            previous_player.remove_die()
            self.game_state.hands[self.look_prev()] = previous_player.rolls
            # Set active player and index to the previous player who lost a die
            self.IDX = previous_player.p_index
            self.game_state.current_player = self.IDX
            self.active_player = previous_player

        self.face_to_number_of_bids = {}
        # If the previous player or caller have no dice, remove them from the game.
        if self.game_over:
            return None

        # Reset the game state for the new round
        self.game_state.last_bid = None
        self.round_history = []
        self.state_manager.initialize_from_game_state(self.game_state)

        self.state_manager.update_from_action(action)
        caller.update_q_value(
            action,
            caller.reward
        )
        if previous_player in self.players:
            previous_player.update_q_value(
                Action.make_bid(*last_bid),
                previous_player.reward
            )
        self.roll()
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
    def _dice_totals(self) -> Dict[int, int]:
        return {face: sum(dice.count(face) for dice in self.game_state.hands) for face in range(1, MAX_FACE_VALUE + 1)}
    # Move to the previous player and return index.
    def prev(self) -> int:
        """Move to the previous player and return index."""
        self.IDX = (self.IDX - 1)
        if self.IDX < 0:
            self.IDX = self.player_ct - 1
        return self.IDX

    @no_type_check # ignore UNION x None warning
    def last_bet(self) -> Tuple[int, int]:
        return self.game_state.last_bid

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

    def roll(self):
        """Roll dice for all players and update the game state."""
        hands = []
        for p in range(len(self.players)):
            self.players[p].roll()
            hands.append(tuple(sorted(self.players[p].rolls)))  # Sort hands for consistency
        self.game_state.add_hands(hands)

    def total_dice(self) -> int:
        return sum(p.NUMDICE for p in self.players)

    def reset_hands(self):
        """Reset all players' hands."""
        for p in self.players:
            p.rolls = []
            for _ in range(self.dice_per):  # Initialize with correct number of dice
                p.rolls.append(1)
            p.roll()
        self.roll()  # Roll all hands again to ensure proper initialization
    #endregion
