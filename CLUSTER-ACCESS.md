# Cluster Access Cheat Sheet

Quick commands for Argo CD, Prometheus, Grafana and the Todo API on two clusters:

| Cluster | kubectl context | Where it runs |
|---|---|---|
| **AKS** (Azure) | `aks-todo` | Azure, South India. Does not need Docker |
| **k3d** (local) | `k3d-todo-cluster` | Your laptop. Needs Docker Desktop |

Sections 0-7 are for the **local k3d** cluster. The **AKS** section is at the end ([jump](#aks-azure)).
All commands are for **PowerShell**.

**Always check which cluster you are on before running anything:**
```powershell
kubectl config current-context
kubectl config use-context aks-todo            # or: k3d-todo-cluster
```

---

## 0. Before you start (local k3d)

```powershell
# Docker Desktop must be running. Then check the cluster:
k3d cluster list

# If todo-cluster is stopped, start it:
k3d cluster start todo-cluster

# Confirm kubectl points at the right cluster (should print k3d-todo-cluster):
kubectl config current-context
```

---

## 1. Quick reference

| Tool | Port-forward port | URL | Username | Password |
|---|---|---|---|---|
| Argo CD | 8080 | https://localhost:8080 | `admin` | from secret (section 2) |
| Grafana | 3000 | http://localhost:3000 | `admin` | from secret (section 3) |
| Prometheus | 9090 | http://localhost:9090 | none | none |

- Run **each port-forward in its own terminal** and keep it open. Closing the terminal closes the tunnel.
- The three ports are different, so all three can run at the same time.
- Argo CD uses HTTPS with a self-signed certificate. Chrome shows "Your connection is not private":
  click **Advanced → Proceed to localhost**. This is safe because the traffic stays on your laptop.

---

## 2. Argo CD

### Port-forward (terminal 1)
```powershell
kubectl port-forward svc/argocd-server -n argocd 8080:443
```
Open: **https://localhost:8080**

### Login
- **Username:** `admin`
- **Password:**
```powershell
$p = kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}"
[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($p))
```

### Check that the app is Synced and Healthy
```powershell
# Short view: look for SYNC STATUS = Synced and HEALTH STATUS = Healthy
kubectl get applications -n argocd

# Just the two values for todo-app-gitops
kubectl get application todo-app-gitops -n argocd -o jsonpath="Sync: {.status.sync.status}  Health: {.status.health.status}{'\n'}"

# Full details (events, errors, last sync time)
kubectl describe application todo-app-gitops -n argocd
```

### Check the Argo CD pods
```powershell
kubectl get pods -n argocd
```
All pods should show `1/1` under READY and `Running` under STATUS.

---

## 3. Grafana

### Port-forward (terminal 2)
```powershell
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
```
Open: **http://localhost:3000**

### Login
- **Username:** `admin`
- **Password:**
```powershell
$p = kubectl get secret monitoring-grafana -n monitoring -o jsonpath="{.data.admin-password}"
[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($p))
```
`monitoring/values.yaml` sets it to `prom-operator`, so this should print that.

### Check the Grafana pod
```powershell
kubectl get pods -n monitoring | Select-String grafana
```
It should show `3/3` under READY and `Running` under STATUS.

---

## 4. Prometheus

### Port-forward (terminal 3)
```powershell
kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090
```
Open: **http://localhost:9090**

### Login
**None.** Prometheus has no username or password.

### Check the Prometheus pod
```powershell
kubectl get pod prometheus-monitoring-kube-prometheus-prometheus-0 -n monitoring
```
It should show `2/2` under READY and `Running` under STATUS.

---

## 5. Optional: Alertmanager

```powershell
kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093
```
Open: **http://localhost:9093** (no login)

---

## 6. Check everything at once

```powershell
# All Argo CD pods
kubectl get pods -n argocd

# All monitoring pods (Prometheus, Grafana, Alertmanager, exporters)
kubectl get pods -n monitoring

# All services (shows the ClusterIP / NodePort type)
kubectl get svc -n argocd
kubectl get svc -n monitoring

# Argo CD app status
kubectl get applications -n argocd
```

---

## 7. Troubleshooting

| Problem | Fix |
|---|---|
| `Unable to connect to the server` | Docker Desktop is not running, or the cluster is stopped: `k3d cluster start todo-cluster` |
| `address already in use` | The port is busy. Use another local port, e.g. `8081:443` for Argo CD, then open `https://localhost:8081` |
| Page does not load | The port-forward terminal was closed. Run the command again |
| Pod is not `Running` | `kubectl describe pod <pod-name> -n <namespace>` and `kubectl logs <pod-name> -n <namespace>` |
| App is `OutOfSync` or `Degraded` | `kubectl describe application todo-app-gitops -n argocd` and read the Events and Conditions |

---

## Why port-forward?

Argo CD, Grafana and Prometheus run as **ClusterIP** services, which are reachable only inside the cluster.
`kubectl port-forward` opens a temporary tunnel from your laptop into the cluster, so the tools are not exposed publicly.

---

# AKS (Azure)

Cluster `aks-todo` in resource group `rg-todo-aks` (South India). It runs in Azure, so Docker Desktop is not needed and it keeps running when your laptop is off.
Everything is `ClusterIP`, so you reach it with `kubectl port-forward`. Run **each port-forward in its own terminal** and keep it open.

## A1. Connect

```powershell
az login
az aks get-credentials --resource-group rg-todo-aks --name aks-todo   # once per machine
kubectl config use-context aks-todo
kubectl get nodes                                                      # 1 node, Ready
```

## A2. Quick reference

Docker Desktop (k3d) already uses local ports 8000 and 8080, so the AKS tunnels use different ones.

| Tool | Port-forward command | URL | Login |
|---|---|---|---|
| Todo API / Swagger | `kubectl port-forward -n todo-gitops svc/todo-app-api 8002:8000` | http://localhost:8002/docs | an app user (e.g. `noman`, admin) |
| Argo CD | `kubectl port-forward svc/argocd-server -n argocd 8081:443` | https://localhost:8081 | `admin` / secret below |
| Grafana | `kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80` | http://localhost:3000 | `admin` / the password set at install |
| Prometheus | `kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090` | http://localhost:9090 | none |

"Failed to fetch" in Swagger or "connection refused" in the browser almost always means that port-forward terminal was closed or dropped. Start it again.

Argo CD password (AKS has its own, different from k3d):
```powershell
$p = kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}"
[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($p))
```

## A3. Health checks

```powershell
kubectl get applications -n argocd        # todo-app: Synced / Healthy
kubectl get pods -n todo-gitops           # API + Postgres: Running
kubectl get pods -n monitoring            # all Running
kubectl get pvc -n todo-gitops            # todo-app-postgres: Bound (managed-csi)
kubectl top node                          # memory/CPU of the single node
```

## A4. Using the API

- Click **Authorize** in Swagger and log in. Todo endpoints need a token.
- `GET /api/v1/todos/by-owner` returns only the logged-in user's todos. `GET /api/v1/todos/all` is admin only.
- There is no endpoint that lists users. To look at users, query the database:
```powershell
kubectl exec -n todo-gitops deploy/todo-app-postgres -- sh -c "psql -U `$POSTGRES_USER -d `$POSTGRES_DB -c 'select id, username, role from users order by id'"
```
(In PowerShell 5.1 keep SQL in single quotes inside a double-quoted string and escape `$` as `` `$ ``; embedded double quotes get stripped.)

## A5. Save credit

The node costs about $0.12/hour while the cluster runs. Stop it when you are not using it:
```powershell
az aks stop  --resource-group rg-todo-aks --name aks-todo
az aks start --resource-group rg-todo-aks --name aks-todo
```
The Postgres disk survives a stop. After `start`, wait a minute or two for pods to become Running.

## A6. Back up the database (do this before `terraform destroy`)

`terraform destroy` deletes the Azure Disk, so the data is lost unless you dump it first. Run from a folder outside the repo (the dump holds password hashes) and delete the file when done:
```powershell
Set-Location $env:TEMP
$pod = kubectl get pod -n todo-gitops -l app=todo-app-postgres -o jsonpath="{.items[0].metadata.name}"
kubectl exec -n todo-gitops $pod -- sh -c "pg_dump -U `$POSTGRES_USER -d `$POSTGRES_DB --no-owner --no-acl --clean --if-exists -f /tmp/todo.sql"
kubectl cp "todo-gitops/${pod}:/tmp/todo.sql" todo-dump.sql        # relative path: C:\ confuses kubectl cp
kubectl exec -n todo-gitops $pod -- rm /tmp/todo.sql
```
Restore into a fresh database the same way, in reverse (`kubectl cp` the file in, then `psql -v ON_ERROR_STOP=1 -f /tmp/todo.sql`), then delete the API pod so it reloads.

## A7. Tear down

```powershell
cd terraform-aks
terraform destroy        # removes rg-todo-aks, the cluster and the budget; weather project is untouched
```

## A8. Troubleshooting (AKS)

| Problem | Fix |
|---|---|
| `Unable to connect to the server` | Wrong context, or the cluster is stopped: `kubectl config use-context aks-todo`, `az aks start ...` |
| `address already in use` | Port taken (Docker Desktop holds 8000 and 8080). Use another local port |
| Swagger "Failed to fetch" | Port-forward closed. Start it again and reload the page |
| 403 on `/todos/all` | The user is not an admin |
| Postgres pod `CrashLoopBackOff` | Check `kubectl logs`. The chart sets `PGDATA` to a sub-folder because an Azure Disk has a `lost+found` folder |
| `terraform apply` fails with a network/DNS error mid-way | State may not have saved. Check for `errored.tfstate`, run `terraform state push errored.tfstate`, and `terraform untaint` the cluster if it was marked tainted. Do not re-apply first |
