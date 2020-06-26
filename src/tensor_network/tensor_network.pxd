from libcpp.vector cimport vector

cdef struct TensorNetworkEdge:
    int id
    size_t tensor1_id
    size_t tensor2_id

cdef struct FactorResult:
    size_t new_tensor_id
    size_t intermediate_edge_id

cdef class TensorNetwork:
    cdef public object __nodes
    cdef public vector[TensorNetworkEdge] __edges
    cdef public vector[vector[int]] __index_lists
    cdef public int __disconnected_edge_id

    cdef FactorResult factor_out(self, size_t tensor_index, size_t dim1, size_t dim2)
