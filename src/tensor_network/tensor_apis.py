contraction_info = []


class OutOfMemoryError(Exception):
    pass


class NumpyAPI:
    def __init__(self, entry_type, thread_limit=None):
        self._thread_limit = thread_limit
        if thread_limit is not None:
            import threadpoolctl

            self._thread_limiter = threadpoolctl

        import numpy

        self._numpy = numpy
        self._entry_type = self._get_numpy_type(entry_type)

    def create_tensor(self, shape, default_value=None):
        if default_value is None:
            return self._numpy.empty(shape, dtype=self._entry_type)
        else:
            return self._numpy.full(shape, default_value, dtype=self._entry_type)

    def tensordot(self, a, b, axes):
        return self._numpy.tensordot(a, b, axes)

    def contract(self, network, contraction_tree, log):
        try:
            if self._thread_limit is not None:
                with self._thread_limiter.threadpool_limits(
                    limits=self._thread_limit, user_api="blas"
                ):
                    return network.identify(contraction_tree, self, log)
            else:
                return network.identify(contraction_tree, self, log)
        except MemoryError:
            raise OutOfMemoryError

    def warm(self):
        """
        Warm up the library, if needed.
        :return: None
        """
        pass

    def _get_numpy_type(self, entry_type):
        types = {
            "float64": self._numpy.float64,
            "float32": self._numpy.float32,
            "float16": self._numpy.float16,
            "uint": self._numpy.uint64,
            "int": self._numpy.int64,
            "bigint": self._numpy.object,
        }

        if entry_type in types:
            return types[entry_type]
        else:
            raise ValueError("Unknown numpy type %s" % entry_type)

    def get_entry_size(self):
        return self._numpy.dtype(self._entry_type).itemsize


class NumpyTensor:
    def __init__(self, base, tensorflow, dtype):
        self._base = base
        self._tensorflow = tensorflow
        self._dtype = dtype

    def __setitem__(self, key, value):
        self._base.__setitem__(key, value)

    def __getitem__(self, item):
        return NumpyTensor(self._base.__getitem__(item), self._tensorflow, self._dtype)

    def as_tensorflow(self):
        return self._tensorflow.convert_to_tensor(self._base, dtype=self._dtype)

    def as_numpy(self):
        return self._base

    @property
    def rank(self):
        return len(self._base.shape)


class TensorflowTensor:
    def __init__(self, base):
        self._base = base

    def as_tensorflow(self):
        return self._base

    def as_numpy(self):
        return self._base.numpy()

    @property
    def rank(self):
        return len(self._base.shape)


class TensorFlowAPI:
    def __init__(self, entry_type, thread_limit=None):
        import tensorflow

        tensorflow.compat.v1.enable_v2_behavior()
        self._tensorflow = tensorflow
        self._entry_type = self._get_tf_type(entry_type)
        self._numpi_api = NumpyAPI(entry_type, thread_limit)

    def _get_tf_type(self, entry_type):
        types = {
            "float64": self._tensorflow.dtypes.float64,
            "float32": self._tensorflow.dtypes.float32,
            "float16": self._tensorflow.dtypes.float16,
            "int": self._tensorflow.dtypes.int64,
        }

        if entry_type in types:
            return types[entry_type]
        else:
            raise ValueError("Unknown TensorFlow type %s" % entry_type)

    def create_tensor(self, shape, default_value=None):
        return NumpyTensor(
            self._numpi_api.create_tensor(shape, default_value),
            self._tensorflow,
            self._entry_type,
        )

    def tensordot(self, a, b, axes):
        return TensorflowTensor(
            self._tensorflow.tensordot(a.as_tensorflow(), b.as_tensorflow(), axes)
        )

    def contract(self, network, contraction_tree, log):
        result, log = network.identify(contraction_tree, self, log)
        return result.as_numpy(), log

    def warm(self):
        pass

    def get_entry_size(self):
        return self._entry_type.size


class TensorFlowGPUAPI(TensorFlowAPI):
    def __init__(self, entry_type, thread_limit=None):
        super().__init__(entry_type, thread_limit)

    def contract(self, network, contraction_tree, log):
        try:
            with self._tensorflow.device("/GPU:0"):
                return super().contract(network, contraction_tree, log)
        except self._tensorflow.errors.ResourceExhaustedError:
            raise OutOfMemoryError

    def warm(self):
        """
        Warm up the GPU with a simple operation.
        :return: None
        """
        with self._tensorflow.device("/GPU:0"):
            self.tensordot(
                self.create_tensor((2,), default_value=2),
                self.create_tensor((2,), default_value=2),
                ([0], [0]),
            )


class TensorFlowGPUSwapAPI(TensorFlowGPUAPI):
    def __init__(self, entry_type, swap_at, thread_limit=None):
        super().__init__(entry_type, thread_limit)
        self.swap_at = swap_at

    def tensordot(self, a, b, axes):
        if (
            a.rank < self.swap_at
            and b.rank < self.swap_at
            and a.rank + b.rank - 2 * len(axes[0]) < self.swap_at
        ):
            return NumpyTensor(
                self._numpi_api.tensordot(a.as_numpy(), b.as_numpy(), axes),
                self._tensorflow,
                self._entry_type,
            )
        else:
            return TensorflowTensor(
                self._tensorflow.tensordot(a.as_tensorflow(), b.as_tensorflow(), axes)
            )

    def contract(self, network, contraction_tree, log):
        if contraction_tree.maxrank < self.swap_at:
            return self._numpi_api.contract(
                network, contraction_tree, log
            )  # No GPU needed

        try:
            with self._tensorflow.device("/GPU:0"):
                return super().contract(network, contraction_tree, log)
        except self._tensorflow.errors.ResourceExhaustedError:
            raise OutOfMemoryError


ALL_APIS = {
    "numpy": NumpyAPI,
    "tensorflow": TensorFlowAPI,
    "tensorflow-gpu": TensorFlowGPUAPI,
    "tensorflow-gpu20": lambda entry_type, **kwargs: TensorFlowGPUSwapAPI(
        entry_type, 20, **kwargs
    ),
}
