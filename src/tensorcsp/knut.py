#################################################################
#                                                               #
#   KNOT UTILITIES                                              #
#   ==============                                              #
#   ( knut.py )                                                 #
#   written by Konstantinos Meichanetzidis (phykme@leeds.ac.uk) #
#                                                               #
#   Auxiliary routines for reading and converting between       #
#   representations of knots, evaluation of basic knot          #
#   properties, encoding the Potts partition function in        #
#   CSP form, and evaluating the Jones polynomial.              #
#                                                               #
#   DEPENDENCIES: numpy, tensorcsp.py, cmath, timeit            #
#                                                               #
#################################################################

import sys                      # Import system-specific library
sys.dont_write_bytecode = True  # Do not write compiled bytecode
from numpy import *
from tensorcsp import *
import cmath
from timeit import default_timer


def writhe(x,return_signs=False):
    """ Return writhe of planar code x for len(x)>1. """
    # Since planar code contains only "under" crossings,
    # this yields handedness sign for each one:
    sg = array([c[1]-c[3] for c in x])
    # Make sure to treat the last arc properly:
    sg[abs(sg)>1] = -sign(sg[abs(sg)>1])
    if ( return_signs ): return sum(sg),sg
    return sum(sg)

def taitnumber(c):
    """ Return Tait number from signed edge list of Tait graph. """
    c =array(c)                 # If type(c) != ndarray
    tau=sum(sign(c[:,0]))
    return tau
    
def pd2tait(X):
    """ Extract Tait graph from Planar Diagram presentation. """
    x  = array(X)               # If type(X) != ndarray
    na = x.max()                # Number of arcs
    # Gather region 1
    p0=argwhere(x==1)[0]  # Position in x where arc 1 appears first
    p=p0 # Arc index
    # Arc (after left turn) positions in x:
    # replace current position with the one which belongs to a
    # different 4-tuple (crossing), repeat until return to arc 1
    regions=[[]]
    # Left turn is the number to the left (up to cyclic
    # permutation in the 4-tuple)
    pp = argwhere(x==x[p[0],(p[1]-1)%4])
    if not(pp[0][0]==p[0]):
        p=pp[0]
        regions[0].append(x[p[0],p[1]]) # Arcs belonging to region 1
    else:
        p=pp[1]
        regions[0].append(x[p[0],p[1]]) # Arcs belonging to region 1
    while not(x[p[0],p[1]]==1):
        pp = argwhere(x==x[p[0],(p[1]-1)%4])
        if not(pp[0][0]==p[0]):
            p=pp[0]
            regions[0].append(x[p[0],p[1]]) # Arcs belonging to region1
        else:
            p=pp[1]
            regions[0].append(x[p[0],p[1]]) # Arcs belonging to region1
    # Gather rest of black regions.On odd (even) arc turn left (right).
    # Skip arcs which belong to regions already.
    for ii in range(2,na+1):
        p1=argwhere(x==ii)  # Position in x where arc ii appears 
        if not(p1[0][0]==p0[0]):
            p0=p1[0]
        else:
            p0=p1[1]
        p=p0
        # Only continue if the arc is unaccounted for:
        if sum([ii in r for r in regions])==0:
            # Left turns:
            if ii%2==1:
                regions.append([])
                # Left turn is the number to the left (up to cyclic
                # permutation in the 4-tuple)
                pp = argwhere(x==x[p[0],(p[1]-1)%4])
                if not(pp[0][0]==p[0]):
                    p=pp[0]
                    regions[len(regions)-1].append(x[p[0],p[1]])
                else:
                    p=pp[1]
                    regions[len(regions)-1].append(x[p[0],p[1]])
                while not(x[p[0],p[1]]==ii):
                    pp = argwhere(x==x[p[0],(p[1]-1)%4])
                    if not(pp[0][0]==p[0]):
                        p=pp[0]
                        regions[len(regions)-1].append(x[p[0],p[1]])
                    else:
                        p=pp[1]
                        regions[len(regions)-1].append(x[p[0],p[1]])
            # Right turns:
            if ii%2==0:
                regions.append([])
                # Right turn is the number to the right (up to cyclic
                # permutation in the 4-tuple)
                pp = argwhere(x==x[p[0],(p[1]+1)%4])
                if not(pp[0][0]==p[0]):
                    p=pp[0]
                    regions[len(regions)-1].append(x[p[0],p[1]])
                else:
                    p=pp[1]
                    regions[len(regions)-1].append(x[p[0],p[1]])
                while not(x[p[0],p[1]]==ii):
                    pp = argwhere(x==x[p[0],(p[1]+1)%4])
                    if not(pp[0][0]==p[0]):
                        p=pp[0]
                        regions[len(regions)-1].append(x[p[0],p[1]])
                    else:
                        p=pp[1]
                        regions[len(regions)-1].append(x[p[0],p[1]])
    # Now that we have all the regions in terms of the arcs that
    # enclose the region we go through all crossings (4 tuples)
    # and obtain the signed edge list.
    el=[[] for ii in range(len(x))]
    for iic,ii in enumerate(x):
        if not(na in ii and 1 in ii):
            eps= (-1)**min(ii) *(-1)**(argmin(ii)+1)
        else:
            eps= (-1)**max(ii) *(-1)**(argmax(ii)+1)
        pair1=[ii[0],ii[1]]
        pair2=[ii[2],ii[3]]
        for rc,r in enumerate(regions):
            if (pair1[0] in r) and (pair1[1] in r):
                el[iic].append((rc+1)*eps)
    
            if (pair2[0] in r) and (pair2[1] in r):
                el[iic].append((rc+1)*eps)
        pair1=[ii[0],ii[3]]
        pair2=[ii[1],ii[2]]   
        for rc,r in enumerate(regions):
            if (pair1[0] in r) and (pair1[1] in r):
                el[iic].append((rc+1)*eps)
            if (pair2[0] in r) and (pair2[1] in r):
                el[iic].append((rc+1)*eps)
    return array(el)

