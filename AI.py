from Rules import *
import torch
from collections import deque
from StartRound import Game
import numpy as np 
import random
from model import LinearNet, Trainer
from scipy import stats

MAX_MEM = 100_000
BATCH_SIZE = 2**6
LEARN_RATE = 0.01

RULE_IDX = 0
BET_HIST_IDX = 1
VISIBLE_DICE_CT_IDX = 2
ACTIVE_PLAYER_CT_IDX = 3
LAST_ACTION_IDX = 4


class Agent:
    def __init__(self, ruleset):
        self.memory = deque(maxlen=MAX_MEM)
        self.n_games = 0
        self.epsilon = 0 # control randomness
        self.gamma = 0.5
        self.ruleset = ruleset
        self.model  = LinearNet(11, 256, 10)
        self.trainer = Trainer(self.model, learn_rate=LEARN_RATE, gamma=self.gamma)
        self.state = np.array([])

    # TODO: make hidden dice relative to current players position (e.g. if the next player has 2 dice, the first element should be 2)
    def get_state(self, game):
        bet_hist_len = len(game.bet_history)
        hidden_dice = game.hidden_dice()
        visible_dice_ct = len(game.active_player.rolls)
        visible_dice = game.active_player.rolls
        active_players = game.player_ct
        last_action = game.last_action

        self.state = [self.ruleset, bet_hist_len, visible_dice_ct, active_players, last_action.value]


        for d in hidden_dice:
            self.state.append(d)
        self.state += [visible_dice_ct]

        for d in visible_dice:
                    self.state.append(d)

        if bet_hist_len > 0:
            for i in range(bet_hist_len):
                self.state.append(game.bet_history[i][0])
                self.state.append(game.bet_history[i][1])
        
        
        return np.array(self.state)

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def train_memory(self):
        pass

    def train_short_memory(self):        
        pass
        
    def get_action(self, state):
        self.epsilon = 80 - self.n_games
        hist = []
        for i in range(2, 2 + (self.state[BET_HIST_IDX] * 2)):
            hist.append(self.state[i])
        
        bid_type = -1
        bid_increment = (0,0)
        # if first bidder, they cannot call liar
        if state[BET_HIST_IDX] == 0:
            bid_type = 0

        # chance to use baked-in strategy        
        if random.randint(0,200) < self.epsilon:
            bid_type = random.randint(0,2)
            # increment somewhere between 1, but go no larger than the total number of dice for q
            if bid_type == 1:
                return None
            else:
                bid_increment[0] = random.randint(1, min(hist[-2] + 2, state[VISIBLE_DICE_CT_IDX]+ self._hidden_dice_total(state)))
                bid_increment[1] = self._determine_face_bet(hist, self._visible_dice(state))
                return bid_increment
        else:
            state0 = torch.tensor(state)
            pred = self.model(state0)
            if bid_type == 1:
                return None
            else:
                bid_res = torch.argmax(pred).item()
                return bid_res

    def _determine_face_bet(self, hist, visible_dice):
        face_bets = []
        for i in range(0, len(hist), step=2):
            face_bets.append(hist[i])
 
        seed = random.randint(0,100)
        if seed < 10:
            return random.randint(1,6)
        elif seed < 50:
            return stats.mode(visible_dice)
        elif seed < 60:
            return np.median(face_bets)
        else:
            return stats.mode(face_bets)
    
    def _hidden_dice_total(self, state):
        return sum(state[LAST_ACTION_IDX+1:LAST_ACTION_IDX+state[ACTIVE_PLAYER_CT_IDX]])
   
    def _visible_dice(self, state):
        offset = LAST_ACTION_IDX + state[ACTIVE_PLAYER_CT_IDX]
        dice_ct = state[VISIBLE_DICE_CT_IDX]
        dice = state[offset:offset + 1 + dice_ct]
        return dice
    
def train():
    agent = Agent(0)
    game = Game(2,5,1)
    prev_state = agent.get_state(game)
    print(prev_state)
    

if __name__ == '__main__':
    train()