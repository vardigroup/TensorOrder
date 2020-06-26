import click
import os
import pickle
import random
import sys
import time
import traceback

import contraction_methods
import tensor_network
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
@click.option(
    "--store",
    required=False,
    type=click.Path(writable=True),
    help="Folder to store all discovered contraction trees",
    default=None,
)
@click.option(
    "--method_affinity",
    required=False,
    default=None,
    help="CPU affinity for finding decomposition",
)
def run(
    benchmark,
    timeout,
    output,
    seed,
    network_construction,
    method,
    store,
    method_affinity,
):
    sys.setrecursionlimit(100000)
    stopwatch = util.Stopwatch()
    if seed is not None:
        random.seed(seed)
    else:
        seed = random.randrange(1000000)  # for decomposition solvers

    if store is not None and not os.path.exists(store):
        os.makedirs(store)

    network = network_construction(benchmark)
    util.log("Constructed network", flush=True)
    stopwatch.record_interval("Construction")

    log_trees = []  # Discovered trees, to be saved at the end
    log = []  # Log and store only decompositions of lower carving width
    full_log = []  # Log all decompositions
    best_cw = None
    with util.TimeoutTimer(timeout) as timer:
        tree_gen = method.generate_contraction_trees(
            network, timer, seed=seed, affinity=method_affinity
        )
        try:
            for tree, new_network in tree_gen:
                width = {"Carving": tree.maxrank}

                # Treewidth-based methods include the width of the underlying tree decomposition
                if hasattr(tree, "treewidth"):
                    width["Tree"] = tree.treewidth
                if hasattr(tree, "branchwidth"):
                    width["Branch"] = tree.branchwidth

                util.log("Found decomposition with " + str(width), flush=True)
                elapsed_time = stopwatch.elapsed_time()

                FLOPs, _, _ = tree.estimate_cost(set())
                full_log.append((elapsed_time, width, FLOPs))
                if best_cw is None or best_cw > width["Carving"]:
                    best_cw = width["Carving"]
                    log.append((elapsed_time, width, FLOPs))
                    if store is not None:
                        log_trees.append(
                            (
                                (elapsed_time, tree, new_network),
                                store + "/" + str(len(log)) + ".con",
                            )
                        )
                        util.log(
                            "Saved contraction tree " + str(time.time()), flush=True
                        )
        except TimeoutError:
            if best_cw is None:
                util.log("No decomposition found within the timeout", flush=True)
                output.output_pair("Error", "decomposition timeout")
        except MemoryError:
            util.log("Ran out of memory during search for decomposition", flush=True)
            output.output_pair("Error", "decomposition memout")
        except:
            util.log("Error during search for decomposition", flush=True)
            util.log(traceback.format_exc())
            output.output_pair("Error", "decomposition unknown error")
        tree_gen.close()
    output.output_pair("Log", repr(str(log)))
    output.output_pair("FullLog", repr(str(full_log)))
    for info, filename in log_trees:
        pickle.dump(info, open(filename, "wb"))


if __name__ == "__main__":
    run()
