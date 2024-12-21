import random

RANDOM_SELECTION = "random"
MIN_COPY_SETS_SELECTION = "min_copy_sets"
BUDDY_SELECTION = "buddy"


class NodeSelectionStrategy:
    """ "Parent class for node selection strategies"""

    def __init__(self, no_nodes, no_fragments, no_replicas):
        self.no_nodes = no_nodes
        self.no_fragments = no_fragments
        self.no_replicas = no_replicas

    def choose_nodes(self):
        """Select <no_replicas> nodes for each fragment"""
        raise NotImplementedError("This method must be implemented by the subclass")


class RandomSelection(NodeSelectionStrategy):
    """Selects nodes randomly"""
    def choose_nodes(self):
        chosen = []
        for _ in range(self.no_replicas):
            selected_nodes = random.sample(
                range(1, self.no_nodes + 1), self.no_fragments
            )
            chosen.append(selected_nodes)
        return chosen

class MinCopySetsSelection(NodeSelectionStrategy):
    """Selects nodes using the minimum copy sets algorithm"""

    def __init__(self, no_nodes, no_fragments, no_replicas):
        super().__init__(no_nodes, no_fragments, no_replicas)
        self.copy_sets = None
        self.__initiate_copy_sets()

    def choose_nodes(self):
        chosen = []
        for _ in range(self.no_fragments):
            selected_nodes = random.choice(self.copy_sets)
            chosen.append(selected_nodes)
        
        # return transpose of the chosen nodes
        return [list(x) for x in zip(*chosen)]

    def __initiate_copy_sets(self):
        """Initiate the copy sets for all nodes"""

        no_copysets = self.no_nodes // self.no_replicas

        copy_sets = []
        available_nodes = list(
            range(1, self.no_nodes+1)
        )  # List of node IDs (1 to no_nodes)

        random.shuffle(available_nodes)

        for _ in range(no_copysets):
            copy_set = random.sample(available_nodes, self.no_replicas)
            copy_sets.append(copy_set)

            # Remove the used nodes
            for node in copy_set:
                available_nodes.remove(node)

        self.copy_sets = copy_sets

class BuddySelection(NodeSelectionStrategy):
    """Selects K nodes using the buddy system"""

    def choose_nodes(self):
        pass
