from Rules import *
import torch
# Approach: (reinforcement) -> into supervised learning
# create bots that play against each other and log the results
# want most bots to play like people rather than in a statistically optimal way
# so can use classification to pick strong candidates for different bot types e.g.
# a good, aggressive bot or a conservative play style bot 

"""
    Game
    Model
        Train
            get_state
            get_move(state)
                model.predict
            game.step
            new_state
            train
    Use case:

        Bot b = Bot("Aggressive")
"""
class Action:
    # There are only two actions available: raising the bet or calling
    def __init__(self):
        # use one-hot encoding
        self.increment_bet = [1,0]
        self.call_liar = [0,1]

class Game:
    def __init__(self, num_dice, num_players, dice_sides, ruleset) -> None:

        self.active_player = None
        self.last_bet = (0,0)
        self.pub_dicehst = [()]
        self.priv_dice = []
        self.dice_per_player = num_dice
        self.dice_public = num_dice * num_players
        self.dice_sides = dice_sides
        self.CUR_IDX = 1  # acting player
        self.RULESET = ruleset
    
    # represent past actions
    def make_state(self):
        state = torch.zeros(self.dice_public * self.dice_sides)
        state[self.CUR_IDX] = 1
        return state
    
    def make_bet(self):
        pass

    def step():
        pass


