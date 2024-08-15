from Rules import *
import torch
from collections import deque
from StartRound import Game
from numpy import np

MAX_MEM = 100_000
BATCH_SIZE = 2**6
LEARN_RATE = 0.01

class Agent:
    def __init__(self, num_dice, num_players, dice_sides, ruleset):
        self.memory = deque(maxlen=MAX_MEM)
        self.n_games = 0
        self.epsilon = 0 # control randomness
        self.gamma = 0
    
    def get_state(self, game):
        bet_hist = game.bet_history
        hidden_dice = game.hidden_dice(game.active_player)
        active_players = len(hidden_dice) + 1
        last_action = game.last_action

        state = [
            bet_hist,
            hidden_dice,
            active_players,
            last_action
        ]
        return np.array(state)

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def train_memory(self):
        pass

    def train_short_memory(self):
        pass

    def get_action(self, state):
        pass

    # # represent past actions
    # def make_state(self):
    #     state = torch.zeros(self.dice_public * self.dice_sides)
    #     state[self.CUR_IDX] = 1
    #     return state
    
    def _make_bet(self):
        pass

    def _step():
        pass



def train():
    
    pass

if __name__ == '__main__':
    train()