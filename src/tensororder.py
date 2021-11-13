import click
import os
import random
import sys

import contraction_methods
import tensor_network
import util
import planning
import execution


"""
Main entry point for the full TensorOrder tool
"""


@click.command(
    cls=util.GroupedHelp,
    groups={
        "weights": "Reduction Stage",
        "planner ": "Planning Stage",
        "tensor_library": "Execution Stage",
    },
)
@click.argument("benchmark", type=click.File(mode="r"), default="-")
@click.option(
    "--timeout", type=float, default=0, help="Timeout for entire computation (s)",
)
@click.option(
    "--verbosity",
    type=util.TaggedChoice(
        {str(v.value): v for v in util.Verbosity}, case_sensitive=False
    ),
    default=str(int(util.Verbosity.debug)),
    show_default=True,
    help="Detail level of output",
)
@click.option(
    "--seed", type=int, default=None, help="Seed for random number generation"
)
# Reduction Stage options
@click.option(
    "--weights",
    required=True,
    help="Weight format of benchmark",
    type=util.TaggedChoice(
        {w.name: w for w in util.WeightFormat}, case_sensitive=False
    ),
)
@click.option(
    "--reduction",
    help="How to get tensor network from benchmark",
    default="wmc",
    type=util.TaggedChoice(tensor_network.ALL_CONSTRUCTIONS, case_sensitive=False),
)
# Planning Stage options
@click.option(
    "--planner",
    required=True,
    help="Method to find contraction tree",
    type=util.TaggedChoice(contraction_methods.ALL_SOLVERS, case_sensitive=False),
)
@click.option(
    "--planner_timeout", type=float, default=0, help="Timeout for planning only (s)",
)
@click.option(
    "--planner_affinity",
    required=False,
    default=None,
    help="CPU affinity for finding decomposition",
)
@click.option(
    "--performance_factor",
    type=float,
    help="Ratio to end planning",
    default=10 ** (-11),
    show_default=True,
)
@click.option(
    "--log_contraction_tree",
    required=False,
    type=bool,
    help="Log the best contraction tree found",
    default=False,
)
# Execution Stage options
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
@click.option(
    "--entry_type",
    default="float64",
    help="Type of tensor entries",
    type=click.Choice(
        ["uint", "int", "bigint", "float16", "float32", "float64"], case_sensitive=False
    ),
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
    "--early", type=int, help="Contract tensors early", default=0, show_default=False,
)
@click.option(
    "--tpu", required=False, type=str, help="Address of TPU to use", default=None,
)
@click.option(
    "--minimum_slice",
    required=False,
    type=int,
    help="Minimum number of variables to slice",
    default=0,
)
@click.option(
    "--slice_cutoff",
    required=False,
    type=int,
    help="Only perform the first [slice_cutoff] slices",
)
@click.option(
    "--jax_ensure_small",
    required=False,
    type=bool,
    help="Place smaller tensors on the right of the contraction tree",
    default=True,
)
@click.option(
    "--jax_oneshot",
    required=False,
    type=bool,
    help="Compile a single large JAX function for contraction",
    default=True,
)
@click.option(
    "--jax_tensordot",
    required=False,
    type=click.Choice(
        ["tensordot", "matmul", "matmul_ind_transpose", "matmul_no_transpose"],
        case_sensitive=False,
    ),
    help="Implementation of tensordot to use in contraction",
    default="tensordot",
)
def run(
    benchmark,
    timeout,
    verbosity,
    seed,
    # Reduction Stage options
    weights,
    reduction,
    # Planning Stage options
    planner,
    planner_timeout,
    planner_affinity,
    performance_factor,
    log_contraction_tree,
    # Execution Stage options
    tensor_library,
    rank_limit,
    entry_type,
    thread_limit,
    mem_limit,
    slicer,
    early,
    tpu,
    slice_cutoff,
    minimum_slice,
    jax_ensure_small,
    jax_oneshot,
    jax_tensordot,
):
    # Setup general system parameters
    sys.setrecursionlimit(100000)
    util.set_verbosity(verbosity)
    if seed is not None:
        random.seed(seed)
    else:
        seed = random.randrange(1000000)  # for decomposition solvers

    # Initialize the tensor API
    tensor_library = tensor_library()
    tensor_library.add_argument("entry_type", entry_type)
    if thread_limit is not None:
        tensor_library.add_argument("thread_limit", thread_limit)
    if not jax_ensure_small:
        tensor_library.add_argument("ensure_small", jax_ensure_small)
    if not jax_oneshot:
        tensor_library.add_argument("oneshot", jax_oneshot)
    if jax_tensordot is not "tensordot":
        tensor_library.add_argument("tensordot", jax_tensordot)
    if tpu is not None and len(tpu) > 0:
        tensor_library.add_argument("TPU", tpu)

    # Mem limit should be in terms of number of entries, not bytes
    # So divide by the number of bytes per entry
    if mem_limit is not None:
        mem_limit /= tensor_library.get_entry_size()
        util.log(
            "Setting memory limit of " + str(mem_limit) + str(" entries"),
            util.Verbosity.stages,
        )

    stopwatch = util.Stopwatch()

    # Reduction phase: Construct the tensor network
    network = reduction(benchmark, weights)
    util.log("Completed reduction to tensor network", util.Verbosity.stages)
    stopwatch.record_interval("Construction")

    result = None
    if planner_timeout <= 0:
        planner_timeout = timeout
    with util.TimeoutTimer(planner_timeout) as timer:
        # Planning phase: find the execution plan to use
        #   (see tensor_network/sliced_execution_plan.py)
        plan, _ = planning.run(
            planner,
            network,
            seed,
            timer,
            planner_affinity,
            rank_limit,
            performance_factor,
            mem_limit=None,
            slicer=None,
            stopwatch=None,
        )
        stopwatch.record_interval("Tree")

        if plan is not None:
            # Report on plan information
            util.log(
                "Identified plan has max-rank " + str(plan.tree.maxrank),
                util.Verbosity.stages,
            )
            if log_contraction_tree:
                util.log("Contraction Tree: " + str(plan.tree), util.Verbosity.always)

            # Execution phase: Contract the tensor network
            timer.reset_timeout(timeout)
            try:
                # Slice the network according to resource constraints
                slicer.slice_until(
                    plan, memory=mem_limit, rank=rank_limit, slices=minimum_slice
                )

                # Contract each tensor network slice
                if early > 0:
                    plan.contract_small(
                        early, tensor_network.ALL_APIS["numpy"](),
                    )
                result = execution.run(plan, tensor_library, slicer, slice_cutoff)
                stopwatch.record_interval("Contraction")
            except:
                util.output_pair(
                    "Error", "Tree above specified limits", util.Verbosity.always
                )

            stopwatch.record_total("Total")
            timer.cancel()

            util.output("-", util.Verbosity.stages)

            # Treewidth-based methods include the width of the underlying tree decomposition
            for width_name, width in plan.widths.items():
                util.output_pair(width_name, width, util.Verbosity.plan_info)

            # Report plan statistics
            plan.report_statistics()

    # Report time statistics
    stopwatch.report_times()
    if result is not None:
        util.output_pair("Count", result, util.Verbosity.always)


if __name__ == "__main__":
    run(prog_name=os.getenv("TENSORORDER_CALLER", None))
