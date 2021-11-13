import itertools


class OutOfMemoryError(Exception):
    pass


class BaseTensorAPI:
    def add_argument(self, key, value):
        raise ValueError(
            "Invalid argument " + str(key) + " for selected tensor_library"
        )

    def contract(self, network, contraction_tree):
        raise NotImplementedError

    def contract_sliced(self, execution_plan, num_slice_limit=None):
        """
        Contract the provided SlicedExecutionPlan
        """
        result = 0
        slices = execution_plan.network.slice_groups(execution_plan.groups_to_slice)
        if num_slice_limit is not None:
            slices = itertools.islice(slices, num_slice_limit)
        for slice_network in slices:
            tensor_result = self.contract(slice_network, execution_plan.tree)
            result += tensor_result[tuple()]
        return result
