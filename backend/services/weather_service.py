from datetime import datetime

import requests
from flask import current_app

from services.geo_utils import clamp


def _score_weather_payload(weather_payload):
    rain_1h = float(weather_payload.get("rain", {}).get("1h", 0) or 0)
    wind_speed = float(weather_payload.get("wind", {}).get("speed", 0) or 0)
    temperature = float(weather_payload.get("main", {}).get("temp", 0) or 0)
    conditions = [item.get("main", "").lower() for item in weather_payload.get("weather", [])]

    severity = 0.0
    severity += min(rain_1h / 10, 0.45)
    severity += min(wind_speed / 40, 0.25)
    if "thunderstorm" in conditions:
        severity += 0.25
    elif "rain" in conditions:
        severity += 0.18
    if temperature >= 40 or temperature <= 5:
        severity += 0.18

    return {
        "main": weather_payload.get("weather", [{}])[0].get("main", "Unknown"),
        "description": weather_payload.get("weather", [{}])[0].get("description", ""),
        "temperature": temperature,
        "rain_1h": rain_1h,
        "wind_speed": wind_speed,
        "severity": clamp(severity),
    }


def _score_pollution_payload(pollution_payload):
    data = pollution_payload.get("list", [{}])[0]
    aqi = data.get("main", {}).get("aqi", 1)
    components = data.get("components", {})
    severity = clamp((float(aqi) - 1) / 4)
    return {"aqi": aqi, "components": components, "severity": severity}


def _summarize_forecast_payload(forecast_payload):
    windows = forecast_payload.get("list", [])[:8]
    max_rain_3h = 0.0
    max_temp = 0.0
    max_wind = 0.0
    rainy_windows = 0
    storm_windows = 0
    hot_windows = 0

    for window in windows:
        max_rain_3h = max(max_rain_3h, float(window.get("rain", {}).get("3h", 0) or 0))
        max_temp = max(max_temp, float(window.get("main", {}).get("temp", 0) or 0))
        max_wind = max(max_wind, float(window.get("wind", {}).get("speed", 0) or 0))
        condition = (window.get("weather", [{}])[0].get("main", "") or "").lower()
        if float(window.get("rain", {}).get("3h", 0) or 0) >= 1:
            rainy_windows += 1
        if condition == "thunderstorm":
            storm_windows += 1
        if float(window.get("main", {}).get("temp", 0) or 0) >= 38:
            hot_windows += 1

    predicted_disruption_hours = (rainy_windows * 3) + (storm_windows * 2) + hot_windows
    predicted_severity = clamp((max_rain_3h / 9) + (max_wind / 42) + (hot_windows * 0.08))

    return {
        "max_rain_3h": round(max_rain_3h, 2),
        "max_temp": round(max_temp, 2),
        "max_wind": round(max_wind, 2),
        "rainy_windows": rainy_windows,
        "storm_windows": storm_windows,
        "hot_windows": hot_windows,
        "predicted_disruption_hours": int(predicted_disruption_hours),
        "predicted_severity": predicted_severity,
    }


def _simulate_environment(lat, lon):
    month = datetime.utcnow().month
    monsoon_factor = 0.35 if month in {6, 7, 8, 9} else 0.15
    coastal_factor = abs((lon % 1) - 0.5) * 0.2
    heat_factor = 0.2 if month in {4, 5} else 0.08
    rain_1h = round(max(0.0, (monsoon_factor + coastal_factor) * 6), 2)
    temperature = round(25 + (lat % 6) + (heat_factor * 20), 1)
    wind_speed = round(7 + ((abs(lon) % 3) * 2), 1)
    aqi = 4 if abs(lat) > 20 else 3

    weather_main = "Rain" if rain_1h >= 1.5 else "Clouds"
    weather = {
        "main": weather_main,
        "description": "simulated conditions",
        "temperature": temperature,
        "rain_1h": rain_1h,
        "wind_speed": wind_speed,
        "severity": clamp((rain_1h / 10) + (wind_speed / 45) + heat_factor),
    }
    pollution = {
        "aqi": aqi,
        "components": {"pm2_5": round(42 + abs(lat % 5) * 8, 2)},
        "severity": clamp((aqi - 1) / 4),
    }
    forecast = {
        "max_rain_3h": round(rain_1h * 2.1, 2),
        "max_temp": round(temperature + 2.6, 1),
        "max_wind": round(wind_speed + 3.4, 1),
        "rainy_windows": 2 if rain_1h >= 1 else 1,
        "storm_windows": 1 if weather_main == "Rain" and wind_speed >= 8 else 0,
        "hot_windows": 1 if temperature >= 36 else 0,
        "predicted_disruption_hours": int(max(2, round((rain_1h * 2) + (heat_factor * 8)))),
        "predicted_severity": clamp((rain_1h / 8) + (wind_speed / 42) + heat_factor),
    }
    combined = clamp(max(weather["severity"], pollution["severity"]))
    return {
        "source": "simulation",
        "weather": weather,
        "pollution": pollution,
        "forecast": forecast,
        "risk_scores": {
            "weather_severity": weather["severity"],
            "pollution_severity": pollution["severity"],
            "forecast_severity": forecast["predicted_severity"],
            "combined": clamp(max(combined, forecast["predicted_severity"])),
        },
    }


