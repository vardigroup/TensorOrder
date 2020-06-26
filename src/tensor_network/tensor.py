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
