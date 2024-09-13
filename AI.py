from Rules import *
import torch
from collections import deque
import numpy as np 
import random
from model import LinearNet, Trainer
from scipy import stats
from itertools import combinations_with_replacement
from Action import *
from const import *

q_vals = np.zeros

class Agent:
    def __init__(self, p_index):
        self.memory = deque(maxlen=MAX_MEM)
        # self.n_games = 0
        # hard coding as 5 dice per agent for now
        self.NUMDICE = 5
        self.epsilon = 200 
        self.gamma = 0.5
        self.model  = LinearNet(11, 256, 10)
        self.trainer = Trainer(self.model, learn_rate=LEARN_RATE, gamma=self.gamma)
        self.rolls = np.array([]) # private state
        self.reward = 0
        self.p_index = p_index

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))
 
    def get_action(self, pub_state, player_ct):
        #self.epsilon = 80 - self.n_games
        if pub_state[LAST_ACTION_IDX] in (Action.INC_BID, Action.NONE):
            bid = self.perform_bid_action(pub_state, player_ct)
            return bid

    def roll(self):
        self.rolls = []
        for _ in range(self.NUMDICE):
            self.rolls.append(random.randrange(1,6))
            
    def perform_bid_action(self, pub_state, player_ct):
        initial_bid = self._is_initial_bid(pub_state)
        hist = [] if initial_bid else [i for i in enumerate(pub_state[pub_state[BET_HIST_IDX]+1:-player_ct])]
        bid_increment = [0, 0]
        # chance to use baked-in strategy (always do this for now)
        #if random.randint(0,200) < self.epsilon:
            # if you can call a player a liar (i.e. there is a previous call that can be reacted to, chacne to call lie)
        # increment somewhere between 1, but go no larger than the total number of dice for q
        if (bid_increment[0] >= pub_state[TOTAL_DICE_IDX] or self.feeling_feisty()) and initial_bid == False:
            return LIE_TUPLE
        if initial_bid:
            bid_increment[0] = random.randint(1, pub_state[TOTAL_DICE_IDX])
            bid_increment[1] = random.randint(1,7)
        else:
            bid_increment[0] = random.randint(1, min(hist[-2] + 2, pub_state[TOTAL_DICE_IDX]))
            bid_increment[1] = self._determine_face_bet(hist, self.rolls)
        return tuple(bid_increment)
        # else:
        #     state0 = torch.tensor(pub_state)
        #     pred = self.model(state0)
        #     if bid_type == 1:
        #         return None
        #     else:
        #         bid_res = torch.argmax(pred).item()
        #         return bid_res
    
    def _is_initial_bid(self, pub_state):
        return pub_state[BET_HIST_IDX] == 0

    def feeling_feisty(self):
        return random.randint(1,100) < 33

    # create q table private state component
    def _all_rolls(self, player):
        dice = player.NUMDICE
        # hard coding 6 dice for now
        possible_d_rolls = list(range(1,7))
        return list(combinations_with_replacement(possible_d_rolls, dice))
    # hard coding 6 sided dice for now
    def _all_actions(self, last_bet, global_dice_ct):
        res = []
        if last_bet:
            res.append(LIE_TUPLE)
            q = last_bet[0]
            f = last_bet[1]
            for x in range(f,7):
                res.append((q,x))
            for q2 in range(q+1,global_dice_ct+1):
                for f2 in range(1,7):
                    res.append(q2,f2)
        else:
            for q2 in range(1,global_dice_ct+1):
                for f2 in range(1,7):
                    res.append(q2,f2)
        return res

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
    
    def remove_die(self):
        self.NUMDICE -= 1   

    def get_rolls(self):
        return self.rolls
    # TODO section
    
    # rather than representing every state, we seek to derive optimal play by piggybacking 
    # off of extremes    
    def derive_extremes(self):
        pass
    
    def calc_reward(self):
        pass

    def train_memory(self):
        pass

    def train_short_memory(self):        
        pass