import subprocess
import tempfile

from decompositions import TreeDecomposition, BranchDecomposition
import util


class DecompositionSolver:
    def __init__(self, argument_map):
        self.__argument_map = argument_map

    def generate_decompositions(self, write_graph, solver_parameters, timer):
        with tempfile.NamedTemporaryFile() as input_file:
            write_graph(input_file)
            input_file.flush()
            input_file.seek(0)

            parameters = {
                "locate": util.FileLocator(),
                "graph": input_file.name,
                **solver_parameters,
            }
            solve_cmd = [arg.format(**parameters) for arg in self.__argument_map]
            if (
                "affinity" in solver_parameters
                and solver_parameters["affinity"] is not None
            ):
                solve_cmd = ["taskset", "-c", solver_parameters["affinity"]] + solve_cmd
            process = subprocess.Popen(
                solve_cmd,
                stdin=input_file,
                bufsize=1,  # Line-buffered
                universal_newlines=True,  # Required for line-buffered
                stdout=subprocess.PIPE,
                preexec_fn=util.kill_on_crash(),
            )

            buffered_stream = util.BufferedStream(process.stdout, timer)
            try:
                while True:
                    result = parse_decomposition(buffered_stream)
                    if result is None:
                        break
                    yield result
            finally:  # Note this triggers on a GeneratorExit (i.e. when this generator is garbage collected)
                process.kill()


def parse_decomposition(stream):
    def record(comment):
        util.log(comment.rstrip(), flush=True)

    dimacs = util.DimacsStream(
        stream, process_comment=record, comment_prefixes=frozenset({"c", "O", "="})
    )
    header = dimacs.parse_line("s")
    if header is None:
        return None
    if header[1] == "td":
        return TreeDecomposition.parse(stream, header=header)
    elif header[1] == "bd":
        return BranchDecomposition.parse(stream, header=header)
    else:
        raise RuntimeError("Decomposition header unknown: " + str(header))


tcg_meiji_heuristic_online = DecompositionSolver(
    "java -classpath {locate[solvers/TCS-Meiji]} -Xmx25g -Xms25g -Xss1g tw.heuristic.MainDecomposer -s {seed} -p {print_tw_below}".split()
)

flow_cutter_online = DecompositionSolver(
    "{locate[solvers/flow-cutter-pace17/flow_cutter_pace17]} -s {seed} -p {print_tw_below}".split()
)

htd_online = DecompositionSolver(
    "{locate[solvers/htd-master/bin/htd_main]} -s {seed} --opt width --iterations 0 --strategy challenge --print-progress --preprocessing full".split()
)

hicks = DecompositionSolver("{locate[solvers/hicks/bw]}".split())

portfolio1 = DecompositionSolver(
    [
        "{locate[solvers/portfolio/build/portfolio]}",
        "{graph}",
        "{locate[solvers/flow-cutter-pace17/flow_cutter_pace17]} -s {seed} -p {print_tw_below}",
    ]
)


portfolio2 = DecompositionSolver(
    [
        "{locate[solvers/portfolio/build/portfolio]}",
        "{graph}",
        "java -classpath {locate[solvers/TCS-Meiji]} -Xmx25g -Xms25g -Xss1g tw.heuristic.MainDecomposer -s {seed} -p {print_tw_below}",
        "{locate[solvers/flow-cutter-pace17/flow_cutter_pace17]} -s {seed} -p {print_tw_below}",
    ]
)


portfolio3 = DecompositionSolver(
    [
        "{locate[solvers/portfolio/build/portfolio]}",
        "{graph}",
        "java -classpath {locate[solvers/TCS-Meiji]} -Xmx25g -Xms25g -Xss1g tw.heuristic.MainDecomposer -s {seed} -p {print_tw_below}",
        "{locate[solvers/flow-cutter-pace17/flow_cutter_pace17]} -s {seed} -p {print_tw_below}",
        "{locate[solvers/htd-master/bin/htd_main]} -s {seed} --opt width --iterations 0 --strategy challenge --print-progress --preprocessing full",
    ]
)

portfolio4 = DecompositionSolver(
    [
        "{locate[solvers/portfolio/build/portfolio]}",
        "{graph}",
        "java -classpath {locate[solvers/TCS-Meiji]} -Xmx25g -Xms25g -Xss1g tw.heuristic.MainDecomposer -s {seed} -p {print_tw_below}",
        "{locate[solvers/flow-cutter-pace17/flow_cutter_pace17]} -s {seed} -p {print_tw_below}",
        "{locate[solvers/htd-master/bin/htd_main]} -s {seed} --opt width --iterations 0 --strategy challenge --print-progress --preprocessing full",
        "{locate[solvers/hicks/bw]}",
    ]
)
