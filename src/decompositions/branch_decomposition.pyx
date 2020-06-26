# distutils: language=c++
# distutils: extra_compile_args=-O3

import util
import time

from libcpp.vector cimport vector

cdef class BranchDecomposition:
    """
    A class used to represent a branch decomposition
    """

    cdef void add_edge(self, int src, int dst):
        """
        Add an edge between src and dst
        """
        self.neighbors[src].push_back(dst)
        self.neighbors[dst].push_back(src)

    def width(self):
        """
        Compute the branchwidth of this branch decomposition.
        :return: The branchwidth of this branch decomposition.
        """
        return self.__width

    cdef int add_node(self):
        self.neighbors.push_back(vector[int]())
        return self.neighbors.size() - 1

    cdef int extend_leaf(self, int node):
        """
        Add a new leaf node adjacent to [node].
        The degree of [node] and the degree of its previous neighbors will not change.
        :param node: The node to add a leaf to.
        :return: The id of the new leaf node.
        """
        cdef int new_leaf
        cdef int new_internal
        cdef size_t i

        new_leaf = self.add_node()
        if new_leaf == 1:
            self.neighbors[node].push_back(new_leaf)
            self.neighbors[new_leaf].push_back(node)
            return new_leaf

        # Add a new internal node and attach the leaf
        neighbor = self.neighbors[node][0]
        new_internal = self.add_node()
        self.neighbors[node][0] = new_internal
        self.neighbors[new_internal].push_back(node)
        self.neighbors[new_internal].push_back(neighbor)
        for i in range(self.neighbors[neighbor].size()):
            if self.neighbors[neighbor][i] == node:
                self.neighbors[neighbor][i] = new_internal
                break
        self.add_edge(new_internal, new_leaf)
        return new_leaf

    @staticmethod
    def parse(stream, separator="=", header=None):
        """
        Parse a single BranchDecomposition from a .bd filestream.

        :param stream: Stream to parse
        :param separator: Character separator to indicate the end of a branch decomposition
        :param header: Header previously parsed from a stream, if provided
        :return: The parsed BranchDecomposition
        """

        def record(comment):
            util.log(comment.rstrip(), flush=True)

        dimacs = util.DimacsStream(stream, process_comment=record)

        if header is None:
            header = dimacs.parse_line("s")
            if header is None:
                return None
        num_bags, num_nodes, branch_width, _ = int(header[2]), int(header[3]), int(header[4]), int(header[5])
        util.log("Read header at " + str(time.time()))

        cdef size_t i
        result = BranchDecomposition()
        result.neighbors.reserve(num_nodes)
        result.node_to_edge.reserve(num_bags)
        result.__width = branch_width
        for i in range(<size_t>num_nodes):
            result.neighbors.push_back(vector[int]())

        bags = []
        for _ in range(num_bags):
            bag = dimacs.parse_line("b")
            if bag is None:
                raise RuntimeError("EOF reached while reading bags")
            if len(bag) != 3:
                raise RuntimeError("Unable to determine edge on node")
            result.node_to_edge[int(bag[1])-1] = int(bag[2]) - 1

        numbers = frozenset("0123456789" + separator)
        while True:
            edge = dimacs.parse_line(numbers)
            # Allow EOF or '=' to end the tree-decomposition
            if edge is None or edge[0] == separator:
                break
            result.add_edge(int(edge[0]) - 1, int(edge[1]) - 1)

        return result
