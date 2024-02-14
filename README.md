# SW4ML-cw3

## docker
assume the simulator will run outside of docker
* python simulator.py

build docker image
* docker build -t cw3 .

set docker environment variables for running
* docker run -e MLLP_ADDRESS=host.docker.internal:8440 -e PAGER_ADDRESS=host.docker.internal:8441 cw3

if run locally
* dockerfile: --local=True
