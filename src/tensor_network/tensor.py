from itertools import product, islice


class Tensor:
    def __init__(self, shape, label=None):
        self.shape = shape
        self.label = label

    @property
    def rank(self):
        return len(self.shape)

    @property
    def display(self):
        if self.label is None:
            return {}
        else:
            return {"label": self.label}

    def get_slice(self, which_edge, value):
        lookup = [
            (value,) if i == which_edge else slice(0, self.shape[i])
            for i in range(len(self.shape))
        ]
        return SlicedTensor(self, lookup)

    @property
    def diagonal(self):
        return False

    def build(self, tensor_factory):
        raise NotImplementedError()

    def get_factor_components(self, left_indices, right_indices):
        raise NotImplementedError()


class BuiltTensor(Tensor):
    def __init__(self, base, label=None):
        Tensor.__init__(self, base.shape, label)
        self.base = base

    def build(self, tensor_factory):
        result = tensor_factory(self.base.shape)
        if len(self.base.shape) == 0:
            result[tuple()] = self.base[tuple()]
        else:
            result[:] = self.base[:]
        return result

    def get_factor_components(self, left_indices, right_indices):
        raise NotImplementedError()


class SlicedTensor(Tensor):
    def __init__(self, parent, slice_lookup):
        Tensor.__init__(self, parent.shape, parent.label)

        self.__parent = parent
        self.__slice_lookup = slice_lookup

    @property
    def diagonal(self):
        return self.__parent.diagonal()

    def build(self, tensor_factory):
        result = self.__parent.build(tensor_factory)
        return result[tuple(self.__slice_lookup)]

    def get_slice(self, which_edge, value):
        new_lookup = list(self.__slice_lookup)
        new_lookup[which_edge] = slice(value, value + 1)
        return SlicedTensor(self.__parent, new_lookup)

    def get_factor_components(self, left_indices, right_indices):
        raise NotImplementedError()


class SliceSequence:
    def __init__(self, base_tensor, full_sliced_indices, local_to_global):
        self.__base_tensor = base_tensor
        self.__full_sliced_indices = full_sliced_indices
        self.__local_to_global = local_to_global

    def is_constant(self):
        return len(self.__local_to_global) == 0

    @property
    def shape(self):
        original = list(self.__base_tensor.shape)
        for local_index in self.__local_to_global:
            original[local_index] = 1
        return tuple(original)

    def reordered_tensor(self, tensor_api):
        sliced_indices = []
        unsliced_indices = []
        resulting_shape = []
        for i, size in enumerate(self.__base_tensor.shape):
            if i in self.__local_to_global:
                sliced_indices.append(i)
            else:
                unsliced_indices.append(i)
                resulting_shape.append(size)

        slice_lookup = [0] * len(self.__full_sliced_indices)
        offset = 1
        for i in reversed(sliced_indices):
            slice_lookup[self.__local_to_global[i]] += offset
            offset *= self.__base_tensor.shape[i]

        reordered = tensor_api.reshape(
            tensor_api.transpose(
                self.__base_tensor, perm=sliced_indices + unsliced_indices
            ),
            tuple([offset] + resulting_shape),
        )

        return reordered, slice_lookup, tuple(resulting_shape)

    def as_list(self):
        if len(self.__local_to_global) == 0:
            tensor = self.__base_tensor.as_tensorflow()
            return [tensor for _ in product(*self.__full_sliced_indices)]
        else:
            result = []
            for assignment in product(*self.__full_sliced_indices):
                which_slice = [
                    slice(0, dim_size) for dim_size in self.__base_tensor.shape
                ]
                for local_index, global_index in self.__local_to_global.items():
                    which_slice[local_index] = slice(
                        assignment[global_index], assignment[global_index] + 1
                    )
                result.append(self.__base_tensor[tuple(which_slice)].as_tensorflow())
            return result

    def as_list_groups(self, group_size):
        assignments = product(*self.__full_sliced_indices)
        if len(self.__local_to_global) == 0:
            tensor = self.__base_tensor.as_tensorflow()
            while True:
                result = [tensor for _ in islice(assignments, group_size)]
                if len(result) > 0:
                    yield result
                else:
                    return
        else:
            which_slice = [slice(0, dim_size) for dim_size in self.__base_tensor.shape]
            while True:
                result = []
                for assignment in islice(assignments, group_size):
                    for local_index, global_index in self.__local_to_global.items():
                        which_slice[local_index] = slice(
                            assignment[global_index], assignment[global_index] + 1
                        )
                    result.append(
                        self.__base_tensor[tuple(which_slice)].as_tensorflow()
                    )
                if len(result) > 0:
                    yield result
                else:
                    return

    def as_generator(self):
        if len(self.__local_to_global) == 0:
            for _ in product(*self.__full_sliced_indices):
                yield self.__base_tensor.as_tensorflow()
        else:
            which_slice = [slice(0, dim_size) for dim_size in self.__base_tensor.shape]
            for assignment in product(*self.__full_sliced_indices):
                for local_index, global_index in self.__local_to_global.items():
                    which_slice[local_index] = slice(
                        assignment[global_index], assignment[global_index] + 1
                    )
                yield self.__base_tensor[tuple(which_slice)].as_tensorflow()
