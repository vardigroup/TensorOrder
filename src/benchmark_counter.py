import click
import subprocess
import tempfile
import traceback

from util import KeyValueOutput, TimeoutTimer, Stopwatch, log
from util import Formula

"""
This tool provides a uniform API to run benchmarks on various other model counters.
"""


@click.group()
def run():
    pass


@run.command()
@click.argument("benchmark", default="-", type=click.Path(exists=True, dir_okay=False))
@click.option("--timeout", required=False, type=int, help="Timeout (s).")
@click.option(
    "--output",
    type=KeyValueOutput("a", lazy=False),
    default="-",
    help="File to write output to",
)
@click.option(
    "--counter",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="Location of sharpSAT executable",
)
def sharpsat(benchmark, timeout, output, counter):
    try:
        with TimeoutTimer(timeout) as _:
            process = subprocess.Popen(
                [counter, benchmark],
                bufsize=1,  # Line-buffered
                universal_newlines=True,  # Required for line-buffered
                stdout=subprocess.PIPE,
            )

            count_is_next = False
            for line in process.stdout:
                log(line, end="")

                if count_is_next:
                    output.output_pair("Count", float(line.split()[-1]))
                    count_is_next = False
                if line.startswith("# solutions"):
                    count_is_next = True
                if line.startswith("time: "):
                    output.output_pair(
                        "Total Time", float(line.split()[-1].replace("s", ""))
                    )
    except TimeoutError:
        output.output_pair("Error", "timeout")
    except:
        output.output_pair("Error", "unknown")
        log(traceback.format_exc())


@run.command()
@click.argument("benchmark", default="-", type=click.Path(exists=True, dir_okay=False))
@click.option("--timeout", required=False, type=int, help="Timeout (s).")
@click.option(
    "--output",
    type=KeyValueOutput("a", lazy=False),
    default="-",
    help="File to write output to",
)
@click.option(
    "--counter",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="Location of miniC2D executable",
)
@click.option(
    "--rewrite_benchmark",
    type=bool,
    default=True,
    help="Rewrite the benchmark to use miniC2D weight format",
)
def minic2d(benchmark, timeout, output, counter, rewrite_benchmark):
    temp_directory = None
    if rewrite_benchmark:
        with open(benchmark, "r") as benchmark_file:
            formula = Formula.parse_DIMACS(benchmark_file, include_missing_vars=False)
        temp_directory = tempfile.TemporaryDirectory()

        benchmark = temp_directory.name + "/formula.cnf"
        formula.write_miniC2D(benchmark)

    try:
        with TimeoutTimer(timeout) as _:
            process = subprocess.Popen(
                [counter, "-W", "-c", benchmark],
                bufsize=1,  # Line-buffered
                universal_newlines=True,  # Required for line-buffered
                stdout=subprocess.PIPE,
            )

            for line in process.stdout:
                log(line, end="")

                if line.startswith("Total Time"):
                    output.output_pair(
                        "Total Time", float(line.split()[-1].replace("s", ""))
                    )
                elif not line.startswith("  Count Time") and line.startswith("  Count"):
                    output.output_pair("Count", float(line.split()[-1]))
    except TimeoutError:
        output.output_pair("Error", "timeout")
    except:
        output.output_pair("Error", "unknown")
        log(traceback.format_exc())

    if temp_directory is not None:
        temp_directory.cleanup()


@run.command()
@click.argument("benchmark", default="-", type=click.Path(exists=True, dir_okay=False))
@click.option("--timeout", required=False, type=int, help="Timeout (s).")
@click.option(
    "--output",
    type=KeyValueOutput("a", lazy=False),
    default="-",
    help="File to write output to",
)
@click.option(
    "--counter",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="Location of d4 executable",
)
@click.option(
    "--weighted",
    type=bool,
    default=False,
    help="True if d4 should be used as a weighted counter (undocumented)",
)
def d4(benchmark, timeout, output, counter, weighted):
    temp_directory = None

    try:
        if weighted:
            with open(benchmark, "r") as benchmark_file:
                formula = Formula.parse_DIMACS(
                    benchmark_file, include_missing_vars=False
                )

            temp_directory = tempfile.TemporaryDirectory()
            benchmark = temp_directory.name + "/formula.cnf"
            weights = temp_directory.name + "/weights.wts"
            formula.write_DNNF(benchmark, weights)

            log("Separated weights", flush=True)

            with TimeoutTimer(timeout) as _:

                stopwatch = Stopwatch()

                process = subprocess.Popen(
                    [counter, benchmark, "-wFile=" + weights + ""],
                    bufsize=1,  # Line-buffered
                    universal_newlines=True,  # Required for line-buffered
                    stdout=subprocess.PIPE,
                )

                is_unsatisfiable = False
                for line in process.stdout:
                    log(line, end="")

                    if line.startswith("c Final time:"):
                        output.output_pair(
                            "Compilation Time", float(line.split()[-1].replace("s", ""))
                        )
                    elif line.startswith("c The formula is unsatisfiable"):
                        is_unsatisfiable = True
                        output.output_pair("Count", 0)
                    elif line.startswith("s ") and not is_unsatisfiable:
                        output.output_pair("Count", float(line.split()[-1]))
                stopwatch.record_total("Total")

            for name, record in stopwatch.records.items():
                output.output_pair(name + " Time", record)

        else:
            with TimeoutTimer(timeout) as _:
                process = subprocess.Popen(
                    [counter, benchmark],
                    bufsize=1,  # Line-buffered
                    universal_newlines=True,  # Required for line-buffered
                    stdout=subprocess.PIPE,
                )

                for line in process.stdout:
                    log(line, end="")

                    if line.startswith("c Final time:"):
                        output.output_pair(
                            "Total Time", float(line.split()[-1].replace("s", ""))
                        )
                    elif line.startswith("s "):
                        output.output_pair("Count", float(line.split()[-1]))
    except TimeoutError:
        output.output_pair("Error", "timeout")
    except:
        output.output_pair("Error", "unknown")
        log(traceback.format_exc())

    if temp_directory is not None:
        temp_directory.cleanup()


