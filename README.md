
# SW4ML-cw3

## Run Docker Locally
Assume the simulator will run outside of Docker:
```bash
python simulator.py
```

Build Docker image:
```bash
docker build -t cw3 .
```

Set Docker environment variables for running:
```bash
docker run -e MLLP_ADDRESS=host.docker.internal:8440 -e PAGER_ADDRESS=host.docker.internal:8441 -p 8000:8000 cw3
```

* Dockerfile: `--local=True`

View `localhost:8000` for metrics.

## Kubernetes
Login to Azure:
```bash
az login
```

Login to Azure Container Registry (ACR):
```bash
az acr login --name imperialswemlsspring2024
```

Build Docker image for Linux x86-64 platform:
```bash
docker build --platform=linux/x86-64 -t imperialswemlsspring2024.azurecr.io/coursework4-trinity .
```

Push Docker image to ACR:
```bash
docker push imperialswemlsspring2024.azurecr.io/coursework4-trinity
```

Delete existing Kubernetes deployment:
```bash
kubectl delete deployment aki-detection -n trinity
```

Apply Kubernetes configuration:
```bash
kubectl apply -f coursework4.yaml
```

To see logs:
```bash
kubectl logs --namespace=trinity -l app=aki-detection -n trinity
```

To check port:
```bash
kubectl get pods -n trinity
```

To forward Prometheus to local port (then access via http://localhost:8000) or simply access http://172.166.8.31:9090:
```bash
kubectl -n trinity port-forward {port_name} 8000:8000
```

To deploy alerting rules, first apply the alert rule yaml
```bash
kubectl apply -f alerting_rules.yaml
```
Then restart prometheus server to fetch the newest alerting_rules
```bash
kubectl delete deployment prometheus -n trinity
kubectl apply -f prometheus-deployment.yaml
```