import networkx as nx
from itertools import product, combinations
from typing import Tuple, List, NamedTuple, FrozenSet, Iterator


class Tensor:
    def __init__(self, value, **display_args):
        self._value = value
        self.__display_args = display_args

    @property
    def shape(self):
        return self._value.shape

    @property
    def rank(self):
        return len(self.shape)

    @property
    def display(self):
        return self.__display_args

    @property
    def value(self):
        return self._value

    def get_factor_components(self, left_indices, right_indices):
        raise NotImplementedError()

    def __getitem__(self, key):
        return self.value.__getitem__(key)

    def __setitem__(self, key, value):
        return self.value.__setitem__(key, value)

    # A simple method to generate a tensor according to a lambda rule.
    @staticmethod
    def generate(shape, rule, tensor_factory, **display_args):
        tensor = Tensor(tensor_factory(shape, None), **display_args)
        for tup in product(*map(range, shape)):
            tensor[tup] = rule(*tup)
        return tensor


class TensorNetworkEdge(NamedTuple):
    id: int
    tensors: FrozenSet[int]


class TensorNetwork:
    __nodes: List[Tensor]
    __edges: List[TensorNetworkEdge]
    __index_lists: List[List[int]]

    def __init__(self, base=None):
        if base is not None:
            self.__nodes = list(base.__nodes)
            self.__edges = list(base.__edges)
            self.__index_lists = list(base.__index_lists)
        else:
            self.__nodes = []
            self.__index_lists = []
            self.__edges = []

    def copy(self):
        return TensorNetwork(self)

    @property
    def tensors(self) -> Iterator[Tensor]:
        return iter(self.__nodes)

    def tensor(self, tensor_id: int) -> Tensor:
        return self.__nodes[tensor_id]

    def __getitem__(self, tensor_id: int) -> Tensor:
        return self.__nodes[tensor_id]

    def __len__(self):
        return len(self.__nodes)

    def index_list(self, tensor_id: int) -> List[int]:
        return list(self.__index_lists[tensor_id])

    @property
    def edges(self) -> Iterator[TensorNetworkEdge]:
        return iter(self.__edges)

    def edge(self, edge_index: int) -> TensorNetworkEdge:
        return self.__edges[edge_index]

    def add_node(self, tensor: Tensor):
        self.__nodes.append(tensor)
        self.__index_lists.append([None] * tensor.rank)

        def connected(tensor_id, edge_id):
            return self.__index_lists[tensor_id][edge_id] is not None

        def connect(tensor1, edge1, tensor2, edge2):
            if tensor1 == tensor2:
                raise ValueError("Self loops are not allowed")
            if connected(tensor1, edge1):
                raise ValueError("Index of first tensor has already been assigned")
            if connected(tensor2, edge2):
                raise ValueError("Index of second tensor has already been assigned")

            edge_id = len(self.__edges)
            self.__index_lists[tensor1][edge1] = edge_id
            self.__index_lists[tensor2][edge2] = edge_id
            self.__edges.append(
                TensorNetworkEdge(edge_id, frozenset((tensor1, tensor2)))
            )
            return edge_id

        class LocalTensorConnection:
            def __init__(self, parent_network, my_tensor, my_edge):
                self.__parent_network = parent_network
                self.__tensor_index = my_tensor
                self.__index = my_edge

            @property
            def network(self):
                return self.__parent_network

            def connected(self):
                return connected(self.__tensor_index, self.__index)

            def connect(self, other):
                if self.network != other.network:
                    raise ValueError("These connections lie in different networks")
                return connect(
                    self.__tensor_index,
                    self.__index,
                    other.__tensor_index,
                    other.__index,
                )

        return [
            LocalTensorConnection(self, len(self.__nodes) - 1, i)
            for i in range(tensor.rank)
        ]

    def structure(self, display: bool = True):
        result = nx.MultiGraph()
        for index, node in enumerate(self.__nodes):
            result.add_node(index, **(node.display if display else {}))

        for edge in self.__edges:
            result.add_edge(*edge.tensors, label=edge.id)
        return result

    def line_structure(self):
        result = nx.Graph()

        for node_id, connections in enumerate(self.__index_lists):
            result.add_edges_from(combinations(connections, 2), label=node_id)

        return result

    def draw(self, *args, **kwargs):
        return draw_graph(self.structure(*args, **kwargs))

    def draw_line(self):
        return draw_graph(self.line_structure())

    # Return the value of the contracted network using einsum
    def contract_einsum(self):
        import numpy as np

        tensors = [node.value for node in self.__nodes]
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
            if node.is_leaf():
                stack.append(self.__nodes[node.tensor_index])
            else:
                right_tensor = stack.pop()
                left_tensor = stack.pop()

                left_edges = node.left.free_edges
                right_edges = node.right.free_edges

                shared_edges = [
                    e for e in left_edges if e is not None and e in right_edges
                ]

                contraction_result = tensor_api.tensordot(
                    left_tensor.value,
                    right_tensor.value,
                    (
                        [left_edges.index(e) for e in shared_edges],
                        [right_edges.index(e) for e in shared_edges],
                    ),
                )
                stack.append(Tensor(contraction_result, label=""))
        return stack[0]

    def factor_out(
        self, tensor_index: int, dimension_indices: List[int]
    ) -> Tuple[int, int]:
        if self.__nodes[tensor_index].rank <= 2:
            raise ValueError("Unable to factor rank 2 or smaller tensor")
        if len(dimension_indices) <= 1:
            raise ValueError("Not enough indices")
        if len(dimension_indices) >= self.__nodes[tensor_index].rank:
            raise ValueError("Too many indices")

        if self.__nodes[tensor_index].rank == 3:
            return (
                tensor_index,
                next(
                    self.__index_lists[tensor_index][i]
                    for i in range(3)
                    if i not in dimension_indices
                ),
            )

        right_indices = [
            j
            for j in range(self.__nodes[tensor_index].rank)
            if j not in dimension_indices
        ]
        left, right = self.__nodes[tensor_index].get_factor_components(
            dimension_indices, right_indices
        )

        new_tensor_index = len(self.__index_lists)
        self.__nodes.append(left)
        self.__nodes[tensor_index] = right

        self.__index_lists.append(
            [self.__index_lists[tensor_index][j] for j in dimension_indices]
        )
        self.__index_lists[tensor_index] = [
            self.__index_lists[tensor_index][j] for j in right_indices
        ]
        for edge_id in self.__index_lists[new_tensor_index]:
            if edge_id is not None:
                self.__edges[edge_id] = TensorNetworkEdge(
                    edge_id,
                    self.__edges[edge_id].tensors
                    ^ frozenset((tensor_index, new_tensor_index)),
                )

        # Add an edge between the two last indices of the left and right tensors
        edge_id = len(self.__edges)
        self.__index_lists[tensor_index].append(edge_id)
        self.__index_lists[-1].append(edge_id)
        self.__edges.append(
            TensorNetworkEdge(edge_id, frozenset((tensor_index, new_tensor_index)))
        )

        return new_tensor_index, edge_id


class LazyTensor(Tensor):
    def __init__(self, shape, **display_args):
        super().__init__(None, **display_args)

        self.__shape = tuple(shape)

    @property
    def shape(self):
        return self.__shape

    def _generate_tensor(self):
        raise NotImplementedError()

    def get_factor_components(self, left_indices, right_indices):
        raise NotImplementedError()

    @property
    def value(self):
        if self._value is None:
            self._value = self._generate_tensor()
            if self._value.shape != self.__shape:
                raise AttributeError(
                    "Generated tensor had shape {0} but expected shape {1}".format(
                        self._value.shape, self.__shape
                    )
                )
        return self._value


def draw_graph(networkx_graph):
    from IPython.display import Image

    # convert from networkx -> pydot
    pydot_graph = nx.nx_pydot.to_pydot(networkx_graph)

    # render pydot by calling dot, no file saved to disk
    png_str = pydot_graph.create_png(prog="dot")
    return Image(png_str)
