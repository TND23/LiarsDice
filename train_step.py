# import torch
# import torch.nn as nn
# import torch.optim as optim
# import torch.nn.functional as F
from aigame import AIGame
from AI import AI
from Action import Action, ActionType
import os
import time
from typing import List
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

def write_bids_to_file(bid_hist: List[str], filename: str = f'test{time.time()}.txt'):
    """Write bid history to a file.
    
    Args:
        bid_hist: List of bid history strings
        filename: Name of the file to write to
    """
    if os.path.isdir('test'):
        with open(f'test/{filename}', 'w+') as f:
            f.writelines([i + '\n' for i in bid_hist])
    else:
        print('Test directory not found')

def train():
    """Train AI agents by playing games."""
    game = AIGame(2, 5)
    agents = game.players   
    pub_state = game.pub_state
    game.start_round()
    agent = game.active_player
    hist = []
    i = 0
    max_bids = 10
    while game.player_ct > 1 and i < max_bids:
        action = game.step()
        i += 1
        hist.append(f'{game.active_player.name} {action}')
        
        if action.is_call_liar():
            game.start_round()
        else:
            game.step()
            
    write_bids_to_file(hist, '1.txt')
    
if __name__ == '__main__':
    train()


