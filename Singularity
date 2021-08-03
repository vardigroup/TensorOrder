Bootstrap: docker
From: python:3.7-slim

%setup
    cp -R ${TENSORORDER_DIR-$PWD}/solvers ${SINGULARITY_ROOTFS}/solvers
    cp -R ${TENSORORDER_DIR-$PWD}/src ${SINGULARITY_ROOTFS}/src
    wget http://glaros.dtc.umn.edu/gkhome/fetch/sw/metis/metis-5.1.0.tar.gz -P ${SINGULARITY_ROOTFS}/solvers/

%post
    apt-get update

    # TensorOrder
    apt-get -y install g++ make libxml2-dev zlib1g-dev libopenblas-dev
    pip install click==7.1.2 numpy python-igraph networkx==2.1.0 cython threadpoolctl

    # METIS
    apt-get -y install g++ make cmake
    cd /solvers/
    tar -xvf metis-5.1.0.tar.gz
    rm metis-5.1.0.tar.gz
    cd /solvers/metis-5.1.0
    make config shared=1
    make
    make install
    pip install metis

    # TCS-Meiji
    # deal with slim variants not having man page directories (which causes "update-alternatives" to fail)
    mkdir -p /usr/share/man/man1
    apt-get install -y make openjdk-11-jdk
    cd /solvers/TCS-Meiji
    make heuristic
    
    # FlowCutter
    apt-get -y install g++
    cd /solvers/flow-cutter-pace17
    chmod +x ./build.sh
    ./build.sh

    # Htd
    apt-get -y install g++ cmake
    cd /solvers/htd-master
    cmake .
    make

    # Hicks solver
    cd /solvers/hicks
    make

    # Portfolio Solver
    cd /solvers/portfolio
    make

    # Tensororder
    cd /src
    make

%environment
    export METIS_DLL=/solvers/metis-5.1.0/build/Linux-x86_64/libmetis/libmetis.so

%help
    This is a Singularity container for the TensorOrder tool.
    See "$SINGULARITY_NAME --help" for usage.

%runscript
    export TENSORORDER_CALLER="$SINGULARITY_NAME"
    exec python /src/tensororder.py "$@"


