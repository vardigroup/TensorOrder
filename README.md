# TensorOrder
A Python 3 tool for automatically contracting tensor networks for weighted model counting on multiple CPUs and on a GPU.

## Running with docker
Because of the variety of dependencies used in the various graph decomposition tools, it is recommended to use the docker container to run TensorOrder.

### Building the container
The container (for singlecore and multi-core) can be built with the following commands:
```
docker build --tag tensororder .
```

In order to leverage a GPU, you must compile the (larger) docker container with TensorFlow and gpu drivers:
```
docker build --tag tensororder-gpu -f Dockerfile-gpu .
```

### Using the container
Once built, containers can be used as follows to run TensorOrder:
```
docker run -i tensororder:latest python /src/tensororder.py --method="line-Flow" < "benchmarks/cubic_vertex_cover/cubic_vc_50_0.cnf"
```

By default, this runs the tensor network contraction on all available CPU cores. One can also choose to use the GPU to perform the contraction:
```
docker run -i tensororder-gpu:latest python /src/tensororder.py --method="line-Flow" --tensor_library="tensorflow-gpu" < "benchmarks/cubic_vertex_cover/cubic_vc_50_0.cnf"
```

Both docker containers are compatible with [Turbine](https://github.com/Kasekopf/Turbine) to run experiments on Google Cloud.


## Running without containers
TensorOrder can also be used directly as a Python 3 tool. Since TensorOrder uses [Cython](https://cython.org/), it must be compiled:
```
make -C src
```

Moreover, the various tensor methods each require additional setup. Consult the [Docker file](Dockerfile) for an example set of installation commands.
* For KCMR-metis and KCMR-gn, METIS must be installed using the instructions [here](src/tensorcsp).
* For line-Tamaki and factor-Tamaki, the tree-decomposition solver Tamaki must be compiled using the `heuristic` instructions [here](solvers/TCS-Meiji).
* For line-Flow and factor-Flow, the tree-decomposition solver FlowCutter must be compiled using the instructions [here](solvers/flow-cutter-pace17).
* For line-htd and factor-htd, the tree-decomposition solver htd must be compiled using the instructions [here](solvers/htd-master).
* For factor-hicks, the branch-decomposition solver Hicks must be compiled using the Makefile [here](solvers/hicks).
* For line-portfolio3 and line-portfolio3, all tree-decompositions solvers must be compiled, and the portfolio must be compiled using the instructions [here](solvers/portfolio).

Once everything has been built, the primary script is located in `src/tensororder.py`. Example usage is
```
python src/tensororder.py --method="line-Flow" < "benchmarks/cubic_vertex_cover/cubic_vc_50_0.cnf"
```

TensorOrder requires the following python packages (see [requirements.txt](requirements.txt) for a working set of exact version information if needed):
1. `click`
2. `numpy`
3. `python-igraph`
4. `networkx`
5. `cython`
6. `threadpoolctl`
7. `tensorflow` (optional)
