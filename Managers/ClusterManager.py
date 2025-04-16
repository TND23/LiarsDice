import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from const import CLUSTER_CENTERS_FILE, MAX_FACE_VALUE

# There are too many states to use a Q-table.
# Instead, we use a cluster manager to manage the centers.
# The centers are updated based on the bet histories.
# TODO: Use sklearn instead of this nonsense.
class ClusterManager:
    """Manages cluster centers for bet histories"""
    def __init__(self, method: str = "avg"):
        self.method = method
        self.centers = []
        self._load_centers()

    def _get_cluster_file_path(self) -> Path:
        """Get the path to the cluster centers file"""
        return Path(CLUSTER_CENTERS_FILE)

    def _load_centers(self):
        """Load cluster centers from JSON file"""
        file_path = self._get_cluster_file_path()
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    self.centers = [tuple(center) for center in data.get('centers', [])]
                    self.method = data.get('method', self.method)
            else:
                # Use the same default centers that were used to create the Q-table
                self.centers = [
                    (0.16666666666666666, 0.16666666666666666),
                    (0.6666666666666666, 0.6666666666666666)
                ]
                self.save_centers()
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading cluster centers: {e}")
            # Use the same default centers that were used to create the Q-table
            self.centers = [
                (0.16666666666666666, 0.16666666666666666),
                (0.6666666666666666, 0.6666666666666666)
            ]
            self.save_centers()

    def save_centers(self):
        """Save cluster centers to JSON file"""
        file_path = self._get_cluster_file_path()
        try:
            with open(file_path, 'w') as f:
                json.dump({
                    'centers': self.centers,
                    'method': self.method
                }, f, indent=2)
        except IOError as e:
            print(f"Error saving cluster centers: {e}")

    def update_centers(self, bet_histories: List[List[Tuple[int, int]]], total_dice: int):
        """Update cluster centers based on new bet histories"""
        if self.method == "avg":
            self._update_avg_centers(bet_histories, total_dice)
        #elif self.method == "pattern":
        #    self._update_pattern_centers(bet_histories, total_dice)
        self.save_centers()  # Save after updating

    def get_centers(self) -> List[Tuple[int, int]]:
        return self.centers

    def _update_avg_centers(self, bet_histories: List[List[Tuple[int, int]]], total_dice: int):
        """Update centers using average-based method"""
        assert isinstance(bet_histories, list)
        assert isinstance(total_dice, int)
        if not bet_histories:
            return

        # Group bet histories by length
        length_groups = {}
        for history in bet_histories:
            length = len(history)
            if length not in length_groups:
                length_groups[length] = []
            length_groups[length].append(history)

        # Calculate average centers for each length
        new_centers = []

        for length, histories in length_groups.items():
            if len(histories) < 2:  # Need at least 2 histories to form a pattern
                continue

            # Calculate average quantity and face value
            avg_qty = sum(h[0] for h in histories) / len(histories)
            avg_face = sum(h[1] for h in histories) / len(histories)

            norm_qty = avg_qty / total_dice
            norm_face = avg_face / MAX_FACE_VALUE

            new_centers.append((norm_qty, norm_face))

        if new_centers:
            self.centers = new_centers

    def find_closest_center(self, bet_history: List[Tuple[int, int]], total_dice: int) -> int:
        """Find the closest center for a given bet history."""
        if not self.centers:
            return -1

        # Calculate the normalized bet history
        if not bet_history:
            return 0  # Default to first center for empty bet history

        # Calculate average bid
        total_bids = len(bet_history)
        avg_quantity = sum(bid[0] for bid in bet_history) / total_bids
        avg_face = sum(bid[1] for bid in bet_history) / total_bids

        # Normalize by total dice
        if total_dice == 0:
            norm_quantity = 0
        else:
            norm_quantity = avg_quantity / total_dice
        norm_face = avg_face / MAX_FACE_VALUE

        # Find closest center
        min_dist = float('inf')
        closest_idx = 0
        for i, center in enumerate(self.centers):
            dist = ((center[0] - norm_quantity) ** 2 + (center[1] - norm_face) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                closest_idx = i

        return closest_idx

