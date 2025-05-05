from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple, no_type_check
from Action import Action
from const import *

@dataclass
class GameState:
    current_player: int
    hands: List[Tuple[int]]
    most_freq_opp_face: int
    last_bid: Optional[Tuple[int, int]]
    players: int

    def to_public_state(self) -> List[List[Any]]:
        """Convert to the public state representation used by AI"""
        # Using STATE_COMPONENTS list instead of hardcoding indices.
        pub_state = [[] for _ in range(len(STATE_COMPONENTS))]
        pub_state[STATE_COMPONENTS['PLAYER_IDX']] = self.current_player
        pub_state[STATE_COMPONENTS['HANDS']] = self.hands
        pub_state[STATE_COMPONENTS['MOST_FREQ_OPP_BID']] = self.most_freq_opp_face
        pub_state[STATE_COMPONENTS['LAST_BID']] = self.last_bid
        pub_state[STATE_COMPONENTS['PLAYERS']] = self.players
        return pub_state

    @classmethod
    @no_type_check
    # very smelly
    def from_public_state(cls, pub_state: List[List[Any]], current_player: int) -> 'GameState':
        """Create GameState from the public state representation"""
        last_bid = pub_state[STATE_COMPONENTS['LAST_BID']]
        # this should never happen
        if isinstance(last_bid, list):
            last_bid = last_bid[0] if last_bid else None
        most_freq_opp_face = pub_state[STATE_COMPONENTS['MOST_FREQ_OPP_BID']]
        # this would happen if there were more than two players
        if isinstance(most_freq_opp_face, list):
            most_freq_opp_face = most_freq_opp_face[0] if most_freq_opp_face else 0
        hands = pub_state[STATE_COMPONENTS['HANDS']] if STATE_COMPONENTS['HANDS'] < len(pub_state) else []
        players = pub_state[STATE_COMPONENTS['PLAYERS']]
        # this should never happen
        if isinstance(players, list):
            players = players[0] if players else STATE_COMPONENTS['PLAYERS']

        game_state = cls(
            hands=hands,
            most_freq_opp_face=most_freq_opp_face,
            last_bid=last_bid,
            current_player=current_player,
            players=players
        )
        return game_state
        """Get the hand of the current active player."""
        return self.hands[self.current_player] if self.hands and self.current_player < len(self.hands) else tuple()

    def get_model_hand(self) -> Tuple[int]:
        """Get the hand of the model (player 1)

    def get_active_player_hand(self) -> Tuple[int]:."""
        return self.hands[1] if self.hands and len(self.hands) > 1 else tuple()

    def add_hands(self, hands: List[Tuple[int]]) -> None:
        """Add or update the hands of all players."""
        self.hands = hands

    def get_last_bid(self) -> Optional[Tuple[int, int]]:
        """Get the last bid as a tuple of (quantity, face_value) or None."""
        if isinstance(self.last_bid, list):
            if self.last_bid and isinstance(self.last_bid[0], tuple):
                return self.last_bid[0]
            return None
        return self.last_bid

