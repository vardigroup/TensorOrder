FROM python:3.7-slim

ADD http://glaros.dtc.umn.edu/gkhome/fetch/sw/metis/metis-5.1.0.tar.gz /solvers/metis-5.1.0.tar.gz
ENV METIS_DLL=/solvers/metis-5.1.0/build/Linux-x86_64/libmetis/libmetis.so

RUN apt-get clean \
&& cd /var/lib/apt \
&& mv lists lists.old \
&& mkdir -p lists/partial \
&& apt-get update \
&& apt-get upgrade -y \
&& mkdir -p /usr/share/man/man1 \
&& apt-get -y install g++ make libxml2-dev zlib1g-dev cmake openjdk-11-jdk libopenblas-dev \
&& cd /solvers/ \
&& tar -xvf metis-5.1.0.tar.gz \
&& rm metis-5.1.0.tar.gz \
&& cd /solvers/metis-5.1.0 \
&& make config shared=1 \
&& make \
&& make install \
&& pip install click==7.1.2 numpy python-igraph networkx==2.1.0 metis turbine cython threadpoolctl

COPY solvers/htd-master /solvers/htd-master
RUN cd /solvers/htd-master \
&& cmake . \
&& make

COPY solvers/TCS-Meiji /solvers/TCS-Meiji
RUN cd /solvers/TCS-Meiji \
&& make heuristic

COPY solvers/flow-cutter-pace17 /solvers/flow-cutter-pace17
RUN cd /solvers/flow-cutter-pace17 \
&& chmod +x ./build.sh \
&& ./build.sh

COPY solvers/hicks /solvers/hicks
RUN cd /solvers/hicks \
&& make

COPY solvers/portfolio /solvers/portfolio
RUN cd /solvers/portfolio \
&& make

COPY src /src
RUN cd /src \
&& make
