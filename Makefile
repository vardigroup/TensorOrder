export TENSORORDER_DIR=$(dir $(abspath $(lastword $(MAKEFILE_LIST))))

tensororder: Singularity
	singularity build tensororder Singularity
	
clean:
	rm tensororder
