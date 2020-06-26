from util import Formula
from tensor_network.tensor_network import TensorNetwork
from tensor_network.tensor import Tensor
from collections import Counter


def cnf_count(dimacs_file):
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
                formula.literal_weight(var),
                formula.literal_weight(-var),
            )
        )

    # Prepare a tensor to represent each clause, and connect it to the variable tensors
    for clause in formula.clauses:
        literals_positive = [literal > 0 for literal in clause]
        clause_edges = network.add_node(OrTensor(literals_positive))

        for clause_edge, literal in zip(clause_edges, clause):
            network.connect(*clause_edge, *variable_edges[abs(literal)].pop())
    return network


class OrTensor(Tensor):
    def __init__(self, literals_positive, output_index=None):
        super().__init__([2] * len(literals_positive), label="or")

        self.__literals_positive = literals_positive
        self.__output_index = output_index

    @property
    def output_index(self):
        return self.__output_index

    def build(self, tensor_factory):
        result = tensor_factory(self.shape, 1)
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
            left = OrTensor(left_literals, len(left_literals) - 1)
            right = OrTensor(right_literals)
            return left, right
        elif self.__output_index in left_indices:
            left = OrTensor(left_literals, left_indices.index(self.__output_index))
            right = OrTensor(right_literals, len(right_literals) - 1)
        elif self.__output_index in right_indices:
            left = OrTensor(left_literals, len(left_literals) - 1)
            right = OrTensor(right_literals, right_indices.index(self.__output_index))
        else:
            raise RuntimeError(
                "Provided indices must partition the indices of this tensor"
            )
        return left, right


class VariableTensor(Tensor):
    def __init__(self, rank, positive_weight, negative_weight, label=None):
        super().__init__((2,) * rank, label=label)
        self.__positive_weight = positive_weight
        self.__negative_weight = negative_weight

    @property
    def diagonal(self):
        return True

    def build(self, tensor_factory):
        # Tensor is 1 at (a, b, c, ..., z) if a == b == c == ... == z, and 0 otherwise
        result = tensor_factory(self.shape, 0)
        if len(self.shape) == 0:
            result[()] = self.__negative_weight + self.__positive_weight
        else:
            result[(0,) * self.rank] = self.__negative_weight
            result[(1,) * self.rank] = self.__positive_weight
        return result

    def get_factor_components(self, left_indices, right_indices):
        left = VariableTensor(
            len(left_indices) + 1, self.__positive_weight, self.__negative_weight
        )
        right = VariableTensor(len(right_indices) + 1, 1, 1)
        return left, right


ALL_CONSTRUCTIONS = {"wmc": cnf_count}
