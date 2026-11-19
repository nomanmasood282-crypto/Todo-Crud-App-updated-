# terraform-aks — AKS cluster for the Todo app

Creates a small Azure Kubernetes Service (AKS) cluster for the Todo app, plus a budget alert.
Independent from `terraform-azure-weather/`: own resource group, own state file.

## What it creates

| Resource | Name | Notes |
|---|---|---|
| Resource group | `rg-todo-aks` | South India |
| AKS cluster | `aks-todo` | Free tier, 1 node, fixed size, no autoscaling, no zones |
| Budget alert | `budget-todo-aks` | $150/month, emails at 80% and 100% |

State is stored in the existing storage account `sttfstatec8992e09` (`rg-tfstate`) under the key `todo-aks.tfstate`.

## Why these choices

The subscription is a **free trial**:

- **Region:** Central India blocks every VM size for this subscription. **South India** allows them.
- **Quota:** 4 vCPUs per region, so at most 2 nodes of 2 vCPU.
- **Node size:** `Standard_D2as_v5` (2 vCPU / 8 GB). The cheap B-series sizes are not offered in South India.
- **No autoscaling or auto-upgrade:** an upgrade needs a spare node, which would not fit the quota and would cost extra credit.
- **Cost:** about $0.121/hour per node, roughly $64 for 22 days always-on. Stop the cluster when you are not using it.

## Run it (PowerShell, from this folder)

```powershell
# 1. Log in and confirm the subscription
az login
az account show --query name -o tsv

# 2. Set your alert email (terraform.tfvars is git-ignored)
Copy-Item terraform.tfvars.example terraform.tfvars
notepad terraform.tfvars

# 3. Download providers and connect to the remote state
terraform init

# 4. READ the plan before applying: it lists everything that will be created
terraform plan

# 5. Create it (type "yes"). Takes about 5-10 minutes.
terraform apply

# 6. Add the cluster to kubectl and check it
az aks get-credentials --resource-group rg-todo-aks --name aks-todo
kubectl config current-context        # should print aks-todo
kubectl get nodes                     # 1 node, STATUS Ready
```

`kubectl` now points at AKS. Your local cluster is still there:

```powershell
kubectl config get-contexts
kubectl config use-context k3d-todo-cluster   # back to local
kubectl config use-context aks-todo           # back to AKS
```

Always check `kubectl config current-context` before running a command.

## Save credit

```powershell
az aks stop  --resource-group rg-todo-aks --name aks-todo   # stops the node billing
az aks start --resource-group rg-todo-aks --name aks-todo
```

A stopped cluster still pays a little for disks. Note that Postgres data lives on a disk inside the cluster.

## Tear down

Take a database dump first if you want to keep the data, then:

```powershell
terraform destroy
```

This removes only the AKS resources. The weather project and the state storage are not touched.
