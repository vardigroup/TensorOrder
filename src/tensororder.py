import click
import os
import random
import sys
import traceback

import contraction_methods
import tensor_network
import util


@click.command()
@click.argument("benchmark", type=click.File(mode="r"), default="-")
@click.option(
    "--timeout",
    type=float,
    default=0,
    help="Timeout for all steps of the computation (s).",
)
@click.option(
    "--tree_timeout",
    type=float,
    default=0,
    help="Timeout for the computation of the contraction tree (s).",
)
@click.option(
    "--output",
    type=util.KeyValueOutput("a", lazy=False),
    default="-",
    help="File to write output to",
)
@click.option(
    "--seed", type=int, default=None, help="Seed for random number generation"
)
@click.option(
    "--method",
    required=True,
    help="Method to use to find contraction tree",
    type=util.TaggedChoice(contraction_methods.ALL_SOLVERS, case_sensitive=False),
)
@click.option(
    "--network_construction",
    help="How to construct tensor network from benchmark",
    default="wmc",
    type=util.TaggedChoice(tensor_network.ALL_CONSTRUCTIONS, case_sensitive=False),
)
@click.option(
    "--entry_type",
    default="float64",
    help="Data type to use for all tensor computations",
    type=click.Choice(
        ["uint", "int", "bigint", "float16", "float32", "float64"], case_sensitive=False
    ),
)
@click.option(
    "--tensor_library",
    default="numpy",
    help="Tensor library to use",
    type=util.TaggedChoice(tensor_network.ALL_APIS, case_sensitive=False),
)
@click.option(
    "--max_rank",
    type=int,
    help="Contraction trees of larger max-rank are not used",
    default=30,
)
@click.option(
    "--thread_limit", type=int, help="Number of threads to limit tensor manipulations"
)
@click.option(
    "--performance_factor",
    type=float,
    help="Float to scale estimated computation time by",
    default=10 ** (-11),
)
@click.option(
    "--log_contraction_tree",
    required=False,
    type=bool,
    help="Log the best contraction tree found",
    default=False,
)
@click.option(
    "--method_affinity",
    required=False,
    default=None,
    help="CPU affinity for finding decomposition",
)
@click.option(
    "--mem_limit",
    type=float,
    help="Hard limit on contraction memory usage (bytes); network is sliced to stay below the limit",
    required=False,
)
def run(
    benchmark,
    timeout,
    tree_timeout,
    output,
    seed,
    method,
    network_construction,
    entry_type,
    tensor_library,
    max_rank,
    thread_limit,
    performance_factor,
    log_contraction_tree,
    method_affinity,
    mem_limit,
):
    sys.setrecursionlimit(100000)
    tensor_library = tensor_library(entry_type, thread_limit=thread_limit)
    if mem_limit is not None:
        mem_limit /= tensor_library.get_entry_size()

    stopwatch = util.Stopwatch()
    if seed is not None:
        random.seed(seed)
    else:
        seed = random.randrange(1000000)  # for decomposition solvers

    if tree_timeout <= 0:
        tree_timeout = timeout

    network = network_construction(benchmark)
    util.log("Constructed network", flush=True)

    stopwatch.record_interval("Construction")
    with util.TimeoutTimer(tree_timeout) as timer:
        tree, network, groups_to_slice, edges_to_slice = find_contraction_tree(
            method,
            network,
            seed,
            timer,
            output,
            max_rank,
            performance_factor,
            method_affinity,
            mem_limit,
        )
        stopwatch.record_interval("Tree")

        if tree is not None:
            util.log("Using tree of max-rank " + str(tree.maxrank))
            if log_contraction_tree:
                util.log("Contraction Tree: " + str(tree))

            if tree.maxrank <= max_rank:
                try:
                    timer.reset_timeout(timeout)

                    while True:
                        try:
                            result = 0
                            for slice_network in network.slice_groups(groups_to_slice):
                                tensor_result, contract_log = tensor_library.contract(
                                    slice_network, tree, False
                                )
                                result += tensor_result[tuple()]
                            break
                        except tensor_network.OutOfMemoryError:
                            if mem_limit is None:
                                raise RuntimeError(
                                    "Ran out of memory when performing contractions"
                                )

                            # The estimation of memory usage is imperfect; another slice is required
                            _, memory, edge_to_slice = tree.estimate_cost(
                                edges_to_slice
                            )

                            equivalent_edges = network.find_equivalent_edges(
                                edge_to_slice
                            )
                            util.log(
                                "Memory usage at "
                                + str(memory)
                                + "; slicing network at equivalent edges "
                                + str(equivalent_edges),
                                flush=True,
                            )
                            groups_to_slice.append(equivalent_edges)
                            edges_to_slice |= equivalent_edges
                    stopwatch.record_interval("Contraction")
                    stopwatch.record_total("Total")
                    timer.cancel()
                    output.output_pair("Count", result)
                except TimeoutError:
                    util.log("Timed out during contraction", flush=True)
                    output.output_pair("Error", "contraction timeout")
                except MemoryError:
                    util.log("Ran out of memory during contraction", flush=True)
                    output.output_pair("Error", "contraction memout")
                except:
                    util.log("Error during contraction", flush=True)
                    util.log(traceback.format_exc())
                    output.output_pair("Error", "contraction unknown error")

            # Treewidth-based methods include the width of the underlying tree decomposition
            if hasattr(tree, "treewidth"):
                output.output_pair("Treewidth", tree.treewidth)
            if hasattr(tree, "branchwidth"):
                output.output_pair("Branchwidth", tree.branchwidth)

            output.output_pair("Max Rank", tree.maxrank)
            FLOPs, memory, _ = tree.estimate_cost(set().union(*groups_to_slice))
            output.output_pair("# Network Slices", 2 ** len(groups_to_slice))
            output.output_pair("Estimated Memory", float(memory))
            output.output_pair(
                "Estimated FLOPs", float(FLOPs * (2 ** len(groups_to_slice)))
            )

    for name, record in stopwatch.records.items():
        output.output_pair(name + " Time", record)

    if len(tensor_network.tensor_apis.contraction_info) > 0:
        output.output_pair(
            "Contraction Log", repr(str(tensor_network.tensor_apis.contraction_info))
        )


