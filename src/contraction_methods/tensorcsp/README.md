# **tensorCSP**

tensorCSP is a small collection of Python functions for casting constraint satisfaction problems into tensor networks and basic implementations of algorithms for full contraction of the resulting tensor networks. Concepts from algorithmic graph theory and network theory, namely graph partitioning and community structure detection, are used to determine advantageous contraction sequences for arbitrary graphs of tensors.

The methods implemented in tensorCSP are described in:

* S. Kourtis, C. Chamon, E. R. Mucciolo, and A. E. Ruckenstein, *Fast counting with tensor networks*, [arXiv:1805.00475](https://arxiv.org/abs/1805.00475)

# **Prerequisites**

* [numpy](http://www.numpy.org/)
* [igraph](http://igraph.org/python/)
* [METIS](http://glaros.dtc.umn.edu/gkhome/metis/metis/overview)
* [METIS for Python](https://metis.readthedocs.io)

The respective websites provide instructions on installation of the above prerequisites. Note that METIS needs to be configured and compiled as a shared library with:
```
make config shared=1
```
and that the METIS for Python wrapper requires setting the environment variable **METIS_DLL** to point to libmetis.so (or whatever the shared object filename is). With bash this is achieved by issuing the command:
```
export METIS_DLL=/path/to/libmetis.so
```
where `/path/to/` should be replaced with the actual location of the library (presumably `/usr/local/lib/` for a global installation on a Linux system).

# **Installation**

None needed. Just launch an [ipython](https://ipython.org) terminal (recommended) in the directory of tensorCSP and execute:
```
run tensorcsp.py
```

# **Documentation**

The scripts are commented and an example script is provided that illustrates some of the functionality.
