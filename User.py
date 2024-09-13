import random
from Rules import is_valid_bet
from GameMessage import display_dice
from Action import Action
import itertools

names = ['Alex', 'Bob', 'Charlie', 'Denise', 'Ellyn', 'Frank', 'George', 'Hugh', 'InteractivRobot', 'John', 'Kristin', 'Leeroy', 'Marco', 'Nate', 'Orville', 'Parm', 'Quincy', 'Roger', 'Scott', 'TJ', 'Usher', 'Victor', 'Winston', 'Sir Xylophone', 'Yvette', 'Zach']

# Agent
class Player:
    def __init__(self, dice: int):
        self.NUMDICE = dice        
        self.name = names[random.randrange(len(names))]
        self.active = 1
        self.rolls = []        
        self.last_action = Action.INC_BID
        self.ret = 0 # sum of rewards
        self.reward = 0
        self.discount = .1
        self.trans_prob = .5
    
    # generate dice
    def roll(self):
        self.rolls = []
        for i in range(self.NUMDICE):
            self.rolls.append(random.randrange(1,6))
                
    def get_qty_bet(self):
        qty = int(input())       
        return qty
    
    def get_face_val_bet(self, state):
        in_range = False
        face_val = 0
        while in_range == False:
            face_val = int(input())
            in_range = (face_val >= 1 and face_val <= 6)
        return face_val
    
    def get_action(self, state):
        qty, face_val = 0, 0
        valid_bet = False
        while valid_bet == False:
            qty = self.get_qty_bet()
            face_val = self.get_face_val_bet()
            valid_bet = is_valid_bet(qty, last_qty, face_val, last_face_val)
        return (qty, face_val)

    def choose_bet_type(self, state):
        valid_selection = False
        selection = -1
        while valid_selection == False:
            selection = int(input())
            if selection == Action.INC_BID or selection == Action.CALL_LIE:
                valid_selection = True
        # 1 == increment bet
        if selection == Action.INC_BID:
            self.get_action(state)
        # anything else == call
        else:
            return None
    
    def _get_last_bet(self, state):
        pass
    # we will only calculate 
        
        
    def _get_dice(self):
        return self.rolls
    
    def remove_die(self):
        self.NUMDICE -= 1        