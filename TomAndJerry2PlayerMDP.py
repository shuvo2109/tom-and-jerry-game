import networkx as nx
import matplotlib.pyplot as plt
import sys
import random
import copy

NORTH = (0, 1)
SOUTH = (0, -1)
EAST = (1, 0)
WEST = (-1, 0)
STAY = (0, 0)

NORTH_INDEX = 0
EAST_INDEX = 1
SOUTH_INDEX = 2
WEST_INDEX = 3
STAY_INDEX = 4

class TomAndJerry2PlayerMDP:
    def __init__(self, board_dimensions, jerry_start, tom_start):
        ####### BOARD ATTRIBUTES #######################
        self.width = board_dimensions[0]
        self.height = board_dimensions[1]

        self.cheese_locations = []
        self.trap_locations = []

        self.jerry_start = jerry_start
        self.tom_start = tom_start
        
        self.states = []
        for x in range(0, self.width):
            for y in range(0, self.height):
                self.states.append((x,y))

        self.random_transition = {}
        for x in range(self.width):
            for y in range(self.height):
                # Middle Tiles
                q_values = [0.2]*5
                # Top Edge
                if y == self.height - 1:
                    q_values = [0.0 if i == NORTH_INDEX else 0.25 for i in range(5)]
                # East Edge
                if x == self.width - 1:
                    q_values = [0.0 if i == EAST_INDEX else 0.25 for i in range(5)]
                # South Edge
                if y == 0:
                    q_values = [0.0 if i == SOUTH_INDEX else 0.25 for i in range(5)]
                # West Edge
                if x == 0:
                    q_values = [0.0 if i == WEST_INDEX else 0.25 for i in range(5)]
                # NW Corner
                if x == 0 and y == self.height-1:
                    q_values = [0.0 if i == NORTH_INDEX or i == WEST_INDEX else 0.33 for i in range(5)]
                # NE Corner
                if x == self.width - 1 and y == self.height-1:
                    q_values = [0.0 if i == NORTH_INDEX or i == EAST_INDEX else 0.33 for i in range(5)]
                # SE Corner
                if x == self.width - 1 and y == 0:
                    q_values = [0.0 if i == SOUTH_INDEX or i == EAST_INDEX else 0.33 for i in range(5)]
                # SW Corner
                if x == 0 and y == 0:
                    q_values = [0.0 if i == SOUTH_INDEX or i == WEST_INDEX else 0.33 for i in range(5)]
                    
                self.random_transition[(x,y)] = list(q_values)

        self.controlled_transition = nx.DiGraph()
        self.controlled_transition.add_nodes_from(self.states)
        for source in self.states:
            for dest in self.states:
                delta = (dest[0] - source[0], dest[1] - source[1])
                if delta == NORTH:
                    self.controlled_transition.add_edge(source, dest, move="NORTH")
                elif delta == SOUTH:
                    self.controlled_transition.add_edge(source, dest, move="SOUTH")
                elif delta == EAST:
                    self.controlled_transition.add_edge(source, dest, move="EAST")
                elif delta == WEST:
                    self.controlled_transition.add_edge(source, dest, move="WEST")
                elif delta == STAY:
                    self.controlled_transition.add_edge(source, dest, move="STAY")
                else:
                    pass

        # Generate all possible combinations of Tom and Jerry's positions
        # Format: tuple of tuples - ((jerry_x, jerry_y), (tom_x, tom_y)) or vise versa
        dfa_states = []
        for jerry_state in self.states:
            for tom_state in self.states:
                dfa_states.append((jerry_state, tom_state))
        
        # DFA states are in the following format: ((controlled player), (uncontrolled player))
        # Therefore, when Tom looks at the DFA, he places himself in position 0, and Jerry in position 1 of the state
        # And Jerry vise versa
        # Because each player views the movement of the other player as random
        # In this way both players' transitions can be calculated from one transition function
        self.DFA = nx.DiGraph()
        self.DFA.add_nodes_from(dfa_states)

        # This recursive function will overrun the default recursion limit of 1000 if the board is >4x4 tiles
        sys.setrecursionlimit(2000)
        self.create_dfa_recursive(self.jerry_start, self.tom_start, [])
        sys.setrecursionlimit(1000)

        ####### JERRY ATTRIBUTES ########################
        self.jerry_state = self.jerry_start
        self.jerry_won = False
        self.jerry_using_policy = ""

        self.jerry_reach_policy = dict()
        self.jerry_safety_policy = dict()

        self.jerry_reward_function = dict()
        self.jerry_value_function = dict()
        self.jerry_reward_policy = dict()

        self.jerry_caught_reward = -1000000 # reward jerry gets for being caught by tom
        self.jerry_trapped_reward = -1000000 # reward jerry gets for landing in a trap
        self.jerry_cheese_reward = 1000 # rewards jerry gets for reaching the cheese

        # Setup Jerry reward function
        for state in self.DFA.nodes():
            if state[0] == state[1]: self.jerry_reward_function[state] = self.jerry_caught_reward
            elif state[0] in self.trap_locations: self.jerry_reward_function[state] = self.jerry_trapped_reward
            elif state[0] in self.cheese_locations: self.jerry_reward_function[state] = self.jerry_cheese_reward
            else: self.jerry_reward_function[state] = 0

        ####### TOM ATTRIBUTES #########################
        self.tom_state = self.tom_start
        self.tom_won = False
        self.tom_using_policy = ""

        self.tom_reach_policy = dict()
        self.tom_safety_policy = dict()

        self.tom_reward_function = dict()
        self.tom_value_function = dict()
        self.tom_reward_policy = dict()

        self.tom_caught_reward = 1000 # reward tom gets for catching jerry
        self.tom_trapped_reward = 1000 # reward tom gets for catching jerry in a trap
        self.tom_cheese_reward = -1000000 # reward tom gets for jerry reaching the cheese

        # Setup Tom reward function
        for state in self.DFA.nodes():
            if state[1] == state[0]: self.tom_reward_function[state] = self.tom_caught_reward
            elif state[1] in self.trap_locations: self.tom_reward_function[state] = self.tom_trapped_reward
            elif state[1] in self.cheese_locations: self.tom_reward_function[state] = self.tom_cheese_reward
            else: self.tom_reward_function[state] = 0

    def create_dfa_recursive(self, jerry_pos, tom_pos, nodes_already_visited):
        '''
            Recursively initialize the system's Product Transition System
            (Product between board states and player states):
            Size = 2 players * (board states)^2 
        '''
        # Case: all nodes visited
        if (jerry_pos, tom_pos) in nodes_already_visited:
            return

        # General case: visit a new node 
        nodes_already_visited.append((jerry_pos, tom_pos))
        for new_jerry in self.controlled_transition.adj[jerry_pos]:
            for new_tom in self.controlled_transition.adj[tom_pos]:
                source = (jerry_pos, tom_pos)
                dest = (new_jerry, new_tom)
                jerry_move = self.controlled_transition.adj[jerry_pos][new_jerry]["move"]
                delta_tom = (new_tom[0] - tom_pos[0], new_tom[1] - tom_pos[1])
                tom_prob=0.0
                if delta_tom==NORTH:
                    tom_prob=self.random_transition[tom_pos][NORTH_INDEX]
                elif delta_tom==EAST:
                    tom_prob=self.random_transition[tom_pos][EAST_INDEX]
                elif delta_tom==WEST:
                    tom_prob=self.random_transition[tom_pos][WEST_INDEX]
                elif delta_tom==SOUTH:
                    tom_prob=self.random_transition[tom_pos][SOUTH_INDEX]
                elif delta_tom==STAY:
                    tom_prob=self.random_transition[tom_pos][STAY_INDEX]
                else:
                    pass
                self.DFA.add_edge(source, dest, move=jerry_move, prob=tom_prob)
                self.create_dfa_recursive(new_jerry, new_tom, nodes_already_visited=nodes_already_visited)
    
    def SetCheese(self, cheese_locations: list):
        '''
            Initialize cheese positions
        '''
        self.cheese_locations = cheese_locations

    def SetTraps(self, trap_locations: list):
        '''
            Initialize trap positions
        '''
        self.trap_locations = trap_locations

    def AttrUC(self, F_unsafe):
        '''
            Compute unconditional attractor of F_unsafe on the game's DFA.
            AttrUC gives the list of states from which every move has a
            positive probability of leading to the unsafe set, as well as
            a policy for avoiding those states.
        '''
        Xsets = []
        Xsets.append(F_unsafe)

        policy = dict()
        
        while True:
            X_new = set()
            for state in self.DFA.nodes() - Xsets[-1]:

                # Find all possible moves from state
                possible_moves_from_state = set()
                for nbr, edge_data in self.DFA.adj[state].items():
                    possible_moves_from_state.add(edge_data['move'])

                # Find all moves from state with a positive probability of reaching X
                moves_to_add = set()
                for Xstate in Xsets[-1]:
                    if self.DFA.has_edge(state, Xstate):
                        moves_to_add.add(self.DFA.adj[state][Xstate]['move'])

                # If all moves have positive probability of leading to a state in the 
                # uncontrollable attractor, then add state
                if moves_to_add == possible_moves_from_state:
                    X_new.add(state)
                
                # Policy keeps track of all moves which won't lead to the uncontrollable attractor
                policy[state] = possible_moves_from_state - moves_to_add
            
            new_X = X_new.union(Xsets[-1])
            if new_X == Xsets[-1]:
                return new_X, policy

            Xsets.append(new_X)
    
    def Attr(self, Y0: nx.DiGraph, F_goal):
        '''
            Compute attractor of F_goal on the game's DFA.
            Attr gives policy for reaching F_goal with probability one.
            (Not necessarily in finite time)
        '''
        Y = Y0.copy()
        policy = {s: set() for s in Y.nodes()}

        num_steps = 0

        # outer loop
        while True:
            X = F_goal
            X_new = X

            # Inner loop
            while True:
                for s in X_new:
                    
                    for p in Y.predecessors(s):
                        if p not in X_new:
                            X_new.append(p)                                    
                            move = Y.get_edge_data(p,s)['move']
                            policy[p].add(move)
                                
                num_steps += 1
                if num_steps > 1000:
                    print("Error in Attractor computation: Max iterations surpassed")
                    return Y, policy

                if X_new == X:
                    break
                else:
                    X = X_new           

            Y_new = Y.subgraph(X)

            # break when fixed point is reached
            if Y.nodes == Y_new.nodes:
                break
            
            # update Y
            Y = Y_new.copy()
    
        return list(Y.nodes), policy

    def ComputeWins(self):
        '''
            Compute winning regions for Tom and Jerry.
            First, MaxSat policies are computed using value iteration.
            Then, safety shields are computed for Tom and Jerry.
                !!! NOTE: For the majority of boards, Tom's unsafe region will
                the whole board!
            Then, reachability policies are computed for Tom and Jerry.
        '''
        # Make a copy of the TS to modify
        Y_jerry = self.DFA.copy()
        Y_tom = self.DFA.copy()

        ############### Compute MaxSat Policies ####################################
        self.ValueIterationJerry(0.9, 0.05)
        self.ValueIterationTom(0.9, 0.05)

        ############### Compute Safety-Shielded Reachability Policies ###############
        # Find and remove all unsafe states
        F_unsafe_jerry = []
        for state in self.DFA.nodes:
            # Mark all states where jerry lands on a trapped node as unsafe
            if state[0] in self.trap_locations:
                F_unsafe_jerry.append(state)
            # Mark all states where jerry and tom are on the same node as unsafe
            elif state[0] == state[1]:
                F_unsafe_jerry.append(state)
        unsafe_states_jerry, self.jerry_safety_policy = self.AttrUC(F_unsafe_jerry)
        unsafe_states_tom = set(self.DFA.nodes()) - unsafe_states_jerry
        Y_jerry.remove_nodes_from(unsafe_states_jerry)

        # Find and remove all unsafe states
        F_unsafe_tom = []
        for state in self.DFA.nodes:
            # Mark all states where jerry lands on a trapped node as unsafe
            if state[1] in self.cheese_locations:
                F_unsafe_tom.append(state)
        unsafe_states_tom, self.tom_safety_policy = self.AttrUC(F_unsafe_tom)
        Y_tom.remove_nodes_from(unsafe_states_tom)

        # Find goal states
        F_goal_jerry = []
        for state in Y_jerry.nodes():
            if state[0] in self.cheese_locations:
                F_goal_jerry.append(state)
        jerry_states_to_goal, self.jerry_reach_policy = self.Attr(Y_jerry, F_goal_jerry)

        # Find goal states
        F_goal_tom = []
        for state in Y_tom.nodes():
            # Mark all states where jerry lands on a trapped node as goal
            if state[1] in self.trap_locations:
                F_goal_tom.append(state)
            # Mark all states where jerry and tom are on the same node as goal
            elif state[1] == state[0]:
                F_goal_tom.append(state)
        tom_states_to_goal, self.tom_reach_policy = self.Attr(Y_tom, F_goal_tom)

        print(len(unsafe_states_jerry),"out of",len(self.DFA.nodes()),"states are in Jerry's unsafe region")
        print(len(unsafe_states_tom),"out of",len(self.DFA.nodes()),"states are in Tom's unsafe region")

    def ValueIterationJerry(self, gamma, convergence_const):
        '''
            Compute a MaxSat policy for Jerry using Value Iteration.
            Approach outlined in Stanford CS221 Lecture: https://www.youtube.com/watch?v=9g32v7bK3Co
        '''
        V = dict()
        for state in self.DFA.nodes():
            V[state] = 0.0
        
        def Q(state, action):
            neighbors_given_action = set()
            for nbr, edge_data in self.DFA.adj[state].items():
                if edge_data['move'] == action:
                    neighbors_given_action.add(nbr)
            value = 0
            for next_state in neighbors_given_action:
                prob = self.DFA.get_edge_data(state, next_state)['prob']
                value += prob * (self.jerry_reward_function[next_state] + gamma*V[next_state])
            return value
        
        while True:
            V_next = dict()
            for state in self.DFA.nodes():
                # Setup reward function
                if state[0] == state[1]:
                    V_next[state] = self.jerry_caught_reward
                elif state[0] in self.trap_locations:
                    V_next[state] = self.jerry_trapped_reward
                elif state[0] in self.cheese_locations:
                    V_next[state] = self.jerry_cheese_reward
                else:
                    poss_moves = set()
                    for succ in self.DFA.successors(state):                                    
                        move = self.DFA.get_edge_data(state,succ)['move']
                        poss_moves.add(move)
                    V_next[state] = max(Q(state, action) for action in poss_moves)
            
            if max(abs(V[state] - V_next[state]) for state in self.DFA.nodes()) < convergence_const:
                break
            else:
                V = V_next
            
        # Policy
        policy = dict()
        for state in self.DFA.nodes():
            # Don't care what policy for final states
            if state[0] == state[1]:
                policy[state] = set()
            elif state[0] in self.trap_locations:
                policy[state] = set()
            elif state[0] in self.cheese_locations:
                policy[state] = set()
            else:
                poss_moves = set()
                for succ in self.DFA.successors(state):                                    
                    move = self.DFA.get_edge_data(state,succ)['move']
                    poss_moves.add(move)
                policy[state] = { max((Q(state, action), action) for action in poss_moves) [1] }
        self.jerry_reward_policy = policy
        self.jerry_value_function = V

    def ValueIterationTom(self, gamma, convergence_const):
        '''
            Compute a MaxSat policy for Tom using Value Iteration.
            Approach outlined in Stanford CS221 Lecture: https://www.youtube.com/watch?v=9g32v7bK3Co
        '''
        V = dict()
        for state in self.DFA.nodes():
            V[state] = 0.0
        
        def Q(state, action):
            neighbors_given_action = set()
            for nbr, edge_data in self.DFA.adj[state].items():
                if edge_data['move'] == action:
                    neighbors_given_action.add(nbr)
            value = 0
            for next_state in neighbors_given_action:
                prob = self.DFA.get_edge_data(state, next_state)['prob']
                value += prob * (self.tom_reward_function[next_state] + gamma*V[next_state])
            return value
        
        while True:
            V_next = dict()
            for state in self.DFA.nodes():
                # Setup reward function
                if state[1] == state[0]:
                    V_next[state] = self.tom_caught_reward
                elif state[1] in self.trap_locations:
                    V_next[state] = self.tom_trapped_reward
                elif state[1] in self.cheese_locations:
                    V_next[state] = self.tom_cheese_reward
                else:
                    poss_moves = set()
                    for succ in self.DFA.successors(state):                                    
                        move = self.DFA.get_edge_data(state,succ)['move']
                        poss_moves.add(move)
                    V_next[state] = max(Q(state, action) for action in poss_moves)
            
            if max(abs(V[state] - V_next[state]) for state in self.DFA.nodes()) < convergence_const:
                break
            else:
                V = V_next
            
        # Policy
        policy = dict()
        for state in self.DFA.nodes():
            # Don't care what policy for final states
            if state[1] == state[0]:
                policy[state] = set()
            elif state[1] in self.trap_locations:
                policy[state] = set()
            elif state[1] in self.cheese_locations:
                policy[state] = set()
            else:
                poss_moves = set()
                for succ in self.DFA.successors(state):                                    
                    move = self.DFA.get_edge_data(state,succ)['move']
                    poss_moves.add(move)
                policy[state] = { max((Q(state, action), action) for action in poss_moves) [1] }
        self.tom_reward_policy = policy
        self.tom_value_function = V

    def Update(self):
        '''
            Update Tom and Jerry's positions based on each of their respective policies.
            If possible, each player will use a Safety-Shielded Almost-Sure policy.
            If not, each player will use a MaxSat policy.
        '''
        if (len(self.jerry_reach_policy) < 1 or len(self.jerry_reward_policy) < 1):
            print("Error updating: policies have not been calculated yet")
            return

        # If Jerry has a move by which to reach the cheese using the almost-sure reach polic, and
        # that move is within his safe region, then take the safe, Almost-Sure move.
        # If such a move does not exist, then use MaxSat to find the move which maximizes
        # the discounted reward.
        jerry_current_state = (self.jerry_state, self.tom_state)
        jerry_possible_moves = set()
        if self.jerry_reach_policy[jerry_current_state].issubset(self.jerry_safety_policy[jerry_current_state]):
            # Safety-shielded almost-sure reachability policy
            jerry_possible_moves = self.jerry_reach_policy[jerry_current_state]
            self.jerry_using_policy = "Almost Sure"
            print("Jerry Used Safety Shield")
        else:
            # MAXSAT
            jerry_possible_moves = self.jerry_reward_policy[jerry_current_state]
            self.jerry_using_policy = "MaxSat"
            print("Jerry Used RewardMDP")

        jerry_move = random.choice(list(jerry_possible_moves))
        for nbr, edge_data in self.controlled_transition.adj[self.jerry_state].items():
                if edge_data['move'] == jerry_move:
                    self.jerry_state = nbr

        tom_current_state = (self.tom_state, self.jerry_state)
        tom_possible_moves = set()
        if tom_current_state in self.tom_reach_policy:
            if self.tom_reach_policy[tom_current_state].issubset(self.tom_safety_policy[tom_current_state]):
                # Safety-shielded almost-sure reachability policy
                tom_possible_moves = self.tom_reach_policy[tom_current_state]
                self.tom_using_policy = "Almost Sure"
                print("Tom Used Safety Shield")
            else:
                # MAXSAT
                tom_possible_moves = self.tom_reward_policy[tom_current_state]
                self.tom_using_policy = "MaxSat"
                print("Tom Used RewardMDP")
        else:
            # MAXSAT
            tom_possible_moves = self.tom_reward_policy[tom_current_state]
            self.tom_using_policy = "MaxSat"
            print("Tom Used RewardMDP")
        
        tom_move = random.choice(list(tom_possible_moves))
        for nbr, edge_data in self.controlled_transition.adj[self.tom_state].items():
                if edge_data['move'] == tom_move:
                    self.tom_state = nbr
        
        if self.jerry_state == self.tom_state:
            print("GAME OVER: Tom Caught Jerry")
            self.tom_won = True
        elif self.jerry_state in self.trap_locations:
            print("GAME OVER: Jerry Hit a Trap")
            self.tom_won = True
        elif self.jerry_state in self.cheese_locations:
            print("GAME OVER: Jerry Reached the Cheese!")
            self.jerry_won = True

    ################## FUNCTIONS TO HELP VISUALIZE TRANSITION SYSTEMS #####################
    def print_transitions(self):
        for n in self.controlled_transition.nodes:
            print(n,"has outgoing neighbors:")
            for nbr, dict in self.controlled_transition.adj[n].items():
                print(nbr, dict)

    def print_DFA(self):
        for n in self.DFA.nodes:
            print(n,"has outgoing neighbors:")
            for nbr, dict in self.DFA.adj[n].items():
                print(nbr, dict)

    def display_transitions(self):
        pos = nx.spring_layout(self.controlled_transition)

        nx.draw_networkx_nodes(self.controlled_transition, pos=pos)
        nx.draw_networkx_labels(self.controlled_transition, pos=pos)
        nx.draw_networkx_edges(self.controlled_transition, pos=pos, connectionstyle="arc3,rad=0.15") # maek sure edges are separated
        
        edge_labels = nx.get_edge_attributes(self.controlled_transition, "move")
        nx.draw_networkx_edge_labels(self.controlled_transition, pos=pos, edge_labels=edge_labels, verticalalignment="baseline")

        plt.show()

    def display_DFA(self):
        pos = nx.spring_layout(self.DFA)

        nx.draw_networkx_nodes(self.DFA, pos=pos)
        nx.draw_networkx_labels(self.DFA, pos=pos)
        nx.draw_networkx_edges(self.DFA, pos=pos, connectionstyle="arc3,rad=0.15") # maek sure edges are separated
        
        edge_labels = nx.get_edge_attributes(self.DFA, "prob")
        nx.draw_networkx_edge_labels(self.DFA, pos=pos, edge_labels=edge_labels, verticalalignment="baseline")

        plt.show()