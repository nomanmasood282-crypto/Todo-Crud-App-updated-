# Todo-Crud-App-updated-

FastAPI Todo app with PostgreSQL, deployed with Helm and Argo CD (GitOps), monitored with Prometheus and Grafana.
It runs in two places:

| Environment | Cluster | Purpose |
|---|---|---|
| **Local** | k3d (`k3d-todo-cluster`, needs Docker Desktop) | development |
| **Azure** | AKS (`aks-todo`, South India, `rg-todo-aks`) | cloud deployment (training, free-trial credit) |

## Where things are

| Folder / file | What it is |
|---|---|
| `app/` | FastAPI application |
| `todo-app/` | Helm chart. `values.yaml` = local k3d, `values-aks.yaml` = AKS overrides |
| `argocd/` | Argo CD setup. `application-aks.yaml` + `apply-aks-app.ps1` deploy the app on AKS. See `argocd/README.md` |
| `monitoring/` | Prometheus + Grafana values and notes. See `monitoring/README.md` |
| `terraform-aks/` | Terraform for the AKS cluster and the budget alert. See `terraform-aks/README.md` |
| `terraform-azure-weather/` | Separate project: daily weather email on Azure Functions |
| `CLUSTER-ACCESS.md` | Day-to-day commands for both clusters (ports, passwords, stop/start, backups) |

## AKS at a glance

- Created with Terraform (`terraform-aks/`), 1 node `Standard_D2as_v5`, Free tier, fixed size.
- Argo CD (installed with Helm) deploys the chart from this repo's `main` branch.
- The API service is `ClusterIP`: not exposed publicly. Open Swagger with `kubectl port-forward`.
- Postgres data is on an Azure Disk (persistent volume, `managed-csi`). It survives pod restarts and `az aks stop`, but **not** `terraform destroy`: take a `pg_dump` first.
- Secrets are never committed. `argocd/apply-aks-app.ps1` asks for them and injects them at apply time.

Start with `CLUSTER-ACCESS.md`.
