# distutils: language=c++
# distutils: extra_compile_args=-O3

import random
import time

from contraction_methods.contraction_method import ContractionMethod
import decompositions.decomposition_solver
import util

from decompositions.tree_decomposition cimport TreeDecomposition
from decompositions.branch_decomposition cimport BranchDecomposition
from contraction_methods.contraction_tree cimport ContractionTreeContext
from tensor_network.tensor_network cimport TensorNetwork
from libcpp.unordered_map cimport unordered_map
from libcpp.vector cimport vector

cdef extract_tree_decomposition_edges(TensorNetwork tensor_network, TreeDecomposition decomposition):
    """
    For each edge in the tensor network, choose one of the nodes in the tree decomposition
    containing that edge. Add a leaf at that node whose bag contains the tensors incident
    to that edge.
    
    Note that we do not specify a cython return type unordered_map[int, int] so that exceptions
    can be returned (in particular, TimeoutException).

    :param tensor_network: The associated tensor network.
    :param decomposition: The tree decomposition to use.
    :return: A mapping from each tree decomposition leaf to the corresponding edge of the network.
    """

    # Use 64-bit to avoid overflow in bag_pair_id with fewer than 2^32 tensors
    cdef long long a, b, id1, id2, bag_pair_id, sorted_tensors
    max_bag_item = len(tensor_network)

    # For every pair of tensors, record which nodes contain both in its bag
    cdef unordered_map[int, vector[int]] pairs_in_nodes
    cdef size_t node
    for node in range(decomposition.bags.size()):
        for a in decomposition.bags[node]:
            for b in decomposition.bags[node]:
                if a != b:
                    bag_pair_id = a * max_bag_item + b  # Since ctuple does not have default hashing defined in cython
                    if pairs_in_nodes.find(bag_pair_id) == pairs_in_nodes.end():
                        pairs_in_nodes[bag_pair_id] = vector[int]()
                    pairs_in_nodes[bag_pair_id].push_back(node)

    # For each tensor network edge, choose a leaf that contains both incident tensors
    cdef unordered_map[long long, int] chosen_node_cache
    cdef size_t chosen_node_index
    cdef int chosen_node
    cdef unordered_map[int, int] node_to_edge
    cdef size_t edge_id
    for edge_id in range(tensor_network.__edges.size()):
        id1 = tensor_network.__edges[edge_id].tensor1_id
        id2 = tensor_network.__edges[edge_id].tensor2_id
        sorted_tensors = min(id1, id2) * max_bag_item + max(id1, id2)
        if chosen_node_cache.find(sorted_tensors) == chosen_node_cache.end():
            if pairs_in_nodes[sorted_tensors].size() == 1:
                chosen_node_index = 0
            else:
                chosen_node_index = random.randint(0, pairs_in_nodes[sorted_tensors].size()-1)
            chosen_node = pairs_in_nodes[sorted_tensors][chosen_node_index]
            chosen_node_cache[sorted_tensors] = decomposition.extend_leaf(chosen_node)
        else:
            chosen_node = chosen_node_cache[sorted_tensors]
            chosen_node_cache[sorted_tensors] = decomposition.extend_leaf(chosen_node)
        node_to_edge[chosen_node_cache[sorted_tensors]] = edge_id
    return node_to_edge


cdef class ChildInfo:
    cdef int contraction_tree
    cdef unordered_map[size_t, int] intermediate_edge


