# TensorOrder
A Python 3 tool for automatically contracting tensor networks for weighted model counting.

## Running with Singularity
Because of the variety of dependencies used in the various tree decomposition tools, it is recommended to use the [Singularity](https://www.sylabs.io/) container to run TensorOrder.

### Building the container
The container can be built with the following commands (make requires root to build the Singularity container):
```
git clone https://github.com/vardigroup/TensorOrder.git
cd TensorOrder
sudo make
```

### Usage
Once built, example usage is:
```
./tensororder --method="line-Flow" < "benchmarks/cubic_vertex_cover/cubic_vc_50_0.cnf"
```


## Running without Singularity
TensorOrder can also be used directly as a Python 3 tool. The primary script is located in `src/tensororder.py`. Example usage is
```python src/tensororder.py --method="line-Flow" < "benchmarks/cubic_vertex_cover/cubic_vc_50_0.cnf" ```

TensorOrder requires the following python packages (see [requirements.txt](requirements.txt) for a working set of exact version information if needed):
1. `click`
2. `numpy`
3. `python-igraph`
4. `networkx`
5. `cached_property`

Moreover, the various tensor methods each require additional setup.
* For KCMR-metis and KCMR-gn, METIS must be installed using the instructions [here](src/tensorcsp).
* For line-Tamaki and factor-Tamaki, the tree-decomposition solver Tamaki must be compiled using the `heuristic` instructions [here](solvers/TCS-Meiji).
* For line-Flow and factor-Flow, the tree-decomposition solver FlowCutter must be compiled using the instructions [here](solvers/flow-cutter-pace17).
* For line-htd and factor-htd, the tree-decomposition solver htd must be compiled using the instructions [here](solvers/htd-master).