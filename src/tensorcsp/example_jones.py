#################################################################
#                                                               #
#   EXAMPLE: EVALUATING JONES POLYNOMIAL OF KNOTS               #
#   ==========================================                  #
#   ( example_jones.py )                                        #
#   written by Konstantinos Meichanetzidis (phykme@leeds.ac.uk) #
#                                                               #
#   Example script demonstrating the evaluation of the Jones    #
#   Polynomial in terms of the q-state Potts model partition    #
#   function via tensor network contraction. Example knots are  #
#   provided in a dictionary in Planar Diagram presentation     #
#   along with the analytic form of their Jones polynomial.     #
#                                                               #
#   DEPENDENCIES: tensorcsp.py, knut.py                         #
#                                                               #
#################################################################

import sys                      # Import system-specific library
sys.dont_write_bytecode = True  # Do not write compiled bytecode

from tensorcsp import *
from knut import *

# Dictionary of knots of the form knots['knot']=[X,jones]
# where knot (string) is the knot name, X is the planar diagram
# presentation (list of lists), and jones is the analytic form
# of the Jones polynomial.

def jpoly_3_1(t):
    return - t**-4 + t**-3 + t**-1
def jpoly_4_1(t):
    return t**2+ t**-2 -t- t**-1 +1
def jpoly_5_2(t):
    return - t**-6 + t**-5 - t**-4 +2* t**-3 - t**-2 + t**-1
def jpoly_6_3(t):
    return -t**3+2* t**2-2 *t+3-2 *t**-1 +2 *t**-2 - t**-3 
def jpoly_7_6(t):
    return t-2+3 * t**-1 -3* t**-2 +4* t**-3 -3* t**-4 +2* t**-5 - t**-6
def jpoly_8_10(t):
    return    -t**6+2* t**5-4* t**4+5* t**3-4* t**2+5* t-3+2* t**-1 - t**-2
def jpoly_9_14(t):
    return (t**6-2 *t**5+3 *t**4-5 *t**3+6 *t**2-6* t+6-4 *t**-1 +3 *t**-2
    - t**-3)


# Some knots from 3 to 9 crossings:
knots=dict( [
    ( '3_1' , [ [[1,4,2,5],[3,6,4,1],[5,2,6,3]] , jpoly_3_1 ] ) ,
    ( '4_1' , [ [[4,2,5,1],[8,6,1,5],[6,3,7,4],[2,7,3,8]] , jpoly_4_1 ]),
    ( '5_2' , [ [[1,4,2,5],[3,8,4,9],[5,10,6,1],[9,6,10,7],[7,2,8,3]] ,
        jpoly_5_2 ] ),
    ( '6_3' , [ [[4,2,5,1],[8,4,9,3],[12,9,1,10],[10,5,11,6],[6,11,7,12],
        [2,8,3,7]] , jpoly_6_3 ] ),
    ( '7_6' , [ [[1,4,2,5],[3,8,4,9],[5,12,6,13],[9,1,10,14],[13,11,14,10],
        [11,6,12,7],[7,2,8,3]] , jpoly_7_6 ] ),
    ( '8_10', [ [[1,4,2,5],[3,8,4,9],[9,15,10,14],[5,13,6,12],[13,7,14,6],
        [11,1,12,16],[15,11,16,10],[7,2,8,3]] , jpoly_8_10 ] ),
    ( '9_14', [ [[1,4,2,5],[5,12,6,13],[3,11,4,10],[11,3,12,2],
        [13,18,14,1],[9,15,10,14],[7,17,8,16],[15,9,16,8],[17,7,18,6]] ,
         jpoly_9_14 ] ),
    ] )



##########################################################################
# Choose example knot by calling its name from the knots dictionary.
# Compute Jones polynomial by greedy contraction
# and compare with analytical result.
##########################################################################

knot='3_1'

X=knots[knot][0]
jones=knots[knot][1]

##########################################################################

c=pd2tait(X) # signed edge list of Tait graph

tau=taitnumber(c) # Tait number from c

w=writhe(X) # writhe from X

# Function DH_greedy sets q=1 (in order to take
# up minimal memory) and contracts the underlying graph of the tensor
# network (but not the tensor network),
# returning the maximal degree encountered during greedy contraction.
# We also make available an equivalent function for METIS contraction
# in knut.py.

DH_greedy=DeltaH_greedy(c)
print('Maximal degree during contraction is '+str(DH_greedy)+'.')

# Function Jones_greedy contracts the tensor
# network for the chosen q
# and returns the Jones polynomial evaluated at t(q)
# along with the contraction runtime

# Choose a q and compare with analytic expression of the
# Jones polynomial

#integer!
q=5

jpoly,rt=Jones_greedy(c,tau,w,q)

print(('Jones polynomial is V(t(q='+str(q)+'))='+str(jpoly))
+' and was computed in '+str(rt)+' seconds.')
# tpotts from satqtensorjones.py is the t(q) function
# relating Potts parameter q to Jones variable t
print(('The analytical result is V(t(q='+str(q)+'))=')
+str(jones(tpotts(q)))+'.')

