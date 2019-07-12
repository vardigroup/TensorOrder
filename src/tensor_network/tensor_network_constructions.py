from util import Formula, log
from tensor_network.tensor_network import TensorNetwork, Tensor, LazyTensor
from collections import Counter


def cnf_count(dimacs_file, tensor_factory):
    formula = Formula.parse_DIMACS(dimacs_file, include_missing_vars=False)

    network = TensorNetwork()

    # Count the number of occurrences of each variable.
    variable_count = Counter()
    for clause in formula.clauses:
        variable_count.update(map(abs, clause))

    # Prepare a tensor to represent each variable, with rank of the tensor = # of occurrences of the variable.
    variable_edges = {}
    for var in formula.variables:
        variable_edges[var] = network.add_node(
            VariableTensor(
                variable_count[var],
                tensor_factory,
                formula.literal_weight(var),
                formula.literal_weight(-var),
            )
        )

    # Prepare a tensor to represent each clause, and connect it to the variable tensors
    for clause in formula.clauses:
        literals_positive = [literal > 0 for literal in clause]
        clause_edges = network.add_node(OrTensor(literals_positive, tensor_factory))

        for clause_edge, literal in zip(clause_edges, clause):
            clause_edge.connect(variable_edges[abs(literal)].pop())
    return network


class OrTensor(LazyTensor):
    def __init__(self, literals_positive, tensor_factory, output_index=None):
        super().__init__([2] * len(literals_positive), label="or")

        self.__literals_positive = literals_positive
        self.__factory = tensor_factory
        self.__output_index = output_index

    @property
    def output_index(self):
        return self.__output_index

    def _generate_tensor(self):
        result = self.__factory(self.shape, 1)
        if self.__output_index is None:
            # Tensor is 1 at (a[1], a[2], ...) if (a[1] or a[2] or ...) == True, and 0 otherwise
            # F | F | ... | F | F is false
            result[
                tuple(0 if lit_pos else 1 for lit_pos in self.__literals_positive)
            ] = 0
        else:
            # Tensor is 1 at (a[1], a[2], ...) if (a[1] or a[2] or ...) == a[output_index], and 0 otherwise
            # * | * | ... | * | * = F is almost always incorrect
            output_index_false_value = (
                0 if self.__literals_positive[self.__output_index] else 1
            )
            result[
                tuple(
                    output_index_false_value
                    if i == self.__output_index
                    else slice(0, 2)
                    for i in range(len(self.shape))
                )
            ] = 0

            # Except F | F | ... | F | F = F is correct
            all_false = [0 if lit_pos else 1 for lit_pos in self.__literals_positive]
            result[tuple(all_false)] = 1

            # F | F | ... | F | F = T is incorrect
            all_false[self.__output_index] = 1 - all_false[self.__output_index]
            result[tuple(all_false)] = 0
        return result

    def get_factor_components(self, left_indices, right_indices):
        left_literals = [self.__literals_positive[i] for i in left_indices] + [True]
        right_literals = [self.__literals_positive[i] for i in right_indices] + [True]

        if self.__output_index is None:
            left = OrTensor(left_literals, self.__factory, len(left_literals) - 1)
            right = OrTensor(right_literals, self.__factory)
            return left, right
        elif self.__output_index in left_indices:
            left = OrTensor(
                left_literals, self.__factory, left_indices.index(self.__output_index)
            )
            right = OrTensor(right_literals, self.__factory, len(right_literals) - 1)
        elif self.__output_index in right_indices:
            left = OrTensor(left_literals, self.__factory, len(left_literals) - 1)
            right = OrTensor(
                right_literals, self.__factory, right_indices.index(self.__output_index)
            )
        else:
            raise RuntimeError(
                "Provided indices must partition the indices of this tensor"
            )
        return left, right


class VariableTensor(LazyTensor):
    def __init__(self, rank, tensor_factory, positive_weight, negative_weight):
        super().__init__(
            (2,) * rank,
            label="",
            style="filled",
            fillcolor="black",
            height=0.1,
            width=0.1,
        )
        self.__factory = tensor_factory
        self.__positive_weight = positive_weight
        self.__negative_weight = negative_weight

    def _generate_tensor(self):
        # Tensor is 1 at (a, b, c, ..., z) if a == b == c == ... == z, and 0 otherwise
        result = self.__factory(self.shape, 0)
        if len(self.shape) == 0:
            result[()] = self.__negative_weight + self.__positive_weight
        else:
            result[(0,) * self.rank] = self.__negative_weight
            result[(1,) * self.rank] = self.__positive_weight
        return result

    def get_factor_components(self, left_indices, right_indices):
        left = VariableTensor(
            len(left_indices) + 1,
            self.__factory,
            self.__positive_weight,
            self.__negative_weight,
        )
        right = VariableTensor(len(right_indices) + 1, self.__factory, 1, 1)
        return left, right


class CopyTensor(LazyTensor):
    def __init__(self, shape, tensor_factory, central_value=1):
        super().__init__(
            shape, label="", style="filled", fillcolor="black", height=0.1, width=0.1
        )
        self.__factory = tensor_factory
        self.__central_value = central_value

    def _generate_tensor(self):
        # Tensor is 1 at (a, b, c, ..., z) if a == b == c == ... == z, and 0 otherwise
        result = self.__factory(self.shape, 0)
        for i in range(min(self.shape)):
            result[(i,) * self.rank] = self.__central_value
        return result

    def get_factor_components(self, left_indices, right_indices):
        left_shape = [self.shape[i] for i in left_indices]
        right_shape = [self.shape[j] for j in right_indices]

        new_size = min(self.shape)
        left_shape.append(new_size)
        right_shape.append(new_size)

        left = CopyTensor(
            left_shape, self.__factory, central_value=self.__central_value
        )
        right = CopyTensor(right_shape, self.__factory, central_value=1)
        return left, right


ALL_CONSTRUCTIONS = {"wmc": cnf_count}
