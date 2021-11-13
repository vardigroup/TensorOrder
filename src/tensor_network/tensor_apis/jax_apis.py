from tensor_network.tensor_apis.base_api import BaseTensorAPI
from tensor_network.tensor_apis.numpy_apis import NumpyAPI

import itertools
import math
import util
import time


class JaxAPI(BaseTensorAPI):
    def __init__(self,):
        import jax
        import jax.numpy as jnp

        self._jax = jax
        self._numpy = jnp
        self._base_numpy_api = NumpyAPI()
        self._entry_type = self._numpy.float64
        self._build_full = True
        self._ensure_small = True  # Ensure the smaller matrix occurs on the right
        self._tensordot_method = "tensordot"

    def add_argument(self, key, value):
        if key == "ensure_small":
            self._ensure_small = value
            return
        if key == "oneshot":
            self._build_full = value
            return
        if key == "tensordot":
            self._tensordot_method = value
            return

        if key == "entry_type":
            types = {
                "float64": self._numpy.float64,
                "float32": self._numpy.float32,
                "float16": self._numpy.float16,
                "uint": self._numpy.uint64,
                "int": self._numpy.int64,
            }

            if value in types:
                self._entry_type = types[value]
                if self._entry_type is self._numpy.float64:
                    self._jax.config.update("jax_enable_x64", True)
            else:
                raise ValueError("Unknown jax type %s" % value)
        else:
            super(JaxAPI, self).add_argument(key, value)

        self._base_numpy_api.add_argument(key, value)

    def get_entry_size(self):
        return self._base_numpy_api.get_entry_size()

    def create_tensor(self, shape, default_value=None):
        return self._base_numpy_api.create_tensor(shape, default_value)

    def tensordot(self, a, b, axes):
        if len(a.shape) == 0 or len(b.shape) == 0:
            return a * b

        if self._tensordot_method == "tensordot":
            return self.tensordot_direct(a, b, axes)
        elif self._tensordot_method == "matmul":
            return self.tensordot_transpose_all(a, b, axes)
        elif self._tensordot_method == "matmul_ind_transpose":
            return self.tensordot_transpose_one_by_one(a, b, axes)
        elif self._tensordot_method == "matmul_no_transpose":
            return self.tensordot_disable_transpose(a, b, axes)

    def tensordot_direct(self, a, b, axes):
        return self._numpy.tensordot(a, b, axes)

    def tensordot_transpose_all(self, a, b, axes):
        k = 1
        for i in axes[0]:
            k *= a.shape[i]
        N = len(axes[0])

        # Transpose the tensors so the the shared dimensions appear at the back of a and the front of b
        a_t = self._numpy.transpose(
            a, axes=[i for i in range(a.ndim) if i not in axes[0]] + axes[0]
        )
        b_t = self._numpy.transpose(
            b, axes=axes[1] + [i for i in range(b.ndim) if i not in axes[1]]
        )

        # Reshape the tensors to prepare for the matrix multiplication
        a_r = self._numpy.reshape(a_t, (-1, k))
        b_r = self._numpy.reshape(b_t, (k, -1))

        res = self._numpy.matmul(a_r, b_r)

        # Reshape the resulting matrix back into a tensor
        if N == 0:
            return self._numpy.reshape(res, a_t.shape + b_t.shape)
        else:
            return self._numpy.reshape(res, a_t.shape[:-N] + b_t.shape[N:])

    def tensordot_transpose_one_by_one(self, a, b, axes):
        k = 1
        for i in axes[0]:
            k *= a.shape[i]
        N = len(axes[0])

        # Transpose the tensors so the the shared dimensions appear at the back of a and the front of b
        a_t = self.flat_transpose(a, axes=axes[0], on_left=False)
        b_t = self.flat_transpose(b, axes=axes[1], on_left=True)

        # Reshape the tensors to prepare for the matrix multiplication
        a_r = self._numpy.reshape(a_t, (-1, k))
        b_r = self._numpy.reshape(b_t, (k, -1))

        res = self._numpy.matmul(a_r, b_r)

        # Reshape the resulting matrix back into a tensor
        if N == 0:
            return self._numpy.reshape(res, a_t.shape + b_t.shape)
        else:
            return self._numpy.reshape(res, a_t.shape[:-N] + b_t.shape[N:])

    def tensordot_disable_transpose(self, a, b, axes):
        k = 2 ** len(axes[0])
        N = len(axes[0])

        # Reshape the tensors to prepare for the matrix multiplication
        a_r = self._numpy.reshape(a, (-1, k))
        b_r = self._numpy.reshape(b, (k, -1))

        res = self._numpy.matmul(a_r, b_r)

        # Reshape the resulting matrix back into a tensor
        if N == 0:
            return self._numpy.reshape(res, a.shape + b.shape)
        else:
            return self._numpy.reshape(res, a.shape[:-N] + b.shape[N:])

    def reshape(self, tensor, new_shape):
        return self._numpy.reshape(tensor, new_shape)

    def transpose(self, tensor, perm):
        return self._numpy.transpose(tensor, axes=perm)

    def flat_transpose(self, tensor, axes, on_left):
        if len(axes) == 0:
            return tensor

        if on_left:
            axes = reversed(axes)

        moved = []
        perm = [1, 0, 2] if on_left else [0, 2, 1]
        for i in axes:
            # Compute the new position of axis i
            pos = i - sum(1 for j in moved if j < i) + (on_left * len(moved))
            moved.append(i)

            tensor = self._numpy.reshape(tensor, (2 ** pos, 2, -1))
            tensor = self._numpy.transpose(tensor, perm)
        return tensor

    def contract(self, network, contraction_tree):
        result = network.identify(contraction_tree, self)
        return result

    def __build_function(self, tree, sequences):
        reordering_info = [s.reordered_tensor(self) for s in sequences]
        lookup_matrix = self._numpy.stack(
            list(self._numpy.array(info[1]) for info in reordering_info)
        )

        # Check if 64-bit integers are enabled (for lookup)
        int_type = (
            self._numpy.int64
            if self._jax.config.read("jax_enable_x64")
            else self._numpy.int32
        )

        def compute_lookup(assignment):
            # Compute a map from tensor_index -> slice_id
            # This tells you the slices of each tensor that correspond to this assignment
            # Note that this computation can be done on the TPU!
            if assignment.shape[0] == 0:
                return self._numpy.zeros(lookup_matrix.shape[0]).astype(int_type)
            else:
                return self._jax.lax.dot(lookup_matrix, assignment).astype(int_type)

        def at_leaf(leaf):
            def compute(lookup):
                # Compute the relevant slice (of this tensor
                full_tensor, _, resulting_shape = reordering_info[leaf.tensor_index]
                which_slice = lookup[leaf.tensor_index]
                tensor_slice = self._jax.lax.dynamic_slice(
                    self._numpy.asarray(full_tensor),
                    start_indices=tuple([which_slice] + [0] * len(resulting_shape)),
                    slice_sizes=([1] + list(resulting_shape)),
                )
                return self.reshape(tensor_slice, resulting_shape)

            return compute

        def at_join(join):
            def compute(left, right):
                return self.tensordot(
                    left, right, (join.left_edge_map, join.right_edge_map),
                )

            return compute

        # Record the functions to perform at each node in the tree
        funcs = [
            at_leaf(n) if n.is_leaf else at_join(n) for n in tree.iterate_postorder()
        ]

        if self._build_full:
            apply = (
                lambda x: x
            )  # Perform the operation directly; we are already in a pmap context
        else:
            apply = self._jax.pmap  # Compile and perform the specified operation

        # Walk through the tree, applying the specified functions
        def identify(assignment):
            start = time.time()
            lookup = apply(compute_lookup)(assignment)
            # util.log(f" lookup: {time.time() - start}", flush=True)
            stack = []
            for i, node in enumerate(tree.iterate_postorder()):
                start = time.time()
                if node.is_leaf:
                    stack.append(apply(funcs[i])(lookup))
                    # util.log(
                    #     f" {i}: {time.time() - start} : {len(node.free_edges)}",
                    #     flush=True,
                    # )
                else:
                    right_tensor = stack.pop()
                    left_tensor = stack.pop()
                    stack.append(apply(funcs[i])(left_tensor, right_tensor))
                    # util.log(
                    #     f" {i}: {time.time() - start} : {left_tensor.shape} {right_tensor.shape} - {node.left_edge_map} {node.right_edge_map} -> {len(node.free_edges)}",
                    #     flush=True,
                    # )
            return stack[0]

        if self._build_full:
            return self._jax.pmap(identify)
        else:
            return identify

    def contract_sliced_base(self, execution_plan, num_devices, num_slice_limit=None):
        start = time.time()

        (
            total_slice_count,
            sequences,
            assignments,
        ) = execution_plan.network.get_tensor_slices(
            execution_plan.groups_to_slice, self.create_tensor
        )

        if num_slice_limit is not None:
            assignments = itertools.islice(assignments, num_slice_limit)

        tree = execution_plan.network.remove_sliced_indices_from(
            execution_plan.tree, execution_plan.groups_to_slice
        )
        if self._ensure_small:
            # Ensure that the smaller tensor is on the right
            # The left matrix A is stored in the local unified buffer of 96k × 256 words
            # The right matrix B has size 256 × 256
            tree.sort_small()
        util.output_pair("Tree Size", len(list(tree.iterate_postorder())), flush=True)

        identify = self.__build_function(tree, sequences)
        result = self.create_tensor(shape=(1,), default_value=0)
        first_slice_time = 0
        util.log("Compiling sliced network contraction", util.Verbosity.progress)
        for i, assignment_set in enumerate(util.split_every(assignments, num_devices)):
            slice_time_start = time.time()

            slice_result = identify(self._numpy.array(assignment_set))
            util.log(f"Slice {i+1} Result: {slice_result}", util.Verbosity.debug)
            result += sum(slice_result)

            if i == 0:
                first_slice_time = time.time() - slice_time_start
                util.output_pair(
                    "Slice 1 Time",
                    first_slice_time,
                    verbosity=util.Verbosity.debug,
                    flush=True,
                )
            else:
                elapsed = time.time() - slice_time_start
                util.output_pair(
                    f"Slice {i+1} Time",
                    elapsed,
                    verbosity=util.Verbosity.debug,
                    flush=True,
                )
                util.log(
                    "Estimated Execution Time: "
                    + str(
                        (elapsed * (math.ceil(total_slice_count / num_devices) - 1))
                        + first_slice_time
                    ),
                    verbosity=util.Verbosity.debug,
                )

        return result.item()


