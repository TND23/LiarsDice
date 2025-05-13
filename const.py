# Training constants
MAX_MEM = 100_000
BATCH_SIZE = 2**9
LEARN_RATE = 0.01

MAX_DICE_PER_PLAYER = 5 # if it can go up, even better.

# Game state structure
# The state is represented as a 2D list where each row is a different component
# Each row is prefixed with its length for tensor conversion
STATE_COMPONENTS = {
    'PLAYER_IDX': 0,
    'HANDS': 1,      # [length, player1_dice, player2_dice, ...]
    'MOST_FREQ_OPP_BID': 2,         # [length, quantity, face_value]
    'LAST_BID': 3,       # [length, cluster_manager_ref]
    'PLAYERS': 2,
}
FEATURE_WEIGHTS = {
    'PLAYER_IDX': 0.1,
    'HANDS': 0.9,
    'MOST_FREQ_OPP_BID': 2.0,
    'LAST_BID': 0.1,
    'PLAYERS': 0.1,
}
# Maximum lengths for each component
MAX_PLAYERS = 6
MAX_ACTIONS = 1
MAX_DICE_COUNTS = MAX_DICE_PER_PLAYER
MAX_LAST_BID = 2

# Game constants
MAX_FACE_VALUE = 6
MIN_FACE_VALUE = 1
MIN_PLAYERS = 2

# State approximation constants
MEMORY_SIZE = 10000
# Approximation constants
MAX_ROUND_MEMORY = 4
NUMBER_FACES = 6

MAX_DIE_PER_PLAYER = 5
RANDOM_LIAR_PROB = 0.5
# AI constants
EPSILON = .3
DISCOUNT_FACTOR = 0.9
LEARNING_RATE = 0.001

# Distance constants
# if a die face is maximum, it is considered more distant from the next highest die face than it would be otherwise.
MAX_DIE_BONUS_WEIGHT = 2

PUB_STATE_SIZE = 10
MAX_TOTAL_DICE = MAX_PLAYERS * MAX_DICE_PER_PLAYER
# Data constants
CUR_Q_TABLE_NAME = "SD"
CUR_MODEL_NAME = "SD.pt"
CUR_MODEL_PATH = "models/deep_q/" + CUR_MODEL_NAME
CUR_MODEL_ONNX_PATH = "models/deep_q/" + CUR_MODEL_NAME + ".onnx"
