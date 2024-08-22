
# Liar's Dice

Goal: Create a flexible AI for the liar's dice game using a modified neural fictitious self-play implementation.

Optimal play for a two-player game of liar's dice has already been implemented by thomasahle in his liar's dice repo. The goal of this project is to implement a learning approach that can generate models to play either at a specified sub-optimal level, which will be limited by limiting the set of actions available in the action-value function.

## Motivation

The complexity of state and particularly available actions increases exponentially with relation to players and dice. Therefore it is easier to create something that is approximately optimal. Moreover, a computer that plays perfectly may not be particularly engaging for people who play against it, and creating models with some exploitability may make it more enjoyable. 