class JaxCPUAPI(JaxAPI):
    def contract_sliced(self, execution_plan, num_slice_limit=None):
        num_devices = self._jax.device_count("cpu")
        util.log(
            "Running on " + str(num_devices) + " CPU cores", util.Verbosity.progress
        )
        return self.contract_sliced_base(execution_plan, num_devices, num_slice_limit)


class JaxTPUAPI(JaxAPI):
    def __init__(self):
        super().__init__()
        self.__tpu_addr = None

    def add_argument(self, key, value):
        if key == "TPU":
            self.__tpu_addr = value
        else:
            super(JaxTPUAPI, self).add_argument(key, value)

    def contract_sliced(self, execution_plan, num_slice_limit=None):
        if self.__tpu_addr is None:
            raise RuntimeError("No TPU address provided (--tpu)")

        start = time.time()
        self._jax.config.FLAGS.jax_xla_backend = "tpu_driver"
        self._jax.config.FLAGS.jax_backend_target = util.normalize_TPU_addr(
            self.__tpu_addr
        )
        util.log("Connection Time: " + str(time.time() - start), util.Verbosity.debug)

        num_devices = self._jax.device_count("tpu")
        util.log(
            "Running on " + str(num_devices) + " TPU cores", util.Verbosity.progress
        )
        return self.contract_sliced_base(execution_plan, num_devices, num_slice_limit)


JAX_APIS = {"jax": JaxCPUAPI, "jax-tpu": JaxTPUAPI}
