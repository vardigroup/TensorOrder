from contraction_methods.contraction_tree import (
    ContractionTreeNode,
    ContractionTreeLeaf,
    include_rank_zero_tensors,
)


def igraph_do_tree_combine(d):
    if len(d) == 0:
        return d
    elif len(d) == 1:
        return d[0]
    else:
        return ContractionTreeNode(*d)


def igraph_contraction(contractor):
    def generate_contraction_trees(network, random_seed):
        import igraph

        structure_graph = network.structure()
        graph = igraph.Graph()

        # TensorCSP methods do not handle graphs with degree 0 nodes, so remove them
        # (remove them after adding edges to maintain edge numbers)
        to_remove = []
        for index in structure_graph.nodes(data=False):
            if structure_graph.degree(index) == 0:
                to_remove.append(index)
            graph.add_vertex(
                index, contraction_tree=ContractionTreeLeaf(network, index)
            )
        for edge in structure_graph.edges(data=False):
            graph.add_edge(*edge)
        graph.delete_vertices(to_remove)

        _, result = contractor(
            graph, combine_attrs={"contraction_tree": igraph_do_tree_combine}
        )
        tree = include_rank_zero_tensors(network, result.vs[0]["contraction_tree"])
        yield tree, network

    return generate_contraction_trees


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
    "KCMR-greedy": igraph_contraction(tensorcsp_greedy),
    "KCMR-metis": igraph_contraction(tensorcsp_metis),
    "KCMR-gn": igraph_contraction(tensorcsp_girvan),
}
