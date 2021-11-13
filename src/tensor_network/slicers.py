import collections
import math
import random


class BaseSlicer:
    def slice_once(self, plan):
        raise NotImplementedError

    def slice_until(self, plan, memory=None, rank=None, slices=None):
        """
        Determine which slices to make in the tensor network to adhere to the given resource constraints
        :param plan: Plan to modify by slicing
        :param memory: Upper bound of memory usage, in terms of number of tensor entries
        :param rank: Upper bound on tensor dimensions
        :param slices: Lower bound on number of slices to use
        :return:
        """
        while memory is not None and memory < plan.memory:
            self.slice_once(plan)
        while rank is not None and rank < plan.maxrank:
            self.slice_once(plan)
        while slices is not None and len(plan.groups_to_slice) < slices:
            self.slice_once(plan)


class GreedyMemSlicer(BaseSlicer):
    """
    Slice greedily to lower memory usage
    """

    def slice_once(self, plan):
        plan.slice_at(plan.next_edge_to_slice)


class GreedyLargestSlicer(BaseSlicer):
    """
    Slice an edge of the largest intermediate tensor, randomly.
    """

    def slice_once(self, plan):
        max_size, edges = 0, None
        for node in plan.tree.iterate_postorder():
            size = sum(0 if e in plan.edges_to_slice else 1 for e in node.free_edges)
            if size > max_size:
                max_size = size
                edges = node.free_edges

        plan.slice_at(random.choice(edges))


class GreedyMostSlicer(GreedyMemSlicer):
    """
    Slice the edge that appears in the most intermediate tensors above the resource limit.
    """

    def slice_until(self, plan, memory=None, rank=None, slices=None):
        highest_allowable_rank = min(
            float("inf") if rank is None else rank,
            float("inf") if memory is None else math.floor(math.log2(memory)),
        )
        if not math.isinf(highest_allowable_rank):
            rep_edge = plan.network.equivalent_edge_sets()
            nodes = list(plan.tree.iterate_postorder())
            node_sizes = [
                sum(0 if e in plan.edges_to_slice else 1 for e in node.free_edges)
                for node in nodes
            ]

            # For each edge e, record the large nodes that e is incident to
            large_nodes_by_edge = collections.defaultdict(set)
            for i in range(len(nodes)):
                if node_sizes[i] > highest_allowable_rank:
                    for e in nodes[i].free_edges:
                        if e not in plan.edges_to_slice:
                            large_nodes_by_edge[rep_edge[e]].add(i)

            if len(large_nodes_by_edge) > 0:  # Otherwise, there are no large nodes
                while True:
                    max_count = max(len(n) for n in large_nodes_by_edge.values())
                    if max_count == 0:
                        break
                    chosen_edge = random.choice(
                        [
                            e
                            for e in large_nodes_by_edge
                            if len(large_nodes_by_edge[e]) == max_count
                        ]
                    )
                    # Update large_nodes_by_edge for the next iteration
                    #   (Note the top-level list to avoid modifying the iterated set)
                    for i in list(large_nodes_by_edge[chosen_edge]):
                        for e in nodes[i].free_edges:
                            if e not in plan.edges_to_slice:
                                large_nodes_by_edge[rep_edge[e]].discard(i)

                    plan.slice_at(chosen_edge)
        # To handle the remaining slices, revert to the old greedy strategy
        super().slice_until(plan, memory, rank, slices)


class DisabledSlicer(BaseSlicer):
    """
    Perform no slicing.
    """

    def slice_once(self, plan):
        raise RuntimeError("Slicing is disabled")

    def slice_until(self, plan, memory=None, rank=None, slices=None):
        if memory is not None and memory < plan.memory:
            raise RuntimeError("Slicing is disabled but plan memory is too large ")
        if rank is not None and rank < plan.maxrank:
            raise RuntimeError("Slicing is disabled but plan maxrank is too large")
        if slices is not None and len(plan.groups_to_slice) < slices:
            raise RuntimeError("Slicing is disabled; --minimum_slice is disallowed")


ALL_SLICERS = {
    "greedy_mem": GreedyMemSlicer(),
    "disable": DisabledSlicer(),
    "greedy_largest": GreedyLargestSlicer(),
    "greedy_most": GreedyMostSlicer(),
}
