import random
from Rules import is_valid_bet
class Player:
    def __init__(self, dice: int):
        self.dice = dice
        self.active = 1
        self.rolls = []
        self.called_liar = 0
        self._prev, self._next = None, None
        
    def roll(self):
        self.rolls = []
        for i in range(self.dice):
            self.rolls.append(random.randrange(1,6))
        print(self.rolls)
            
    def call_liar(self, last_qty: int, last_face_val: int):
        print(f"you called {self.prev} a liar")
        self.called_liar = 1
        return (last_qty, last_face_val)
    
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
        print("Would you like to: 1. Increase the bet or 2. Call the last better a liar (Pick 1 or 2)")
        valid_selection = False
        selection = -1
        while valid_selection == False:
            selection = int(input())
            if selection == 1 or selection == 2:
                valid_selection = True
        
        if selection == 1:
            self.place_bet(last_qty, last_face_val)

        else:
            self.call_liar(last_qty, last_face_val)

    def remove_die(self):
        self.dice = self.dice - 1
    
    
        return self._prev
    

    
    