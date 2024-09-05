import random
from Rules import *
from User import Player
from GameMessage import *
from Action import Action
#import argparse

# this is not working with VSCode
# parser = argparse.ArgumentParser()
# parser.add_argument("q", type=int, help="Starting quantity of dice")
# #parser.add_argument("", type=int, help="Starting quantity of dice")
# args = parser.parse_args()

    
class AIGame:

    def __init__(self, player_ct: int, dice_per: int):
        self.player_ct = player_ct
        self.dice_per = dice_per
        self.players = []
        self.IDX = 0     
        self.active_player = Player(dice_per) # index of player who is betting
        self.bet_history = []
        self.dice_totals = {}        
        self.game_over = 0
        self.last_action = Action.NONE
        self.initialize_game()        

    def initialize_game(self):
        self.make_players()
        self.start_round()

    def make_players(self):
        if(self.player_ct < 2):
            self.player_ct = 2
        for p in range(self.player_ct):                            
            self.players.append(Player(self.dice_per))

    def start_round(self):
        self.reset_bet_history()
        self.reset_dice_totals()
        self.game_over = 0        
        for p in range(self.player_ct):
            p.roll()
        self._sum_dice()
        self.active_player = self.players[0]
        while self.game_over == 0:
            self.step()
        
    def step(self):
        # parms passed to ensure legality of bet
        raised_to = self.active_player.choose_bet_type(self.last_bet()[0], self.last_bet()[1])       
        # if current player called the last one a liar
        if raised_to is None:
            self.resolve_liar_call()
        else:
            self.update_bet_history(raised_to)
            self.active_player = self.players[self.next()]


    # training implementation:
    def set_bid(self, q, f):
        lqf = self.last_bet()
        assert is_valid_bet(qty=q, face_val=f, last_qty=lqf[0], last_face_val=lqf[1])
        self.update_bet_history((q,f))

    def resolve_bid(self, raised_to):
            self.update_bet_history(raised_to)
            self.next()
            self.step(self.last_bet()[0], self.last_bet()[1])

    def resolve_liar_call(self):
        q,f = self.last_bet()
        if self.dice_totals.get(f) is None:
            self.active_player = self.players[self.prev()]
            self.active_player.remove_die()
            self.start_round()          
        if self.dice_totals[f] >= q:
            self.active_player = self.players[self.prev()]
            self.active_player.remove_die()
            self.start_round()                
        else:
            self.active_player = self.players[self.prev()]
            self.active_player.remove_die()
            if self.active_player.dice == 0:
                self.active_player.reward = -10
                self.remove_player(self.active_player)
            self.start_round()

    def next(self):
        self.IDX = (self.IDX + 1) % self.player_ct
        return self.IDX

    # don't update the index
    def look_prev(self):
        tmp = (self.IDX - 1)
        if tmp < 0 : tmp = self.player_ct -1 
        return tmp
    # does update the index
    def prev(self):
        self.IDX = (self.IDX - 1)
        if self.IDX < 0 : self.IDX = self.player_ct -1 
        return self.IDX
    
    def _sum_dice(self):
        for p in range(self.player_ct):
            for d in self.players[p].rolls:
                if self.dice_totals.get(d) is None:
                    self.dice_totals[d] = 1
                else:
                    self.dice_totals[d] += 1
    
    def update_bet_history(self, qv):
        self.bet_history.append(qv)
    
    def reset_bet_history(self):
        self.bet_history = []

    def reset_dice_totals(self):
        self.dice_totals = {}

    def last_bet(self):
        return self.bet_history[-1]

    def check_game_over(self):
        return self.players.count == 1
      
    def remove_player(self, player):
        self.players.remove(player)
        self.player_ct -= 1 # Eliminate this variable?
        if self.check_game_over():
            self.end_game()
        else:
            self.set_turn_order() # Reset the turn order now that there is one fewer player

    def end_game(self):
        self.game_over = 1
        print(f'{self.players[0]} wins.')

    # represent the dice that player cannot see as an array of ints representing how many dice they have
    def hidden_dice(self):
        hd = []
        for p in self.players:
            if self.active_player != p:
                hd.append(p.NUMDICE)
        return hd

# start a game with 3 people and 5 dice
#Game(3, 5, 0)