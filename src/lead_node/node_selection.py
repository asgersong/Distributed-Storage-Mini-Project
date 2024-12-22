import random
import math

RANDOM_SELECTION = "random"
MIN_COPY_SETS_SELECTION = "min_copy_sets"
BUDDY_SELECTION = "buddy"


class NodeSelectionStrategy:
    """Parent class for node selection strategies"""

    def __init__(self, no_nodes, no_fragments, no_replicas):
        self.no_nodes = no_nodes
        self.no_fragments = no_fragments
        self.no_replicas = no_replicas

    def choose_nodes(self):
        """Select <no_replicas> nodes for each fragment"""
        raise NotImplementedError("This method must be implemented by the subclass")

    def initiate_replication_groups(self, no_groups, group_size):
        """Initiate the replication group for all nodes"""
        replication_groups = []
        available_nodes = list(range(1, self.no_nodes + 1))
        random.shuffle(available_nodes)
        for _ in range(no_groups):
            group = random.sample(available_nodes, group_size)
            replication_groups.append(group)
            for node in group:
                available_nodes.remove(node)

        # remove unused nodes from available nodes
        available_nodes = [node for group in replication_groups for node in group]
        return replication_groups, available_nodes


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
        self.available_nodes = None
        self.__initiate_copy_sets()

    def choose_nodes(self):
        # choose no_fragments nodes at random
        primary_nodes = random.choices(self.available_nodes, k=self.no_fragments)

        # find the copy sets that contain the primary nodes
        copy_sets = []
        for primary_node in primary_nodes:
            for copy_set in self.copy_sets:
                if primary_node in copy_set:
                    copy_sets.append(copy_set)
                    break
        # return transpose of copy_sets
        return list(map(list, zip(*copy_sets)))

    def __initiate_copy_sets(self):
        """Initiate the copy sets for all nodes"""

        no_copysets = self.no_nodes // self.no_replicas
        self.copy_sets, self.available_nodes = self.initiate_replication_groups(
            no_copysets, self.no_replicas
        )


class BuddySelection(NodeSelectionStrategy):
    """Selects K nodes using the buddy system"""

    def __init__(self, no_nodes, no_fragments, no_replicas):
        super().__init__(no_nodes, no_fragments, no_replicas)
        self.buddies = None
        self.available_nodes = None
        self.__initiate_buddies()

    def choose_nodes(self):
        # choose no_fragments buddy groups at random
        buddy_groups = random.choices(range(len(self.buddies)), k=self.no_fragments)

        # within each buddy group, choose no_replicas nodes at random for each fragment
        chosen = []
        for buddy_group in buddy_groups:
            selected_nodes = random.sample(self.buddies[buddy_group], self.no_replicas)
            chosen.append(selected_nodes)
        return list(map(list, zip(*chosen)))

    def __initiate_buddies(self):
        """Initiate the replication group for all nodes"""
        no_groups = math.floor(math.sqrt(self.no_nodes / self.no_replicas))
        self.buddies, self.available_nodes = self.initiate_replication_groups(
            no_groups, self.no_nodes // no_groups
        )
        print("Buddies:", self.buddies)
