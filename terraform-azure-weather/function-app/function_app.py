import azure.functions as func
import logging
import os
from datetime import datetime, timezone
from weather import get_weather_summary

app = func.FunctionApp()


@app.timer_trigger(
	schedule="0 0 5 * * *",
	arg_name="my_timer",
	run_on_startup=False,
	use_monitor=True,
)
def islamabad_weather_timer(my_timer: func.TimerRequest) -> None:
	if my_timer.past_due:
		logging.warning("The scheduled Islamabad weather report is past due.")

	weather_summary = get_weather_summary()
	logging.info(weather_summary)

	connection_string = os.environ.get("AZURE_COMMUNICATION_CONNECTION_STRING")
	sender_email = os.environ.get("SENDER_EMAIL")
	recipient_email = os.environ.get("RECIPIENT_EMAIL")
	if not connection_string or not sender_email or not recipient_email:
		raise ValueError(
			"AZURE_COMMUNICATION_CONNECTION_STRING, SENDER_EMAIL, and "
			"RECIPIENT_EMAIL must be configured"
		)

	from azure.communication.email import EmailClient

	email_client = EmailClient.from_connection_string(connection_string)
	message = {
		"senderAddress": sender_email,
		"recipients": {"to": [{"address": recipient_email}]},
		"content": {
			"subject": "Islamabad weather report",
			"plainText": weather_summary,
		},
	}
	result = email_client.begin_send(message).result()
	if result.get("status") != "Succeeded":
		raise RuntimeError(f"ACS email send failed: {result.get('error')}")

	logging.info("Email queued for delivery; operation ID: %s", result.get("id"))


@app.route(route="weather", auth_level=func.AuthLevel.ANONYMOUS)
def weather_ui(req: func.HttpRequest) -> func.HttpResponse:
	try:
		summary = get_weather_summary()
	except Exception as exc:
		return func.HttpResponse(
			f"<h1>Error fetching weather</h1><p>{exc}</p>",
			mimetype="text/html",
			status_code=500,
		)

	fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

	html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Islamabad Weather</title>
  <style>
    body {{ font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0;
           margin: 0; padding: 2rem; min-height: 100vh; display: flex;
           justify-content: center; align-items: center; }}
    .card {{ background: #1e293b; border-radius: 16px; padding: 2.5rem;
             max-width: 540px; width: 100%; box-shadow: 0 20px 60px rgba(0,0,0,0.5); }}
    .badge {{ display: inline-block; background: #0ea5e9; color: white;
              font-size: 0.75rem; font-weight: 600; padding: 4px 14px;
              border-radius: 999px; margin-bottom: 1.5rem; letter-spacing: 0.05em; }}
    h1 {{ font-size: 1.75rem; margin: 0 0 0.4rem; color: #f8fafc; }}
    .city {{ color: #94a3b8; font-size: 0.9rem; margin-bottom: 2rem; }}
    .summary {{ font-size: 1.1rem; line-height: 1.8; color: #cbd5e1;
                border-left: 3px solid #0ea5e9; padding-left: 1rem; }}
    .footer {{ margin-top: 2rem; color: #64748b; font-size: 0.8rem; }}
  </style>
</head>
<body>
  <div class="card">
    <span class="badge">&#9729; Live from Azure</span>
    <h1>Islamabad Weather</h1>
    <p class="city">Islamabad, Pakistan &mdash; Real-time data via Open-Meteo</p>
    <p class="summary">{summary}</p>
    <p class="footer">Fetched at {fetched_at} &bull; Running on Azure Functions</p>
  </div>
</body>
</html>"""

	return func.HttpResponse(html, mimetype="text/html", status_code=200)