def get_environment_context(lat, lon):
    api_key = current_app.config["OPENWEATHER_API_KEY"]
    if not api_key:
        return _simulate_environment(lat, lon)

    try:
        weather_response = requests.get(
            current_app.config["OPENWEATHER_WEATHER_URL"],
            params={"lat": lat, "lon": lon, "appid": api_key, "units": "metric"},
            timeout=6,
        )
        weather_response.raise_for_status()
        weather = _score_weather_payload(weather_response.json())

        pollution_response = requests.get(
            current_app.config["OPENWEATHER_AIR_URL"],
            params={"lat": lat, "lon": lon, "appid": api_key},
            timeout=6,
        )
        pollution_response.raise_for_status()
        pollution = _score_pollution_payload(pollution_response.json())

        forecast_response = requests.get(
            current_app.config["OPENWEATHER_FORECAST_URL"],
            params={"lat": lat, "lon": lon, "appid": api_key, "units": "metric"},
            timeout=6,
        )
        forecast_response.raise_for_status()
        forecast = _summarize_forecast_payload(forecast_response.json())
        combined = clamp(max(weather["severity"], pollution["severity"], forecast["predicted_severity"]))

        return {
            "source": "openweathermap",
            "weather": weather,
            "pollution": pollution,
            "forecast": forecast,
            "risk_scores": {
                "weather_severity": weather["severity"],
                "pollution_severity": pollution["severity"],
                "forecast_severity": forecast["predicted_severity"],
                "combined": combined,
            },
        }
    except Exception:
        return _simulate_environment(lat, lon)


def validate_disruption(reason, location, incident_at):
    lat = float(location["lat"])
    lon = float(location["lon"])
    normalized_reason = (reason or "").strip().lower()
    context = get_environment_context(lat, lon)
    weather = context["weather"]
    pollution = context["pollution"]
    forecast = context["forecast"]
    signals = []

    disruption_real = False
    confidence = 0.25

    if normalized_reason in {"rain", "storm"}:
        disruption_real = weather["rain_1h"] >= 1 or weather["main"].lower() in {"rain", "thunderstorm"}
        confidence = clamp(0.35 + weather["severity"] * 0.6)
        if disruption_real:
            signals.append("Active rain or storm conditions detected.")
    elif normalized_reason == "flood":
        disruption_real = weather["rain_1h"] >= 4 or forecast["max_rain_3h"] >= 5 or weather["severity"] >= 0.65
        confidence = clamp(0.3 + max(weather["severity"], forecast["predicted_severity"]) * 0.65)
        if disruption_real:
            signals.append("Heavy rain threshold suggests flooding risk.")
    elif normalized_reason == "pollution":
        disruption_real = pollution["aqi"] >= 4 or pollution["severity"] >= 0.6
        confidence = clamp(0.3 + pollution["severity"] * 0.65)
        if disruption_real:
            signals.append("Air quality index is high enough to disrupt outdoor work.")
    else:
        disruption_real = context["risk_scores"]["combined"] >= 0.6 or forecast["predicted_disruption_hours"] >= 6
        confidence = clamp(0.25 + context["risk_scores"]["combined"] * 0.55)
        if disruption_real:
            signals.append("Composite environmental risk indicates a credible disruption.")

    age_hours = abs((datetime.utcnow() - incident_at).total_seconds()) / 3600
    if age_hours > 24:
        confidence = clamp(confidence - 0.1)
        signals.append("Historical validation confidence reduced because the claim is not near real-time.")

    return {
        "disruption_real": disruption_real,
        "confidence": confidence,
        "matched_signals": signals,
        "context": context,
    }
