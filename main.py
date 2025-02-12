from math import inf
from random import randint

class Automaton:

    def check(self, node):
        if node not in self.S:
            raise f'Error: "{node}" is not in the nodes.'

    def __init__(self, input_file):
        ''' Create an automaton from the data contained in input_file '''
        with open(input_file, 'r') as file:
            self.S = file.readline().strip().split(' ')
            self.s0 = file.readline().strip()
            self.check(self.s0)
            self.T = {}
            self.L = []
            for tr in file:
                src, label, dest = tr.strip().split(' ')
                self.check(src)
                self.check(dest)
                self.T[(src, label)] = dest
                self.L.append(label[1:])
        self.is_bipartite = False

    def to_bipartite(self):
        ''' Transform the automaton into a bipartite one '''

        # Init V, E and marks (1 for V_R, -1 for V_B)
        self.V = []
        self.E = {}
        self.marks = {}
        for node in self.S:
            self.V.append(node)
            self.E[node] = []
            self.marks[node] = -1

        # Add of "error" states
        self.V.append("errorR")
        self.marks["errorR"] = 1
        self.V.append("errorB")
        self.marks["errorB"] = -1
        self.E["errorB"] = ["errorR"]
        self.E["errorR"] = ["errorB"]

        # Detection of V_R
        for (src, label) in self.T:
            if label[0] == '!':
                self.marks[src] = 1

        # Generate E (check for transitions within V_R/V_B)
        nb_added = 0
        for (src, label), dest in self.T.items():
            if self.marks[src] * self.marks[dest] == 1:
                node = f'new{nb_added}'
                self.V.append(node)
                self.marks[node] = -self.marks[src]
                self.E[src].append(node)
                self.E[node] = [dest]
                if self.marks[node] == 1:
                    self.E[node].append("errorB")
                nb_added += 1
            else:
                self.E[src].append(dest)

        # Add transitions from V_R to errorB
        for node in self.S:
            if self.marks[node] == 1:
                self.E[node].append("errorB")

        # Remember the process has been done
        self.is_bipartite = True

    def compute_ranks(self, obj):
        ''' Compute the ranks '''

        # Get sure the graph is bipartite
        if not(self.is_bipartite):
            self.to_bipartite()

        # Init ranks
        ranks = {}
        ranks[obj] = 0
        k = 1

        added = True
        while added:
            added = False
            for p in self.V:
                if p in ranks:
                    continue
                if self.marks[p] == -1:
                    for q in self.E[p]:
                        if q in ranks:
                            ranks[p] = k
                            added = True
                            break
                else:
                    for q in self.E[p]:
                        if q not in ranks:
                            break
                    else:
                        ranks[p] = k
                        added = True
            if added == False:
                # W(i+1, j) = W(i, j): we need to increment j
                for p in self.V:
                    if p not in ranks and self.marks[p] == 1:
                        is_found_in = False
                        is_found_not_in = False
                        for q in self.E[p]:
                            if q in ranks:
                                is_found_in = True
                            else:
                                is_found_not_in = True
                        if is_found_in == True and is_found_not_in == True:
                            ranks[p] = k
                            added = True
            k += 1

        # Return the results
        return ranks

    def winning_strategy(self, obj):
        ''' Compute the winning strategy '''

        res = {}
        ranks = self.compute_ranks(obj)

        for node in self.V:
            if self.marks[node] == -1:
                if node == "errorB":
                    res[node] = "tau"
                else:
                    tr = None
                    lowest_rank = None
                    # Check each possible transition
                    for (src, label), dest in self.T.items():
                        if src != node:
                            continue
                        if lowest_rank == None or (ranks[dest] < lowest_rank):
                            tr = label
                            lowest_rank = ranks[dest]
                    res[node] = tr

        return res
    
    def blue_move(self, state, strategy):
        return self.T[(state, strategy[state])]

    def red_move(self, state):
        return self.E[state][randint(0, len(self.E[state])-1)]

    def reproduce(self, trace):
        # Get the sequence of transitions to reproduce
        transitions = []
        with open(trace, 'r') as file:
            for label in file:
                transitions.append(file.readline().strip())

        # Get the state before first transition
        for (src, label) in self.T:
            if label == transitions[0]:
                init_state = src
                break

        # Compute strategies
        strategy_s0 = self.winning_strategy(self.s0)
        strategy_init = self.winning_strategy(init_state)
        
        # Try to reproduce trace
        while True:
            # Init
            print("Trying to read the trace")
            state = self.s0
            print(state)

            # Reach init_state
            while True:
                # Blue turn
                if state == "errorB":
                    break
                else:
                    state = self.blue_move(state, strategy_init)
                    print(state)
                    if state == init_state:
                        player = 1
                        break
                # Red turn
                state = self.red_move(state)
                print(state)
                if state == init_state:
                    player = -1
                    break

            if state == "errorB":
                print("Unexpected comportement of red. Abortion of try.")
                continue

            # Try to follow the transitions
            deviated = False
            for label in transitions:
                if player == -1:
                    if (state, label) not in self.T:
                        deviated = True
                        break
                    else:
                        state = self.T[(state, label)]
                        print(state)
                else:
                    state = self.red_move(state)
                    print(state)
                player = -player

            if deviated:
                print("Deviation from trace. Abortion of try.")
                continue
            else:
                player = -player

            # Reach s0
            while True:
                if player == -1:
                    # Blue turn
                    if state == "errorB":
                        break
                    else:
                        state = self.blue_move(state, strategy_s0)
                        print(state)
                else:
                    # Red turn
                    state = self.red_move(state)
                    print(state)
                if state == self.s0:
                    break
                player = -player
            
            if state == "errorB":
                print("Unexpected comportement of red. Abortion of try.")
                continue
            
            # Win
            print("The trace has been read and is ready to be read again!")
            return


    # def compute_couples_ranks(self):
    #     ''' Compute couples ranks '''

    #     # Get sure the graph is bipartite
    #     if not(self.is_bipartite):
    #         self.to_bipartite()

    #     #Initialize W and the rank dictionary
    #     self.W = [[],[self.t]]
    #     Wmemory = [] #List keeping in memory the previous iteration of W[-1]
    #     self.rankdic = {self.t: (0,0)}
    #     i,j = 0,0

    #     while self.W[-1] != Wmemory:
    #         j+=1
    #         Wmemory = self.W[-1][:]
    #         for p in filter(lambda x: x not in Wmemory, self.V):
    #             if self.marks[p]==-1:
    #                 for q in self.E[p]:
    #                     if q in Wmemory:
    #                         self.W[-1].append(p)
    #                         self.rankdic[p] = (i,j)
    #                         break
    #             else:
    #                 b = True
    #                 for q in self.E[p]:
    #                     if self.marks[q]==-1 and q not in Wmemory:
    #                         b = False
    #                         break
    #                 if b:
    #                     self.W[-1].append(p)
    #                     self.rankdic[p] = (i,j)

    #     while self.W[-1] != self.W[-2]:
    #         i+=1
    #         j=0
    #         self.W.append(self.W[-1][:])
    #         for p in filter(lambda x: x not in self.W[-2], self.V):
    #             if self.marks[p]==1:
    #                 b1,b2 = False,False
    #                 for q in self.E[p]:
    #                     if q in self.W[-2]:
    #                         b1 = True
    #                     else:
    #                         b2 = True
    #                 if b1 and b2:
    #                     self.W[-1].append(p)
    #                     self.rankdic[p] = (i,j)

    #         while self.W[-1] != Wmemory:
    #             j+=1
    #             Wmemory = self.W[-1][:]
    #             for p in filter(lambda x: x not in Wmemory, self.V):
    #                 if self.marks[p]==-1:
    #                     for q in self.E[p]:
    #                         if q in Wmemory:
    #                             self.W[-1].append(p)
    #                             self.rankdic[p] = (i,j)
    #                             break
    #                 else:
    #                     b = True
    #                     for q in self.E[p]:
    #                         if self.marks[q]==-1 and q not in Wmemory:
    #                             b = False
    #                             break
    #                     if b:
    #                         self.W[-1].append(p)
    #                         self.rankdic[p] = (i,j)
    #     self.W.pop(0)
    #     self.W.pop()
    #     for p in filter(lambda x: x not in self.W[-1], self.V):
    #         self.rankdic[p]= (inf,inf)


A = Automaton('input_file')

# print(A.winning_strategy("s3"))

# print(A.E)

A.reproduce('trace')

# A.compute_couples_ranks()
# print(A.rankdic)
# print(A.W)

# TODO: check if problem with error nodes
