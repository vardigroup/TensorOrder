import click
import random
import traceback

import contraction_methods
import tensor_network
import tensor_network.tensor_apis
import util


@click.command()
@click.argument("benchmark", type=click.File(mode="r"), default="-")
@click.option(
    "--timeout",
    required=False,
    type=float,
    default=0,
    help="Timeout for the decomposition search (s).",
)
@click.option(
    "--output",
    type=util.KeyValueOutput("a", lazy=False),
    default="-",
    help="File to write output to",
)
@click.option(
    "--seed",
    type=int,
    required=False,
    default=None,
    help="Seed for random number generation",
)
@click.option(
    "--network_construction",
    required=True,
    help="How to construct tensor network from benchmark",
    default="wmc",
    type=util.TaggedChoice(tensor_network.ALL_CONSTRUCTIONS, case_sensitive=False),
)
@click.option(
    "--method",
    required=True,
    help="Method to use to find decomposition",
    type=util.TaggedChoice(contraction_methods.ALL_SOLVERS, case_sensitive=False),
)
def run(benchmark, timeout, output, seed, network_construction, method):
    if seed is not None:
        random.seed(seed)

    tensor_api = tensor_network.tensor_apis.NumpyAPI()
    network = network_construction(benchmark, tensor_api.create_tensor_factory("float"))
    util.log("Constructed network", flush=True)

    stopwatch = util.Stopwatch()
    log = []
    best_width = {}
    with util.TimeoutTimer(timeout) as _:
        try:
            for tree, _ in method(network, random_seed=seed):
                width = {"Carving": tree.maxrank}

                # Treewidth-based methods include the width of the underlying tree decomposition
                if hasattr(tree, "treewidth"):
                    width["Tree"] = tree.treewidth

                util.log("Found decomposition with " + str(width))
                for width_type in width:
                    if (
                        width_type not in best_width
                        or best_width[width_type] > width[width_type]
                    ):
                        best_width[width_type] = width[width_type]
                log.append((stopwatch.elapsed_time(), width))
        except TimeoutError:
            if best_width is {}:
                util.log("No decomposition found within the timeout", flush=True)
                output.output_pair("Error", "decomposition timeout")
        except MemoryError:
            util.log("Ran out of memory during search for decomposition", flush=True)
            output.output_pair("Error", "decomposition memout")
        except:
            util.log("Error during search for decomposition", flush=True)
            util.log(traceback.format_exc())
            output.output_pair("Error", "decomposition unknown error")

    for width_type in best_width:
        output.output_pair(width_type, best_width[width_type])
    output.output_pair("Log", repr(str(log)))


if __name__ == "__main__":
    run()