def tpotts(q):
    """ Relation between Jones variable t (complex for 0<q<4)
        and number of spin states q in the Potts model. """
    t=.5*(q+sqrt(q)*cmath.sqrt(q-4)-2)
    return t

def boltz_tensor(ek,q):
    """ Boltzmann factor matrix for interaction bond of q-state
        Potts model for the Jones polynomial. Diagonal terms are
        set to ek (in general complex). Off-diagonal terms are set
        to 1. Some diagonal entries are later turned to ek**(-1)
        according to the Tait sign of the corresponding edge in
        the Tait graph. This is done with boltz_entry() when the
        tensor network is built. """
    b = ones([q,q],dtype=complex)
    b[diag_indices(q)] = ek*ones(q)
    return b

def boltz_entry(b,q,i,m):
    """ Enforce Tait sign convention in Boltzmann tensor. """
    return b[unravel_index(i,shape(b))]**((-1)**(m+1))

def boltz_tngraph(c,ek,q,dtype=complex):
    """ Constructs graph object endowed with variable and
        interaction tensors corresponding to q-state Potts model
        on graph dictated by signed edge list c. A positive sign
        in an entry of c means a positive Tait sign, and in turn
        a ek bond. Negative sign is a ek**(-1) bond. """
    b  = boltz_tensor(ek,q)
    gt = lambda i,m: boltz_entry(b,q,i,m)
    g  = cnf_tngraph(c,q,gate=gt,dtype=dtype)
    return g

def DeltaH_greedy(c):
    """ Returns maximal degree encountered during greedy
        contraction of the Tait graph encoded in edgelist c. """
    nc = len(c)  # number of crossings
    q=1
    if nc>0:
        nv=cnf_nvar(c)       
        ekpotts=-tpotts(q)  # Potts interaction for Jones
        g=boltz_tngraph(c,ekpotts,q)
        b,gn = contract_greedy(g,combine_attrs=None)
        maxdeg=max(b)
    else:
        nv=1
        maxdeg=1
    
    return maxdeg

def DeltaH_METIS(c):
    """ Returns maximal degree encountered during METIS
        contraction of the Tait graph encoded in edgelist c. """
    nc = len(c)  # number of crossings
    q=1
    if nc>0:
        nv=cnf_nvar(c)       
        ekpotts=-tpotts(q)  # Potts interaction for Jones
        g=boltz_tngraph(c,ekpotts,q)
        m = recursive_bipartition(g)
        md,sg = contract_dendrogram(g,m,combine_attrs=None)
        maxdeg=max(md)
    else:
        nv=1
        maxdeg=1
    
    return maxdeg

def Jones_greedy(c,tau,w,q):
    """ Returns Jones polynomial evaluated at t(q) via greedy
        contraction of the tensor network of the knot encoded
        in edgelist c. w is the writhe of the knot. """
    nc = len(c)  # number of crossings
    if nc>0:
        nv=cnf_nvar(c)       
        ekpotts=-tpotts(q)
        g=boltz_tngraph(c,ekpotts,q)
        t1=default_timer()
        b,gn = contract_greedy(g,combine_attrs=dict(attr=attr_contract))
        t2=default_timer()
        runtime=t2-t1
        Z=gn.vs["attr"][0][1]
    else:
        nv=1
        Z=q
        runtime=0
    # Multiply Z with appropriate prefactors to get Jones polynomial:
    jpoly =  Z * (-tpotts(q)**.5-tpotts(q)**-.5)**(-nv-1) * (-tpotts(q)**(3./4))**w * tpotts(q)**(1./4*tau)
    return jpoly,runtime

def Jones_METIS(c,tau,w,q):
    """ Returns Jones polynomial evaluated at t(q) via METIS
        contraction of the tensor network of the knot encoded
        in edgelist c. w is the writhe of the knot. """
    nc = len(c)  # number of crossings
    if nc>0:
        nv=cnf_nvar(c)       
        ekpotts=-tpotts(q)
        g=boltz_tngraph(c,ekpotts,q)
        t1=default_timer()
        m = recursive_bipartition(g)    # Uses METIS
        md,sg = contract_dendrogram(g,m,combine_attrs=dict(attr=attr_contract))
        t2=default_timer()
        runtime=t2-t1
        Z=sg.vs["attr"][0][1]
    else:
        nv=1
        Z=q
        runtime=0
    # Multiply Z with appropriate prefactors to get Jones polynomial:
    jpoly =  Z * (-tpotts(q)**.5-tpotts(q)**-.5)**(-nv-1) * (-tpotts(q)**(3./4))**w * tpotts(q)**(1./4*tau)
    return jpoly,runtime

