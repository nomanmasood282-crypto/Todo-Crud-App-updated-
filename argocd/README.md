# ArgoCD — GitOps Setup

ArgoCD watches the GitHub repo and automatically keeps the Kubernetes cluster in sync with what Git says. Any change pushed to Git is applied to the cluster automatically. Any manual change made directly on the cluster is detected and reverted.

**Application name:** `todo-app-gitops`
**Namespace (ArgoCD):** `argocd`
**App namespace:** `todo-gitops`
**Repo watched:** `https://github.com/nomanmasood282-crypto/Todo-Crud-App-updated-`
**Path watched:** `todo-app/` (Helm chart)

---

## Argo CD on AKS (Azure)

Besides the local k3d cluster, the same chart is deployed on AKS by a second Argo CD installed on that cluster.

| | Local k3d | AKS |
|---|---|---|
| Application name | `todo-app-gitops` | `todo-app` |
| Values files | `values.yaml` | `values.yaml` + `values-aks.yaml` |
| API service | NodePort | ClusterIP |
| Postgres storage | `local-path` | `managed-csi` (Azure Disk) |
| Defined in | cluster only | `application-aks.yaml` |

**Install Argo CD on AKS** (lighter install for a single small node):
```powershell
kubectl config use-context aks-todo
helm repo add argo https://argoproj.github.io/argo-helm
helm install argocd argo/argo-cd -n argocd --create-namespace --set dex.enabled=false --set notifications.enabled=false
```

**Deploy the app.** Do not `kubectl apply` `application-aks.yaml` directly: it contains no secrets. Run the script, which asks for the admin login and generates random values for the Postgres password and `SECRET_KEY` if you leave them empty. Secrets go straight into the Application object in the cluster and never touch a file or Git.
```powershell
.\argocd\apply-aks-app.ps1          # add -DryRun to preview with secrets masked
kubectl get applications -n argocd  # wait for Synced / Healthy
```

**Open the AKS Argo CD UI** (port 8080 is often taken by Docker Desktop, so use 8081):
```powershell
kubectl port-forward svc/argocd-server -n argocd 8081:443
$p = kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}"
[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($p))    # password, user is admin
```
Open `https://localhost:8081`. Always check `kubectl config current-context` first: both clusters have an `argocd` namespace.

Because both Argo CD instances watch `main`, a push to `todo-app/` updates **both** clusters. Template changes must render identically for `values.yaml` (check with `helm template`).

---

## Requirements Before Starting

- Docker Desktop running with Kubernetes enabled
- ArgoCD already installed in the cluster
- Run this to confirm everything is up:

```powershell
kubectl get nodes
kubectl get pods -n argocd
```

All ArgoCD pods should show `Running`.

---

## Access the ArgoCD UI

**Step 1 — Port-forward the ArgoCD server:**
```powershell
kubectl port-forward svc/argocd-server -n argocd 8080:443
```
Keep this terminal open while using the UI.

**Step 2 — Get the login password:**
```powershell
kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}"
```
Copy the output, then decode it:
```powershell
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("PASTE_OUTPUT_HERE"))
```

**Step 3 — Open the browser:**
- URL: `https://localhost:8080`
- Username: `admin`
- Password: decoded value from Step 2

You will see the `todo-app-gitops` application with status **Synced** and **Healthy**.

---

## Test Option 1 — Auto Sync (Change in Git, ArgoCD applies it)

This shows ArgoCD detects Git changes and applies them to the cluster automatically.

**Step 1 — Change replicas in values.yaml:**

Open `todo-app/values.yaml` and change:
```yaml
replicaCount: 1
```
to:
```yaml
replicaCount: 2
```

**Step 2 — Push to GitHub:**
```powershell
git add todo-app/values.yaml
git commit -m "Test ArgoCD auto-sync: scale to 2 replicas"
git push origin main
```

**Step 3 — Watch ArgoCD apply the change:**
```powershell
kubectl get pods -n todo-gitops -w
```
Within 1-3 minutes a second `todo-app-api` pod will appear automatically.

**Step 4 — Verify:**
```powershell
kubectl get pods -n todo-gitops
```
You should see 2 `todo-app-api` pods running.

**Step 5 — Revert back when done:**

Change `replicaCount` back to `1` in `values.yaml`, then:
```powershell
git add todo-app/values.yaml
git commit -m "Revert replicas back to 1"
git push origin main
```
ArgoCD will scale back down to 1 automatically.

---

## Test Option 2 — Self-Heal (Manual change, ArgoCD reverts it)

This shows ArgoCD reverts any manual change that does not match Git. Git is the single source of truth.

**Step 1 — Manually scale the pods directly on the cluster (bypassing Git):**
```powershell
kubectl scale deployment todo-app-api --replicas=3 -n todo-gitops
```

**Step 2 — Confirm 3 pods are running:**
```powershell
kubectl get pods -n todo-gitops
```
You will see 3 `todo-app-api` pods.

**Step 3 — Watch ArgoCD revert it:**
```powershell
kubectl get pods -n todo-gitops -w
```
Within 1-2 minutes ArgoCD detects the cluster has 3 replicas but Git says 1 — it kills the 2 extra pods automatically.

**Step 4 — See the proof in the event logs:**
```powershell
kubectl get events -n todo-gitops --sort-by='.lastTimestamp'
```
You will see these lines:
```
ScalingReplicaSet   Scaled up replica set from 1 to 3     ← your manual change
ScalingReplicaSet   Scaled down replica set from 3 to 1   ← ArgoCD reverted it
SuccessfulDelete    Deleted pod: todo-app-api-...          ← extra pods removed
```

---

## Check ArgoCD Did Its Job

**Check application sync status:**
```powershell
kubectl get applications -n argocd
```
Should show `Synced` and `Healthy`.

**Check detailed application info:**
```powershell
kubectl describe application todo-app-gitops -n argocd
```
Look for `Sync Status: Synced` and `Health Status: Healthy`.

**Check events (proof of auto-sync and self-heal):**
```powershell
kubectl get events -n todo-gitops --sort-by='.lastTimestamp'
```

**Check running pods:**
```powershell
kubectl get pods -n todo-gitops
kubectl get all -n todo-gitops
```

---

## Important Commands Summary

| Command | What it does |
|---|---|
| `kubectl get applications -n argocd` | Show all ArgoCD applications and their sync status |
| `kubectl get pods -n argocd` | Check all ArgoCD pods are running |
| `kubectl get pods -n todo-gitops` | Check the deployed app pods |
| `kubectl get all -n todo-gitops` | Show all resources managed by ArgoCD |
| `kubectl get events -n todo-gitops --sort-by='.lastTimestamp'` | See sync and self-heal activity logs |
| `kubectl describe application todo-app-gitops -n argocd` | Full ArgoCD application details |
| `kubectl port-forward svc/argocd-server -n argocd 8080:443` | Open ArgoCD UI on localhost:8080 |
| `kubectl scale deployment todo-app-api --replicas=3 -n todo-gitops` | Manually scale to test self-heal |

---

## What to Tell Your Evaluator

**On auto-sync:**
> "ArgoCD watches the GitHub repo every 3 minutes. When I pushed a replica change to Git, ArgoCD detected it and applied it to the cluster automatically — no manual `kubectl apply` needed."

**On self-heal:**
> "I manually scaled the deployment to 3 replicas directly on the cluster. ArgoCD detected the drift between the cluster and Git within 19 seconds and reverted it back to 1. `selfHeal: true` is set in the application manifest, so Git is always the source of truth."
