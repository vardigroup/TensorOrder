#################################################################
#                                                               #
#   EXAMPLE: SOLVING 3-REGULAR #2SAT INSTANCES                  #
#   ==========================================                  #
#   ( example_2sat3.py )                                        #
#   first instance: 20180425                                    #
#   written by Stefanos Kourtis ( kourtis@bu.edu )              #
#                                                               #
#   Example script demonstrating the solution of instances of   #
#   3-regular #2SAT (also known as #CUBIC-VERTEX-COVER) using   #
#   graph partitioning and tensor network contraction. Random   #
#   instances are generated as random 3-regular graphs, where   #
#   vertices correspond to variables and edges to clauses.      #
#                                                               #
#   DEPENDENCIES: tensorcsp.py                                  #
#                                                               #
#################################################################

import sys                      # Import system-specific library
sys.dont_write_bytecode = True  # Do not write compiled bytecode
from timeit import default_timer# Use this to time solvers
from tensorcsp import *         # Import tensorCSP functions

# Generate random 3-regular graph with nv vertices. Equivalently
# these can be thought of as 2SAT instances with nv variables and
# each edge represents a clause. Write the corresponding CNF to
# a DIMACS file for purposes of comparison with other solvers.
#
# NB: Counts for nv>100 start to overflow default numpy int. Pass
#     dtype=float to cnf_tngraph for floating-point precision.
nv = 80
cg = Graph.Degree_Sequence([3]*nv,method="vl")
cf = array(cg.get_edgelist())+1 # Edgelist is 2SAT CNF formula cf
__ = cnf_write(cf,"tmp.cnf")    # Write to file in DIMACS format
tg = cnf_tngraph(cf,dtype=int)  # Build tensor graph

# First solve using a greedy contraction algorithm:
start = default_timer()
md,sg = contract_greedy(tg,combine_attrs=dict(attr=attr_contract))
end   = default_timer()
sol   = sg.vs[0]["attr"][1]
print('Solved with greedy contraction in ',end-start,' seconds')
print('  #Solutions:',sol)
print('  Max degree:',md.max())

# Then solve using METIS graph partitioning:
start = default_timer()
m = recursive_bipartition(tg,metis_bipartition)
md,sg = contract_dendrogram(tg,m,combine_attrs=dict(attr=attr_contract))
end   = default_timer()
sol   = sg.vs[0]["attr"][1]
print('Solved with METIS partitioning in ',end-start,' seconds')
print('  #Solutions:',sol)
print('  Max degree:',md.max())

# Finally solve using Girvan-Newman community detection:
start = default_timer()
d = tg.community_edge_betweenness()
m = d.merges
md,sg = contract_dendrogram(tg,m,combine_attrs=dict(attr=attr_contract))
end   = default_timer()
sol   = sg.vs[0]["attr"][1]
print('Solved with Girvan-Newman in ',end-start,' seconds')
print('  #Solutions:',sol)
print('  Max degree:',md.max())

