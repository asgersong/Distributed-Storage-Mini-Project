import random
from itertools import permutations
from config import N, K, NODE_SELECTION

class NodeSelectionStrategy:
    """"Parent class for node selection strategies"""
    def choose_nodes(self):
        """"Selects K nodes from the N available nodes"""
        raise NotImplementedError("This method must be implemented by the subclass")

class RandomSelection(NodeSelectionStrategy):
    """Selects K random nodes from the N available nodes"""
    def choose_nodes(self):
        return random.sample(range(N), K)
    
class MinCopySetsSelection(NodeSelectionStrategy):
    """Selects K nodes using the minimum copy sets algorithm"""
    def __init__(self):
        self.copy_sets = None
        self.__initiate_copy_sets()
    
    def choose_nodes(self):
        pass 


    def __initiate_copy_sets(self, scatter_width=2): 
        """Initiate the copy sets for all nodes"""
        no_permutations = scatter_width // (K-1) # higher scatter width ==> more copysets/permutatins ==> higher frequency of data loss though with fewer lost chunks? 

        # Divide each permutation into groups of K
        # TODO: it might be really slow to compute all permutations for larger N's (O(N!))
        self.copy_sets = random.sample(permutations(range(N), K), no_permutations)
        




class BuddySelection(NodeSelectionStrategy):
    """Selects K nodes using the buddy system algorithm"""
    def choose_nodes(self):
        pass

def get_node_selection_strategy():
    if NODE_SELECTION == "random":
        return RandomSelection()
    elif NODE_SELECTION == "min_copy_sets":
        return MinCopySetsSelection()
    elif NODE_SELECTION == "buddy":
        return BuddySelection()
