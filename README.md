# Required Python Version
This code is written using Python 3. Any latest version of Python should be able to run the code.

# About the Game
The code contains the simulation for a two-player turn-based game named the Tom and Jerry game. It is a toned-down version of pursuit-evasion game. Agent Tom has to eventually catch Jerry (reachability condition). Agent Jerry has to eventually reach cheese (reachability condition) while always avoiding Tom and traps (safety condition).

The two-player game is reduced to two individual MDPs for each agent to calculate the winning regions and winning policies.

# About the Code
- The file `TomAndJerry2PlayerMDP.py` contains all the code needed for the necessary implementation of the game.
- The file `main.py` contains the main simulation code.

## How to Use
Open `main.py` in an editor and change the initial board setup (Lines 76-79).
Run `main.py` to start the simulation.
Use `Space` key to go to the next turn.
Use `R` key to reset the board to the initial setup.

## Required Libraries
The simulation primarily uses the following libraries. Please ensure you have the following libraries.
- `networkx`
- `pygame`

The code also uses the following packages expected to be in the standard library
- `matplotlib`
- `random`
- `sys`
- `time`

# Acknowledgment
This simulation is part of a group project for the "Formal Methods in Robotics and AI" course by Dr. Jie Fu, Department of Electrical and Computer Engineering, University of Florida, for the Fall 2024 semester.

The group comprised of:
- Andy Prater (andrew.prater@ufl.edu) : Development of theoretical framework
- Fahimur Rahman Shuvo (md.shuvo@ufl.edu) : Theoretical computation of solutions
- Joey Davis (davis.jcharles@ufl.edu) : Coding and environment development
