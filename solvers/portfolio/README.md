# Portfolio Tree Decomposer
This repository contains a very simple portfolio tree decomposition solver.

The solver can be built with the following commands.
```
make
```

Once build, usage is described as follows.
```
$ ./build/portfolio --help
./build/portfolio [GRAPH] [SOLVER]*
Run all SOLVER commands in parallel with the file [GRAPH] as stdin.
Prints all decompositions output by the SOLVERs, separated by '=\n'.
```
