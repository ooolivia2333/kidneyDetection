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

## Kubernetes
* docker build --platform=linux/x86-64 -t imperialswemlsspring2024.azurecr.io/coursework4-trinity .
* docker push imperialswemlsspring2024.azurecr.io/coursework4-trinity
* kubectl delete deployment aki-detection -n trinity
* kubectl apply -f coursework4.yaml

To check port
* kubectl get pods -n trinity

To forward prometheus to local port (then access via http://localhost:8000)
* kubectl -n trinity port-forward {port_name} 8000:8000

