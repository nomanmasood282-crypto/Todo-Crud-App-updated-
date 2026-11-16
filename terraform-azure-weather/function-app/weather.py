import json
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import urlopen


WEATHER_DESCRIPTIONS = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    80: "Rain showers",
    81: "Heavy rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Heavy thunderstorm with hail",
}

WEATHER_ICONS = {
    0: "☀️",
    1: "🌤️",
    2: "⛅",
    3: "☁️",
    45: "🌫️",
    48: "🌫️",
    51: "🌦️",
    53: "🌦️",
    55: "🌦️",
    61: "🌧️",
    63: "🌧️",
    65: "🌧️",
    71: "🌨️",
    73: "🌨️",
    75: "🌨️",
    80: "🌧️",
    81: "🌧️",
    82: "🌧️",
    95: "⛈️",
    96: "⛈️",
    99: "⛈️",
}


def get_weather_summary():
    params = urlencode({
        "latitude": 33.6844,
        "longitude": 73.0479,
        "current": (
            "temperature_2m,relative_humidity_2m,"
            "apparent_temperature,weather_code,wind_speed_10m"
        ),
        "timezone": "Asia/Karachi",
    })
    url = f"https://api.open-meteo.com/v1/forecast?{params}"

    with urlopen(url, timeout=10) as response:
        weather = json.load(response)

    current = weather["current"]
    condition = WEATHER_DESCRIPTIONS.get(
        current["weather_code"], "Unknown conditions"
    )

    return (
        f"Weather in Islamabad: {current['temperature_2m']}°C, {condition}. "
        f"Feels like {current['apparent_temperature']}°C; "
        f"humidity {current['relative_humidity_2m']}%; "
        f"wind {current['wind_speed_10m']} km/h."
    )


def get_weather_full():
    params = urlencode({
        "latitude": 33.6844,
        "longitude": 73.0479,
        "current": (
            "temperature_2m,relative_humidity_2m,"
            "apparent_temperature,weather_code,wind_speed_10m"
        ),
        "daily": "temperature_2m_max,temperature_2m_min,weather_code",
        "timezone": "Asia/Karachi",
        "forecast_days": 4,
    })
    url = f"https://api.open-meteo.com/v1/forecast?{params}"

    with urlopen(url, timeout=10) as response:
        data = json.load(response)

    current = data["current"]
    daily = data["daily"]

    code = current["weather_code"]
    condition = WEATHER_DESCRIPTIONS.get(code, "Unknown")
    icon = WEATHER_ICONS.get(code, "🌡️")

    forecast = []
    for i in range(1, 4):
        fc_code = daily["weather_code"][i]
        day_name = datetime.strptime(daily["time"][i], "%Y-%m-%d").strftime("%a")
        forecast.append({
            "day": day_name,
            "max": round(daily["temperature_2m_max"][i]),
            "min": round(daily["temperature_2m_min"][i]),
            "condition": WEATHER_DESCRIPTIONS.get(fc_code, "Unknown"),
            "icon": WEATHER_ICONS.get(fc_code, "🌡️"),
        })

    return {
        "temperature": round(current["temperature_2m"]),
        "feels_like": round(current["apparent_temperature"]),
        "humidity": current["relative_humidity_2m"],
        "wind_speed": round(current["wind_speed_10m"]),
        "condition": condition,
        "icon": icon,
        "forecast": forecast,
    }