import random
from Rules import is_valid_bet
from GameMessage import display_dice
from Action import Action, ActionType, Bid
import itertools
from typing import Optional, Tuple, List, Any

names = ['Alex', 'Bob', 'Charlie', 'Denise', 'Ellyn', 'Frank', 'George', 'Hugh', 'InteractivRobot', 'John', 'Kaitlyn', 'Leeroy', 'Marco', 'Nate', 'Orville', 'Parm', 'Quincy', 'Roger', 'Scott', 'TJ', 'Usher', 'Victor', 'Winston', 'Sir Xylophone', 'Yvette', 'Zach']

# Agent
class Player:
    def __init__(self, dice: int):
        self.NUMDICE = dice        
        self.name = names[random.randrange(len(names))]
        self.active = 1
        self.rolls: List[int] = []        
        self.last_action: Optional[Action] = None
        self.ret = 0 # sum of rewards
        self.reward = 0
        self.discount = .1
        self.trans_prob = .5
    
    # generate dice
    def roll(self):
        self.rolls = []
        for i in range(self.NUMDICE):
            self.rolls.append(random.randrange(1,7))
                
    def get_qty_bet(self) -> int:
        qty = int(input("Enter quantity: "))       
        return qty
    
    def get_face_val_bet(self) -> int:
        in_range = False
        face_val = 0
        while not in_range:
            face_val = int(input("Enter face value (1-6): "))
            in_range = (1 <= face_val <= 6)
        return face_val
    
    def get_action(self, state: List[Any], last_action: Optional[Action], total_dice: int) -> Action:
        """Get a valid action from the user.
        
        Args:
            state: The current game state
            last_action: The previous action in the game
            total_dice: Total number of dice in play
            
        Returns:
            Action: The user's chosen action
        """
        print("Choose action type:")
        print("1. Make a bid")
        print("2. Call liar")
        
        action_type = int(input("Enter choice (1 or 2): "))
        
        if action_type == 1:
            # Make a bid
            valid_bet = False
            while not valid_bet:
                qty = self.get_qty_bet()
                face_val = self.get_face_val_bet()
                
                # Create a temporary action to validate
                temp_action = Action.make_bid(qty, face_val)
                valid_bet = is_valid_bet(temp_action, last_action, total_dice)
                
                if not valid_bet:
                    print("Invalid bid. Try again.")
            
            return Action.make_bid(qty, face_val)
        else:
            # Call liar
            return Action.call_liar()
    
    def _get_dice(self) -> List[int]:
        return self.rolls
        
    def remove_die(self):
        """Remove one die when losing"""
        self.NUMDICE -= 1
        if self.rolls:
            self.rolls.pop()        