import click
import pickle
import sys
import traceback

import tensor_network
import util
from tensor_network import sliced_execution_plan


"""
Entry point for just the execution phase
"""


@click.command()
@click.argument("network_pair", type=click.File(mode="rb"), default="-")
@click.option(
    "--timeout",
    required=False,
    type=float,
    default=0,
    help="Timeout for execution (s).",
)
@click.option(
    "--entry_type",
    default="float64",
    help="Type of tensor entries",
    type=click.Choice(
        ["uint", "int", "bigint", "float16", "float32", "float64"], case_sensitive=False
    ),
    show_default=True,
)
@click.option(
    "--tensor_library",
    default="numpy",
    help="Tensor library to use",
    type=util.TaggedChoice(tensor_network.ALL_APIS, case_sensitive=False),
    show_default=True,
)
@click.option(
    "--rank_limit",
    type=int,
    help="Limit size of tensors",
    default=30,
    show_default=True,
)
@click.option("--thread_limit", type=int, help="Limit on execution number of threads")
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
@click.option(
    "--slice_cutoff",
    required=False,
    type=int,
    help="Only perform the first [slice_cutoff] slices",
)
def measure(
    network_pair,
    timeout,
    entry_type,
    tensor_library,
    rank_limit,
    thread_limit,
    mem_limit,
    slicer,
    slice_cutoff,
):
    sys.setrecursionlimit(100000)

    # Initialize the tensor API
    tensor_library = tensor_library()
    tensor_library.add_argument("entry_type", entry_type)
    if thread_limit is not None:
        tensor_library.add_argument("thread_limit", thread_limit)

    # Mem limit should be in terms of number of entries, not bytes
    # So divide by the number of bytes per entry
    if mem_limit is not None:
        mem_limit /= tensor_library.get_entry_size()

    stopwatch = util.Stopwatch()

    # Load the network and plan
    elapsed_time, tree, network = pickle.load(network_pair)
    plan = sliced_execution_plan.SlicedExecutionPlan(tree, network)
    util.log("Using tree of max-rank " + str(plan.tree.maxrank), util.Verbosity.stages)
    stopwatch.record_interval("Load")

    # Ensure the execution plan falls below the resource limits
    slicer.slice_until(plan, memory=mem_limit, rank=rank_limit)

    # Contract the tensor network
    result = None
    with util.TimeoutTimer(timeout) as timer:
        result = run(plan, tensor_library, slicer, slice_cutoff)
    timer.cancel()
    stopwatch.record_interval("Contraction")
    stopwatch.record_total("Total")

    # Treewidth-based methods include the width of the underlying tree decomposition
    for width_name, width in plan.widths.items():
        util.output_pair(width_name, width, util.Verbosity.plan_info)

    # Report runtime statistics
    plan.report_statistics()
    stopwatch.report_times()
    if result is not None:
        util.output_pair("Count", result, util.Verbosity.always)


def run(plan, tensor_library, slicer, slice_cutoff):
    """
    Contract the given tensor network

    :param plan: The execution plan to use
    :param tensor_library: Tensor API (from tensor_network.ALL_APIS) to use
    :param slicer: Slicer to use (from tensor_network.ALL_SLICERS) if MEMOUT
    :param slice_cutoff: Limit the number of slices
    :return: The contraction of the tensor network, or None
    """
    result = None
    try:
        while True:
            try:
                result = tensor_library.contract_sliced(
                    plan, num_slice_limit=slice_cutoff
                )
                break
            except tensor_network.OutOfMemoryError:
                # Slice the network and try again
                slicer.slice_once(plan)
    except TimeoutError:
        util.output_pair("Error", "Timeout during execution", util.Verbosity.always)
    except MemoryError:
        util.output_pair(
            "Error", "Out of Memory during execution", util.Verbosity.always
        )
    except:
        util.log(traceback.format_exc(), util.Verbosity.always)
        util.output_pair("Error", "Exception during execution", util.Verbosity.always)
    return result


if __name__ == "__main__":
    measure()