@run.command()
@click.argument("benchmark", default="-", type=click.File(mode="r"))
@click.option("--timeout", required=False, type=int, help="Timeout (s).")
@click.option(
    "--output",
    type=KeyValueOutput("a", lazy=False),
    default="-",
    help="File to write output to",
)
@click.option(
    "--counter",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="Location of dynQBF executable",
)
def dynqbf(benchmark, timeout, output, counter):
    try:
        formula = Formula.parse_DIMACS(benchmark, include_missing_vars=False)

        temp_directory = tempfile.TemporaryDirectory()
        benchmark = temp_directory.name + "/formula.cnf"
        formula.write_QBF(benchmark)

        with TimeoutTimer(timeout) as _:
            stopwatch = Stopwatch()
            process = subprocess.Popen(
                [counter, "--model-count", "-f", benchmark],
                bufsize=1,  # Line-buffered
                universal_newlines=True,  # Required for line-buffered
                stdout=subprocess.PIPE,
            )

            for line in process.stdout:
                log(line, end="")

                if line.startswith("Model count"):
                    output.output_pair("Count", float(line.split(": ")[-1]))

            stopwatch.record_total("Total")
            for name, record in stopwatch.records.items():
                output.output_pair(name + " Time", record)
    except TimeoutError:
        output.output_pair("Error", "timeout")
    except:
        output.output_pair("Error", "unknown")
        log(traceback.format_exc())


@run.command()
@click.argument("benchmark", default="-", type=click.Path(exists=True, dir_okay=False))
@click.option("--timeout", required=False, type=int, help="Timeout (s).")
@click.option(
    "--output",
    type=KeyValueOutput("a", lazy=False),
    default="-",
    help="File to write output to",
)
@click.option(
    "--counter",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="Location of cachet executable",
)
@click.option(
    "--weighted",
    type=bool,
    default=False,
    help="True if cachet should be used as a weighted counter",
)
def cachet(benchmark, timeout, output, counter, weighted):
    try:
        with TimeoutTimer(timeout) as _:
            process = subprocess.Popen(
                [counter, benchmark],
                bufsize=1,  # Line-buffered
                universal_newlines=True,  # Required for line-buffered
                stdout=subprocess.PIPE,
            )

            for line in process.stdout:
                log(line, end="")

                if weighted and line.startswith("Satisfying probability"):
                    output.output_pair("Count", float(line.split()[-1]))
                if not weighted and line.startswith("s "):
                    output.output_pair("Count", float(line.split()[-1]))
                if line.startswith("Total Run Time"):
                    output.output_pair("Total Time", float(line.split()[-1]))
    except TimeoutError:
        output.output_pair("Error", "timeout")
    except:
        output.output_pair("Error", "unknown")
        log(traceback.format_exc())


@run.command()
@click.argument("benchmark", default="-", type=click.File(mode="r"))
@click.option("--timeout", required=False, type=int, help="Timeout (s).")
@click.option(
    "--output",
    type=KeyValueOutput("a", lazy=False),
    default="-",
    help="File to write output to",
)
@click.option(
    "--counter",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="Location of dynASP executable",
)
@click.option(
    "--gringo",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="Location of gringo executable",
)
def dynasp(benchmark, timeout, output, counter, gringo):
    try:
        formula = Formula.parse_DIMACS(benchmark, include_missing_vars=False)

        temp_directory = tempfile.TemporaryDirectory()
        asp = temp_directory.name + "/formula.asp"
        formula.write_ASP(asp)

        grounded = temp_directory.name + "/grounded.lparse"
        with open(grounded, "w") as grounded_file:
            subprocess.call([gringo, "-o", "smodels", asp], stdout=grounded_file)

        with TimeoutTimer(timeout) as _:
            stopwatch = Stopwatch()
            process = subprocess.Popen(
                [counter, "-S", grounded],
                bufsize=1,  # Line-buffered
                universal_newlines=True,  # Required for line-buffered
                stdout=subprocess.PIPE,
            )

            for line in process.stdout:
                log(line, end="")

                if line.startswith("SOLUTION COUNT:"):
                    output.output_pair(
                        "Count", float(line.split(" ")[-1].split("@")[0])
                    )

            stopwatch.record_total("Total")
            for name, record in stopwatch.records.items():
                output.output_pair(name + " Time", record)
    except TimeoutError:
        output.output_pair("Error", "timeout")
    except:
        output.output_pair("Error", "unknown")
        log(traceback.format_exc())


if __name__ == "__main__":
    run()
