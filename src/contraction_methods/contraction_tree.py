from cached_property import cached_property
from typing import List, Union, FrozenSet
from tensor_network.tensor_network import TensorNetwork


ContractionTree = Union[
    "ContractionTreeNode", "ContractionTreeLeaf", "ContractionTreeEmpty"
]
NonemptyContractionTree = Union["ContractionTreeNode", "ContractionTreeLeaf"]


class ContractionTreeNode:
    __left: NonemptyContractionTree
    __right: NonemptyContractionTree
    __leaves: FrozenSet[int]

    def __init__(self, left: NonemptyContractionTree, right: NonemptyContractionTree):
        self.__left = left
        self.__right = right
        self.__leaves = self.__left.leaves | self.__right.leaves

    def is_leaf(self) -> bool:
        return False

    def iterate_postorder(self):
        processed = [(self, False)]
        while len(processed) > 0:
            node, expanded = processed.pop()
            if expanded or node.is_leaf():
                yield node
            else:
                processed.append((node, True))
                processed.append((node.__right, False))
                processed.append((node.__left, False))

    @property
    def left(self) -> NonemptyContractionTree:
        return self.__left

    @property
    def right(self) -> NonemptyContractionTree:
        return self.__right

    @property
    def leaves(self) -> FrozenSet[int]:
        return self.__leaves

    @cached_property
    def free_edges(self) -> List[int]:
        edges = []
        left_edges = self.__left.free_edges
        right_edges = self.__right.free_edges
        edges.extend(e for e in left_edges if e is None or e not in right_edges)
        edges.extend(e for e in right_edges if e is None or e not in left_edges)
        return edges

    @cached_property
    def maxrank(self) -> int:
        rank = 0
        for node in self.iterate_postorder():
            rank = max(rank, len(node.free_edges))
        return rank

    @cached_property
    def required_FLOPS(self) -> int:
        res = 0
        for node in self.iterate_postorder():
            if node.is_leaf():
                continue

            # Compute the number of multiplications that must be performed across all np.tensordot calls during identify
            log_terms_in_sum = int(
                len(node.__left.free_edges)
                + len(node.__right.free_edges)
                - len(node.free_edges) / 2
            )
            log_num_sums = len(node.free_edges)

            # One multiply to compute each term and one add to sum it in
            res += 2 ** (log_terms_in_sum + log_num_sums)
        return res

    def is_complete(self, tensor_network: TensorNetwork) -> bool:
        # The leaves of the contraction-tree must be the tensors of the tensor-network
        if self.leaves != frozenset(range(len(tensor_network))):
            return False

        # The leaves of every subtree must be disjoint
        def leaves_disjoint(tree):
            if tree.is_leaf():
                return True
            else:
                return (
                    len(tree.left.leaves & tree.right.leaves) == 0
                    and leaves_disjoint(tree.left)
                    and leaves_disjoint(tree.right)
                )

        return leaves_disjoint(self)

    def __str__(self):
        return "(" + str(self.__left) + ", " + str(self.__right) + ")"

    def combine(self, other: ContractionTree) -> ContractionTree:
        return combine_contraction_trees(self, other)


class ContractionTreeLeaf:
    __tensor_index: int
    __edges: List[int]

    def __init__(self, tensor_network: TensorNetwork, tensor_index: int):
        self.__tensor_index = tensor_index
        self.__edges = tensor_network.index_list(tensor_index)

    def is_leaf(self) -> bool:
        return True

    @property
    def tensor_index(self) -> int:
        return self.__tensor_index

    @cached_property
    def leaves(self) -> FrozenSet[int]:
        return frozenset({self.__tensor_index})

    @property
    def free_edges(self) -> List[int]:
        return self.__edges

    @property
    def maxrank(self) -> int:
        return len(self.__edges)

    @property
    def required_FLOPS(self) -> int:
        return 0

    def __str__(self):
        return str(self.__tensor_index)

    def combine(self, other: ContractionTree) -> ContractionTree:
        return combine_contraction_trees(self, other)


class ContractionTreeEmpty:
    @property
    def leaves(self) -> FrozenSet[int]:
        return frozenset()

    @property
    def free_edges(self) -> List[int]:
        return []

    def combine(self, other: ContractionTree) -> ContractionTree:
        return other

    def __str__(self):
        return "()"


def combine_contraction_trees(
    left: ContractionTree, right: ContractionTree
) -> ContractionTree:
    if left is None or isinstance(left, ContractionTreeEmpty):
        return right
    if right is None or isinstance(right, ContractionTreeEmpty):
        return left
    return ContractionTreeNode(left, right)


def include_rank_zero_tensors(tensor_network, contraction_tree):
    remaining = frozenset(range(len(tensor_network))) - contraction_tree.leaves

    combine_zero_rank = ContractionTreeEmpty()
    for tensor in remaining:
        if tensor_network[tensor].rank == 0:
            combine_zero_rank = combine_zero_rank.combine(
                ContractionTreeLeaf(tensor_network, tensor)
            )
    return combine_zero_rank.combine(contraction_tree)
