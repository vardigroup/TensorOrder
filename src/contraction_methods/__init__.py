from contraction_methods.contraction_tree import ContractionTree

import contraction_methods.tensorcsp_method
import contraction_methods.line_graph_method
import contraction_methods.factor_tree_method

ALL_SOLVERS = {
    **contraction_methods.tensorcsp_method.SOLVERS,
    **contraction_methods.line_graph_method.SOLVERS,
    **contraction_methods.factor_tree_method.SOLVERS,
}
