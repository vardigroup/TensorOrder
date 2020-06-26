# distutils: language=c++
# distutils: extra_compile_args=-O3

import util
import time

from libcpp.vector cimport vector

cdef class TreeDecomposition:
    """
    A class used to represent a tree decomposition
    """

    cdef void add_edge(self, int src, int dst):
        """
        Add an edge between src and dst
        """
        self.neighbors[src].push_back(dst)
        self.neighbors[dst].push_back(src)

    @property
    def bags(self):
        return self.bags

    cdef int add_node(self, vector[int] bag):
        self.bags.push_back(bag)
        self.neighbors.push_back(vector[int]())
        return self.neighbors.size() - 1

    cdef int extend_leaf(self, int node):
        """
        Add a new leaf node adjacent to [node].
        The degree of [node] and the degree of its previous neighbors will not change,
        unless the decomposition has exactly one node.
        
        :param node: The node to add a leaf to.
        :return: The id of the new leaf node.
        """
        cdef int new_leaf
        cdef int new_internal
        cdef size_t i

        new_leaf = self.add_node(self.bags[node])
        if new_leaf == 1:
            self.neighbors[node].push_back(new_leaf)
            self.neighbors[new_leaf].push_back(node)
            return new_leaf

        # Add a new internal node and attach the leaf
        neighbor = self.neighbors[node][0]
        new_internal = self.add_node(self.bags[node])
        self.neighbors[node][0] = new_internal
        self.neighbors[new_internal].push_back(node)
        self.neighbors[new_internal].push_back(neighbor)
        for i in range(self.neighbors[neighbor].size()):
            if self.neighbors[neighbor][i] == node:
                self.neighbors[neighbor][i] = new_internal
                break
        self.add_edge(new_internal, new_leaf)
        return new_leaf

    cdef void split_high_degree_nodes(self):
        """
        Adjust the tree-decomposition so that no node has degree more than 3.
        :return: None
        """

        cdef int neighbor_1
        cdef int neighbor_2
        cdef size_t i
        cdef size_t j

        for i in range(self.neighbors.size()):
            while self.neighbors[i].size() > <size_t>3:
                neighbor_1 = self.neighbors[i].back()
                self.neighbors[i].pop_back()

                neighbor_2 = self.neighbors[i].back()
                self.neighbors[i].pop_back()

                new_internal = self.add_node(self.bags[i])
                self.neighbors[i].push_back(new_internal)
                self.neighbors[new_internal].push_back(i)
                self.neighbors[new_internal].push_back(neighbor_1)
                self.neighbors[new_internal].push_back(neighbor_2)

                for j in range(self.neighbors[neighbor_1].size()):
                    if self.neighbors[neighbor_1][j] == <int>i:
                        self.neighbors[neighbor_1][j] = new_internal
                        break
                for j in range(self.neighbors[neighbor_2].size()):
                    if self.neighbors[neighbor_2][j] == <int>i:
                        self.neighbors[neighbor_2][j] = new_internal
                        break

    def traverse_postorder(self, root, func, *args):
        """
        Recursively process all nodes of this decomposition in postorder style. That is, for each
        node with children {child1, child2, ... childN}, recursively compute:
            result(node) = func(node, [result(child1), result(child2), ..., result(childN)], *args).
        Note that this function does not actually use recursion in order to handle deep trees.
        :param root: The node to begin the recursive computation
        :param func: The function to apply at each node
        :param args: Other arguments to pass to the function
        :return: result(root)
        """
        results = {}
        processed = [(root, None, False)]
        while len(processed) > 0:
            node, parent, expanded = processed.pop()
            base_list = []
            if node != root and len(self.neighbors[node]) == 1:
                results[node] = func(node, base_list, *args)
            elif expanded:
                for n in self.neighbors[node]:
                    if n != parent:
                        base_list.append(results[n])
                results[node] = func(node, base_list, *args)
                for n in self.neighbors[node]:
                    if n != parent:
                        del results[n]
            else:
                processed.append((node, parent, True))
                for child in self.neighbors[node]:
                    if child != parent:
                        processed.append((child, node, False))
        return results[root]

    def width(self):
        """
        Compute the treewidth of this tree decomposition.
        :return: The treewidth of this tree decomposition.
        """
        cdef size_t max_size = 0

        for bag in self.bags:
            max_size = max(max_size, bag.size())
        return max_size - 1

    @staticmethod
    def parse(stream, separator="=", header=None):
        """
        Parse a single TreeDecomposition from a .td filestream.

        :param stream: Stream to parse
        :param separator: Character separator to indicate the end of a tree decomposition
        :param header: Header previously parsed from a stream, if provided
        :return: The parsed TreeDecomposition
        """

        def record(comment):
            util.log(comment.rstrip(), flush=True)

        dimacs = util.DimacsStream(stream, process_comment=record)

        if header is None:
            header = dimacs.parse_line("s")
            if header is None:
                return None
        numbags, bag_size, _ = int(header[2]), int(header[3]), int(header[4])
        util.log("Read header at " + str(time.time()), flush=True)

        cdef size_t num_nodes = numbags
        cdef size_t i
        result = TreeDecomposition()
        result.neighbors.reserve(num_nodes)
        result.bags.reserve(num_nodes)
        for i in range(num_nodes):
            result.neighbors.push_back(vector[int]())
            result.bags.push_back(vector[int]())

        bags = []
        for _ in range(numbags):
            bag = dimacs.parse_line("b")
            if bag is None:
                raise RuntimeError("EOF reached while reading bags")
            node = int(bag[1]) - 1
            if len(bag) - 2 > bag_size:
                raise RuntimeError("Bag larger than identified width")
            if node < 0 or node >= num_nodes:
                continue  # Invalid node id
            for b in bag[2:]:
                result.bags[node].push_back(int(b)-1)

        numbers = frozenset("0123456789" + separator)
        while True:
            edge = dimacs.parse_line(numbers)
            # Allow EOF or '=' to end the tree-decomposition
            if edge is None or edge[0] == separator:
                break
            result.add_edge(int(edge[0]) - 1, int(edge[1]) - 1)

        return result
