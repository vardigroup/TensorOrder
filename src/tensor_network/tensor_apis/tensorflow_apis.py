from tensor_network.tensor_apis.base_api import BaseTensorAPI, OutOfMemoryError
from tensor_network.tensor_apis.numpy_apis import NumpyAPI


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

    @property
    def shape(self):
        return self._base.shape


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

    @property
    def shape(self):
        return self._base.shape


class TensorFlowAPI(BaseTensorAPI):
    def __init__(self):
        try:
            import tensorflow
        except ModuleNotFoundError:
            raise ModuleNotFoundError(
                "No module named 'tensorflow'. Please install tensorflow or use TensorOrder with Dockerfile-gpu."
            )
        tensorflow.compat.v1.enable_v2_behavior()
        self._tensorflow = tensorflow
        self._entry_type = self._tensorflow.dtypes.float64
        self._numpi_api = NumpyAPI()

    def add_argument(self, key, value):
        if key == "entry_type":
            types = {
                "float64": self._tensorflow.dtypes.float64,
                "float32": self._tensorflow.dtypes.float32,
                "float16": self._tensorflow.dtypes.float16,
                "int": self._tensorflow.dtypes.int64,
            }

            if value in types:
                self._entry_type = types[value]
            else:
                raise ValueError("Unknown tensorflow type %s" % value)
        else:
            super(TensorFlowAPI, self).add_argument(key, value)

        self._numpi_api.add_argument(key, value)

    def create_tensor(self, shape, default_value=None):
        return NumpyTensor(
            self._numpi_api.create_tensor(shape, default_value),
            self._tensorflow,
            self._entry_type,
        )

    def reshape(self, tensor, new_shape):
        return TensorflowTensor(
            self._tensorflow.reshape(tensor.as_tensorflow(), new_shape)
        )

    def transpose(self, tensor, perm):
        return TensorflowTensor(
            self._tensorflow.transpose(tensor.as_tensorflow(), perm=perm)
        )

    def tensordot(self, a, b, axes):
        return TensorflowTensor(
            self._tensorflow.tensordot(a.as_tensorflow(), b.as_tensorflow(), axes)
        )

    def contract(self, network, contraction_tree):
        result = network.identify(contraction_tree, self)
        return result.as_numpy()

    def warm(self):
        pass

    def get_entry_size(self):
        return self._entry_type.size


class TensorFlowGPUAPI(TensorFlowAPI):
    def contract(self, network, contraction_tree):
        try:
            with self._tensorflow.device("/GPU:0"):
                return super().contract(network, contraction_tree)
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
    def __init__(self, swap_at):
        super().__init__()
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

    def contract(self, network, contraction_tree):
        if contraction_tree.maxrank < self.swap_at:
            return self._numpi_api.contract(network, contraction_tree)  # No GPU needed

        try:
            with self._tensorflow.device("/GPU:0"):
                return super().contract(network, contraction_tree)
        except self._tensorflow.errors.ResourceExhaustedError:
            raise OutOfMemoryError


TENSORFLOW_APIS = {
    "tensorflow": TensorFlowAPI,
    "tensorflow-gpu": TensorFlowGPUAPI,
    "tensorflow-gpu20": lambda: TensorFlowGPUSwapAPI(20),
}
