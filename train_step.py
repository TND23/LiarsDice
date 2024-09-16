# import torch
# import torch.nn as nn
# import torch.optim as optim
# import torch.nn.functional as F
from aigame import AIGame
from AI import *
from Action import *
#import numpy as np
# state = [0,5,3,0,5,5,5,6,6,5,3,1]
# q_table = {(0,1): .2, (0,0): .3, (1,0) : .2, (1,1) : .8}
# next_state = [1,5,3,0,4,5,5,6,5,3,1,1,3,3]
# q_vals = np.zeros((0,0,5))
# def train_step(state):
#     state = torch.tensor(state, dtype=torch.float)
#     unsq_state = torch.usnsqueeze(state, 0)
#  #   next_state = torch.tensor(next_state, dtype=torch.float)
#     print(state)
#     print(unsq_state)
# train_step(state)
    # action = torch.tensor(action, dtype=torch.long)
    # reward = torch.tensor(reward, dtype=torch.float)

def train():
    game = AIGame(2,5)
    agents = game.players
    agent = agents[0]
    pub_state = game.pub_state
    while game.player_ct > 1:
        #prev_state = agent.get_state(game)
        bid = agent.get_action(pub_state)
        if bid == LIE_TUPLE:
            game.start_round()

if __name__ == '__main__':
    train()


