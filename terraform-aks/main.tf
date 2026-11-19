terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 5.0"
    }
  }

  # Remote state in the SAME storage account the weather project uses
  # (created once by terraform-azure-weather/bootstrap-state.ps1), but with its
  # OWN state key. Separate key = separate state, so `terraform destroy` here
  # can never touch the weather resources, and the reverse.
  backend "azurerm" {
    resource_group_name  = "rg-tfstate"
    storage_account_name = "sttfstatec8992e09"
    container_name       = "tfstate"
    key                  = "todo-aks.tfstate"
  }
}

provider "azurerm" {
  features {}
}

data "azurerm_client_config" "current" {}

locals {
  tags = {
    project = "todo-app"
    purpose = "training"
  }
}

# Own resource group, so everything for this cluster can be seen (and deleted)
# in one place without affecting rg-islamabad-weather.
resource "azurerm_resource_group" "aks" {
  name     = "rg-todo-aks"
  location = var.location
  tags     = local.tags
}

# ── The AKS cluster ────────────────────────────────────────────────────────────
# Sized for a free-trial subscription: regional quota is 4 vCPUs, and only some
# VM sizes are open to the subscription (see README).
resource "azurerm_kubernetes_cluster" "todo" {
  name                = "aks-todo"
  location            = azurerm_resource_group.aks.location
  resource_group_name = azurerm_resource_group.aks.name
  dns_prefix          = "aks-todo"
  tags                = local.tags

  # Free tier: the control plane costs nothing, you only pay for the nodes.
  sku_tier = "Free"

  # automatic_upgrade_channel is deliberately NOT set = no automatic upgrades.
  # An upgrade adds a temporary extra node ("surge"), which would not fit in a
  # 4 vCPU quota and would cost extra credit.

  default_node_pool {
    name    = "system"
    vm_size = var.node_vm_size

    # Fixed size on purpose: no autoscaler, so the cost can never grow by itself.
    node_count = var.node_count

    os_disk_size_gb = var.os_disk_size_gb

    # Azure fills this default in by itself. Stating it here keeps `terraform plan`
    # clean (no change). It only matters during an upgrade, which we don't do.
    upgrade_settings {
      max_surge = "10%"
    }

    # No availability zones: zonal capacity often fails on trial subscriptions
    # and is not needed for a training cluster.
  }

  # "Manual" = we pick the node size and count ourselves (what default_node_pool
  # above says). The alternative, "Auto", lets AKS create nodes on demand
  # (node auto-provisioning), which could spend credit we did not plan for.
  node_provisioning_profile {
    mode = "Manual"
  }

  # The cluster uses its own managed identity to create load balancers, disks, etc.
  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin    = "azure"
    network_policy    = "azure"
    load_balancer_sku = "standard"
  }
}

# ── Budget alert ───────────────────────────────────────────────────────────────
# Emails you when spending on the subscription reaches 80% and 100% of the budget.
# (Cost Management budgets only alert, they do not stop anything.)
resource "azurerm_consumption_budget_subscription" "trial" {
  name            = "budget-todo-aks"
  subscription_id = "/subscriptions/${data.azurerm_client_config.current.subscription_id}"

  amount     = var.budget_amount
  time_grain = "Monthly"

  time_period {
    start_date = var.budget_start_date
  }

  notification {
    enabled        = true
    threshold      = 80
    operator       = "GreaterThan"
    threshold_type = "Actual"
    contact_emails = [var.alert_email]
  }

  notification {
    enabled        = true
    threshold      = 100
    operator       = "GreaterThan"
    threshold_type = "Actual"
    contact_emails = [var.alert_email]
  }
}
