from GameState import GameState
from typing import List, Tuple, Any, no_type_check
from const import STATE_COMPONENTS
from Managers.ClusterManager import ClusterManager
from Action import Action, ActionType

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

    #region Overloaded methods for initializing state from different representations
    def initialize_from_game_state(self, game_state: GameState) -> None:
        """Initialize all state representations from a GameState object."""
        self._game_state = game_state
        self._update_public_state()
        self._update_state_key()

    def initialize_from_public_state(self, pub_state: List[List[Any]], current_player: int) -> None:
        """Initialize from a public state representation."""
        if current_player is None:
            current_player = 0
        self._game_state = self._convert_public_to_game_state(pub_state, current_player)
        self._public_state = pub_state
        self._update_state_key()

    def initialize_from_state_key(self, state_key: Tuple, cluster_manager: ClusterManager) -> None:
        """Initialize from a state key representation."""
        self._game_state = self._convert_state_key_to_game_state(state_key, cluster_manager)
        self._update_public_state()
        self._state_key = state_key

    #endregion
    #region coversion between state representations
    def _convert_public_to_game_state(self, pub_state: List[List[Any]], current_player: int) -> GameState:
        """Convert public state to GameState."""
        return GameState.from_public_state(pub_state, current_player)

    def _convert_state_key_to_game_state(self, state_key: Tuple, cluster_manager: ClusterManager) -> GameState:
        """Convert state key to GameState."""
        sorted_rolls, total_dice, bet_history, current_cluster = state_key

        return GameState(
            action_history=[],
            player_dice_counts=[len(sorted_rolls)],
            current_player=0,
            total_dice=total_dice,
            dice_totals={},
            bet_history=list(bet_history),
            cluster_manager=cluster_manager
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
    #region update state after action taken
    def update_from_action(self, action: Action) -> None:
        """Update all state representations after an action."""
        # Update GameState
        self._game_state.action_history.append(action)
        t_action = action.to_tuple()

        if t_action[0] == ActionType.BID:
            self._game_state.bet_history.append(t_action[1].to_tuple())

        # Update other representations
        self._update_public_state()
        self._update_state_key()
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

        # print(f"Debug - Updating state key from game state:")
        # print(f"  Bet history: {self._game_state.bet_history}")
        # print(f"  Current player: {self._game_state.current_player}")
        # print(f"  Total dice: {self._game_state.total_dice}")
        # print(f"  Cluster method: {self._game_state.cluster_manager.method}")
        # print(f"  Centers: {self._game_state.cluster_manager.centers}")

        # Ensure bet_history is a tuple of tuples
        bet_history = tuple(tuple(bid) for bid in self._game_state.bet_history)

        # Ensure centers is a tuple of tuples
        centers = tuple(tuple(center) for center in self._game_state.cluster_manager.centers)

        # Create the state key with the exact format expected by QTablePersistence
        self._state_key = (
            bet_history,
            self._game_state.current_player,
            self._game_state.total_dice,
            self._game_state.cluster_manager.method,
            centers
        )
        #print(f"Debug - New state key: {self._state_key}")
    #endregion
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
        test_key = self._state_key

        return (test_public == self._public_state and
                test_key == self._state_key)
    @no_type_check
    def _get_current_cluster(self) -> int:
        """Find the current cluster."""
        if not self._game_state.cluster_manager.centers:
            return -1
        return self._game_state.cluster_manager.find_closest_center(
            self._game_state.bet_history,
            self._game_state.total_dice
        )
