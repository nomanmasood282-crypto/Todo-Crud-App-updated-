# Islamabad Weather Email on Azure: Progress Guide

> 📘 New here? Read [PROJECT_EXPLAINED.md](PROJECT_EXPLAINED.md) for the full explanation, and [EVALUATION_QA.md](EVALUATION_QA.md) to prepare for the evaluation.

## Goal

A Python Azure Function fetches current Islamabad weather from Open-Meteo and sends a daily email through Azure Communication Services (ACS) Email. Terraform manages the Azure resources. The Azure work is kept separate from the To-Do application.

## Completed ✅

- [x] Azure CLI login and the Terraform Azure provider checked against the active subscription.
- [x] Local Azure Functions Python v2 project created in `function-app` with Core Tools v4.
- [x] `weather.py` fetches current Islamabad weather from Open-Meteo.
- [x] `function_app.py` has a daily timer at 09:00 Pakistan time (`0 0 4 * * *` UTC).
- [x] Local test with Azurite: the timer fetched and logged the weather.
- [x] ACS Email sending added. Settings are read from `AZURE_COMMUNICATION_CONNECTION_STRING`, `SENDER_EMAIL` and `RECIPIENT_EMAIL`.
- [x] Terraform created the resource group, Communication Service, Email Communication Service, Azure-managed email domain, sender username and domain association.
- [x] Fixed: `Microsoft.Communication` resource provider not registered (registered it, then re-ran apply).
- [x] Fixed: invalid connection string, and environment variables set in a different PowerShell window.
- [x] **Email delivered successfully** on Wednesday 11 Nov 2026 and Thursday 12 Nov 2026. 🎉
- [x] `.gitignore` covers Terraform state, `.terraform/`, `local.settings.json`, `.venv/` and Azurite data.
- [x] Project documentation and evaluation Q&A written.

## Current Status

- **Working end to end:** weather → function → ACS → inbox.
- The **function runs locally** (`func start`). The Azure Function App itself is **not yet deployed** with Terraform.

## How to run it again (local)

```powershell
# 1. Start Azurite (local storage emulator) in its own terminal
azurite

# 2. In ONE PowerShell window, set the settings (never commit these)
cd terraform-azure-weather\function-app
.\.venv\Scripts\Activate.ps1
$env:AZURE_COMMUNICATION_CONNECTION_STRING = "<ACS connection string>"
$env:SENDER_EMAIL    = "<terraform output weather_sender_address>"
$env:RECIPIENT_EMAIL = "<recipient email>"

# 3. Start the function host in the SAME window
func start

# 4. Optional: trigger the timer now instead of waiting for 09:00 (sends a real email)
Invoke-RestMethod -Method Post -Uri "http://localhost:7071/admin/functions/islamabad_weather_timer" -ContentType "application/json" -Body "{}"
```

## Next Steps (optional improvements)

1. Add the Azure Function App, storage account and plan to Terraform. Review `terraform plan` and the cost, then deploy only after approval.
2. Move Terraform state to a remote Azure Storage backend.
3. Move secrets into Function App settings or Key Vault.
4. Add `variables.tf` and outputs for the names that are currently written directly in `main.tf`.
5. Commit the project folder, including `.terraform.lock.hcl`, but **not** the state files.

## Safety

- Azure Free Trial credit is limited. Email and cloud resources may use it, and usage after the credit runs out may need paid billing.
- Terraform state contains the ACS connection strings and keys in plain text. Keep state files private. `.gitignore` excludes them.
- Never share credentials, connection strings, keys, or unredacted subscription IDs.
- To remove everything: `terraform destroy`.
