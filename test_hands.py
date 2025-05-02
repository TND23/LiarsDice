from Robot.qtable_persistence import QTablePersistence
from typing import Dict, Tuple

def test_qtable_loading():
    # Initialize the persistence handler
    persistence = QTablePersistence()

    # Create a test Q-table with the new state structure
    test_q_table: Dict[Tuple, Dict[str, float]] = {
        # State key format: (current_player, hands, most_freq_opp_face, last_bid)
        (0, ((1, 2, 3), (4, 5, 6)), 3, (2, 4)): {
            "bid_2_4": 0.5,
            "call_liar": -0.3
        },
        (1, ((2, 2), (3, 3)), 2, (1, 3)): {
            "bid_3_4": 0.7,
            "call_liar": 0.2
        }
    }

    # Save the test Q-table
    test_table_id = "test_persistence"
    print(f"\nSaving test Q-table with ID: {test_table_id}")
    persistence.save_q_table(test_q_table, test_table_id)

    # List available tables
    tables = persistence.list_saved_tables()
    print(f"\nAvailable tables: {tables}")

    # Load the saved Q-table
    print(f"\nLoading test Q-table with ID: {test_table_id}")
    try:
        loaded_q_table = persistence.load_q_table(test_table_id)

        # Verify the loaded Q-table matches the original
        if loaded_q_table == test_q_table:
            print("Success: Loaded Q-table matches the original!")
            # Print a sample state and its actions
            sample_state = next(iter(loaded_q_table))
            print("\nSample state:")
            print(f"State key: {sample_state}")
            print(f"Actions: {loaded_q_table[sample_state]}")
        else:
            print("Error: Loaded Q-table does not match the original")
            print(f"\nOriginal Q-table: {test_q_table}")
            print(f"\nLoaded Q-table: {loaded_q_table}")

    except Exception as e:
        print(f"Error loading Q-table: {str(e)}")

if __name__ == "__main__":
    test_qtable_loading()
