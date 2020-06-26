from libcpp.vector cimport vector
from libcpp.unordered_map cimport unordered_map

cdef class BranchDecomposition:
    cdef vector[vector[int]] neighbors
    cdef unordered_map[int, int] node_to_edge
    cdef size_t __width

    cdef void add_edge(self, int src, int dst)
    cdef int add_node(self)
    cdef int extend_leaf(self, int node)

