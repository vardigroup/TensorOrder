# distutils: language=c++
# distutils: extra_compile_args=-O3

from libcpp.vector cimport vector
from libcpp.set cimport set as cset

class ContractionTree:
    """
    A recursive interface into a contraction tree, useful for tensor network contraction
    """
    def __init__(self, context, node):
        self.__context = context
        self.__node = node
        self.__node_info = context.get_data(node)

    @property
    def left(self):
        return ContractionTree(self.__context, self.__node_info.left)

    @property
    def right(self):
        return ContractionTree(self.__context, self.__node_info.right)

    @property
    def tensor_index(self):
        return self.__node_info.tensor_index

    @property
    def is_leaf(self):
        return self.__node_info.is_leaf

    @property
    def maxrank(self):
        return self.__node_info.maxrank

    @property
    def left_edge_map(self):
        return self.__node_info.left_edge_map

    @property
    def right_edge_map(self):
        return self.__node_info.right_edge_map

    @property
    def free_edges(self):
        return self.__node_info.free_edges

    def estimate_cost(self, slices=frozenset()):
        """
        Compute the time and memory cap required to contract starting from this node.

        :param slices: A set of edges that have been sliced (and so have dimension 1)
        :return: The number of FLOPs, the needed memory cap, and the best (greedy) edge to slice to reduce memory cap
        """
        result = self.__context.estimate_cost(self.__node, slices)
        return result.get_total_FLOPs(), result.get_total_memory(), result.get_best_edge()

    def iterate_postorder(self):
        processed = [(self, False)]
        while len(processed) > 0:
            node, expanded = processed.pop()
            if expanded or node.is_leaf:
                yield node
            else:
                processed.append((node, True))
                processed.append((node.right, False))
                processed.append((node.left, False))


cdef class CostInfo:
    def get_total_FLOPs(self):
        return self.FLOPs

    def get_total_memory(self):
        return self.total_memory

    def get_best_edge(self):
        return self.best_edge


cdef class ContractionTreeNode:
    cdef public int left
    cdef public int right
    cdef public int tensor_index
    cdef public vector[int] free_edges
    cdef public object left_edge_map
    cdef public object right_edge_map

    cdef public size_t maxrank
    cdef public bint is_leaf