def find_contraction_tree(
    method,
    network,
    seed,
    timer,
    output,
    max_rank,
    performance_factor,
    method_affinity,
    mem_limit,
):
    best_tree = None
    best_network = None
    best_groups_to_slice = []
    best_edges_to_slice = set([])

    try:
        # Continue the search for a new contraction tree until we have spent more than half of the estimated total
        # time on the search (i.e., we have spent more than the expected contraction time on the search).
        for tree, factored_network in method.generate_contraction_trees(
            network, timer, seed=seed, affinity=method_affinity
        ):
            util.log("Found tree of max-rank " + str(tree.maxrank))

            if best_tree is None or best_tree.maxrank > tree.maxrank:
                best_tree = tree
                best_network = factored_network
                best_edges_to_slice = set([])
                best_groups_to_slice = []

                # If the new tree is usable, update the timeout
                if best_tree.maxrank <= max_rank:
                    FLOPs, memory, edge_to_slice = tree.estimate_cost(
                        best_edges_to_slice
                    )
                    while mem_limit is not None and memory > mem_limit:
                        equivalent_edges = best_network.find_equivalent_edges(
                            edge_to_slice
                        )
                        util.log(
                            "Memory usage at "
                            + str(memory)
                            + "; slicing network at equivalent edges "
                            + str(equivalent_edges),
                            flush=True,
                        )
                        best_groups_to_slice.append(equivalent_edges)
                        best_edges_to_slice |= equivalent_edges
                        FLOPs, memory, edge_to_slice = tree.estimate_cost(
                            best_edges_to_slice
                        )

                    estimated_contraction_time = (
                        FLOPs * (2 ** len(best_groups_to_slice)) * performance_factor
                    )
                    timer.recap_timeout(estimated_contraction_time)
    except TimeoutError:
        if best_tree is None:
            util.log("Timed out during search for contraction tree", flush=True)
            output.output_pair("Error", "tree timeout")
    except MemoryError:
        util.log("Ran out of memory during search for contraction tree", flush=True)
        output.output_pair("Error", "tree memout")
    except:
        util.log("Error during search for contraction tree", flush=True)
        util.log(traceback.format_exc())
        output.output_pair("Error", "tree unknown error")

    # Use the best tree that we have found so far
    return best_tree, best_network, best_groups_to_slice, best_edges_to_slice


if __name__ == "__main__":
    run(prog_name=os.getenv("TENSORORDER_CALLER", None))
