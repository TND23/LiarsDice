import random
from Rules import *
from User import Player
class Game:


    def __init__(self, player_ct: int, dice_per: int):
        self.player_ct = player_ct
        self.dice_per = dice_per
        self.players = []
        self.running = 1    
        
        self.active_player = Player(dice_per) # index of player who is betting
        self.turns = self.Turn(self.active_player)
        self.last_qty = 0
        self.last_dice_val = 0
        self.bet_history = []

        self.dice_totals = {}
        
        self.initialize_game()        

    # want to track turn order in here
    # class TurnOrder:
    #     def __init__(self, players: list):
    #         self.last_bet = (0,0)
    #         self.bet_history = [(0,0)] # only useful if there are bots
    #         self.player_circle = self.set_circle(players)
    #         pass

    #     def set_circle(self, players):
    #         for p in players:
                
    class Turn:
        def __init__(self, player):
            self.player = player
            self._next = None
            self._prev = None

        def next_player(self):
            return self._next
        
        def prev_player(self):
            return self._prev

        def assign_next(self, next_player):
            self._next = next_player

        def assign_prev(self, prev_player):
            self._last


    def initialize_game(self):
        self.make_players()
        self.start_round()

    def make_players(self):
        # cannot play solo
        if(self.player_ct < 2):
            self.player_ct = 2
        for p in range(self.player_ct):                            
            self.players.append(Player(self.dice_per))
        
        for i in range(self.player_ct):
            _p = self.players[i]
            if i == 0:
                _p._prev = self.players[-1]
                _p._next = self.players[1]
            elif i == len(self.players) - 1:
                _p._next = self.players[0]
                _p._prev = self.players[-2]
            else:
                _p._next = self.players[i+1]
                _p._prev
         
    def start_round(self):
        for p in range(self.player_ct):
            self.players[p].roll()
        # track the total dice
        self.sum_dice()

        cur = self.players[0]
        cur.place_bet(self.last_qty, self.last_dice_val)
        self.continue_round(self.last_qty, self.last_dice_val)

    def continue_round(self, last_qty: int, last_dice_val: int):
        # move to next player
        cur = self.next_player()
        res = cur.choose_bet_type(self.last_qty, self.last_dice_val)
        # if current player called the last one a liar
        if self.active_player.called_liar:
            if self.dice_totals[self.last_dice_val] <= self.last_qty:
                self.active_player.remove_die()
                print(f'Player {self.active_player} incorrectly called {self.active_player._prev} a liar.')
                print(f'There were {self.dice_totals[self.last_dice_val]} dice of {self.last_dice_val}.')
                self.start_round()
            else:
                self.active_player._prev.remove_die()
                self.active_player = self.active_player._prev
                print(f'Player {self.active_player._prev} was a liar! {self.active_player} called them out.')
                print(f'There were {self.dice_totals[self.last_dice_val]} dice of {self.last_dice_val}')
                self.start_round()
        else:
            self.last_qty = res[0]
            self.last_dice_val = res[1]
            self.continue_round(self.last_qty, self.last_dice_val)

    def next_player(self):
        self.active_player = self.active_player._next
        return self.active_player
    
    def sum_dice(self):
        for p in range(self.player_ct):
            for d in self.players[p].rolls:
                if self.dice_totals.get(d) is None:
                    self.dice_totals[d] = 1
                else:
                    self.dice_totals[d] += 1
    
    def show_dice(self):
        for p in self.players:
            print(f'{p} had {p.rolls}')
       

class AI:
    
    def __init__(self):
        print("Hey")
    

g = Game(1,2)