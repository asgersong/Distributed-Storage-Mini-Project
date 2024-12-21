import random
from itertools import permutations

RANDOM_SELECTION = "random"
MIN_COPY_SETS_SELECTION = "min_copy_sets"
BUDDY_SELECTION = "buddy"

class NodeSelectionStrategy:
    """"Parent class for node selection strategies"""
    def __init__(self, no_nodes, no_fragments):
        self.no_nodes = no_nodes
        self.no_fragments = no_fragments

    def choose_nodes(self):
        """"Selects K nodes from the N available nodes"""
        raise NotImplementedError("This method must be implemented by the subclass")

class RandomSelection(NodeSelectionStrategy):
    """Selects K random nodes from the N available nodes TODO: Update comment"""
    def choose_nodes(self):
        chosen = []
        for _ in range(self.no_fragments):
            selected_nodes = random.sample(range(self.no_nodes), self.no_copies)
            chosen.append(selected_nodes)
        return chosen
    
class MinCopySetsSelection(NodeSelectionStrategy):
    """Selects K nodes using the minimum copy sets algorithm"""
    def __init__(self):
        self.copy_sets = None
        self.__initiate_copy_sets()
    
    def choose_nodes(self):
        pass 


    def __initiate_copy_sets(self, scatter_width=2): 
        """Initiate the copy sets for all nodes"""
        no_permutations = scatter_width // (self.no_copies-1) # higher scatter width ==> more copysets/permutatins ==> higher frequency of data loss though with fewer lost chunks? 

        # Divide each permutation into groups of K
        # TODO: it might be really slow to compute all permutations for larger N's (O(N!))
        self.copy_sets = random.sample(permutations(range(self.no_nodes), self.no_copies), no_permutations)
        
class BuddySelection(NodeSelectionStrategy):
    """Selects K nodes using the buddy system"""
    def choose_nodes(self):
        pass

