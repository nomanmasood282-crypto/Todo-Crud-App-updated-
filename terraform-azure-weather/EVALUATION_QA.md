# Evaluation Prep: Islamabad Weather Email

Use this file to practise. Read the 2-minute pitch out loud, then go through the questions.
For the full details, see [PROJECT_EXPLAINED.md](PROJECT_EXPLAINED.md).

---

## The 2-minute pitch (say this first)

> "I built a project that sends me Islamabad's weather by email every morning.
>
> The code is a **Python Azure Function** with a **timer trigger** set to 9 AM Pakistan time. When it runs, it calls the free **Open-Meteo API** for Islamabad's current temperature, humidity and wind. It turns that into one readable sentence and sends it using **Azure Communication Services Email**.
>
> I created the Azure resources with **Terraform** instead of clicking through the portal: a resource group, an email service, an Azure-managed email domain, a sender address, a Communication Service, and the link between the domain and the service. So the setup is **repeatable and version-controlled**.
>
> I kept secrets out of the code. The connection string is read from **environment variables**, and the Terraform state file is in `.gitignore` because it contains keys.
>
> I fixed two problems along the way: the `Microsoft.Communication` provider wasn't registered on my subscription, and my first connection string setup was wrong.
>
> It works. I received the weather email on Wednesday and Thursday. Next, I'd deploy the Function App itself with Terraform so it runs in the cloud instead of on my laptop."

---

## Questions about the project

**Q: What does your project do?**
It emails Islamabad's current weather every day at 09:00 Pakistan time. Python gets the data from Open-Meteo, Azure Functions runs it on a schedule, and Azure Communication Services sends the email.

**Q: Why did you choose Azure Functions?**
It's **serverless**: I only write the function, and Azure handles the server. A timer trigger is perfect for "run once a day", and on the Consumption plan you only pay when it runs.

**Q: What is a timer trigger? Explain your schedule.**
It runs the function on a schedule written as a cron expression. Mine is `0 0 4 * * *`, which means second 0, minute 0, hour 4, every day. Azure uses **UTC**, and 04:00 UTC is **09:00 in Pakistan** (UTC+5).

**Q: Why Open-Meteo?**
It's free and needs no API key, so there's no secret to manage for the weather part.

**Q: How does the weather code become text like "Partly cloudy"?**
Open-Meteo returns a numeric `weather_code`. I map it to words with a Python dictionary, `WEATHER_DESCRIPTIONS`. If a code isn't in the dictionary, it says "Unknown conditions".

**Q: How is the email sent?**
With the `azure-communication-email` SDK. I create an `EmailClient` from the connection string, build a message (sender, recipient, subject, plain text), call `begin_send()`, and wait for `.result()`. If the status isn't `"Succeeded"`, the function raises an error.

**Q: What happens if a setting is missing?**
The function checks all three environment variables first. If any is missing, it raises a `ValueError` with a clear message instead of failing later with a confusing error.

**Q: Is it running in the cloud right now?**
Not yet, and I'd say so honestly. The **email resources are in Azure**, created by Terraform. The **function runs locally** with Azure Functions Core Tools (`func start`). Deploying a Function App with Terraform is my next step.

---

## Questions about Terraform

**Q: What is Terraform and why use it?**
It's an **Infrastructure as Code** tool. I describe the resources in `.tf` files, and Terraform creates, updates or deletes them to match. The benefits: it's repeatable, it's version-controlled in git, I can preview changes with `plan`, and I can remove everything with `destroy`.

**Q: Explain the main Terraform commands.**
| Command | What it does |
|---|---|
| `terraform init` | Downloads the providers (here `azurerm`) and prepares the folder |
| `terraform validate` | Checks the code for syntax errors |
| `terraform fmt` | Formats the code neatly |
| `terraform plan` | **Previews** what will be created, changed or destroyed, without changing anything |
| `terraform apply` | Actually makes the changes in Azure |
| `terraform output` | Shows output values (like my sender email) |
| `terraform state list` | Lists the resources Terraform manages |
| `terraform destroy` | Deletes everything Terraform created |

