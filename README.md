
# SW4ML-cw3

## Run Docker Locally
* Dockerfile: `--local=True`

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
kubectl apply -f deployment.yaml
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
kubectl apply -f alerting-rules.yaml
```
Then restart prometheus server to fetch the newest alerting_rules
```bash
kubectl delete deployment prometheus -n trinity
kubectl apply -f prometheus-deployment.yaml
```

## Design Overview
1. using pandas, numpy to read and preprocess patients' data, and maintain it in a pd.df. including >10000 patients, >100000 blood test data
2. using XGBoost to build a decision tree model, to predict if a patient has AKI from his/her general info and historical blood test data. with >98% accuracy
3. using socket to read real-time blood testdata from simulator, predict simultaneously, and page to the hospital with low latency.
4. build docker image; write unit test, integration test, validation module; run and test automatically.
5. pushed docker image to Azure Kubernetes. add recovery mechanisms (store and reload csv files)
6. use prometheus and alertmanager to generate metrics, send alerts automatically. 