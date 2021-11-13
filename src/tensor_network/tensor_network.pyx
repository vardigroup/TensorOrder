# distutils: language=c++
# distutils: extra_compile_args=-O3

from itertools import combinations, product
from typing import Tuple, List, Iterator
import tensor_network.tensor
import contraction_methods.contraction_tree

from libcpp.vector cimport vector

cdef class TensorNetwork:
    def __init__(self, base=None):
        if base is not None:
            self.__nodes = list(base.__nodes)
            self.__edges = base.__edges
            self.__index_lists = base.__index_lists
            self.__disconnected_edge_id = base.__disconnected_edge_id
        else:
            self.__nodes = []
            self.__disconnected_edge_id = -1

    def copy(self):
        return TensorNetwork(self)

    @property
    def tensors(self) -> Iterator[tensor_network.tensor.Tensor]:
        return iter(self.__nodes)

    def tensor(self, tensor_id: int) -> tensor_network.tensor.Tensor:
        return self.__nodes[tensor_id]

    def __getitem__(self, tensor_id: int) -> tensor_network.tensor.Tensor:
        return self.__nodes[tensor_id]

    def __len__(self):
        return len(self.__nodes)

    def index_list(self, tensor_id: int) -> List[int]:
        return self.__index_lists[tensor_id]

    @property
    def edges(self):
        return iter(self.__edges)

    def edge(self, edge_index: int):
        return self.__edges[edge_index]

    def num_edges(self):
        return self.__edges.size()

    def connected(self, tensor_id: int, edge_id: int) -> bool:
        return self.__index_lists[tensor_id][edge_id] >= 0

    def connect(self, tensor1: int, edge1: int, tensor2: int, edge2: int) -> int:
        if tensor1 == tensor2:
            raise ValueError("Self loops are not allowed")
        if self.__index_lists[tensor1][edge1] >= 0:
            raise ValueError("Index of first tensor has already been assigned")
        if self.__index_lists[tensor2][edge2] >= 0:
            raise ValueError("Index of second tensor has already been assigned")

        edge_id = self.__edges.size()
        self.__index_lists[tensor1][edge1] = edge_id
        self.__index_lists[tensor2][edge2] = edge_id
        self.__edges.push_back(TensorNetworkEdge(edge_id, tensor1, tensor2))
        return edge_id

    def add_node(self, tensor: tensor_network.tensor.Tensor) -> List[Tuple[int, int]]:
        self.__nodes.append(tensor)
        self.__index_lists.push_back(vector[int]())
        cdef size_t rank = tensor.rank
        cdef size_t i
        for i in range(rank):
            self.__index_lists.back().push_back(self.__disconnected_edge_id - i)
        self.__disconnected_edge_id -= rank
        return [(len(self.__nodes) - 1, i) for i in range(rank)]

    def save_structure(self, file, include_rank_zero: bool = False):
        file.write(
            b"p tw %d %d\n" % (self.__index_lists.size(), self.__edges.size())
        )
        for edge in self.__edges:
            file.write(b"%d %d\n" % (edge.tensor1_id + 1, edge.tensor2_id + 1))

    def structure(self, include_rank_zero: bool = False, display: bool = True):
        import networkx as nx

        result = nx.MultiGraph()
        for index, node in enumerate(self.__nodes):
            if not include_rank_zero and node.rank == 0:
                continue
            result.add_node(index, **(node.display if display else {}))

        for edge in self.__edges:
            result.add_edge(edge.tensor1_id, edge.tensor2_id, label=edge.id)
        return result

    def save_line_structure(self, file):
        cdef int num_line_edges = 0
        for connections in self.__index_lists:
            num_line_edges += (connections.size() * (connections.size() - 1)) // 2
        file.write(
            b"p tw %d %d\n" % (self.__edges.size(), num_line_edges)
        )
        for node_id in range(self.__index_lists.size()):
            for i in range(self.__index_lists[node_id].size()):
                for j in range(i+1, self.__index_lists[node_id].size()):
                    file.write(b"%d %d\n" % (self.__index_lists[node_id][i]+1, self.__index_lists[node_id][j]+1))

    def line_structure(self):
        import networkx as nx
        result = nx.Graph()

        for node_id, connections in enumerate(self.__index_lists):
            result.add_edges_from(combinations(connections, 2), label=node_id)

        return result

    def draw(self, *args, **kwargs):
        return draw_graph(self.structure(*args, **kwargs))

    def draw_line(self):
        return draw_graph(self.line_structure())

    # Return the value of the contracted network using einsum
    def contract_einsum(self, tensor_api):
        import numpy as np

        tensors = [node.build(tensor_api.create_tensor) for node in self.__nodes]
        index_lists = self.__index_lists
        all_dimensions = list(set.union(*map(set, index_lists)))

        if len(all_dimensions) > 26:
            raise ValueError("Unable to use einsum: more than 26 dimensions")

        labels = {dim: chr(ord("a") + i) for i, dim in enumerate(all_dimensions)}
        operands = ",".join(
            ["".join([labels[i] for i in dim_list]) for dim_list in index_lists]
        )
        return np.einsum(operands, *tensors)

    def identify(self, contraction_tree, tensor_api):
        stack = []
        for node in contraction_tree.iterate_postorder():
            if node.is_leaf:
                stack.append(
                    self.__nodes[node.tensor_index].build(tensor_api.create_tensor)
                )
            else:
                right_tensor = stack.pop()
                left_tensor = stack.pop()
                contraction_result = tensor_api.tensordot(
                    left_tensor, right_tensor, (node.left_edge_map, node.right_edge_map)
                )
                stack.append(contraction_result)
        return stack[0]

    def contract_pair(self, left_index, left_edge_map, right_index, right_edge_map, free_edges, tensor_api):
        left = self.__nodes[left_index].build(tensor_api.create_tensor)
        right = self.__nodes[right_index].build(tensor_api.create_tensor)
        result = tensor_api.tensordot(left, right, (left_edge_map, right_edge_map))
        result_connections = self.add_node(tensor_network.tensor.BuiltTensor(result))
        cdef result_index = len(self.__nodes) - 1

        # Correct the edges incident to the new node
        cdef size_t i, e
        cdef size_t rank = len(free_edges)
        for i in range(rank):
            e = free_edges[i]
            self.__index_lists[result_index][i] = e
            if self.__edges[e].tensor1_id == left_index or self.__edges[e].tensor1_id == right_index:
                self.__edges[e].tensor1_id = result_index
            elif self.__edges[e].tensor2_id == left_index or self.__edges[e].tensor2_id == right_index:
                self.__edges[e].tensor2_id = result_index

        left = self.__nodes[left_index] = None
        right = self.__nodes[right_index] = None
        return result_index

    def identify_partial(self, contraction_tree, tensor_api, contract_below):
        stack = []

        result_tree_context = contraction_methods.contraction_tree.ContractionTreeContext()

        for node in contraction_tree.iterate_postorder():
            if node.is_leaf:
                stack.append((True, node.tensor_index))
            else:
                right_created, right = stack.pop()
                left_created, left = stack.pop()
                if left_created and right_created and len(node.free_edges) < contract_below:
                    contraction_result = self.contract_pair(
                        left, node.left_edge_map, right, node.right_edge_map, node.free_edges, tensor_api
                    )
                    stack.append((True, contraction_result))
                else:
                    if left_created:
                        # virtualize left
                        left = result_tree_context.leaf(self, left)
                    if right_created:
                        # virtualize right
                        right = result_tree_context.leaf(self, right)
                    stack.append((False, result_tree_context.join(left, right)))

        top_created, top = stack.pop()
        if top_created:
            # virtualize top
            top = result_tree_context.leaf(self, top)

        # Remove tensors that have already been used
        cdef vector[int] new_tid_from_old
        cdef size_t current_tensor, fixed_tensor = 0
        for current_tensor in range(<size_t>len(self.__nodes)):
            if self.__nodes[current_tensor] is not None:
                self.__nodes[fixed_tensor] = self.__nodes[current_tensor]
                self.__index_lists[fixed_tensor] = self.__index_lists[current_tensor]
                new_tid_from_old.push_back(fixed_tensor)
                fixed_tensor += 1
            else:
                new_tid_from_old.push_back(-1)
        self.__nodes = self.__nodes[:fixed_tensor]
        self.__index_lists.resize(fixed_tensor)

        # Remove edges that were contracted away
        cdef vector[int] new_eid_from_old
        cdef size_t current_edge, fixed_edge = 0
        for current_edge in range(self.__edges.size()):
            if new_tid_from_old[self.__edges[current_edge].tensor1_id] >= 0 and new_tid_from_old[self.__edges[current_edge].tensor1_id] >= 0:
                # Both edges of the tensor still exist; correct the tensor ids
                self.__edges[fixed_edge].tensor1_id = new_tid_from_old[self.__edges[current_edge].tensor1_id]
                self.__edges[fixed_edge].tensor2_id = new_tid_from_old[self.__edges[current_edge].tensor2_id]
                new_eid_from_old.push_back(fixed_edge)
                fixed_edge += 1
            else:
                new_eid_from_old.push_back(-2)
        self.__edges.resize(fixed_edge)
        cdef size_t t_id, index
        for t_id in range(fixed_tensor):
            for index in range(self.__index_lists[t_id].size()):
                self.__index_lists[t_id][index] = new_eid_from_old[self.__index_lists[t_id][index]]

        # Update the contraction tree
        result_tree_context.reindex(new_tid_from_old, new_eid_from_old)
        return result_tree_context.get_tree(top), new_eid_from_old

    """
    def identify_partial(self, contraction_tree, tensor_api, contract_below):
        stack = []

        result_network = TensorNetwork()
        result_tree_context = contraction_methods.contraction_tree.ContractionTreeContext()

        for node in contraction_tree.iterate_postorder():
            if node.is_leaf:
                stack.append(
                    (True, self.__nodes[node.tensor_index].build(tensor_api.create_tensor))
                )
            else:
                right_created, right = stack.pop()
                left_created, left = stack.pop()
                if left_created and right_created \
                    and left.rank < contract_below \
                    and right.rank < contract_below \
                    and len(node.free_edges) < contract_below:

                    contraction_result = tensor_api.tensordot(
                        left, right, (node.left_edge_map, node.right_edge_map)
                    )
                    stack.append((True, contraction_result))
                else:
                    if left_created:
                        # virtualize left
                        pass
                    if right_created:
                        # virtualize right
                        pass
                    stack.append((False, result_tree_context.join(left, right)))
        return result_network, result_tree_context
    """

    cdef FactorResult factor_out(self, size_t tensor_index, size_t dim1, size_t dim2):
        cdef size_t rank = self.__index_lists[tensor_index].size()
        if rank <= <size_t>2:
            raise ValueError("Unable to factor rank 2 or smaller tensor")

        if rank == <size_t>3:
            return FactorResult(
                tensor_index,
                self.__index_lists[tensor_index][3 - dim1 - dim2]
            )

        right_indices = [
            j
            for j in range(rank)
            if j != dim1 and j != dim2
        ]
        left, right = self.__nodes[tensor_index].get_factor_components(
            [dim1, dim2], right_indices
        )
        new_tensor_index = self.__index_lists.size()
        self.__nodes.append(left)
        self.__nodes[tensor_index] = right

        self.__index_lists.push_back(vector[int]())
        self.__index_lists.back().push_back(self.__index_lists[tensor_index][dim1])
        self.__index_lists.back().push_back(self.__index_lists[tensor_index][dim2])
        self.__index_lists[tensor_index].clear()
        for j in range(rank):
            if j != dim1 and j != dim2:
                self.__index_lists[tensor_index].push_back(self.__index_lists[tensor_index][j])

        for edge_id in self.__index_lists[new_tensor_index]:
            if edge_id >= 0:
                if self.__edges[edge_id].tensor1_id == tensor_index:
                    self.__edges[edge_id].tensor1_id = new_tensor_index
                else:
                    self.__edges[edge_id].tensor2_id = new_tensor_index

        # Add an edge between the two last indices of the left and right tensors
        edge_id = self.__edges.size()
        self.__index_lists[tensor_index].push_back(edge_id)
        self.__index_lists[new_tensor_index].push_back(edge_id)
        self.__edges.push_back(TensorNetworkEdge(edge_id, tensor_index, new_tensor_index))

        return FactorResult(new_tensor_index, edge_id)

    def slice(self, edges):
        if len(edges) == 0:
            yield self
            return

        index_values = []
        tensor1_infos = []
        tensor2_infos = []
        cdef size_t e, t1_id, t2_id, i
        for e in edges:
            t1_id = self.__edges[e].tensor1_id
            t2_id = self.__edges[e].tensor2_id
            found = False

            for i in range(self.__index_lists[t1_id].size()):
                if self.__index_lists[t1_id][i] == <int>e:
                    tensor1_infos.append((t1_id, i))
                    found = True
                    break
            for i in range(self.__index_lists[t2_id].size()):
                if self.__index_lists[t2_id][i] == <int>e:
                    tensor2_infos.append((t2_id, i))
                    break
            if not found:
                raise RuntimeError('Unable to determine size of edge ' + str(e))

            index_values.append(list(range(self.__nodes[t1_id].shape[tensor1_infos[-1][-1]])))

        for assignment in product(*index_values):
            tn_slice = self.copy()
            for t1, t2, value in zip(tensor1_infos, tensor2_infos, assignment):
                tn_slice.__nodes[t1[0]] = tn_slice.__nodes[t1[0]].get_slice(t1[1], value)
                tn_slice.__nodes[t2[0]] = tn_slice.__nodes[t2[0]].get_slice(t2[1], value)
            yield tn_slice


    def slice_groups(self, edge_groups):
        if len(edge_groups) == 0:
            yield self
            return

        index_values = []
        tensor_infos = []
        cdef size_t e, t1_id, t2_id, i
        for group in edge_groups:
            if len(group) == 0:
                continue

            tensor_infos.append([])
            for e in group:
                t1_id = self.__edges[e].tensor1_id
                t2_id = self.__edges[e].tensor2_id
                found = False

                for i in range(self.__index_lists[t1_id].size()):
                    if self.__index_lists[t1_id][i] == <int>e:
                        tensor_infos[-1].append((t1_id, i))
                        found = True
                        break
                for i in range(self.__index_lists[t2_id].size()):
                    if self.__index_lists[t2_id][i] == <int>e:
                        tensor_infos[-1].append((t2_id, i))
                        break
                if not found:
                    raise RuntimeError('Unable to determine size of edge ' + str(e))
            # Note t2_id falls through from the above loop
            info = tensor_infos[-1][-1]
            index_values.append(list(range(self.__nodes[info[0]].shape[info[1]])))

        for assignment in product(*index_values):
            tn_slice = self.copy()
            for group, value in zip(tensor_infos, assignment):
                for info in group:
                    tn_slice.__nodes[info[0]] = tn_slice.__nodes[info[0]].get_slice(info[1], value)
            yield tn_slice


    def get_tensor_slices(self, edge_groups, tensor_factory):
        if len(edge_groups) == 0:
            # Return a slice generator for each tensor that does no slicing
            return 1, [tensor_network.tensor.SliceSequence(t.build(tensor_factory), ([],), {}) for t in self.__nodes], [[]]

        index_values = []
        tensor_slice_lookup = [{} for tensor_id in range(len(self.__nodes))]
        cdef size_t e, t1_id, t2_id, i, size=0, which_assignment_index=0
        total_slice_count = 1
        for group in edge_groups:
            if len(group) == 0:
                continue

            for e in group:
                t1_id = self.__edges[e].tensor1_id
                t2_id = self.__edges[e].tensor2_id
                found = False

                for i in range(self.__index_lists[t1_id].size()):
                    if self.__index_lists[t1_id][i] == <int>e:
                        tensor_slice_lookup[t1_id][i] = which_assignment_index
                        size = self.__nodes[t1_id].shape[i]
                        found = True
                        break
                for i in range(self.__index_lists[t2_id].size()):
                    if self.__index_lists[t2_id][i] == <int>e:
                        tensor_slice_lookup[t2_id][i] = which_assignment_index
                        break
                if not found:
                    raise RuntimeError('Unable to determine size of edge ' + str(e))
            # Note t2_id and i fall through from the above loop
            index_values.append(list(range(size)))
            total_slice_count *= size
            which_assignment_index += 1

        return total_slice_count, [
            tensor_network.tensor.SliceSequence(t.build(tensor_factory), index_values, lookup)
                for t, lookup in zip(self.__nodes, tensor_slice_lookup)
        ], product(*index_values)

    def remove_sliced_indices_from(self, contraction_tree, edge_groups):
        result_tree_context = contraction_methods.contraction_tree.ContractionTreeContext()
        cdef vector[size_t] is_edge_sliced
        cdef TensorNetworkEdge i
        cdef int edge_id
        for i in self.__edges:
            is_edge_sliced.push_back(0)
        for group in edge_groups:
            for edge_id in group:
                is_edge_sliced[edge_id] = 1

        stack = []
        cdef vector[int] free_edges
        for node in contraction_tree.iterate_postorder():
            if node.is_leaf:
                free_edges.clear()
                for edge_id in self.__index_lists[node.tensor_index]:
                    if edge_id >= 0 and is_edge_sliced[edge_id] == 0:
                        free_edges.push_back(edge_id)
                stack.append(result_tree_context.leaf_manual(node.tensor_index, free_edges))
            else:
                right = stack.pop()
                left = stack.pop()
                stack.append(result_tree_context.join(left, right))
        return result_tree_context.get_tree(stack.pop())

    def find_equivalent_edges(self, edge):
        to_process = [edge]
        seen = {edge}

        cdef size_t other_e, t1, t2
        while len(to_process) > 0:
            e = to_process.pop()
            t1 = self.__edges[e].tensor1_id
            t2 = self.__edges[e].tensor2_id
            if self.__nodes[t1].diagonal:
                for other_e in self.__index_lists[t1]:
                    if other_e not in seen:
                        to_process.append(other_e)
                        seen.add(other_e)
            if self.__nodes[t2].diagonal:
                for other_e in self.__index_lists[t2]:
                    if other_e not in seen:
                        to_process.append(other_e)
                        seen.add(other_e)
        return seen

    def equivalent_edge_sets(self):
        """
        For each edge, find a representative equivalent edge.

        :return: A dictionary D such that, for each edge e, D[e] is equivalent to e.
        """
        equivalent_edges = {}
        for e in range(self.num_edges()):
            if e not in equivalent_edges:
                for f in self.find_equivalent_edges(e):
                    equivalent_edges[f] = e
        return equivalent_edges


def draw_graph(networkx_graph):
    import networkx as nx
    from IPython.display import Image

    # convert from networkx -> pydot
    pydot_graph = nx.nx_pydot.to_pydot(networkx_graph)

    # render pydot by calling dot, no file saved to disk
    png_str = pydot_graph.create_png(prog="dot")
    return Image(png_str)