cdef ChildInfo factor_tree(
    vector[vector[int]] & neighbors,
    int node,
    int parent,
    TensorNetwork tensor_network,
    ContractionTreeContext context,
    unordered_map[int, int] & node_to_edge
):
    """
    Traverse a tree decomposition to implement Factor-Tree.

    In particular, this implements Part 2 of the proof Thm 4 of https://arxiv.org/abs/1908.04381.

    :param neighbors: The neighbors of the underlying tree to traverse.
    :param node: The current node to process.
    :param parent: The parent of this node in the tree decomposition.
    :param tensor_network: The underlying tensor network.
    :param context: A storage object for the created contraction trees.
    :param node_to_edge: A mapping from tree leaf node ids to tensor edges.
    :return: A processor to implement Factor-Tree on the corresponding tree.
    """
    cdef vector[int] children
    cdef size_t i
    for i in range(neighbors[node].size()):
        if neighbors[node][i] != parent:
            children.push_back(neighbors[node][i])

    # If we are at a node with a single child, just propagate up the marked edges
    if children.size() == 1:
        return factor_tree(neighbors, children[0], node, tensor_network, context, node_to_edge)

    cdef ChildInfo result = ChildInfo()
    cdef size_t tensor_id
    cdef size_t edge_id
    if children.size() == 0:
        # We are at the leaf of the tree decomposition
        result.contraction_tree = context.empty()
        if node_to_edge.find(node) == node_to_edge.end():
            # If no edges are marked at this leaf, do nothing
            return result
        else:
            # Otherwise, we propagate up the edge marked at this leaf
            edge_id = node_to_edge[node]
            edge = tensor_network.__edges[edge_id]
            tensor_id = edge.tensor1_id
            if tensor_network.__index_lists[tensor_id].size() <= 1:
                # Rank 1 tensors can be contracted immediately
                result.contraction_tree = context.join(
                    result.contraction_tree, context.leaf(tensor_network, tensor_id)
                )
            else:
                result.intermediate_edge[tensor_id] = edge.id

            tensor_id = edge.tensor2_id
            if tensor_network.__index_lists[tensor_id].size() <= 1:
                # Rank 1 tensors can be contracted immediately
                result.contraction_tree = context.join(
                    result.contraction_tree, context.leaf(tensor_network, tensor_id)
                )
            else:
                result.intermediate_edge[tensor_id] = edge.id

            return result

    # Otherwise, we are at an internal node of degree 3, and we have the propagated edges from two children
    cdef ChildInfo left = factor_tree(neighbors, children[0], node, tensor_network, context, node_to_edge)
    cdef ChildInfo right = factor_tree(neighbors, children[1], node, tensor_network, context, node_to_edge)

    cdef int left_contraction = left.contraction_tree
    cdef int right_contraction = right.contraction_tree

    cdef vector[int] tensors_to_contract
    cdef int new_tensor
    cdef size_t left_index = 0, right_index = 0
    for pair in left.intermediate_edge:
        tensor_id = pair.first
        # Tensors with edges propagating from a single side propagate cleanly
        if right.intermediate_edge.find(tensor_id) == right.intermediate_edge.end():
            result.intermediate_edge[tensor_id] = left.intermediate_edge[tensor_id]
        # Tensors that have been fully represented in the leaves below do not propagate further
        elif left.intermediate_edge[tensor_id] == right.intermediate_edge[tensor_id]:
            continue
        # A rank 2 tensor with an edge on either side is fully represented, just needs to be joined to some side
        elif tensor_network.__index_lists[tensor_id].size() == 2:
            # Join on the smaller side
            if left.intermediate_edge.size() < right.intermediate_edge.size():
                left_contraction = context.join(
                    left_contraction, context.leaf(tensor_network, tensor_id)
                )
            else:
                right_contraction = context.join(
                    right_contraction, context.leaf(tensor_network, tensor_id)
                )
        # Tensors with a subset of edges on either side induce a factoring
        else:
            # In particular, factor to group the intermediate_edge on either side
            #    Continue to propagate the new edge from the factorization
            for i in range(tensor_network.__index_lists[tensor_id].size()):
                if left.intermediate_edge[tensor_id] == tensor_network.__index_lists[tensor_id][i]:
                    left_index = i
                    break
            for i in range(tensor_network.__index_lists[tensor_id].size()):
                if right.intermediate_edge[tensor_id] == tensor_network.__index_lists[tensor_id][i]:
                    right_index = i
                    break
            factor_result = tensor_network.factor_out(
                tensor_id, left_index, right_index
            )
            new_tensor = factor_result.new_tensor_id
            result.intermediate_edge[tensor_id] = factor_result.intermediate_edge_id

            # We must factor this new tensor as well
            tensors_to_contract.push_back(new_tensor)

    for pair in right.intermediate_edge:
        tensor_id = pair.first
        # Tensors with edges propagating from a single side propagate cleanly
        if left.intermediate_edge.find(tensor_id) == left.intermediate_edge.end():
            result.intermediate_edge[tensor_id] = right.intermediate_edge[tensor_id]

    # Divide the new rank-3 tensors into groups, minimizing the max-rank:
    #   *_left to be contracted on the left tensor,
    #   *_right to be contracted on the right tensor,
    #   *_res to be contracted after joining the left and right tensor
    cdef size_t rank_left = left.intermediate_edge.size()
    cdef size_t rank_right = right.intermediate_edge.size()
    cdef size_t rank_res = result.intermediate_edge.size()
    cdef vector[int] group_left
    cdef vector[int] group_right
    cdef vector[int] group_res
    for new_tensor in tensors_to_contract:
        if rank_left <= rank_right and rank_left <= rank_res:
            group_left.push_back(context.leaf(tensor_network, new_tensor))
            rank_left += 1
        elif rank_right <= rank_res:
            group_right.push_back(context.leaf(tensor_network, new_tensor))
            rank_right += 1
        else:
            group_res.push_back(context.leaf(tensor_network, new_tensor))
            rank_res += 1

    # Finally, contract the new rank-3 tensors by groups
    cdef int leaf
    for leaf in group_left:
        left_contraction = context.join(left_contraction, leaf)
    for leaf in group_right:
        right_contraction = context.join(right_contraction, leaf)
    contraction = context.join(left_contraction, right_contraction)
    for leaf in group_res:
        contraction = context.join(contraction, leaf)

    result.contraction_tree = contraction
    return result


