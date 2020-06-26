from contraction_methods.contraction_method import ContractionMethod
from contraction_methods.contraction_tree import ContractionTreeContext


def igraph_do_tree_combine(context):
    def do(d):
        if len(d) == 0:
            return d
        elif len(d) == 1:
            return d[0]
        else:
            return context.join(*d)

    return do


class IGraphMethod(ContractionMethod):
    def __init__(self, contractor):
        self.__contractor = contractor

    def generate_contraction_trees(self, tensor_network, timer, **solver_args):
        """
        Construct and yield contraction trees for the provided network.

        :param tensor_network: The tensor network to find contraction trees for.
        :param timer: A timer to check expiration of.
        :param solver_args: Additional arguments for the contraction tree algorithm.
        :return: An iterator of contraction trees for the provided network.
        """
        import igraph

        structure_graph = tensor_network.structure(include_rank_zero=False)
        graph = igraph.Graph()

        context = ContractionTreeContext()
        # TensorCSP methods do not handle graphs with degree 0 nodes, so remove them
        # (remove them after adding edges to maintain edge numbers)
        to_remove = []
        for index in structure_graph.nodes(data=False):
            if structure_graph.degree(index) == 0:
                to_remove.append(index)
            graph.add_vertex(
                index, contraction_tree=context.leaf(tensor_network, index)
            )
        for edge in structure_graph.edges(data=False):
            graph.add_edge(*edge)
        graph.delete_vertices(to_remove)

        _, result = self.__contractor(
            graph, combine_attrs={"contraction_tree": igraph_do_tree_combine(context)}
        )
        tree = context.include_rank_zero_tensors(
            tensor_network, result.vs[0]["contraction_tree"]
        )
        yield context.get_tree(tree), tensor_network


def tensorcsp_greedy(graph, **kwargs):
    import tensorcsp.grut

    return tensorcsp.grut.contract_greedy(graph, **kwargs)


def tensorcsp_metis(graph, **kwargs):
    import tensorcsp.grut

    partitioning = tensorcsp.grut.recursive_bipartition(
        graph, tensorcsp.grut.metis_bipartition
    )
    return tensorcsp.grut.contract_dendrogram(graph, partitioning, **kwargs)


def tensorcsp_girvan(graph, **kwargs):
    import tensorcsp.grut

    d = graph.community_edge_betweenness()
    m = d.merges
    return tensorcsp.grut.contract_dendrogram(graph, m, **kwargs)


SOLVERS = {
    "KCMR-greedy": IGraphMethod(tensorcsp_greedy),
    "KCMR-metis": IGraphMethod(tensorcsp_metis),
    "KCMR-gn": IGraphMethod(tensorcsp_girvan),
}
