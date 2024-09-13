import random
from Rules import *
from AI import Agent
from GameMessage import *
from Action import Action
import itertools
from const import * 
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
        self.active_player = None # index of player who is betting
        self.bet_history = []
        self.dice_totals = {}        
        self.game_over = 0
        self.last_action = Action.NONE
        self.pub_state = []
        self.initialize_game()        

    def initialize_game(self):
        self.make_players()
        self.set_pub_state()
        #self.start_round()

    def make_players(self):
        if(self.player_ct < 2):
            self.player_ct = 2
        for p in range(self.player_ct):                            
            self.players.append(Agent(p))

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
        raised_to = self.active_player.get_action(self.last_bet()[0], self.last_bet()[1])       
        # if current player called the last one a liar
        if raised_to is Action.CALL_LIE:
            self.resolve_liar_call()
        else:
            self.update_bet_history(raised_to)
            self.active_player = self.players[self.next()]

    def resolve_bid(self, raised_to):
        self.update_bet_history(raised_to)
        self.next()
        self.step(self.last_bet()[0], self.last_bet()[1])

    def resolve_liar_call(self):
        q,f = self.last_bet()
        if self.dice_totals.get(f) is None:
            self.active_player.reward += self.active_player.discount * 5            
            self.active_player = self.players[self.prev()]
            self.active_player.remove_die()
            self.start_round()          
        if self.dice_totals[f] >= q:
            self.active_player.reward += self.active_player.discount * 5
            self.active_player = self.players[self.prev()]
            self.active_player.reward -= self.active_player.discount * 5
            self.active_player.remove_die()
            self.start_round()                
        else:
            self.players[self.look_prev()].reward  += self.players[self.look_prev()].discount * 5
            self.active_player.remove_die()
            self.active_player.reward -= self.active_player.discount * 5
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

    def _all_rolls(self, player):
        assert player in self.players
        n_faces = self.D1 if player == 0 else self.D2
        return [
            tuple(sorted(r))
            for r in itertools.product(range(1, self.SIDES + 1), repeat=n_faces)
        ]

    def _sum_dice(self):
        for p in range(self.player_ct):
            for d in self.players[p].rolls:
                if self.dice_totals.get(d) is None:
                    self.dice_totals[d] = 1
                else:
                    self.dice_totals[d] += 1
    
    def update_bet_history(self, qv):
        self.bet_history.append(qv)
        self.pub_state.append(qv[0])
        self.pub_state.append(qv[1])
        self.pub_state[BET_HIST_IDX] += 1
    
    def reset_bet_history(self):
        self.bet_history = []
        self.pub_state[BET_HIST_IDX] = 0

    def reset_dice_totals(self):
        self.dice_totals = {}

    def last_bet(self):
        if len(self.bet_history) > 0:
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

    def set_pub_state(self):
        self.pub_state = [len(self.bet_history), self.player_ct, self.last_action]
        dice_ct = 0
        for x in self.players:
            dice_ct += x.NUMDICE
        #dice_ct = sum([x for x in self.players.])
        self.pub_state.append(dice_ct)
        self.pub_state.append(self.hidden_dice())
    
    # represent the dice that player cannot see as an array of ints representing how many dice they have
    def hidden_dice(self):
        hd = []        
        for p in self.players:
            hd.append(p.NUMDICE)
        return hd