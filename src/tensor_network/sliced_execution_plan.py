import util


class SlicedExecutionPlan:
    """
    A complete plan to contract a tensor network, i.e. a contraction tree and indices to slice
    """

    def __init__(self, tree, network):
        """
        Start a plan to contract the tensor network

        :param tree: A contraction tree
        :param network: A tensor network
        """
        self.tree = tree
        self.network = network

        self.edges_to_slice = set()
        self.groups_to_slice = []

        (
            self.FLOPs,
            self.memory,
            self.next_edge_to_slice,
            self.maxrank,
        ) = self.tree.estimate_cost(self.edges_to_slice)

    def contract_small(self, below_size, tensor_api):
        """
        Contract the small tensors in the tensor according to the plan, without slicing

        :param below_size: Contract tensors with fewer than this number of dimensions
        :param tensor_api: Tensor API to use for tensor operations
        :return: None
        """
        # Put a large tensor on top to improve the early contraction
        self.tree = self.tree.reroot(self.network, self.maxrank)

        # Regroup nearby small tensors together
        #   This generally increases the FLOPs of the tree but also improves the early contraction
        self.tree.regroup(below_size)

        self.tree, new_eid_from_old = self.network.identify_partial(
            self.tree, tensor_api, below_size
        )

        # The network edge ids were renumbered, so fix the slice specifications
        self.edges_to_slice = set(
            new_eid_from_old[e] for e in self.edges_to_slice if new_eid_from_old[e] >= 0
        )
        self.groups_to_slice = [
            set(new_eid_from_old[e] for e in group if new_eid_from_old[e] >= 0)
            for group in self.groups_to_slice
        ]
        self.next_edge_to_slice = None

    def slice_at(self, edge):
        """
        Include a slice at this index in the execution plan

        :param edge: The index in the tensor network to slice
        :return: None
        """
        equivalent_edges = self.network.find_equivalent_edges(edge)
        util.log(
            "Memory at "
            + str(self.memory)
            + "; slicing "
            + str(len(equivalent_edges))
            + " edges",
            util.Verbosity.debug,
        )
        self.groups_to_slice.append(equivalent_edges)
        self.edges_to_slice |= equivalent_edges

        (
            self.FLOPs,
            self.memory,
            self.next_edge_to_slice,
            self.maxrank,
        ) = self.tree.estimate_cost(self.edges_to_slice)

    @property
    def total_FLOPs(self):
        return self.FLOPs * (2 ** len(self.groups_to_slice))

    @property
    def widths(self):
        widths = {"Max Rank": self.maxrank}
        # Treewidth-based methods include the width of the underlying tree decomposition
        if hasattr(self.tree, "treewidth"):
            widths["Treewidth"] = self.tree.treewidth
        if hasattr(self.tree, "branchwidth"):
            widths["Branchwidth"] = self.tree.branchwidth
        return widths

    def report_statistics(self, verbosity=util.Verbosity.plan_info):
        """
        Report on the properties of the execution plan.

        :param verbosity: Verbosity to use for printing
        :return: None
        """
        util.output_pair("# Sliced", len(self.groups_to_slice), verbosity)
        util.output_pair("# Network Slices", 2 ** len(self.groups_to_slice), verbosity)
        util.output_pair("Estimated Memory", float(self.memory), verbosity)
        util.output_pair("Estimated FLOPs", float(self.total_FLOPs), verbosity)