cdef object extract_contraction_tree_from_tree(TensorNetwork tensor_network, TreeDecomposition decomposition):
    """
    Extract the contraction tree obtained from Factor+Tree using the provided tree decomposition.

    :param tensor_network: The tensor network to find a contraction tree for.
    :param decomposition: The tree decomposition of [tensor_network] to use.
    :return:
    """
    # Construct a mapping from the leaves of the decomposition and the edges of the network
    cdef unordered_map[int, int] node_to_edge = extract_tree_decomposition_edges(tensor_network, decomposition)
    util.log("Extracted edges at " + str(time.time()), util.Verbosity.solver_output)

    # Ensure every node of the tree decomposition has degree 3 or fewer.
    decomposition.split_high_degree_nodes()
    # To avoid handling the root as a special case, make it a leaf
    cdef int root = decomposition.extend_leaf(1)

    # Run Factor+Tree on the tree decomposition
    context = ContractionTreeContext()
    result = factor_tree(decomposition.neighbors, root, -1, tensor_network, context, node_to_edge)
    full_tree = context.include_rank_zero_tensors(tensor_network, result.contraction_tree)
    return context.get_tree(full_tree)


cdef object extract_contraction_tree_from_branch(TensorNetwork tensor_network, BranchDecomposition decomposition):
    """
    Extract the contraction tree obtained from Factor+Tree using the provided branch decomposition.

    :param tensor_network: The tensor network to find a contraction tree for.
    :param decomposition: The branch decomposition of [tensor_network] to use.
    :return:
    """
    # To avoid handling the root as a special case, make it a leaf
    cdef int root = decomposition.extend_leaf(1)

    # Run Factor+Tree on the branch decomposition
    context = ContractionTreeContext()
    result = factor_tree(
        decomposition.neighbors, root, -1, tensor_network, context, decomposition.node_to_edge
    )
    full_tree = context.include_rank_zero_tensors(tensor_network, result.contraction_tree)
    return context.get_tree(full_tree)


class FactorTree(ContractionMethod):
    def __init__(self, solver):
        self.__solver = solver

    def generate_contraction_trees(self, tensor_network, timer, **solver_args):
        """
        Construct and yield contraction trees for the provided network.

        :param tensor_network: The tensor network to find contraction trees for.
        :param timer: A timer to check expiration of.
        :param solver_args: Additional arguments for the contraction tree algorithm.
        :return: An iterator of contraction trees for the provided network.
        """

        util.log("Starting solver at " + str(time.time()), util.Verbosity.solver_output)
        best_width = None
        for decomposition in self.__solver.generate_decompositions(
            lambda file: tensor_network.save_structure(file, False),
            {"print_tw_below": 100, **solver_args},
            timer
        ):
            util.log("Parsed decomposition at " + str(time.time()), util.Verbosity.solver_output)

            network = tensor_network.copy()  # make a copy of the network to modify
            if isinstance(decomposition, TreeDecomposition):
                tree = extract_contraction_tree_from_tree(network, decomposition)
                tree.tree_decomposition = decomposition
                tree.treewidth = decomposition.width()
            elif isinstance(decomposition, BranchDecomposition):
                tree = extract_contraction_tree_from_branch(network, decomposition)
                tree.branch_decomposition = decomposition
                tree.branchwidth = decomposition.width()
            else:
                raise RuntimeError("Unknown decomposition type " + str(decomposition))
            util.log("Built contraction tree " + str(time.time()), util.Verbosity.solver_output)
            yield tree, network


SOLVERS = {
    "factor-Tamaki": FactorTree(
        decompositions.decomposition_solver.tcg_meiji_heuristic_online
    ),
    "factor-Flow": FactorTree(
        decompositions.decomposition_solver.flow_cutter_online
    ),
    "factor-htd": FactorTree(decompositions.decomposition_solver.htd_online),
    "factor-hicks": FactorTree(decompositions.decomposition_solver.hicks),
    "factor-portfolio1": FactorTree(
        decompositions.decomposition_solver.portfolio1
    ),
    "factor-portfolio2": FactorTree(
        decompositions.decomposition_solver.portfolio2
    ),
    "factor-portfolio3": FactorTree(
        decompositions.decomposition_solver.portfolio3
    ),
    "factor-portfolio4": FactorTree(
        decompositions.decomposition_solver.portfolio4
    ),
}
