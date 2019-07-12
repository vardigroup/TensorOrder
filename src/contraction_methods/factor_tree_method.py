from collections import defaultdict

import random
from typing import NamedTuple, Dict, List
from contraction_methods.contraction_tree import (
    ContractionTree,
    ContractionTreeLeaf,
    ContractionTreeEmpty,
    include_rank_zero_tensors,
)
import decompositions.tree_decomposition_solver


def extract_contraction_tree_factor(tensor_network, tree_decomposition, root: int):
    # For each edge in the tensor network, choose one of the nodes in the tree decomposition containing that edge
    # Add a leaf at that node whose bag contains the tensors incident to that edge

    pairs_in_nodes = defaultdict(lambda: [])
    for node in tree_decomposition.nodes():
        for a in tree_decomposition.node[node]["bag"]:
            for b in tree_decomposition.node[node]["bag"]:
                if a != b:
                    pairs_in_nodes[(a, b)].append(node)

    chosen_node_cache = {}
    node_to_edges = defaultdict(lambda: [])
    for e in tensor_network.edges:
        if e.tensors not in chosen_node_cache:
            iterator = iter(e.tensors)
            chosen_node = random.choice(
                pairs_in_nodes[(next(iterator), next(iterator))]
            )
            chosen_node_cache[e.tensors] = tree_decomposition.extend_leaf(chosen_node)
        node_to_edges[chosen_node_cache[e.tensors]].append(e)

    node_to_edge = {}
    for node in node_to_edges:
        if len(node_to_edges[node]) == 1:
            node_to_edge[node] = node_to_edges[node][0]
        elif len(node_to_edges[node]) > 1:
            curr_extension = node
            for e in node_to_edges[node]:
                curr_extension = tree_decomposition.extend_leaf(curr_extension)
                node_to_edge[curr_extension] = e

    tree_decomposition.split_high_degree_nodes()

    # To avoid handling the root as a special case below, make it a leaf
    root = tree_decomposition.extend_leaf(root)

    # for n in self.nodes():
    #    self.node[n]['label'] = ''

    class ChildInfo(NamedTuple):
        contraction_tree: ContractionTree
        intermediate_edge: Dict[int, int]

    def factor_children(node: int, child_results: List[ChildInfo]) -> ChildInfo:
        if len(child_results) == 0:
            # We are at the leaf of the tree decomposition

            if node not in node_to_edge:
                # If no edges are marked at this leaf, do nothing
                return ChildInfo(ContractionTreeEmpty(), {})
            else:
                # Otherwise, we propagate up the edge marked at this leaf
                contraction, intermediate = ContractionTreeEmpty(), {}
                for tensor in node_to_edge[node].tensors:
                    if tensor_network[tensor].rank <= 1:
                        # Rank 1 tensors can be contracted immediately
                        contraction = contraction.combine(
                            ContractionTreeLeaf(tensor_network, tensor)
                        )
                    else:
                        intermediate[tensor] = node_to_edge[node].id
                # self.node[node]['label'] = '[{0}]'.format(node_to_edge[node].id)
                return ChildInfo(contraction, intermediate)

        # If we are at a node with a single child, just propagate up the marked edges
        if len(child_results) == 1:
            # self.node[node]['label'] = str("*" + str(child_results[0].intermediate_edge))
            return child_results[0]

        # Otherwise, we are at an internal node of degree 3, and we have the propagated edges from two children
        left = child_results[0]
        right = child_results[1]

        left_contraction = left.contraction_tree
        right_contraction = right.contraction_tree

        intermediate = {}

        tensors_to_contract = []
        for tensor in left.intermediate_edge:
            # Tensors with edges propagating from a single side propagate cleanly
            if tensor not in right.intermediate_edge:
                intermediate[tensor] = left.intermediate_edge[tensor]

            # Tensors that have been fully represented in the leaves below do not propagate further
            elif left.intermediate_edge[tensor] == right.intermediate_edge[tensor]:
                continue
            # A rank 2 tensor with an edge on either side is fully represented, just needs to be joined to some side
            elif tensor_network[tensor].rank == 2:
                left_contraction = left_contraction.combine(
                    ContractionTreeLeaf(tensor_network, tensor)
                )
            # Tensors with a subset of edges on either side induce a factoring
            else:
                # In particular, factor to group the intermediate_edge on either side
                #    Continue to propagate the new edge from the factorization
                left_index = tensor_network.index_list(tensor).index(
                    left.intermediate_edge[tensor]
                )
                right_index = tensor_network.index_list(tensor).index(
                    right.intermediate_edge[tensor]
                )

                new_tensor, intermediate[tensor] = tensor_network.factor_out(
                    tensor, [left_index, right_index]
                )

                # We must factor this new tensor as well
                tensors_to_contract.append(new_tensor)

        for tensor in right.intermediate_edge:
            # Tensors with edges propagating from a single side propagate cleanly
            if tensor not in left.intermediate_edge:
                intermediate[tensor] = right.intermediate_edge[tensor]

        # Divide the new rank-3 tensors into groups, minimizing the max-rank:
        #   [0] to be contracted on the left tensor,
        #   [1] to be contracted on the right tensor,
        #   [2] to be contracted after joining the left and right tensor
        ranks = [
            len(left.intermediate_edge),
            len(right.intermediate_edge),
            len(intermediate),
        ]
        groups = [[], [], []]
        for new_tensor in tensors_to_contract:
            min_direction = ranks.index(min(ranks))
            groups[min_direction].append(
                ContractionTreeLeaf(tensor_network, new_tensor)
            )
            ranks[min_direction] += 1

        # Finally, contract the new rank-3 tensors by groups
        for leaf in groups[0]:
            left_contraction = left_contraction.combine(leaf)
        for leaf in groups[1]:
            right_contraction = right_contraction.combine(leaf)
        contraction = left_contraction.combine(right_contraction)
        for leaf in groups[2]:
            contraction = contraction.combine(leaf)

        # self.node[node]['label'] = str(node) + ": " + str(intermediate)
        return ChildInfo(contraction, intermediate)

    result = tree_decomposition.traverse_postorder(root, factor_children)
    return include_rank_zero_tensors(tensor_network, result.contraction_tree)


def contraction_tree_factor(solver):
    def generate_contraction_trees(tensor_network, random_seed):
        graph = tensor_network.structure()

        parameters = {"treewidth_seed": random_seed, "print_bag_below": 100}
        for tree_decomposition in solver.generate_tree_decompositions(
            graph, parameters
        ):
            network = tensor_network.copy()  # make a copy of the network to modify
            tree = extract_contraction_tree_factor(network, tree_decomposition, 1)
            tree.treewidth = tree_decomposition.width()
            yield tree, network

    return generate_contraction_trees


SOLVERS = {
    "factor-Tamaki": contraction_tree_factor(
        decompositions.tree_decomposition_solver.tcg_meiji_heuristic_online
    ),
    "factor-Flow": contraction_tree_factor(
        decompositions.tree_decomposition_solver.flow_cutter_online
    ),
    "factor-htd": contraction_tree_factor(
        decompositions.tree_decomposition_solver.htd_online
    ),
}
