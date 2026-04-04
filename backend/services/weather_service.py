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
    combined = clamp(max(weather["severity"], pollution["severity"]))
    return {
        "source": "simulation",
        "weather": weather,
        "pollution": pollution,
        "risk_scores": {
            "weather_severity": weather["severity"],
            "pollution_severity": pollution["severity"],
            "combined": combined,
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
        combined = clamp(max(weather["severity"], pollution["severity"]))

        return {
            "source": "openweathermap",
            "weather": weather,
            "pollution": pollution,
            "risk_scores": {
                "weather_severity": weather["severity"],
                "pollution_severity": pollution["severity"],
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
    signals = []

    disruption_real = False
    confidence = 0.25

    if normalized_reason in {"rain", "storm"}:
        disruption_real = weather["rain_1h"] >= 1 or weather["main"].lower() in {"rain", "thunderstorm"}
        confidence = clamp(0.35 + weather["severity"] * 0.6)
        if disruption_real:
            signals.append("Active rain or storm conditions detected.")
    elif normalized_reason == "flood":
        disruption_real = weather["rain_1h"] >= 4 or weather["severity"] >= 0.65
        confidence = clamp(0.3 + weather["severity"] * 0.65)
        if disruption_real:
            signals.append("Heavy rain threshold suggests flooding risk.")
    elif normalized_reason == "pollution":
        disruption_real = pollution["aqi"] >= 4 or pollution["severity"] >= 0.6
        confidence = clamp(0.3 + pollution["severity"] * 0.65)
        if disruption_real:
            signals.append("Air quality index is high enough to disrupt outdoor work.")
    else:
        disruption_real = context["risk_scores"]["combined"] >= 0.6
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

