from libcpp.vector cimport vector

cdef class TreeDecomposition:
    cdef vector[vector[int]] neighbors
    cdef vector[vector[int]] bags

    cdef void add_edge(self, int src, int dst)
    cdef int add_node(self, vector[int] bag)
    cdef int extend_leaf(self, int node)
    cdef void split_high_degree_nodes(self)
