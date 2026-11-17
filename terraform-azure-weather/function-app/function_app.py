import azure.functions as func
import json
import logging
import os
from datetime import datetime, timezone, timedelta
from weather import get_weather_summary, get_weather_full

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


@app.route(route="send-email", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def send_weather_email(req: func.HttpRequest) -> func.HttpResponse:
	connection_string = os.environ.get("AZURE_COMMUNICATION_CONNECTION_STRING")
	sender_email = os.environ.get("SENDER_EMAIL")
	recipient_email = os.environ.get("RECIPIENT_EMAIL")

	if not connection_string or not sender_email or not recipient_email:
		return func.HttpResponse(
			json.dumps({"ok": False, "message": "Email is not configured on this server."}),
			mimetype="application/json",
			status_code=500,
		)

	try:
		from azure.communication.email import EmailClient
		summary = get_weather_summary()
		email_client = EmailClient.from_connection_string(connection_string)
		message = {
			"senderAddress": sender_email,
			"recipients": {"to": [{"address": recipient_email}]},
			"content": {
				"subject": "Islamabad weather report",
				"plainText": summary,
			},
		}
		result = email_client.begin_send(message).result()
		if result.get("status") != "Succeeded":
			return func.HttpResponse(
				json.dumps({"ok": False, "message": f"Send failed: {result.get('error')}"}),
				mimetype="application/json",
				status_code=500,
			)
		return func.HttpResponse(
			json.dumps({"ok": True, "message": f"Email sent to {recipient_email}"}),
			mimetype="application/json",
			status_code=200,
		)
	except Exception as exc:
		return func.HttpResponse(
			json.dumps({"ok": False, "message": str(exc)}),
			mimetype="application/json",
			status_code=500,
		)


@app.route(route="weather", auth_level=func.AuthLevel.ANONYMOUS)
def weather_ui(req: func.HttpRequest) -> func.HttpResponse:
	try:
		weather = get_weather_full()
	except Exception as exc:
		return func.HttpResponse(
			f"<h1>Error fetching weather</h1><p>{exc}</p>",
			mimetype="text/html",
			status_code=500,
		)

	pkt = timezone(timedelta(hours=5))
	local_time = datetime.now(pkt).strftime("%A, %d %b %Y  •  %I:%M %p")
	fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

	forecast_cards = "".join(
		f'<div class="fc-day">'
		f'<div class="fc-name">{d["day"]}</div>'
		f'<div class="fc-icon">{d["icon"]}</div>'
		f'<div class="fc-temps">'
		f'<span class="fc-max">{d["max"]}°</span>'
		f' <span class="fc-min">/ {d["min"]}°</span>'
		f"</div></div>"
		for d in weather["forecast"]
	)

	css = (
		"*{box-sizing:border-box;margin:0;padding:0}"
		"body{font-family:'Segoe UI',sans-serif;background:#0f172a;color:#e2e8f0;"
		"min-height:100vh;display:flex;justify-content:center;"
		"align-items:flex-start;padding:2rem 1rem}"
		".card{background:#1e293b;border-radius:20px;padding:2rem;"
		"max-width:480px;width:100%;box-shadow:0 25px 50px rgba(0,0,0,.5)}"
		".badge{display:inline-block;background:#0ea5e9;color:#fff;"
		"font-size:.7rem;font-weight:700;padding:4px 14px;border-radius:999px;"
		"margin-bottom:1.2rem;letter-spacing:.08em;text-transform:uppercase}"
		".city{font-size:1.5rem;font-weight:700;color:#f8fafc}"
		".local-time{color:#64748b;font-size:.85rem;margin-top:4px;margin-bottom:2rem}"
		".hero{text-align:center;padding:1rem 0 1.5rem}"
		".wi{font-size:5rem;line-height:1;margin-bottom:.5rem}"
		".temp{font-size:4rem;font-weight:800;color:#f8fafc;line-height:1}"
		".cond{color:#94a3b8;font-size:1.1rem;margin-top:.5rem}"
		".stats{display:flex;gap:.75rem;margin-bottom:1.5rem}"
		".stat{flex:1;background:#0f172a;border-radius:12px;padding:.9rem;text-align:center}"
		".stat-ic{font-size:1.3rem}"
		".stat-val{font-size:1.1rem;font-weight:700;color:#f8fafc;margin-top:4px}"
		".stat-lbl{font-size:.7rem;color:#64748b;text-transform:uppercase;"
		"letter-spacing:.05em;margin-top:2px}"
		".fc-title{font-size:.75rem;font-weight:600;color:#64748b;"
		"text-transform:uppercase;letter-spacing:.08em;margin-bottom:.75rem}"
		".forecast{display:flex;gap:.75rem}"
		".fc-day{flex:1;background:#0f172a;border-radius:12px;"
		"padding:.9rem .5rem;text-align:center}"
		".fc-name{font-size:.75rem;color:#64748b;text-transform:uppercase;"
		"letter-spacing:.05em}"
		".fc-icon{font-size:1.5rem;margin:.4rem 0}"
		".fc-max{color:#f8fafc;font-weight:600;font-size:.85rem}"
		".fc-min{color:#64748b;font-size:.85rem}"
		"hr{border:none;border-top:1px solid #334155;margin:1.5rem 0}"
		".footer{color:#475569;font-size:.75rem;text-align:center}"
		".send-btn{display:block;width:100%;margin-top:1.5rem;padding:.85rem;"
		"border:none;border-radius:12px;background:#0ea5e9;color:#fff;"
		"font-size:1rem;font-weight:600;cursor:pointer;transition:background .2s,opacity .2s}"
		".send-btn:hover:not(:disabled){background:#0284c7}"
		".send-btn:disabled{background:#334155;color:#64748b;cursor:not-allowed;opacity:.7}"
		".email-status{margin-top:.75rem;font-size:.85rem;text-align:center;min-height:1.2em}"
		".email-status.ok{color:#34d399}"
		".email-status.err{color:#f87171}"
	)

	html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Islamabad Weather</title>
  <style>{css}</style>
</head>
<body>
  <div class="card">
    <span class="badge">&#9729; Live from Azure</span>
    <div class="city">Islamabad, Pakistan</div>
    <div class="local-time">{local_time} PKT</div>
    <div class="hero">
      <div class="wi">{weather["icon"]}</div>
      <div class="temp">{weather["temperature"]}°C</div>
      <div class="cond">{weather["condition"]}</div>
    </div>
    <div class="stats">
      <div class="stat">
        <div class="stat-ic">\U0001f4a7</div>
        <div class="stat-val">{weather["humidity"]}%</div>
        <div class="stat-lbl">Humidity</div>
      </div>
      <div class="stat">
        <div class="stat-ic">\U0001f4a8</div>
        <div class="stat-val">{weather["wind_speed"]} km/h</div>
        <div class="stat-lbl">Wind</div>
      </div>
      <div class="stat">
        <div class="stat-ic">\U0001f321️</div>
        <div class="stat-val">{weather["feels_like"]}°C</div>
        <div class="stat-lbl">Feels Like</div>
      </div>
    </div>
    <div class="fc-title">3-Day Forecast</div>
    <div class="forecast">{forecast_cards}</div>
    <button class="send-btn" id="sendBtn" onclick="sendEmail()">&#128140; Send Weather Email</button>
    <div class="email-status" id="emailStatus"></div>
    <hr>
    <div class="footer">Fetched at {fetched_at} &bull; Running on Azure Functions</div>
  </div>
  <script>
    async function sendEmail() {{
      const btn = document.getElementById('sendBtn');
      const status = document.getElementById('emailStatus');
      btn.disabled = true;
      btn.textContent = 'Sending…';
      status.className = 'email-status';
      status.textContent = '';
      try {{
        const res = await fetch('/api/send-email', {{method: 'POST'}});
        const data = await res.json();
        if (data.ok) {{
          btn.textContent = '✓ Email Sent!';
          status.className = 'email-status ok';
          status.textContent = data.message;
        }} else {{
          btn.disabled = false;
          btn.textContent = '✉️ Send Weather Email';
          status.className = 'email-status err';
          status.textContent = data.message;
        }}
      }} catch (e) {{
        btn.disabled = false;
        btn.textContent = '✉️ Send Weather Email';
        status.className = 'email-status err';
        status.textContent = 'Network error — try again.';
      }}
    }}
  </script>
</body>
</html>"""

	return func.HttpResponse(html, mimetype="text/html", status_code=200)
