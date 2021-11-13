import click
import pickle
import random
import sys

import tensor_network
import util
from tensor_network import sliced_execution_plan


"""
Entry point for just the slicing part of the execution phase
"""


@click.command()
@click.argument("network_pair", type=click.File(mode="rb"), default="-")
@click.option(
    "--timeout", required=False, type=float, default=0, help="Timeout for slicing (s).",
)
@click.option(
    "--seed",
    type=int,
    required=False,
    default=None,
    help="Seed for random number generation",
)
@click.option(
    "--entry_size",
    type=int,
    help="Size (bytes) of tensor entries",
    default=4,
    show_default=True,
)
@click.option(
    "--rank_limit",
    type=int,
    help="Limit size of tensors",
    default=30,
    show_default=True,
)
@click.option(
    "--mem_limit",
    type=float,
    help="Limit on execution memory usage (bytes); network is sliced to meet the limit",
    required=False,
)
@click.option(
    "--slicer",
    default="greedy_mem",
    help="Method to use for tensor network slicing",
    type=util.TaggedChoice(tensor_network.ALL_SLICERS, case_sensitive=False),
    show_default=True,
)
def measure(
    network_pair, timeout, seed, entry_size, rank_limit, mem_limit, slicer,
):
    # Setup general system parameters
    sys.setrecursionlimit(100000)
    if seed is not None:
        random.seed(seed)

    # Mem limit should be in terms of number of entries, not bytes
    # So divide by the number of bytes per entry
    if mem_limit is not None:
        mem_limit /= entry_size

    stopwatch = util.Stopwatch()

    # Load the network and plan
    elapsed_time, tree, network = pickle.load(network_pair)
    plan = sliced_execution_plan.SlicedExecutionPlan(tree, network)
    util.log("Using tree of max-rank " + str(plan.tree.maxrank), util.Verbosity.stages)
    stopwatch.record_interval("Load")

    # Perform the specified splicing
    with util.TimeoutTimer(timeout) as _:
        try:
            slicer.slice_until(plan, memory=mem_limit, rank=rank_limit)
        except TimeoutError:
            util.output_pair("Error", "Timeout during slicing", util.Verbosity.always)
    stopwatch.record_interval("Slicing")

    stopwatch.record_total("Total")

    # Treewidth-based methods include the width of the underlying tree decomposition
    for width_name, width in plan.widths.items():
        util.output_pair(width_name, width, util.Verbosity.plan_info)

    # Report runtime statistics
    plan.report_statistics()
    stopwatch.report_times()


if __name__ == "__main__":
    measure()
