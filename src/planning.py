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
from tensor_network import sliced_execution_plan

"""
Entry point for just the planning phase
"""


@click.command()
@click.argument("benchmark", type=click.File(mode="r"), default="-")
@click.option(
    "--weights",
    required=True,
    help="Weight format of benchmark",
    type=util.TaggedChoice(
        {w.name: w for w in util.WeightFormat}, case_sensitive=False
    ),
)
@click.option(
    "--timeout", required=False, type=float, default=0, help="Timeout for planning (s)",
)
@click.option(
    "--seed",
    type=int,
    required=False,
    default=None,
    help="Seed for random number generation",
)
@click.option(
    "--reduction",
    required=True,
    help="How to get tensor network from benchmark",
    default="wmc",
    type=util.TaggedChoice(tensor_network.ALL_CONSTRUCTIONS, case_sensitive=False),
)
@click.option(
    "--planner",
    required=True,
    help="Method to find contraction tree",
    type=util.TaggedChoice(contraction_methods.ALL_SOLVERS, case_sensitive=False),
)
@click.option(
    "--store",
    required=False,
    type=click.Path(writable=True),
    help="Folder to store all contraction trees",
    default=None,
)
@click.option(
    "--planner_affinity",
    required=False,
    default=None,
    help="CPU affinity for finding decomposition",
)
def measure(
    benchmark, weights, timeout, seed, reduction, planner, store, planner_affinity,
):
    sys.setrecursionlimit(100000)
    stopwatch = util.Stopwatch()
    if seed is not None:
        random.seed(seed)
    else:
        seed = random.randrange(1000000)  # for decomposition solvers

    if store is not None and not os.path.exists(store):
        os.makedirs(store)

    # Construct the tensor network
    network = reduction(benchmark, weights)
    util.log("Completed reduction to tensor network", util.Verbosity.stages)
    stopwatch.record_interval("Construction")

    log = []  # Log and store only decompositions of lower carving width

    full_log = []  # Log all decompositions
    with util.TimeoutTimer(timeout) as timer:
        best_plan, plan_log = run(
            planner,
            network,
            seed,
            timer,
            planner_affinity,
            rank_limit=None,
            performance_factor=None,
            mem_limit=None,
            slicer=None,
            stopwatch=stopwatch,
        )

    # Record information on all observed plans
    best_cw = None
    for elapsed_time, plan in plan_log:
        full_log.append((elapsed_time, plan.widths, plan.total_FLOPs))
        if best_cw is None or best_cw > plan.tree.maxrank:
            best_cw = plan.tree.maxrank
            log.append((elapsed_time, plan.widths, plan.total_FLOPs))

            if store is not None:
                info = (elapsed_time, plan.tree, plan.network)
                filename = store + "/" + str(len(log)) + ".con"
                pickle.dump(info, open(filename, "wb"))
                util.log(
                    "Saved contraction tree " + str(time.time()), util.Verbosity.debug
                )
    util.output_pair("Log", repr(str(log)), util.Verbosity.always)
    util.output_pair("FullLog", repr(str(full_log)), util.Verbosity.always)


def run(
    planner,
    network,
    seed,
    timer,
    planner_affinity,
    rank_limit,
    performance_factor,
    mem_limit,
    slicer,
    stopwatch=None,
):
    """
    Find a contraction tree for the given tensor network

    :param planner: The planner to use (from contraction_methods.ALL_SOLVERS)
    :param network: The tensor network
    :param seed: A random seed to use for the planning
    :param timer: The current util.TimeoutTimer (timeout may be changed)
    :param planner_affinity: CPU affinity for finding decomposition
    :param rank_limit: Limit rank of tensors in the plan (with slicing)
    :param performance_factor:
    :param mem_limit: Limit memory usage of plan (with slicing)
    :param slicer: Slicer to use (from tensor_network.ALL_SLICERS)
    :param stopwatch: The current Stopwatch
    :return: (execution plan, list of all (time generated, plan) tuples)
    """
    best_plan = None
    log = []

    try:
        # Continue the search for a new contraction tree until we have spent more than half of the estimated total
        # time on the search (i.e., we have spent more than the expected contraction time on the search).
        for tree, factored_network in planner.generate_contraction_trees(
            network, timer, seed=seed, affinity=planner_affinity
        ):
            util.log(
                "Found tree of max-rank " + str(tree.maxrank), util.Verbosity.progress
            )

            if best_plan is None or best_plan.tree.maxrank > tree.maxrank:
                best_plan = sliced_execution_plan.SlicedExecutionPlan(
                    tree, factored_network
                )
                if stopwatch is not None:
                    log.append((stopwatch.elapsed_time(), best_plan))

                if slicer is not None:
                    slicer.slice_until(best_plan, memory=mem_limit, rank=rank_limit)
                if performance_factor is not None:
                    estimated_contraction_time = (
                        best_plan.total_FLOPs * performance_factor
                    )
                    timer.recap_timeout(estimated_contraction_time)
            elif stopwatch is not None:
                log.append(
                    (
                        stopwatch.elapsed_time(),
                        sliced_execution_plan.SlicedExecutionPlan(
                            tree, factored_network
                        ),
                    )
                )
    except TimeoutError:
        if best_plan is None:
            util.output_pair("Error", "Timeout during planning", util.Verbosity.always)
    except MemoryError:
        util.output_pair(
            "Error", "Out of Memory during planning", util.Verbosity.always
        )
    except:
        util.log(traceback.format_exc(), util.Verbosity.always)
        util.output_pair("Error", "Exception during execution", util.Verbosity.always)

    # Use the best tree that we have found so far
    return best_plan, log


if __name__ == "__main__":
    measure()