cdef class ContractionTreeContext:
    def __init__(self):
        self.nodes = []

    def get_data(self, index):
        return self.nodes[index]

    def get_tree(self, index):
        if index < 0:
            raise RuntimeError("Cannot get interface to empty tree")
        return ContractionTree(self, index)

    cpdef int empty(self):
        return -1

    cpdef int leaf(self, TensorNetwork tensor_network, int tensor_index) except -2:
        cdef ContractionTreeNode new_leaf = ContractionTreeNode()
        new_leaf.is_leaf = True
        new_leaf.tensor_index = tensor_index
        cdef int edge_id
        for edge_id in tensor_network.__index_lists[tensor_index]:
            new_leaf.free_edges.push_back(edge_id)

        new_leaf.maxrank = new_leaf.free_edges.size()
        self.nodes.append(new_leaf)
        return len(self.nodes) - 1

    cpdef int join(self, int left, int right) except -2:
        if left == -1:
            return right
        if right == -1:
            return left
        cdef ContractionTreeNode new_join = ContractionTreeNode()
        new_join.left = left
        new_join.right = right

        cdef ContractionTreeNode left_tree = self.nodes[left]
        cdef ContractionTreeNode right_tree = self.nodes[right]

        # Compute the set of free edges for the new contraction tree
        new_join.left_edge_map = []
        new_join.right_edge_map = []
        cdef bint found
        cdef size_t i, j
        for i in range(left_tree.free_edges.size()):
            found = False
            for j in range(right_tree.free_edges.size()):
                if left_tree.free_edges[i] == right_tree.free_edges[j]:
                    new_join.left_edge_map.append(i)
                    new_join.right_edge_map.append(j)
                    found = True
                    break
            if not found:
                new_join.free_edges.push_back(left_tree.free_edges[i])

        for j in range(right_tree.free_edges.size()):
            found = False
            for i in range(left_tree.free_edges.size()):
                if left_tree.free_edges[i] == right_tree.free_edges[j]:
                    found = True
                    break
            if not found:
                new_join.free_edges.push_back(right_tree.free_edges[j])

        # Compute the max rank of the new contraction tree
        new_join.maxrank = max(new_join.free_edges.size(),
                               left_tree.maxrank,
                               right_tree.maxrank)

        self.nodes.append(new_join)
        return len(self.nodes) - 1

    cpdef int include_rank_zero_tensors(self, TensorNetwork tensor_network, int contraction_tree) except -2:
        combine_zero_rank = self.empty()
        cdef size_t tensor_id
        for tensor_id in range(tensor_network.__index_lists.size()):
            if tensor_network.__index_lists[tensor_id].size() == 0:
                combine_zero_rank = self.join(
                    combine_zero_rank, self.leaf(tensor_network, tensor_id)
                )
        return self.join(combine_zero_rank, contraction_tree)


    cpdef CostInfo estimate_cost(self, size_t node_id, cset[int] & sliced_edges):
        """

        :param slices: A set of edges that have been sliced (and so have dimension 1)
        :return: 
        
        Compute the time and memory cap required to contract starting from this node.
        
        :param node_id: The node to contract from
        :param sliced_edges: A set of edges that have been sliced (and so have dimension 1)
        :return: Various information on cost (total FLOPs, memory cap, best edge to slice to reduce memory)
        """
        cdef CostInfo result = CostInfo()
        cdef ContractionTreeNode node = self.nodes[node_id]

        # Compute the memory required to store the left, right, and result tensors
        result.local_memory = 1
        cdef int i
        for i in node.free_edges:
            if sliced_edges.find(i) == sliced_edges.end():
                result.local_memory *= 2

        if node.is_leaf:
            result.FLOPs = 0
            result.total_memory = result.local_memory
            for i in node.free_edges:
                if sliced_edges.find(i) == sliced_edges.end():
                    result.open_edge_total_memory[i] = result.total_memory / 2
            # Leaf tensors do not yet have bond indices
            result.best_edge = -1
            result.best_edge_memory = (2**64)
            return result

        cdef CostInfo left = self.estimate_cost(node.left, sliced_edges)
        cdef CostInfo right = self.estimate_cost(node.right, sliced_edges)

        cdef ContractionTreeNode left_node = self.nodes[node.left]
        cdef ContractionTreeNode right_node = self.nodes[node.right]

        # The left tensor is computed first
        cdef double left_cap = left.total_memory
        # The left tensor must be stored while computing the right
        cdef double right_cap = left.local_memory + right.total_memory
        # The left and right tensors must be stored while computing the result
        # and left and right must be transposed first
        cdef double local_cap = result.local_memory + 2 * left.local_memory + 2 * right.local_memory

        # The overall memory cap needed is max(left_cap, right_cap, local_cap)
        # The best edge to slice (not including edges free in both left and right) follows the maximum value as well
        if left_cap >= right_cap and left_cap >= local_cap:
            result.total_memory = left_cap
            result.best_edge = left.best_edge
            result.best_edge_memory = left.best_edge_memory
        elif right_cap >= local_cap:
            result.total_memory = right_cap
            result.best_edge = right.best_edge
            result.best_edge_memory = left.local_memory + right.best_edge_memory
        else:
            result.total_memory = local_cap
            result.best_edge = left.best_edge
            # Note that this does not actually decrease the memory cap
            # The optimal edge to slice is one of the open edges
            result.best_edge_memory = local_cap

        # Compute the number of multiplications that must be performed across all np.tensordot calls during identify
        cdef size_t log_terms_in_sum = int(
            (left_node.free_edges.size() + right_node.free_edges.size() - node.free_edges.size()) / 2
        )
        cdef size_t log_num_sums = node.free_edges.size()

        # One multiply to compute each term and one add to sum it in
        if log_terms_in_sum + log_num_sums > 100:
            result.FLOPs = 2**100  # Cap
        else:
            result.FLOPs = left.FLOPs + right.FLOPs + 2 ** (log_terms_in_sum + log_num_sums)

        # For each free edge, compute the memory cap needed if it is sliced
        for e in left_node.free_edges:
            if right.open_edge_total_memory.find(e) == right.open_edge_total_memory.end():
                result.open_edge_total_memory[e] = max(max(
                    left.open_edge_total_memory[e],
                    (left.local_memory / 2) + right.total_memory),
                    (result.local_memory / 2) + 2 * (left.local_memory / 2) + 2 * right.local_memory
                )

        cdef double new_cap
        for e in right_node.free_edges:
            if left.open_edge_total_memory.find(e) == left.open_edge_total_memory.end():
                result.open_edge_total_memory[e] = max(max(
                    left.total_memory,
                    left.local_memory + right.open_edge_total_memory[e]),
                    (result.local_memory / 2) + 2 * left.local_memory + 2 * right.local_memory
                )
            elif sliced_edges.find(e) == sliced_edges.end():
                # For each newly bond edge, compute the new memory cap if it is sliced
                new_cap = max(max(
                    left.open_edge_total_memory[e],
                    (left.local_memory / 2) + right.open_edge_total_memory[e]),
                    result.local_memory + 2 * (left.local_memory / 2) + 2 * (right.local_memory / 2)
                )
                # Check if this new bond edge is now the best edge to slice
                if new_cap < result.best_edge_memory:
                    result.best_edge = e
                    result.best_edge_memory = new_cap
        return result


def is_tree_complete(contraction_tree, tensor_network):
    tensors = set(range(len(tensor_network)))
    for node in contraction_tree.iterate_postorder():
        if node.is_leaf:
            continue
        if node.tensor_index not in tensors:  # All leaves must be disjoint
            return False
        tensors.discard(node.tensor_index)
    return len(tensors) == 0  # All tensors must be included in the tree
