terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 5.0"
    }
  }
}

provider "azurerm" {
  features {}
}

data "azurerm_client_config" "current" {}

variable "acs_connection_string" {
  description = "Azure Communication Services primary connection string (from az communication list-key)"
  type        = string
  sensitive   = true
  default     = ""
}

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

  site_config {
    application_stack {
      python_version = "3.11"
    }
  }

  app_settings = {
    AZURE_COMMUNICATION_CONNECTION_STRING = var.acs_connection_string
    SENDER_EMAIL                          = "weather@${azurerm_email_communication_service_domain.weather.from_sender_domain}"
    RECIPIENT_EMAIL                       = var.recipient_email
    WEBSITE_RUN_FROM_PACKAGE              = "1"
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