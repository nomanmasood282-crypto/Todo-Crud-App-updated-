terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 5.0"
    }
  }

  # Remote state in Azure Blob Storage (like S3 + DynamoDB in AWS).
  # Blob leases give state locking automatically.
  # The storage account lives in its own resource group (created once by
  # bootstrap-state.ps1) so `terraform destroy` can never delete its own state.
  backend "azurerm" {
    resource_group_name  = "rg-tfstate"
    storage_account_name = "sttfstatec8992e09"
    container_name       = "tfstate"
    key                  = "islamabad-weather.tfstate"
  }
}

provider "azurerm" {
  features {}
}

data "azurerm_client_config" "current" {}

variable "recipient_email" {
  description = "Email address to receive daily weather reports"
  type        = string
  default     = ""
}

locals {
  storage_suffix = replace(substr(data.azurerm_client_config.current.subscription_id, 0, 8), "-", "")
}

resource "azurerm_resource_group" "weather" {
  name     = "rg-islamabad-weather"
  location = "Central India"
}

resource "azurerm_email_communication_service" "weather" {
  name                = "acs-email-islamabad-weather"
  resource_group_name = azurerm_resource_group.weather.name
  data_location       = "India"
}

resource "azurerm_email_communication_service_domain" "weather" {
  name              = "AzureManagedDomain"
  email_service_id  = azurerm_email_communication_service.weather.id
  domain_management = "AzureManaged"
}

resource "azurerm_email_communication_service_domain_sender_username" "weather" {
  name                    = "weather"
  email_service_domain_id = azurerm_email_communication_service_domain.weather.id
  display_name            = "Islamabad Weather"
}

resource "azurerm_communication_service" "weather" {
  name                = "acs-islamabad-weather"
  resource_group_name = azurerm_resource_group.weather.name
  data_location       = "India"
}

resource "azurerm_communication_service_email_domain_association" "weather" {
  communication_service_id = azurerm_communication_service.weather.id
  email_service_domain_id  = azurerm_email_communication_service_domain.weather.id
}

# ── Key Vault: holds the ACS connection string instead of a plain app setting ──

resource "azurerm_key_vault" "weather" {
  name                       = "kv-islwx-${local.storage_suffix}"
  resource_group_name        = azurerm_resource_group.weather.name
  location                   = azurerm_resource_group.weather.location
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  rbac_authorization_enabled = true
  soft_delete_retention_days = 7
  purge_protection_enabled   = false
}

# Lets whoever runs Terraform write secrets into the vault.
resource "azurerm_role_assignment" "kv_secrets_officer_deployer" {
  scope                = azurerm_key_vault.weather.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Taken straight from the ACS resource, so no secret is passed in by hand.
resource "azurerm_key_vault_secret" "acs_connection_string" {
  name         = "acs-connection-string"
  value        = azurerm_communication_service.weather.primary_connection_string
  key_vault_id = azurerm_key_vault.weather.id

  depends_on = [azurerm_role_assignment.kv_secrets_officer_deployer]
}

# Lets the Function App's managed identity read secrets (read-only).
resource "azurerm_role_assignment" "kv_secrets_user_function" {
  scope                = azurerm_key_vault.weather.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.function.principal_id
}

# User-assigned (not system-assigned) so its principal_id is known before the
# Function App is updated — lets the role assignment be planned in one apply.
resource "azurerm_user_assigned_identity" "function" {
  name                = "id-func-islamabad-weather"
  resource_group_name = azurerm_resource_group.weather.name
  location            = azurerm_resource_group.weather.location
}

resource "azurerm_storage_account" "weather" {
  name                     = "stislwx${local.storage_suffix}"
  resource_group_name      = azurerm_resource_group.weather.name
  location                 = azurerm_resource_group.weather.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_service_plan" "weather" {
  name                = "asp-islamabad-weather"
  resource_group_name = azurerm_resource_group.weather.name
  location            = azurerm_resource_group.weather.location
  os_type             = "Linux"
  sku_name            = "Y1"
}

resource "azurerm_linux_function_app" "weather" {
  name                = "func-islamabad-weather"
  resource_group_name = azurerm_resource_group.weather.name
  location            = azurerm_resource_group.weather.location

  storage_account_name       = azurerm_storage_account.weather.name
  storage_account_access_key = azurerm_storage_account.weather.primary_access_key
  service_plan_id            = azurerm_service_plan.weather.id

  # Managed identity used to read the Key Vault secret — no keys stored anywhere.
  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.function.id]
  }
  key_vault_reference_identity_id = azurerm_user_assigned_identity.function.id

  site_config {
    application_stack {
      python_version = "3.11"
    }
  }

  app_settings = {
    # Key Vault reference: Azure resolves this to the real value at runtime,
    # so the Python code still just reads os.environ as before.
    AZURE_COMMUNICATION_CONNECTION_STRING = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.acs_connection_string.versionless_id})"
    SENDER_EMAIL                          = "weather@${azurerm_email_communication_service_domain.weather.from_sender_domain}"
    RECIPIENT_EMAIL                       = var.recipient_email
    WEBSITE_RUN_FROM_PACKAGE              = "1"
  }

  # GitHub Actions (Azure/functions-action) rewrites these on every code deploy —
  # WEBSITE_RUN_FROM_PACKAGE becomes the URL of the deployed zip. Terraform must
  # not reset them, or the deployed code disappears.
  lifecycle {
    ignore_changes = [
      app_settings["WEBSITE_RUN_FROM_PACKAGE"],
      app_settings["PYTHON_ISOLATE_WORKER_DEPENDENCIES"],
      app_settings["WEBSITE_ENABLE_SYNC_UPDATE_SITE"],
    ]
  }
}

output "azure_subscription_selected" {
  value = length(data.azurerm_client_config.current.subscription_id) > 0
}

output "weather_sender_address" {
  value = "weather@${azurerm_email_communication_service_domain.weather.from_sender_domain}"
}

output "function_app_name" {
  value = azurerm_linux_function_app.weather.name
}

output "function_app_weather_url" {
  value       = "https://${azurerm_linux_function_app.weather.default_hostname}/api/weather"
  description = "Open this URL in a browser to see the live weather UI"
}