**Q: What is a provider?**
A plugin that lets Terraform talk to a platform. I used `hashicorp/azurerm`, version `~> 5.0` (the lock file pins **5.13.0**).

**Q: What does `~> 5.0` mean?**
Any 5.x version is allowed, but not 6.0. This prevents surprise breaking changes.

**Q: What is the Terraform state file?**
`terraform.tfstate` is Terraform's **memory** of what it created, linking my code to real Azure resources. It contains **sensitive values** such as ACS access keys, so it's in `.gitignore`. In a team, I'd store it in a **remote backend** like Azure Storage, with locking.

**Q: What is `.terraform.lock.hcl`, and should it be in git?**
It records the exact provider version and checksums. **Yes, commit it**, so everyone and every pipeline uses the same version.

**Q: How did Terraform know the order to create resources?**
From the **references**. For example, the domain uses `azurerm_email_communication_service.weather.id`. Terraform builds a dependency graph and creates the email service first. I didn't need `depends_on`.

**Q: What is a data source? Did you use one?**
A data source **reads** existing information without creating anything. I used `azurerm_client_config` to check which subscription I'm logged into.

**Q: How does Terraform log in to Azure?**
Through my **Azure CLI login** (`az login`), so I didn't put any credentials in the Terraform files.

**Q: Why is the email domain "AzureManaged"?**
Azure gives a free `<id>.azurecomm.net` domain that works immediately. A custom domain would need me to own it and add DNS records (SPF, DKIM) to verify it.

**Q: Why is the domain association needed?**
The Email Service and the Communication Service are separate resources. The association **connects** them. Without it, the connection string can't send from that domain.

---

## Troubleshooting questions (scenarios)

**Q: Your first `terraform apply` failed. Why, and how did you fix it?**
The error said the `Microsoft.Communication` **resource provider wasn't registered**. Azure subscriptions must enable each service type before first use. I ran
`az provider register --namespace Microsoft.Communication` and then `terraform apply` again.

**Q: The first email send failed. What was wrong?**
The connection string was invalid. I checked that it had the `endpoint=...;accesskey=...` format. I also learned that **PowerShell `$env:` variables only exist in that one window**, so `func start` must run in the same window where they're set.

**Q: The timer function won't start locally. What would you check?**
Whether **Azurite** (the local storage emulator) is running. Timer triggers need storage, and `local.settings.json` uses `UseDevelopmentStorage=true`.

**Q: The email says "Succeeded" but nothing is in the inbox. What would you check?**
The spam folder, then the recipient address. Azure-managed domains can be flagged as spam more often, and a verified custom domain improves delivery.

**Q: Open-Meteo is down. What happens?**
`urlopen` has a 10-second timeout, so the function raises an error, the run fails, and it shows in the logs. An improvement would be a retry or a fallback message.

**Q: Someone changed a resource manually in the portal. What happens next time you run Terraform?**
`terraform plan` detects the **drift** and shows what it will change to make Azure match the code again.

**Q: You accidentally committed the state file. What do you do?**
Treat the keys as leaked: **regenerate the ACS keys** in Azure, remove the file from git history, and make sure `.gitignore` covers `*.tfstate`.

**Q: How would you delete everything?**
`terraform destroy`. Or delete the resource group, but then Terraform state would be out of date.

---

## Questions about "what next"

**Q: What would you improve?**
1. Deploy the **Function App** (with a storage account and service plan) with Terraform, so it runs in the cloud.
2. **Remote state** in Azure Storage.
3. Secrets in **Key Vault** or Function App settings instead of typed in by hand.
4. Use `variables.tf` instead of names written directly in the code.
5. A **CI/CD pipeline** (GitHub Actions) for plan, apply and deploy.
6. An HTML email with a forecast, not just current weather.

**Q: How much does this cost?**
Almost nothing. Open-Meteo is free, ACS Email costs a tiny amount per email, and a Consumption-plan function would also be close to free at one run per day. It's covered by the Azure Free Trial credit.
