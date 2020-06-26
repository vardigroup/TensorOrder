export TENSORORDER_DIR=$(dir $(abspath $(lastword $(MAKEFILE_LIST))))

tensororder:
	python3 setup.py build_ext --inplace

docs:
	cython -3 -a decompositions/tree_decomposition.pyx
	cython -3 -a contraction_methods/contraction_tree.pyx
	cython -3 -a contraction_methods/factor_tree_method.pyx
	cython -3 -a tensor_network/tensor_network.pyx

clean:
	find . -name "*.c" -type f -delete
	find . -name "*.cpp" -type f -delete
	find . -name "*.o" -type f -delete
	find . -name "*.so" -type f -delete
	find . -name "*.html" -type f -delete
	rm -rf build
