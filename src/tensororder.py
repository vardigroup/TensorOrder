import click
import os
import random
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
    default="float",
    help="Data type to use for all tensor computations",
    type=click.Choice(["float", "uint", "int", "bigint"], case_sensitive=False),
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
):
    if seed is not None:
        random.seed(seed)
    else:
        seed = random.randint(0, 2 ** 30 - 1)

    if tree_timeout <= 0:
        tree_timeout = timeout

    stopwatch = util.Stopwatch()
    network = network_construction(
        benchmark, tensor_library.create_tensor_factory(entry_type)
    )
    util.log("Constructed network", flush=True)

    stopwatch.record_interval("Construction")
    with util.TimeoutTimer(tree_timeout) as timer:
        tree, network = find_contraction_tree(
            method, network, seed, timer, output, max_rank
        )
        stopwatch.record_interval("Tree")

        if tree is not None:
            util.log("Using tree of max-rank " + str(tree.maxrank))
            if tree.maxrank <= max_rank:
                try:
                    timer.reset_timeout(timeout)

                    result = network.identify(tree, tensor_library)[tuple()]
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
                    util.log("Error during search for contraction", flush=True)
                    util.log(traceback.format_exc())
                    output.output_pair("Error", "contraction unknown error")

            # Treewidth-based methods include the width of the underlying tree decomposition
            if hasattr(tree, "treewidth"):
                output.output_pair("Treewidth", tree.treewidth)

            output.output_pair("Max Rank", tree.maxrank)
            output.output_pair("Estimated FLOPs", float(tree.required_FLOPS))

    for name, record in stopwatch.records.items():
        output.output_pair(name + " Time", record)


def find_contraction_tree(method, network, random_seed, timer, output, max_rank):
    best_tree = None
    best_factored_network = None

    try:
        # Continue the search for a new contraction tree until we have spent more than half of the estimated total
        # time on the search (i.e., we have spent more than the expected contraction time on the search).
        for tree, factored_network in method(network, random_seed=random_seed):
            util.log("Found tree of max-rank " + str(tree.maxrank))

            if best_tree is None or best_tree.maxrank > tree.maxrank:
                best_tree = tree
                best_factored_network = factored_network

                # If the new tree is usable, update the timeout
                if best_tree.maxrank <= max_rank:
                    estimated_contraction_time = best_tree.required_FLOPS * float(
                        2.56609617e-18
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
    return best_tree, best_factored_network


if __name__ == "__main__":
    run(prog_name=os.getenv("TENSORORDER_CALLER", None))
