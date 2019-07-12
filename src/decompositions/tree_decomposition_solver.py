import networkx
import os
import subprocess
import tempfile

from decompositions import TreeDecomposition
import util


class TreeDecompositionSolver:
    def __init__(self, location, argument_map):
        self.__location = location
        self.__argument_map = argument_map

    def generate_tree_decompositions(self, graph, solver_parameters):
        if os.path.exists(self.__location):
            location = self.__location
        elif os.path.exists("/" + self.__location):
            location = "/" + self.__location
        else:
            raise EnvironmentError("Unable to locate solver " + self.__location)

        solve_cmd = self.__argument_map.format(location=location, **solver_parameters)

        with tempfile.TemporaryFile() as input_file:
            recover_edges = write_benchmark(graph, input_file)
            input_file.flush()
            input_file.seek(0)
            process = subprocess.Popen(
                solve_cmd.split(),
                stdin=input_file,
                bufsize=1,  # Line-buffered
                universal_newlines=True,  # Required for line-buffered
                stdout=subprocess.PIPE,
            )

            try:
                while True:
                    result = TreeDecomposition.parse_one(
                        process.stdout, renumber_bag_components=recover_edges
                    )
                    if result is None:
                        break
                    yield result
            finally:  # Note this triggers on a GeneratorExit (i.e. when this generator is garbage collected)
                process.kill()


tcg_meiji_heuristic_online = TreeDecompositionSolver(
    "solvers/TCS-Meiji",
    "java -classpath {location} -Xmx30g -Xms30g -Xss1g tw.heuristic.MainDecomposer -s {treewidth_seed} -p {print_bag_below}",
)

flow_cutter_online = TreeDecompositionSolver(
    "solvers/flow-cutter-pace17/flow_cutter_pace17",
    "{location} -s {treewidth_seed} -p {print_bag_below}",
)

htd_online = TreeDecompositionSolver(
    "solvers/htd-master/bin/htd_main",
    "{location} -s {treewidth_seed} --opt width --iterations 0 --strategy challenge --print-progress --preprocessing full",
)


def parse_benchmark(file):
    result = networkx.MultiGraph()

    num_nodes = None
    num_edges = None
    with open(file, "r") as f:
        for line in f:
            parts = line.split()
            if len(parts) < 2 or parts[0] == "c":
                util.log(parts)
                continue
            elif parts[0] == "p":
                if len(parts) != 4:
                    raise RuntimeError(
                        "Unable to parse benchmark %s: Incorrect header %s"
                        % (file, line)
                    )
                num_nodes = int(parts[2])
                num_edges = int(parts[3])
            else:
                if len(parts) != 2:
                    raise RuntimeError(
                        "Unable to parse benchmark %s: Invalid line %s" % (file, line)
                    )
                result.add_edge(int(parts[0]), int(parts[1]))

    if result.number_of_nodes() != num_nodes:
        raise RuntimeError(
            "Benchmark expected to have %d nodes but had %d"
            % (num_nodes, result.number_of_nodes())
        )
    if result.number_of_edges() != num_edges:
        raise RuntimeError(
            "Benchmark expected to have %d edges but had %d"
            % (num_edges, result.number_of_edges())
        )
    return result


def write_benchmark(graph, file):
    relabelled = networkx.convert_node_labels_to_integers(
        graph, first_label=1, label_attribute="old_id"
    )
    file.write(
        b"p tw %d %d\n" % (relabelled.number_of_nodes(), relabelled.number_of_edges())
    )
    for edge in relabelled.edges():
        file.write(b"%d %d\n" % edge)
    return lambda x: relabelled.node[x]["old_id"]
