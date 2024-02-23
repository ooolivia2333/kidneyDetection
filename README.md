# SW4ML-cw3

## run docker locally
assume the simulator will run outside of docker
* python simulator.py

build docker image
* docker build -t cw3 .

set docker environment variables for running
* docker run -e MLLP_ADDRESS=host.docker.internal:8440 -e PAGER_ADDRESS=host.docker.internal:8441 -p 8000:8000 cw3

* dockerfile: --local=True

view localhost:8000 for metrics

## Kubernetes
* az loign
* az acr login --name imperialswemlsspring2024
* docker build --platform=linux/x86-64 -t imperialswemlsspring2024.azurecr.io/coursework4-trinity .
* docker push imperialswemlsspring2024.azurecr.io/coursework4-trinity
* kubectl delete deployment aki-detection -n trinity
* kubectl apply -f coursework4.yaml

To see logs
* kubectl logs --namespace=trinity -l app=aki-detection -n trinity

To check port
* kubectl get pods -n trinity

To forward prometheus to local port (then access via http://localhost:8000)
or simply access http://172.166.8.31:9090
* kubectl -n trinity port-forward {port_name} 8000:8000

