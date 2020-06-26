import click
import os
import subprocess


@click.command()
@click.option("--input", "input_path", type=click.Path(exists=True, dir_okay=True))
@click.option("--output", "output_path", type=click.Path(exists=False, dir_okay=True))
@click.option(
    "--preprocessor",
    required=False,
    default="/home/jmd11/pmc/preproc -vivification -eliminateLit -litImplied -iterate=10",
)
@click.option("--copy_weights", required=False, type=bool, default=True)
def run(input_path, output_path, preprocessor, copy_weights):
    benchmarks = find_benchmarks(input_path)
    print(benchmarks)
    for benchmark in benchmarks:
        print(input_path + benchmark + " > " + output_path + benchmark)

        if "/" in benchmark:
            os.makedirs(output_path + benchmark[: benchmark.rfind("/")], exist_ok=True)

        with open(input_path + benchmark, "r") as before:
            with open(os.devnull, "w") as FNULL:
                process = subprocess.Popen(
                    preprocessor.split(),
                    stdin=before,
                    bufsize=1,  # Line-buffered
                    universal_newlines=True,  # Required for line-buffered
                    stdout=subprocess.PIPE,
                    stderr=FNULL,
                )

                # Gather the weight lines from the original benchmark
                weights = []
                if copy_weights:
                    with open(input_path + benchmark, "r") as before_weights:
                        for line in before_weights:
                            if len(line) > 0 and line[0] == "w":
                                weights.append(line)

                with open(output_path + benchmark, "w") as after:
                    for line in process.stdout:
                        after.write(line.rstrip() + "\n")
                        if len(line) > 0 and line[0] == "p":  # DIMACS header
                            for weight in weights:
                                after.write(weight)
                            weights = []  # Ensure weights are only written once


def find_benchmarks(path):
    """
    Return a list of all benchmarks within the provided path.
    :param path: The file/folder to search
    :return: A list of filenames, relative to the provided path
    """
    if os.path.isdir(path):
        result = []
        for obj in os.listdir(path):
            obj_path = path + "/" + obj
            result += ["/" + obj + b for b in find_benchmarks(obj_path)]
        return result
    elif os.path.isfile(path) and "README" not in path:
        return [""]
    else:
        return []


if __name__ == "__main__":
    run()
