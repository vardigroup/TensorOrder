import click
import pickle
import sys
import traceback

import tensor_network
import util


@click.command()
@click.argument("network_pair", type=click.File(mode="rb"), default="-")
@click.option(
    "--timeout",
    required=False,
    type=float,
    default=0,
    help="Timeout for the contraction (s).",
)
@click.option(
    "--output",
    type=util.KeyValueOutput("a", lazy=False),
    default="-",
    help="File to write output to",
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
    "--record_log",
    type=bool,
    default=False,
    help="Log the cost of all tensor computations",
)
@click.option(
    "--mem_limit",
    type=float,
    help="Hard limit on contraction memory usage (bytes); network is sliced to stay below the limit",
    required=False,
)
def run(
    network_pair,
    timeout,
    output,
    entry_type,
    tensor_library,
    max_rank,
    thread_limit,
    record_log,
    mem_limit,
):
    sys.setrecursionlimit(100000)
    tensor_library = tensor_library(entry_type, thread_limit=thread_limit)
    if mem_limit is not None:
        mem_limit /= tensor_library.get_entry_size()

    stopwatch = util.Stopwatch()
    elapsed_time, tree, network = pickle.load(network_pair)
    edges_to_slice = set([])
    groups_to_slice = []
    util.log("Using tree of max-rank " + str(tree.maxrank))
    stopwatch.record_interval("Load")

    if tree.maxrank <= max_rank:
        FLOPs, memory, edge_to_slice = tree.estimate_cost(edges_to_slice)
        while mem_limit is not None and memory > mem_limit:
            equivalent_edges = network.find_equivalent_edges(edge_to_slice)
            util.log(
                "Memory usage at "
                + str(memory)
                + "; slicing network at equivalent edges "
                + str(equivalent_edges),
                flush=True,
            )
            groups_to_slice.append(equivalent_edges)
            edges_to_slice |= equivalent_edges
            FLOPs, memory, edge_to_slice = tree.estimate_cost(edges_to_slice)

        try:
            with util.TimeoutTimer(timeout) as timer:
                while True:
                    try:
                        result = 0
                        for slice_network in network.slice_groups(groups_to_slice):
                            tensor_result, contract_log = tensor_library.contract(
                                slice_network, tree, record_log
                            )
                            result += tensor_result[tuple()]
                        break
                    except tensor_network.OutOfMemoryError:
                        if mem_limit is None:
                            raise RuntimeError(
                                "Ran out of memory when performing contractions"
                            )

                        # The estimation of memory usage is imperfect; another slice is required
                        equivalent_edges = network.find_equivalent_edges(edge_to_slice)
                        util.log(
                            "Memory usage at "
                            + str(memory)
                            + "; slicing network at equivalent edges "
                            + str(equivalent_edges),
                            flush=True,
                        )
                        groups_to_slice.append(equivalent_edges)
                        edges_to_slice |= equivalent_edges
                        FLOPs, memory, edge_to_slice = tree.estimate_cost(
                            edges_to_slice
                        )
                stopwatch.record_interval("Contraction")
                stopwatch.record_total("Total")
                timer.cancel()
                output.output_pair("Count", result)
                if record_log:
                    output.output_pair("Log", repr(str(contract_log)))
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

    for name, record in stopwatch.records.items():
        output.output_pair(name + " Time", record)

    # Treewidth-based methods include the width of the underlying tree decomposition
    if hasattr(tree, "treewidth"):
        output.output_pair("Treewidth", tree.treewidth)

    output.output_pair("Max Rank", tree.maxrank)
    FLOPs, memory, _ = tree.estimate_cost(set().union(*groups_to_slice))
    output.output_pair("# Network Slices", 2 ** len(groups_to_slice))
    output.output_pair("Estimated Memory", float(memory))
    output.output_pair("Estimated FLOPs", float(FLOPs * (2 ** len(groups_to_slice))))


if __name__ == "__main__":
    run()
