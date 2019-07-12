from networkx import Graph, is_tree, get_node_attributes
import random
from typing import FrozenSet

import util


class TreeDecomposition(Graph):
    def write(self, file):
        bag_size = max(len(bag) for bag in get_node_attributes(self, "bag").values())
        num_nodes = max(max(bag) for bag in get_node_attributes(self, "bag").values())

        with open(file, "w") as f:
            f.write("s td %d %d %d\n" % (self.number_of_nodes(), bag_size, num_nodes))
            for node in self.nodes():
                f.write(
                    "b %d %s\n" % (node, " ".join(map(str, self.node[node]["bag"])))
                )
            for edge in self.edges():
                f.write("%d %d\n" % edge)

    def traverse_postorder(self, root, func):
        results = {}
        processed = [(root, None, False)]
        while len(processed) > 0:
            node, parent, expanded = processed.pop()
            if node != root and self.degree(node) == 1:
                results[node] = func(node, [])
            elif expanded:
                results[node] = func(
                    node, [results[n] for n in self.neighbors(node) if n != parent]
                )
                for n in self.neighbors(node):
                    if n != parent:
                        del results[n]
            else:
                processed.append((node, parent, True))
                for child in self.neighbors(node):
                    if child != parent:
                        processed.append((child, node, False))
        return results[root]

    def extend_leaf(self, node: int, bag: FrozenSet[int] = None):
        if bag is None:
            bag = self.node[node]["bag"]
        else:
            assert bag.issubset(self.node[node]["bag"])

        new_leaf = len(self.nodes) + 1
        self.add_node(new_leaf, bag=bag)

        # Add a new internal node and attach the leaf
        if self.degree(node) == 0:
            self.add_edge(node, new_leaf)
        else:
            neighbor = next(self.neighbors(node))
            new_internal = len(self.nodes) + 1

            self.add_node(new_internal, bag=self.nodes[node]["bag"])
            self.remove_edge(node, neighbor)
            self.add_edge(new_internal, node)
            self.add_edge(new_internal, neighbor)
            self.add_edge(new_internal, new_leaf)
        return new_leaf

    def split_high_degree_nodes(self):
        # Adjust the tree-decomposition so that no node has degree more than 3
        for node in list(self.nodes):
            while self.degree(node) > 3:
                neighbors = random.sample(list(self.neighbors(node)), 2)
                self.remove_edge(node, neighbors[0])
                self.remove_edge(node, neighbors[1])
                new_internal = len(self.nodes) + 1
                self.add_node(new_internal, bag=self.nodes[node]["bag"])
                self.add_edge(new_internal, node)
                self.add_edge(new_internal, neighbors[0])
                self.add_edge(new_internal, neighbors[1])

    @staticmethod
    def parse_one(stream, renumber_bag_components=lambda x: x):
        result = TreeDecomposition()

        header = read_line(stream, "s", log_comments=True)
        if header is None:
            return None
        num_bags, bag_size, _ = int(header[2]), int(header[3]), int(header[4])
        for _ in range(num_bags):
            bag = read_line(stream, "b", log_comments=True)
            bag_contents = frozenset(renumber_bag_components(int(b)) for b in bag[2:])
            if len(bag_contents) > bag_size:
                raise RuntimeError("Bag too big")
            result.add_node(int(bag[1]), bag=bag_contents)

        numbers = frozenset("0123456789=")
        while True:
            edge = read_line(stream, allowed_prefixes=numbers, log_comments=True)
            if (
                edge is None or edge[0] == "="
            ):  # Allow EOF or '=' to end the tree-decomposition
                break
            result.add_edge(int(edge[0]), int(edge[1]))

        return result

    @staticmethod
    def parse(file, renumber_bag_components=lambda x: x):
        result = TreeDecomposition()

        num_bags = None
        bag_size = None
        num_nodes = None

        with open(file, "r") as f:
            for line in f:
                parts = line.split()
                if len(parts) < 2 or parts[0] == "c":
                    util.log(line.rstrip())
                    continue
                elif parts[0] == "s":
                    if len(parts) != 5:
                        raise RuntimeError(
                            "Unable to parse %s: Incorrect header %s" % (file, line)
                        )
                    num_bags = int(parts[2])
                    bag_size = int(parts[3])
                    num_nodes = int(parts[4])
                elif parts[0] == "b":
                    if len(parts) <= 2:
                        raise RuntimeError("Unable to parse %s: Empty Bag" % (file,))

                    bag = frozenset(map(int, parts[2:]))
                    if len(bag) > bag_size:
                        raise RuntimeError(
                            "Unable to parse %s: Max bag size %d but bag was %s"
                            % (file, bag_size, bag)
                        )
                    for i in bag:
                        if i < 0 or i > num_nodes:
                            raise RuntimeError(
                                "Unable to parse %s: Unknown node %d" % (file, i)
                            )
                    result.add_node(
                        int(parts[1]), bag=frozenset(map(renumber_bag_components, bag))
                    )
                else:
                    if len(parts) != 2:
                        raise RuntimeError(
                            "Unable to parse %s: Invalid line %s" % (file, line)
                        )
                    result.add_edge(int(parts[0]), int(parts[1]))

        if num_bags is None:
            raise RuntimeError("Unable to parse %s: No header" % (file,))
        if result.number_of_nodes() != num_bags:
            raise RuntimeError(
                "Unable to parse %s: Expected %d bags but had %d"
                % (file, num_bags, result.number_of_nodes())
            )
        if not is_tree(result):
            raise RuntimeError(
                "Unable to parse %s: Decomposition is not a tree" % (file,)
            )
        return result

    def width(self):
        return max(len(bag) for bag in get_node_attributes(self, "bag").values()) - 1


def read_line(stream, allowed_prefixes=None, comment_prefix="c", log_comments=False):
    for line in stream:
        parts = line.split()
        if len(parts) < 1 or parts[0][0] == comment_prefix:
            if log_comments:
                util.log(line.rstrip(), flush=True)
            continue
        elif allowed_prefixes is None or parts[0][0] in allowed_prefixes:
            return parts
        else:
            raise RuntimeError("Unexpected line prefix in: {0}".format(line))
