# One-time setup: creates the Azure Storage container that holds Terraform state.
# Run this ONCE before `terraform init -migrate-state`. Safe to re-run.
#
# It lives in its own resource group (rg-tfstate) so `terraform destroy`
# on the weather project can never delete its own state.

$ErrorActionPreference = "Stop"

$ResourceGroup  = "rg-tfstate"
$Location       = "centralindia"
$StorageAccount = "sttfstatec8992e09"   # must match backend "azurerm" in main.tf
$Container      = "tfstate"

az group create --name $ResourceGroup --location $Location --output none

az storage account create `
  --name $StorageAccount `
  --resource-group $ResourceGroup `
  --location $Location `
  --sku Standard_LRS `
  --kind StorageV2 `
  --min-tls-version TLS1_2 `
  --allow-blob-public-access false `
  --output none

# Keep old versions of the state file so a bad apply can be rolled back.
az storage account blob-service-properties update `
  --account-name $StorageAccount `
  --resource-group $ResourceGroup `
  --enable-versioning true `
  --output none

az storage container create `
  --name $Container `
  --account-name $StorageAccount `
  --auth-mode login `
  --output none 2>$null
if ($LASTEXITCODE -ne 0) {
  # --auth-mode login needs a data-plane role; fall back to the account key.
  az storage container create `
    --name $Container `
    --account-name $StorageAccount `
    --account-key (az storage account keys list -g $ResourceGroup -n $StorageAccount --query "[0].value" -o tsv) `
    --output none
}

Write-Host "State storage ready: $StorageAccount/$Container"
Write-Host "Next: terraform init -migrate-state"
