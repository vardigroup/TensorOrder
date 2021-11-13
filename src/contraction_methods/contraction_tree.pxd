
from tensor_network.tensor_network cimport TensorNetwork
from libcpp.set cimport set as cset
from libcpp.unordered_map cimport unordered_map
from libcpp.vector cimport vector
from libcpp cimport bool

cdef class CostInfo:
    cdef double FLOPs                                           # Total number of floating point operations needed
    cdef double total_memory                                    # Total memory cap needed to obtain tensor
    cdef double local_memory                                    # Memory needed to store tensor
    cdef int largest_tensor                                     # Rank of the largest encountered tensor
    cdef int best_edge                                          # Best bond index to slice to reduce memory cap
    cdef double best_edge_memory                                # Memory cap obtained after slicing best_edge

    cdef unordered_map[size_t, double] open_edge_total_memory   # Total memory cap after slicing each free index

cdef class ContractionTreeContext:
    cdef object nodes
    cdef int root

    cpdef int empty(self)
    cpdef int leaf(self, TensorNetwork tensor_network, int tensor_index) except -2
    cpdef int leaf_manual(self, int tensor_index, vector[int] free_edges) except -2

    cpdef int join(self, int left, int right) except -2
    cpdef int compute_join_properties(self, int node) except -2
    cpdef int include_rank_zero_tensors(self, TensorNetwork tensor_network, int contraction_tree) except -2
    cpdef int reindex(self, vector[int] new_tid_from_old, vector[int] new_eid_from_old) except -2
    cpdef int group_if_below(self, int upper, bool upper_left, bool lower_left, size_t if_below) except -2
    cpdef CostInfo estimate_cost(self, size_t node_id, cset[int] & sliced_edges)

