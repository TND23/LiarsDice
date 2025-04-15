# Training constants
MAX_MEM = 100_000
BATCH_SIZE = 2**6
LEARN_RATE = 0.01

MAX_DICE_PER_PLAYER = 5 # if it can go up, even better.

# Game state structure
# The state is represented as a 2D list where each row is a different component
# Each row is prefixed with its length for tensor conversion
STATE_COMPONENTS = {
    'BET_HISTORY': 0,
    'PLAYER_INFO': 1,
    'LAST_ACTION': 2,
    'DICE_COUNTS': 3,      # [length, player1_dice, player2_dice, ...]
    'CLUSTER_INFO': 4,     # [length, method, count, current_cluster]
    'LAST_BID': 5,         # [length, quantity, face_value]
    'CLUSTER_MGR': 6       # [length, cluster_manager_ref]
}

# Maximum lengths for each component
MAX_BET_HISTORY = 12
MAX_PLAYERS = 6
MAX_ACTIONS = 1
MAX_DICE_COUNTS = MAX_DICE_PER_PLAYER
MAX_CLUSTER_INFO = 4
MAX_LAST_BID = 2
MAX_CLUSTER_MGR = 1
MAX_PLAYERS = 8

# Game constants
MAX_FACE_VALUE = 6
MIN_FACE_VALUE = 1
MIN_PLAYERS = 2

# State approximation constants
NUM_CLUSTERS = 100

# Approximation constants
QTY_DISTANCE_WEIGHT = 0.4
FACE_DISTANCE_WEIGHT = 0.3
QTY_RATIO_DISTANCE_WEIGHT = 0.2
HISTORY_LENGTH_DISTANCE_WEIGHT = 0.1

MAX_ROUND_MEMORY = 4
NUMBER_FACES = 6

MAX_DIE_PER_PLAYER = 5

# AI constants
EPSILON = 0.5
DISCOUNT_FACTOR = 0.9
LEARNING_RATE = 0.1

# Distance constants
# if a die face is maximum, it is considered more distant from the next highest die face than it would be otherwise.
MAX_DIE_BONUS_WEIGHT = 2

PUB_STATE_SIZE = 10
MAX_TOTAL_DICE = MAX_PLAYERS * MAX_DICE_PER_PLAYER
# Data constants
CLUSTER_CENTERS_FILE = "./data/cluster_centers.json"
