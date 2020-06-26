class NumpyAPI:
    def __init__(self):
        import numpy

        self._numpy = numpy

    def create_tensor_factory(self, entry_type):
        numpy_type = self._get_numpy_type(entry_type)

        def tensor_factory(shape, default_value=None):
            if default_value is None:
                return self._numpy.empty(shape, dtype=numpy_type)
            else:
                return self._numpy.full(shape, default_value, dtype=numpy_type)

        return tensor_factory

    def tensordot(self, a, b, axes):
        return self._numpy.tensordot(a, b, axes)

    def _get_numpy_type(self, entry_type):
        types = {
            "float": self._numpy.float64,
            "uint": self._numpy.uint64,
            "int": self._numpy.int64,
            "bigint": self._numpy.object,
        }

        if entry_type in types:
            return types[entry_type]
        else:
            raise ValueError("Unknown numpy type %s" % entry_type)


ALL_APIS = {"numpy": NumpyAPI()}
