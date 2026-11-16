# Islamabad Weather Email — Azure Function

A Python Azure Function that fetches Islamabad's current weather from Open-Meteo and sends a daily email through Azure Communication Services. Azure infrastructure is managed with Terraform. Function is deployed to Azure cloud and also has a live weather UI.

**Result:** Email delivered successfully on Wednesday 11 Nov 2026 and Thursday 12 Nov 2026.

---

## How It Works

1. Timer fires every day at **09:00 Pakistan time** (04:00 UTC)
2. Python function calls **Open-Meteo API** for Islamabad weather
3. Builds a readable sentence: *"Weather in Islamabad: 24°C, Partly cloudy. Feels like 25°C; humidity 40%; wind 8 km/h."*
4. Sends that sentence as an email via **Azure Communication Services**

There is also a **live weather UI** and a **manual send button**:
- Open the page → see current weather with stat cards, weather icon, 3-day forecast, and local Islamabad time
- Click **Send Weather Email** → sends the email instantly without waiting for the timer

**Live weather UI:** `https://func-islamabad-weather.azurewebsites.net/api/weather`

---

## File Structure

```
terraform-azure-weather/
├── main.tf                  — Terraform: all Azure resources
├── .terraform.lock.hcl      — Terraform: pins provider version (commit this)
├── terraform.tfstate        — Terraform state (PRIVATE — not in git)
└── function-app/
    ├── function_app.py      — Timer trigger + weather UI + manual send-email endpoint
    ├── weather.py           — Calls Open-Meteo; get_weather_summary() for email, get_weather_full() for UI
    ├── requirements.txt     — Python packages
    ├── host.json            — Azure Functions runtime settings
    └── local.settings.json  — Local settings (PRIVATE — not in git)
```

---

## Azure Resources Created by Terraform

| Resource | Purpose |
|---|---|
| `rg-islamabad-weather` | Resource group — holds everything |
| `acs-email-islamabad-weather` | Email Communication Service |
| `AzureManagedDomain` | Free Azure email domain (`*.azurecomm.net`) |
| `weather@...` sender username | Sender address shown in email |
| `acs-islamabad-weather` | Communication Service — provides the connection string |
| `stislwxc8992e09` | Storage account — required by Function App |
| `asp-islamabad-weather` | App Service Plan (Consumption/serverless) |
| `func-islamabad-weather` | Linux Function App — runs the code in Azure cloud |

---

## Key Commands

```powershell
# Terraform
terraform init                  # download provider
terraform plan                  # preview changes
terraform apply                 # create/update resources in Azure
terraform output                # show outputs (URL, sender address)
terraform destroy               # delete everything

# Deploy function code to Azure
cd function-app
func azure functionapp publish func-islamabad-weather

# Run locally (needs Azurite running in another terminal)
$env:AZURE_COMMUNICATION_CONNECTION_STRING = "<from Azure portal>"
$env:SENDER_EMAIL    = "<terraform output weather_sender_address>"
$env:RECIPIENT_EMAIL = "<your email>"
func start

# Trigger timer manually (sends a real email)
Invoke-RestMethod -Method Post -Uri "http://localhost:7071/admin/functions/islamabad_weather_timer" -ContentType "application/json" -Body "{}"
```

---

## How to Make Changes

### Change the Timer Schedule

Edit `function-app/function_app.py` line 11:

```python
schedule="0 0 5 * * *"
```

Change the hour number (Azure uses **UTC** — Pakistan is UTC+5):

| Email at (Pakistan) | UTC | Schedule value |
|---|---|---|
| 9:00 AM | 04:00 | `"0 0 4 * * *"` |
| 8:00 AM | 03:00 | `"0 0 3 * * *"` |
| 6:00 AM | 01:00 | `"0 0 1 * * *"` |

After editing, push to GitHub — GitHub Actions automatically redeploys to Azure.

### Change the Recipient Email

**Option A — Azure Portal (instant, no redeployment):**
1. Go to `func-islamabad-weather` in Azure portal
2. Left menu → Settings → Environment variables
3. Find `RECIPIENT_EMAIL` → change the value → Save

**Option B — Terraform (permanent):**
```powershell
terraform apply -var="acs_connection_string=YOUR_STRING" -var="recipient_email=newemail@gmail.com"
```

**Rule of thumb:**
- Schedule change → edit code → push to GitHub → auto-deploys
- Email change → change in Azure portal → instant, no code push needed

---

## Important Q&A

**Q: What does the project do?**
Sends Islamabad's current weather by email every day at 09:00 Pakistan time. It also has a live weather UI page showing current conditions with stat cards, a weather icon, 3-day forecast, and local Islamabad time — plus a button to send the email manually on demand. Python gets the data from Open-Meteo, Azure Functions runs it, and Azure Communication Services sends the email.

**Q: What is a timer trigger and explain the schedule?**
A timer trigger runs the function on a cron schedule. The schedule `0 0 4 * * *` means: second 0, minute 0, hour 4, every day. Azure uses UTC, and 04:00 UTC = 09:00 Pakistan time (UTC+5).

**Q: Why Open-Meteo?**
It is free and needs no API key, so there is no secret to manage for the weather part.

**Q: What is Terraform and why use it?**
Infrastructure as Code tool. I describe Azure resources in `.tf` files and Terraform creates them. Benefits: repeatable, version-controlled, preview changes with `plan`, remove everything with `destroy`.

**Q: What is the Terraform state file?**
`terraform.tfstate` is Terraform's memory of what it created. It contains sensitive values like ACS access keys, so it is in `.gitignore`. In a team, store it in a remote Azure Storage backend.

**Q: How is the email sent?**
Using `azure-communication-email` SDK. Create `EmailClient` from connection string, build message object, call `begin_send()`, wait for `.result()`. If status is not `"Succeeded"` the function raises an error.

**Q: What happens if a setting is missing?**
The function checks all three environment variables first. If any is missing, it raises a `ValueError` with a clear message instead of failing later with a confusing error.

**Q: What problems did you face?**
Two problems. First: `terraform apply` failed because `Microsoft.Communication` provider was not registered — fixed with `az provider register --namespace Microsoft.Communication`. Second: email send failed with invalid connection string — fixed by checking the format and setting variables in the same PowerShell window as `func start`.

**Q: How many functions are in function_app.py?**
Three. `islamabad_weather_timer` — runs on a cron schedule and sends the email automatically. `weather_ui` — HTTP GET that returns the weather page with stat cards, icon, 3-day forecast, and local time. `send_weather_email` — HTTP POST called by the button on the page to send the email on demand.

**Q: Is the function running in the cloud?**
Yes. The Function App `func-islamabad-weather` is deployed to Azure (Central India, Consumption plan). The weather UI is live at `https://func-islamabad-weather.azurewebsites.net/api/weather`. Code was deployed using `func azure functionapp publish` and GitHub Actions handles future deployments automatically.

**Q: How do you delete everything?**
Run `terraform destroy` — it removes all Azure resources. Or delete the resource group `rg-islamabad-weather` from the Azure portal.

---

## Security

- No secrets in code — all read from environment variables
- `terraform.tfstate` is in `.gitignore` — it contains ACS keys in plain text
- `.terraform.lock.hcl` is committed — it pins the provider version
- GitHub Actions secrets store `AZURE_CREDENTIALS`, `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`
