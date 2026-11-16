# Prometheus & Grafana — Monitoring Setup

Prometheus and Grafana are installed via the `kube-prometheus-stack` Helm chart in the `monitoring` namespace. Prometheus collects metrics from the cluster, and Grafana displays them as dashboards.

**Chart:** `kube-prometheus-stack-91.8.2`
**Namespace:** `monitoring`
**Helm release name:** `monitoring`

---

## What is Running in the Cluster

| Pod | Purpose |
|-----|---------|
| `prometheus-monitoring-kube-prometheus-prometheus-0` | Collects and stores metrics |
| `monitoring-grafana-...` | Dashboard UI |
| `alertmanager-...` | Handles alerts |
| `monitoring-kube-state-metrics-...` | Exposes cluster state metrics |
| `monitoring-prometheus-node-exporter-...` (x3) | Collects node-level metrics |

---

## Why No Big Config File?

Prometheus and Grafana were installed with default settings using the Helm chart. The `values.yaml` here shows the key settings — the chart itself handles all the complex configuration internally.

---

## Install From Scratch (if needed)

```powershell
# Step 1 — Add the Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Step 2 — Create the namespace
kubectl create namespace monitoring

# Step 3 — Install using values.yaml from this folder
helm install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring \
  -f monitoring/values.yaml

# Step 4 — Wait for all pods to be ready
kubectl get pods -n monitoring -w
```

---

## Check They Are Running

```powershell
# Check all monitoring pods
kubectl get pods -n monitoring

# Check services
kubectl get svc -n monitoring

# Check Helm release
helm list -n monitoring
```

All pods should show `Running` status.

---

## Access Prometheus UI

```powershell
kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090
```
Open browser → `http://localhost:9090`

**What to check:**
- Go to **Status → Targets** — shows all things Prometheus is scraping
- Go to **Graph** tab → type `up` → click Execute — shows all running services
- Try a query: `container_cpu_usage_seconds_total` — shows CPU usage

---

## Access Grafana UI

```powershell
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
```
Open browser → `http://localhost:3000`

- **Username:** `admin`
- **Password:** `prom-operator`

**What to show your evaluator:**
1. Click **Dashboards** in the left menu
2. Open **"Kubernetes / Compute Resources / Cluster"** — shows CPU and memory of the whole cluster
3. Open **"Kubernetes / Compute Resources / Pod"** — shows per-pod resource usage
4. These dashboards are pre-built and come with the chart automatically

---

## Important Commands Summary

| Command | What it does |
|---|---|
| `kubectl get pods -n monitoring` | Check all monitoring pods are running |
| `kubectl get svc -n monitoring` | List all services and their ports |
| `helm list -n monitoring` | Show Helm release status and chart version |
| `kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80` | Open Grafana on localhost:3000 |
| `kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090` | Open Prometheus on localhost:9090 |
| `kubectl logs -n monitoring prometheus-monitoring-kube-prometheus-prometheus-0` | View Prometheus logs |
| `kubectl logs -n monitoring -l app.kubernetes.io/name=grafana` | View Grafana logs |

---

## What to Tell Your Evaluator

**Q: What is Prometheus?**
> Prometheus is a monitoring tool that scrapes metrics from Kubernetes pods and nodes on a schedule and stores them. It tracks things like CPU usage, memory, pod restarts, and network traffic.

**Q: What is Grafana?**
> Grafana reads the metrics stored in Prometheus and displays them as visual dashboards. The kube-prometheus-stack chart comes with pre-built Kubernetes dashboards so you can see cluster health immediately.

**Q: How did you install them?**
> Using the `kube-prometheus-stack` Helm chart — a single Helm install command sets up Prometheus, Grafana, Alertmanager, and all the exporters together. The config is in `monitoring/values.yaml`.

**Q: Where are the files?**
> The `monitoring/values.yaml` file contains the configuration. The chart itself manages all the internal Kubernetes manifests. You can see the running resources with `kubectl get pods -n monitoring` and `helm list -n monitoring`.
