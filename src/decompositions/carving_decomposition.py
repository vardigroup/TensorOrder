from typing import List, Callable


class CarvingDecomposition:
    __edges_to_contract: List[List[int]]

    def __init__(self, edges_to_contract: List[List[int]]):
        self.__edges_to_contract = edges_to_contract

    @staticmethod
    def parse(file: str, renumber_bag_components: Callable[[int], int] = lambda x: x):
        to_contract = []

        with open(file, "r") as f:
            for line in f:
                parts = line.split()
                if len(parts) < 2 or parts[0] == "c":
                    continue

                to_contract.append([renumber_bag_components(int(n)) for n in parts])
        return CarvingDecomposition(to_contract)
