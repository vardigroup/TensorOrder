from typing import List

from contraction_methods.contraction_method import ContractionMethod
from contraction_methods.contraction_tree import ContractionTreeContext
import decompositions.decomposition_solver


def extract_contraction_tree_line(tensor_network, tree_decomposition, root):
    context = ContractionTreeContext()
    trees = [context.leaf(tensor_network, i) for i in range(len(tensor_network))]
    edges = [frozenset(context.get_tree(tree).free_edges) for tree in trees]

    def combine_children_contraction_trees(node: int, children_trees: List[int]) -> int:
        # Find all tensors whose clique is contained in the current bag
        bag = set(tree_decomposition.bags[node])
        matches = {
            (tree, free_edges)
            for tree, free_edges in zip(trees, edges)
            if bag.issuperset(free_edges)
        }
        for tree, free_edges in matches:
            trees.remove(tree)
            edges.remove(free_edges)

        complete_tree = context.empty()
        for tree in children_trees:
            complete_tree = context.join(complete_tree, tree)
        for tree, _ in matches:
            complete_tree = context.join(complete_tree, tree)
        return complete_tree

    result = tree_decomposition.traverse_postorder(
        root, combine_children_contraction_trees
    )
    return context.get_tree(context.include_rank_zero_tensors(tensor_network, result))


class LineGraph(ContractionMethod):
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

        for tree_decomposition in self.__solver.generate_decompositions(
            lambda file: tensor_network.save_line_structure(file),
            {"print_tw_below": 100, **solver_args},
            timer,
        ):
            tree = extract_contraction_tree_line(tensor_network, tree_decomposition, 1)
            tree.tree_decomposition = tree_decomposition
            tree.treewidth = tree_decomposition.width()
            yield tree, tensor_network


SOLVERS = {
    "line-Tamaki": LineGraph(
        decompositions.decomposition_solver.tcg_meiji_heuristic_online
    ),
    "line-Flow": LineGraph(decompositions.decomposition_solver.flow_cutter_online),
    "line-htd": LineGraph(decompositions.decomposition_solver.htd_online),
    "line-portfolio2": LineGraph(decompositions.decomposition_solver.portfolio2),
    "line-portfolio3": LineGraph(decompositions.decomposition_solver.portfolio3),
}
