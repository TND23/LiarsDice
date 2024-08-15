import random
from Rules import is_valid_bet
from GameMessage import display_dice
from StartRound import Action
names = ['Alex', 'Bob', 'Charlie', 'Denise', 'Ellyn', 'Frank', 'George', 'Hugh', 'InteractivRobot', 'John', 'Kristin', 'Leeroy', 'Marco', 'Nate', 'Orville', 'Parm', 'Quincy', 'Roger', 'Scott', 'TJ', 'Usher', 'Victor', 'Winston', 'Sir Xylophone', 'Yvette', 'Zach']

class Player:
    def __init__(self, dice: int):
        self.NUMDICE = dice        
        self.name = names[random.randrange(len(names))]
        self.active = 1
        self.rolls = []
        self._prev, self._next = None, None
        
    
    # generate dice
    def roll(self):
        self.rolls = []
        for i in range(self.NUMDICE):
            self.rolls.append(random.randrange(1,6))
        print(f'{self.name}: {self.rolls}')
                
    def get_qty_bet(self):
        print("How many dice")
        qty = int(input())       
        return qty
    
    def get_face_val_bet(self):
        in_range = False
        face_val = 0
        while in_range == False:
            print("What dice face are you betting on (1-6)")
            face_val = int(input())
            in_range = (face_val >= 1 and face_val <= 6)
            if in_range == False:
                print("Select a number between 1 and 6.")
        return face_val
    
    def place_bet(self, last_qty: int, last_face_val: int):
        qty, face_val = 0, 0
        valid_bet = False
        while valid_bet == False:
            qty = self.get_qty_bet()
            face_val = self.get_face_val_bet()
            valid_bet = is_valid_bet(qty, last_qty, face_val, last_face_val)
            if valid_bet == False:
                print(f"You tried to bet there were {qty} or more dice with {face_val}, but this is not a larger bet than {last_qty} or more dice with {last_face_val}. Try another bet." )
        print(f"I say that there are {qty} or more dice with the {face_val} facing up!")
        return (qty, face_val)

    def choose_bet_type(self, last_qty: int, last_face_val: int):
        print("Would you like to: 0. Increase the bet or 1. Call the last better a liar (Pick 0 or 1)")
        valid_selection = False
        selection = -1
        while valid_selection == False:
            selection = int(input())
            if selection == Action.INC_BID or selection == Action.CALL_LIE:
                valid_selection = True
        # 1 == increment bet
        if selection == Action.INC_BID:
            self.place_bet(last_qty, last_face_val)
        # anything else == call
        else:
            return None
    
    def _get_dice(self):
        return self.rolls
    
    def remove_die(self):
        self.NUMDICE -= 1
        return self._prev
    
