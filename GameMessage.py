
# helper methods for displaying text to cmd prompt
def show_dice(players):
    for p in players:
        print(f'{p} had {p.rolls}')

def display_players(players):
    for p in players:
        print(p.name)

def display_correct_liar_call(caller, bidder, dice_totals, f):
    print(f'Player {bidder.name} was a liar! {caller.name} called them out.')
    print(f'There were {dice_totals[f]} dice of {f}')

def display_incorrect_liar_call(caller, bidder, dice_totals, f):
    print(f'Player {caller.name} incorrectly called {bidder.name} a liar.')
    if dice_totals == 0:
        print(f'There were no dice of {f}')
    else:
        print(f'There were {dice_totals[f]} dice of {f}.')

def display_dice():
    pass