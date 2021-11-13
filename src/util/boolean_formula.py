from collections import OrderedDict
from enum import Enum


class WeightFormat(Enum):
    unweighted = 0
    cachet = 1
    minic2d = 2
    mcc = 3


class Formula:
    def __init__(self):
        self._variables = OrderedDict()
        self._clauses = []

    def add_clause(self, literals):
        """
        Add a new CNF clause representing the disjunction of the provided literals.

        The elements of literals should be variable id (representing the corresponding
        positive literal) or the negative of a variable id (for the negative literal).

        :param literals: An iterable of variable ids and negations of variable ids.
        :return: None
        """
        self._clauses.append(list(literals))

    def fresh_variable(self, neg_weight, pos_weight):
        """
        Create a new weighted variable in the formula.

        :param neg_weight: Multiplicative weight on an assignment when variable is false
        :param pos_weight: Multiplicative weight on an assignment when variable is true
        :return: An id of the new variable, which can be used to construct clauses
        """
        new_var_id = len(self._variables) + 1
        self._variables[new_var_id] = [neg_weight, pos_weight]
        return new_var_id

    @property
    def clauses(self):
        return list(self._clauses)

    @property
    def variables(self):
        return list(self._variables.keys())

    def literal_weight(self, lit):
        """
        Returns the multiplicative weight of the provided DIMACS literal.

        :param lit: Literal to get weight of
        """
        return self._variables[abs(lit)][1 if lit > 0 else 0]

    def set_literal_weight(self, lit, weight):
        """
        Set the multiplicative weight of the provided DIMACS literal.

        :param lit: Literal to set weight of
        :param weight: Weight to use
        """
        if abs(lit) not in self._variables:
            self._variables[abs(lit)] = [1, 1]
        self._variables[abs(lit)][1 if lit > 0 else 0] = weight

    def set_variable_weight(self, var_id, neg_weight, pos_weight):
        """
        Create a new weighted variable in the formula.

        :param var_id: Variable to set weight of
        :param neg_weight: Multiplicative weight on an assignment when variable is false
        :param pos_weight: Multiplicative weight on an assignment when variable is true
        """
        self._variables[var_id] = [neg_weight, pos_weight]

    def write_cachet(self, filename):
        """
        Write the formula into the format expected by cachet.

        If the weights are non-probabilistic (i.e., positive and negative weights do not add up to 1),
        the weights must be normalized before they are input into cachet. This results in a normalization constant,
        which is returned.

        The proper count of the formula is then the normalization constant multiplied by the result of cachet
        when run on the output file.

        :param filename: The file to write the formula.
        :return: The normalization constant C.
        """
        with open(filename, "w") as f:
            f.write("p cnf %d %d\n" % (len(self._variables), len(self._clauses)))

            # Write all weights, renormalizing if appropriate
            normalization_constant = 1
            for var, weight in self._variables.items():
                negative_weight = weight[0]
                positive_weight = weight[1]

                if positive_weight == negative_weight:
                    normalization_constant *= positive_weight
                    f.write(
                        "w %d %d\n" % (var, -1)
                    )  # special cachet syntax for 1-1 variables
                else:
                    # Normalize the weights, if required
                    if positive_weight + negative_weight != 1:
                        normalization_constant *= positive_weight + negative_weight
                        positive_weight /= positive_weight + negative_weight
                    f.write("w %d %f\n" % (var, positive_weight))
            # Write all clauses.
            f.writelines(
                ["%s 0\n" % " ".join(map(str, clause)) for clause in self._clauses]
            )
        return normalization_constant

    def write_miniC2D(self, filename):
        """
        Write the formula into the format expected by miniC2D.

        :param filename: The file to write the formula.
        :return: None
        """
        with open(filename, "w") as f:
            f.write("p cnf %d %d\n" % (len(self._variables), len(self._clauses)))

            weights = ["c", "weights"]
            for v in range(1, max(self._variables.keys()) + 1):
                if v in self._variables:
                    weights.extend(map(str, reversed(self._variables[v])))
                else:
                    weights.extend([0.5, 0.5])
            f.write(" ".join(weights) + "\n")

            f.writelines(
                ["%s 0\n" % " ".join(map(str, clause)) for clause in self._clauses]
            )

    def write_DNNF(self, formula_filename, weight_filename):
        """
        Write the formula into the format expected by a DNNF reasoner.

        The formula will be split across two files, one storing the clauses and one storing the literal weights.

        :param formula_filename: File to store the formula clauses (as DIMACS)
        :param weight_filename: File to store the formula weights
        :return: None
        """
        self.write_DIMACS(formula_filename)
        with open(weight_filename, "w") as f:
            for variable in self._variables:
                f.write(str(variable) + " " + str(self.literal_weight(variable)) + "\n")
                f.write(
                    str(-variable) + " " + str(self.literal_weight(-variable)) + "\n"
                )

    def write_DIMACS(self, filename):
        """
        Write the formula into DIMACS format.

        Does not include variable weights.

        :param filename: The file to write the formula.
        :return: None
        """
        with open(filename, "w") as f:
            f.write("p cnf %d %d\n" % (len(self._variables), len(self._clauses)))
            f.writelines(
                ["%s 0\n" % " ".join(map(str, clause)) for clause in self._clauses]
            )

    def write_ASP(self, filename):
        def literal_to_ASP(literal):
            if literal > 0:
                # Note positive literals are prepended with not, matching the reduction from the authors of dynASP
                return "not a_" + str(abs(literal))
            else:
                return "a_" + str(abs(literal))

        with open(filename, "w") as f:
            for v in range(1, max(self._variables.keys()) + 1):
                f.write("{a_" + str(v) + "}.\n")

            for clause in self._clauses:
                f.write(":- " + ", ".join(literal_to_ASP(l) for l in clause) + ".\n")

    def write_QBF(self, filename):
        with open(filename, "w") as f:
            f.write("p cnf %d %d\n" % (len(self._variables), len(self._clauses)))
            f.write(
                "e %s\n"
                % " ".join(str(v) for v in range(1, max(self._variables.keys()) + 1))
            )
            f.writelines(
                ["%s 0\n" % " ".join(map(str, clause)) for clause in self._clauses]
            )

    @staticmethod
    def parse_DIMACS(file, weight_format):
        """
        Parse a DIMACS file into a formula.

        The file may optionally contain weights, in the cachet style i.e. lines of the form
        w [var id] [prob]
        that each indicate that the variable [var id] should have positive literal weight [prob]
        and negative literal weight 1-[prob].

        If [prob] is -1, the variable is unweighted

        :param file: A handler to the file to read
        :param weight_format: Format of weights
        :return: the resulting formula
        """
        result = Formula()

        num_vars = 0
        for line in file:
            if weight_format == WeightFormat.minic2d and line.startswith(
                "c weights"
            ):  # MiniC2D weights
                weights = line.split(" ")[2:]
                for i in range(len(weights) // 2):
                    result.set_variable_weight(
                        i + 1, float(weights[2 * i + 1]), float(weights[2 * i])
                    )
            elif len(line) == 0 or line[0] == "c":
                continue
            elif line[0] == "p":
                num_vars = int(line.split()[2])
            elif line[0] == "w":  # Cachet weights
                args = line.split()
                var_id = int(args[1])
                weight = float(args[2])
                if weight_format == WeightFormat.cachet:
                    if weight == -1:
                        result.set_variable_weight(var_id, 1, 1)
                    else:
                        result.set_variable_weight(var_id, 1 - weight, weight)
                elif weight_format == WeightFormat.mcc:
                    result.set_literal_weight(var_id, weight)
                else:
                    raise RuntimeError(
                        "w lines cannot be used in " + str(weight_format)
                    )

            else:
                literals = map(int, line.split())
                literals = [lit for lit in literals if lit != 0]
                if len(literals) == 0:
                    continue
                result.add_clause(literals)

        # Set default weights
        if weight_format == WeightFormat.cachet:
            default_weight = 0.5
        else:
            default_weight = 1
        for var_id in range(1, num_vars + 1):
            if var_id not in result._variables:
                result.set_variable_weight(var_id, default_weight, default_weight)
        return result
