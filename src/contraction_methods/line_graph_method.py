from typing import List

from contraction_methods.contraction_tree import (
    ContractionTree,
    ContractionTreeLeaf,
    ContractionTreeEmpty,
    include_rank_zero_tensors,
)
import decompositions.tree_decomposition_solver


def extract_contraction_tree_line(tensor_network, tree_decomposition, root):
    trees = [ContractionTreeLeaf(tensor_network, i) for i in range(len(tensor_network))]

    def combine_children_contraction_trees(
        node: int, children_trees: List[ContractionTree]
    ) -> ContractionTree:
        # Find all tensors whose clique is contained in the current bag
        matches = {
            tree
            for tree in trees
            if tree_decomposition.node[node]["bag"].issuperset(tree.free_edges)
        }
        for tree in matches:
            trees.remove(tree)

        complete_tree = ContractionTreeEmpty()
        for tree in children_trees:
            complete_tree = complete_tree.combine(tree)
        for tree in matches:
            complete_tree = complete_tree.combine(tree)
        return complete_tree

    result = tree_decomposition.traverse_postorder(
        root, combine_children_contraction_trees
    )
    return include_rank_zero_tensors(tensor_network, result)


def contraction_tree_line(tree_decomposition_solver):
    def generate_contraction_trees(network, random_seed):
        line_graph = network.line_structure()

        parameters = {"treewidth_seed": random_seed, "print_bag_below": 100}
        for (
            tree_decomposition
        ) in tree_decomposition_solver.generate_tree_decompositions(
            line_graph, parameters
        ):
            tree = extract_contraction_tree_line(network, tree_decomposition, 1)
            tree.treewidth = tree_decomposition.width()
            yield tree, network

    return generate_contraction_trees


SOLVERS = {
    "line-Tamaki": contraction_tree_line(
        decompositions.tree_decomposition_solver.tcg_meiji_heuristic_online
    ),
    "line-Flow": contraction_tree_line(
        decompositions.tree_decomposition_solver.flow_cutter_online
    ),
    "line-htd": contraction_tree_line(
        decompositions.tree_decomposition_solver.htd_online
    ),
}
