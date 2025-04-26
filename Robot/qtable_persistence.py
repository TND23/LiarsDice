import json
import struct
import os
from pathlib import Path
from typing import Dict, Tuple, Any
import numpy as np
from datetime import datetime

from sympy import Q

# AI-generated code for persisting Q-tables.
class QTablePersistence:

    def __init__(self, base_dir: str = "./data/q_tables"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_metadata_path(self, table_id: str) -> Path:
        return self.base_dir / f"{table_id}_metadata.json"

    def _get_values_path(self, table_id: str) -> Path:
        return self.base_dir / f"{table_id}_values.bin"

    def _serialize_state_key(self, state_key: Tuple) -> bytes:
        """Convert a state key tuple to a binary format.

        State key structure:
        (
            bet_history_tuple,  # tuple of bid tuples ((qty, face), ...)
            current_player,     # int
            total_dice,        # int
            cluster_method,    # str
            centers_tuple,     # tuple of center tuples (float pairs)
            hands_tuple       # tuple of hand tuples (int tuples)
        )
        """
        if not state_key or len(state_key) != 6:
            print(f"Invalid state key: {state_key}")
            return b''

        bet_history, current_player, total_dice, cluster_method, centers, hands = state_key
        parts = []

        # Serialize bet history
        parts.append(struct.pack('>I', len(bet_history)))
        for bid in bet_history:
            if isinstance(bid, tuple) and len(bid) == 2:
                parts.append(struct.pack('>II', *bid))

        # Serialize current player and total dice
        parts.append(struct.pack('>I', current_player))
        parts.append(struct.pack('>I', total_dice))

        # Serialize cluster method
        method_bytes = cluster_method.encode('utf-8')
        parts.append(struct.pack('>I', len(method_bytes)))
        parts.append(method_bytes)

        # Serialize centers
        parts.append(struct.pack('>I', len(centers)))
        for center in centers:
            if isinstance(center, tuple) and len(center) == 2:
                parts.append(struct.pack('>dd', *center))

        # Serialize hands
        parts.append(struct.pack('>I', len(hands)))
        for hand in hands:
            if isinstance(hand, tuple):
                parts.append(struct.pack('>I', len(hand)))
                for die in hand:
                    parts.append(struct.pack('>I', die))

        return b''.join(parts)

    def _deserialize_state_key(self, data: bytes) -> Tuple:
        if not data:
            return tuple()

        offset = 0

        bet_history_len = struct.unpack('>I', data[offset:offset+4])[0]
        offset += 4
        bet_history = []
        for _ in range(bet_history_len):
            qty, face = struct.unpack('>II', data[offset:offset+8])
            bet_history.append((qty, face))
            offset += 8

        current_player = struct.unpack('>I', data[offset:offset+4])[0]
        offset += 4
        total_dice = struct.unpack('>I', data[offset:offset+4])[0]
        offset += 4

        method_len = struct.unpack('>I', data[offset:offset+4])[0]
        offset += 4
        cluster_method = data[offset:offset+method_len].decode('utf-8')
        offset += method_len

        centers_len = struct.unpack('>I', data[offset:offset+4])[0]
        offset += 4
        centers = []
        for _ in range(centers_len):
            x, y = struct.unpack('>dd', data[offset:offset+16])
            centers.append((x, y))
            offset += 16

        # Deserialize hands
        hands_len = struct.unpack('>I', data[offset:offset+4])[0]
        offset += 4
        hands = []
        for _ in range(hands_len):
            hand_len = struct.unpack('>I', data[offset:offset+4])[0]
            offset += 4
            hand = []
            for _ in range(hand_len):
                die = struct.unpack('>I', data[offset:offset+4])[0]
                hand.append(die)
                offset += 4
            hands.append(tuple(hand))

        return (tuple(bet_history), current_player, total_dice, cluster_method, tuple(centers), tuple(hands))

    def save_q_table(self, q_table: Dict[Tuple, Dict[str, float]], table_id: str) -> None:
        """Save a Q-table to disk efficiently."""
        # print(f"\n=== Saving Q-table {table_id} ===")
        # print(f"Number of states to save: {len(q_table)}")

        if not q_table:
            print("Warning: Attempting to save empty Q-table")
            return

        metadata = {
            'table_id': table_id,
            'timestamp': datetime.now().isoformat(),
            'num_states': len(q_table),
            'state_key_size': 0,
            'action_value_size': 0
        }

        # Serialize state keys and action values
        state_entries = []
        for state_key, actions in q_table.items():
            key_bytes = self._serialize_state_key(state_key)
            if not key_bytes:
                print("  Warning: Failed to serialize state key, skipping")
                continue

            action_values = []
            for action_str, value in actions.items():

                action_bytes = action_str.encode('utf-8')
                value_bytes = struct.pack('>d', value)
                action_values.append((action_bytes, value_bytes))
            state_entries.append((key_bytes, action_values))

        # Update metadata with sizes
        if state_entries:
            metadata['state_key_size'] = len(state_entries[0][0])
            if state_entries[0][1]:
                metadata['action_value_size'] = len(state_entries[0][1][0][0]) + 8

        with open(self._get_metadata_path(table_id), 'w') as f:
            json.dump(metadata, f, indent=2)

        with open(self._get_values_path(table_id), 'wb') as f:
            f.write(struct.pack('>I', len(state_entries)))

            for key_bytes, action_values in state_entries:
                f.write(struct.pack('>I', len(key_bytes)))
                f.write(key_bytes)
                f.write(struct.pack('>I', len(action_values)))

                for action_bytes, value_bytes in action_values:
                    f.write(struct.pack('>I', len(action_bytes)))
                    f.write(action_bytes)
                    f.write(value_bytes)

        print(f"Successfully saved Q-table with {len(state_entries)} states")

    def load_q_table(self, table_id: str) -> Dict[Tuple, Dict[str, float]]:
        """Load a Q-table from disk."""
        metadata_path = self._get_metadata_path(table_id)
        values_path = self._get_values_path(table_id)


        if not metadata_path.exists() or not values_path.exists():
            print("Q-table files not found, returning empty table")
            return {}

        q_table = {}
        with open(values_path, 'rb') as f:
            num_states = struct.unpack('>I', f.read(4))[0]

            for state_idx in range(num_states):
                # Read state key
                key_size = struct.unpack('>I', f.read(4))[0]
                key_bytes = f.read(key_size)
                state_key = self._deserialize_state_key(key_bytes)

                # Initialize state entry
                q_table[state_key] = {}

                # Read number of actions
                num_actions = struct.unpack('>I', f.read(4))[0]

                # Read each action and its value
                for action_idx in range(num_actions):
                    action_size = struct.unpack('>I', f.read(4))[0]
                    action_bytes = f.read(action_size)
                    value_bytes = f.read(8)
                    action_str = action_bytes.decode('utf-8')
                    value = struct.unpack('>d', value_bytes)[0]
                    q_table[state_key][action_str] = value

        return q_table

    def list_saved_tables(self) -> list:
        tables = []
        for file in self.base_dir.glob("*_metadata.json"):
            table_id = file.stem.replace("_metadata", "")
            tables.append(table_id)
        return tables
