# distutils: language=c++
# distutils: extra_compile_args=-O3

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
    def rank(self):
        return len(self.__node_info.free_edges)

    @property
    def free_edges(self):
        return self.__node_info.free_edges

    def reroot(self, network, large_rank):
        """
        Reroot the tree so that one of the final tensors is large.

        :param network: The underlying tensor network
        :param large_rank: A tensor is large if its rank is >= [large_rank].
        :return: A new ContractionTree
        """
        result_tree_context = ContractionTreeContext()

        cdef vector[int] stack
        cdef vector[int] path_up    # [a, b, c, d] indicates a grouping of (a (b (c d)))
        cdef size_t i
        for node in self.iterate_postorder():
            if node.is_leaf:
                stack.push_back(result_tree_context.leaf(network, node.tensor_index))
            else:
                right = stack.back()
                stack.pop_back()
                left = stack.back()
                stack.pop_back()
                if len(path_up) == 0 and node.__node_info.maxrank >= large_rank:
                    path_up.push_back(result_tree_context.join(left, right))
                    stack.push_back(-1)
                else:
                    if right == -1:
                        path_up.push_back(left)
                        stack.push_back(-1)
                    elif left == -1:
                        path_up.push_back(right)
                        stack.push_back(-1)
                    else:
                        stack.push_back(result_tree_context.join(left, right))

        if len(path_up) == 0: # No large tensors found
            return result_tree_context.get_tree(stack[0])
        else:
            top = path_up[path_up.size()-1]
            for i in range(path_up.size() - 1, 0, -1):
                top = result_tree_context.join(path_up[i-1], top)
            return result_tree_context.get_tree(top)

    def regroup(self, rank_limit):
        """
        At places in the tree (A (B C)) where
            1) A and B are small,
            2) C is large, and
            3) (A B) is small,
        regroup this tree like (C (A B)).

        The regrouping is more amenable to early contraction, since (A B) can now be contracted early.
        :param rank_limit: A tensor is small if its maxrank is below [rank_limit]
        :return: None (Modifies the current tree)
        """
        # Entries of stack are (small_on_left, small), where:
        #   small_on_left == True means that a small tensor is on the left and a large tensor is on the right
        #   small_on_left == False means that a small tensor is on the right and a large tensor is on the left
        #   small_on_left == None otherwise (i.e., at a leaf, or both small, or both large)
        #   small is True if the current tensor is small, and large otherwise
        stack = []

        for node in self.iterate_postorder():
            if node.is_leaf:
                stack.append((None, node.maxrank < rank_limit))
            else:
                right_small_on_left, right_small = stack.pop()
                left_small_on_left, left_small = stack.pop()

                if right_small_on_left is not None and left_small:  # (A (B C)) or (A (C B)) => (C (A B))
                    if self.__context.group_if_below(node.__node, True, right_small_on_left, rank_limit) == 1:
                        # Now left is large, right is small
                        left_small = False
                        right_small = True
                elif left_small_on_left is not None and right_small:  # ((B C) A) or ((C B) A) => ((A B) C)
                    if self.__context.group_if_below(node.__node, False, left_small_on_left, rank_limit) == 1:
                        # Now right is large, left is small
                        left_small = True
                        right_small = False

                # Determine the location of the large tensor
                if left_small and not right_small:
                    small_on_left = True
                elif right_small and not left_small:
                    small_on_left = False
                else:
                    small_on_left = None
                stack.append((small_on_left, node.maxrank < rank_limit))

    def sort_small(self):
        """
        Sort each join node in the tree so that the smaller tensor appears on the right
        :return: None (modified the current tree)
        """

        cdef vector[int] stack  # 1 if the edge order below might have changed
        cdef int temp, result
        for node in self.iterate_postorder():
            if node.is_leaf:
                stack.push_back(0)
            else:
                result = stack.back()
                stack.pop_back()
                result += stack.back()
                stack.pop_back()
                if node.left.rank < node.right.rank:
                    temp = node.__node_info.left
                    node.__node_info.left = node.__node_info.right
                    node.__node_info.right = temp
                    result += 1
                if result > 0:
                    node.__context.compute_join_properties(node.__node)
                    stack.push_back(1)
                else:
                    stack.push_back(0)

    def estimate_cost(self, slices=frozenset()):
        """
        Compute the time and memory cap required to contract starting from this node.

        :param slices: A set of edges that have been sliced (and so have dimension 1)
        :return: The number of FLOPs, the needed memory cap, and the best (greedy) edge to slice to reduce memory cap
        """
        result = self.__context.estimate_cost(self.__node, slices)
        return result.get_total_FLOPs(), result.get_total_memory(), result.get_best_edge(), result.get_max_rank()

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

    def get_max_rank(self):
        return self.largest_tensor

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

    cpdef int leaf_manual(self, int tensor_index, vector[int] free_edges) except -2:
        cdef ContractionTreeNode new_leaf = ContractionTreeNode()
        new_leaf.is_leaf = True
        new_leaf.tensor_index = tensor_index
        new_leaf.free_edges = free_edges
        new_leaf.maxrank = new_leaf.free_edges.size()
        self.nodes.append(new_leaf)
        return len(self.nodes) - 1

    cpdef int compute_join_properties(self, int node) except -2:
        """
        (Re)compute the properties of the provided join node.
        :param node: The id of the join node to process.
        :return: The id of the node if successful, or -2 for an exception
        """
        cdef ContractionTreeNode new_join = self.nodes[node]
        cdef ContractionTreeNode left_tree = self.nodes[new_join.left]
        cdef ContractionTreeNode right_tree = self.nodes[new_join.right]

        # Compute the set of free edges for the new contraction tree
        new_join.free_edges.clear()
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
        return node

    cpdef int join(self, int left, int right) except -2:
        if left == -1:
            return right
        if right == -1:
            return left
        cdef ContractionTreeNode new_join = ContractionTreeNode()
        new_join.left = left
        new_join.right = right

        self.nodes.append(new_join)
        return self.compute_join_properties(len(self.nodes) - 1)

    cpdef int include_rank_zero_tensors(self, TensorNetwork tensor_network, int contraction_tree) except -2:
        combine_zero_rank = self.empty()
        cdef size_t tensor_id
        for tensor_id in range(tensor_network.__index_lists.size()):
            if tensor_network.__index_lists[tensor_id].size() == 0:
                combine_zero_rank = self.join(
                    combine_zero_rank, self.leaf(tensor_network, tensor_id)
                )
        return self.join(combine_zero_rank, contraction_tree)


    cpdef int reindex(self, vector[int] new_tid_from_old, vector[int] new_eid_from_old) except -2:
        cdef size_t i
        cdef ContractionTreeNode node
        for node in self.nodes:
            if node.is_leaf:
                node.tensor_index = new_tid_from_old[node.tensor_index]
            for i in range(node.free_edges.size()):
                node.free_edges[i] = new_eid_from_old[node.free_edges[i]]
        return 0


    cpdef int group_if_below(self, int upper, bool upper_left, bool lower_left, size_t if_below) except -2:
        """
        At a node (A (B C)) where (A B) is small, regroup this tree like (C (A B)).
        
        :param upper: The upper join node to consider, which must have a join node as a child.
        :param upper_left: The location of A (True -> left, False -> right)
        :param lower_left: The location of B (True -> left, False -> right)
        :param if_below: Perform regrouping if (A B) has size below [if_below]
        :return: 1 if a swap occurred, otherwise 0
        """
        # Pick out the id of the nodes to consider grouping
        cdef ContractionTreeNode upper_node = self.nodes[upper]
        cdef int upper_chosen_id, lower_chosen_id, lower_other_id, lower
        if upper_left:
            upper_chosen_id = upper_node.left
            lower = upper_node.right
        else:
            upper_chosen_id = upper_node.right
            lower = upper_node.left

        cdef ContractionTreeNode lower_node = self.nodes[lower]
        if lower_left:
            lower_chosen_id = lower_node.left
            lower_other_id = lower_node.right
        else:
            lower_chosen_id = lower_node.right
            lower_other_id = lower_node.left

        # Compute the rank of the tensor obtained from joining the upper and lower chosen nodes
        cdef ContractionTreeNode upper_chosen_node = self.nodes[upper_chosen_id]
        cdef ContractionTreeNode lower_chosen_node = self.nodes[lower_chosen_id]
        cdef size_t i
        cdef size_t rank = upper_chosen_node.free_edges.size() + lower_chosen_node.free_edges.size()
        for i in range(upper_chosen_node.free_edges.size()):
            found = False
            for j in range(lower_chosen_node.free_edges.size()):
                if upper_chosen_node.free_edges[i] == lower_chosen_node.free_edges[j]:
                    rank -= 2   # Edges that appear in both are removed
                    break

        if rank < if_below:
            # Perform the swap
            if upper_left:
                upper_node.left = lower_other_id
            else:
                upper_node.right = lower_other_id
            if lower_left:
                # Note the larger node is on the right if the small node on the left
                lower_node.right = upper_chosen_id
            else:
                lower_node.left = upper_chosen_id

            # Finally, recompute the internal properties of the nodes
            self.compute_join_properties(lower)
            self.compute_join_properties(upper)
            return 1
        return 0

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
            result.largest_tensor = 0
            for i in node.free_edges:
                if sliced_edges.find(i) == sliced_edges.end():
                    result.open_edge_total_memory[i] = result.total_memory / 2
                    result.largest_tensor += 1
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

        # Compute the largest encountered tensor, including the resulting tensor from here
        result.largest_tensor = 0
        for i in node.free_edges:
            if sliced_edges.find(i) == sliced_edges.end():
                result.largest_tensor += 1
        result.largest_tensor = max(result.largest_tensor, left.largest_tensor, right.largest_tensor)


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
