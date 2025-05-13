from GameState import GameState
from typing import List, Tuple, Any, no_type_check
from const import STATE_COMPONENTS
from Action import Action, ActionType
import copy

# The states are: GameState, PublicState, StateKey
# The GameState is the internal state of the game.
# The PublicState is the state of the game as seen by the players.
# The StateKey is the state of the game as seen by the Q-table.
# The StateKey is used to index the Q-table and update the GameState.

class StateManager:
    def __init__(self):
        self._game_state = None
        self._public_state = None
        self._state_key = None
        self._next_state = None
        self._next_state_key = None

    #region Overloaded methods for initializing state from different representations
    def initialize_from_game_state(self, game_state: GameState) -> None:
        """Initialize all state representations from a GameState object."""
        self._game_state = game_state
        self._next_state = copy.deepcopy(game_state)
        self._update_public_state()
        self._update_state_key()
        self._update_next_state_key()

    def initialize_from_public_state(self, pub_state: List[List[Any]], current_player: int) -> None:
        """Initialize from a public state representation."""
        if current_player is None:
            current_player = 0
        self._game_state = self._convert_public_to_game_state(pub_state, current_player)
        self._public_state = pub_state
        self._update_state_key()
        self._update_next_state_key()

    def initialize_from_state_key(self, state_key: Tuple) -> None:
        """Initialize from a state key representation."""
        self._game_state = self._convert_state_key_to_game_state(state_key)
        self._update_public_state()
        self._state_key = state_key

    #endregion
    #region coversion between state representations
    def _convert_public_to_game_state(self, pub_state: List[List[Any]], current_player: int) -> GameState:
        """Convert public state to GameState."""
        return GameState.from_public_state(pub_state, current_player)

    def _convert_state_key_to_game_state(self, state_key: Tuple) -> GameState:
        """Convert state key to GameState."""
        if not state_key or len(state_key) != 4:
            raise ValueError(f"Invalid state key: {state_key}")

        current_player, hands, most_freq_opp_face, last_bid = state_key

        return GameState(
            current_player=current_player,
            hands=list(hands) if hands else [],
            most_freq_opp_face=most_freq_opp_face,
            last_bid=last_bid,
            players=STATE_COMPONENTS['PLAYERS']
        )
    #endregion
    @no_type_check
    def get_game_state(self) -> GameState:
        """Return the internal GameState representation."""
        return self._game_state

    @no_type_check
    def get_public_state(self) -> List[List[Any]]:
        """Return the public state list for AI use."""
        return self._public_state

    @no_type_check
    def get_state_key(self) -> Tuple:
        """Return the state key for Q-table use."""
        return self._state_key

    @no_type_check
    def get_next_state(self, action: Action) -> GameState:
        """Return the next state for Q-table use."""
        self._update_next_state_from_action(action)
        return self._next_state

    @no_type_check
    def get_next_state_key(self, action: Action) -> Tuple:
        """Return the next state key for Q-table use."""
        return self._next_state_key

    @no_type_check
    #region update state after action taken
    def update_from_action(self, action: Action) -> None:
        """Update all state representations after an action."""
        # Update GameState
        t_action = action.to_tuple()
        if t_action[0] == ActionType.BID:
            bid_tuple = t_action[1].to_tuple()
            if isinstance(bid_tuple, list):
                bid_tuple = tuple(bid_tuple[0]) if bid_tuple else None
            self._game_state.last_bid = bid_tuple
            self._game_state.current_player = (self._game_state.current_player + 1) % self._game_state.players
        # Update other representations
        self._update_public_state()
        self._update_state_key()
        self._update_next_state_key()

    @no_type_check
    def _update_next_state_from_action(self, action: Action) -> None:
        """Update all state representations from a GameState object."""
        t_action = action.to_tuple()
        if t_action[0] == ActionType.BID:
            bid_tuple = t_action[1].to_tuple()
            if isinstance(bid_tuple, list):
                bid_tuple = tuple(bid_tuple[0]) if bid_tuple else None
            self._next_state.last_bid = bid_tuple
            self._next_state.current_player = (self._next_state.current_player + 1) % self._next_state.players
        # Ensure hands are properly copied
        self._next_state.hands = list(self._game_state.hands) if self._game_state.hands else []

    @no_type_check
    def _update_public_state(self) -> None:
        """Convert GameState to public state list."""
        self._public_state = self._game_state.to_public_state()

    @no_type_check
    def _update_state_key(self) -> None:
        """Convert GameState to state key for Q-table."""
        if not self._game_state:
            print("Debug - Cannot update state key: game state is None")
            return

        current_player = self._game_state.current_player
        hands = tuple(tuple(hand) for hand in self._game_state.hands) if self._game_state.hands else tuple()
        most_freq_opp_face = self._game_state.most_freq_opp_face
        last_bid = self._game_state.last_bid

        # Create the state key with the exact format expected by QTablePersistence
        self._state_key = (
            current_player,
            hands,
            most_freq_opp_face,
            last_bid
        )

    @no_type_check
    def _update_next_state_key(self) -> None:
        """Convert GameState to state key for Q-table."""
        if not self._next_state:
            print("Debug - Cannot update next state key: game state is None")
            return

        current_player = self._next_state.current_player
        hands = tuple(tuple(hand) for hand in self._next_state.hands) if self._next_state.hands else tuple()
        most_freq_opp_face = self._next_state.most_freq_opp_face
        last_bid = self._next_state.last_bid

        # Create the state key with the exact format expected by QTablePersistence
        self._next_state_key = (
            current_player,
            hands,
            most_freq_opp_face,
            last_bid
        )

    def validate_state(self) -> bool:
        """Just checking."""
        if not self._game_state:
            return False

        if not self._public_state:
            return False

        if not self._state_key:
            return False

        test_public = self._game_state.to_public_state()
        self._update_state_key()
        self._update_next_state_key()
        test_key = self._state_key
        test_next_key = self._next_state_key

        return (test_public == self._public_state and
                test_key == self._state_key)

