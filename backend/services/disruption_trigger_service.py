from datetime import datetime

from services.geo_utils import clamp
from services.historical_data_service import get_nearest_historical_profile
from services.weather_service import get_environment_context


def _build_mock_civic_alert(profile, forecast):
    monsoon_boost = 0.12 if datetime.utcnow().month in {6, 7, 8, 9} else 0.0
    severity = clamp(
        (profile["disaster_disruption"] * 0.7)
        + (forecast["predicted_severity"] * 0.2)
        + monsoon_boost
    )
    return {
        "source": "mock-civic-feed",
        "severity": severity,
        "active": severity >= 0.52,
        "label": "Local disruption bulletin" if severity >= 0.52 else "No civic bulletin",
    }


def evaluate_automated_triggers(location):
    lat = float(location["lat"])
    lon = float(location["lon"])
    environment = get_environment_context(lat, lon)
    profile = get_nearest_historical_profile(lat, lon)
    weather = environment["weather"]
    pollution = environment["pollution"]
    forecast = environment["forecast"]

    waterlogging_risk = clamp((profile["rain_disruption"] * 0.75) + (forecast["max_rain_3h"] / 12))
    civic_alert = _build_mock_civic_alert(profile, forecast)

    triggers = [
        {
            "id": "rainfall_surge",
            "label": "Rainfall surge trigger",
            "source": environment["source"],
            "active": weather["rain_1h"] >= 1.2 or forecast["max_rain_3h"] >= 2.8,
            "severity": clamp(max(weather["severity"], forecast["predicted_severity"])),
            "impact": "Order volumes and rider uptime typically drop during active rain bands.",
        },
        {
            "id": "flood_route",
            "label": "Flooded route trigger",
            "source": "historical-waterlogging-model",
            "active": waterlogging_risk >= 0.58 and forecast["max_rain_3h"] >= 3.5,
            "severity": clamp((waterlogging_risk * 0.7) + (forecast["predicted_severity"] * 0.3)),
            "impact": "Water logging historically causes route closures and missed trips.",
        },
        {
            "id": "air_quality_lockout",
            "label": "Air quality disruption trigger",
            "source": environment["source"],
            "active": pollution["aqi"] >= 4 or pollution["severity"] >= 0.62,
            "severity": pollution["severity"],
            "impact": "Poor AQI reduces rider safety and platform hours.",
        },
        {
            "id": "heatwave_slowdown",
            "label": "Heatwave slowdown trigger",
            "source": environment["source"],
            "active": weather["temperature"] >= 38 or forecast["max_temp"] >= 40,
            "severity": clamp(max((weather["temperature"] - 32) / 12, (forecast["max_temp"] - 34) / 10)),
            "impact": "Extreme heat lowers active shift duration and delivery acceptance.",
        },
        {
            "id": "civic_alert",
            "label": "Civic disruption trigger",
            "source": civic_alert["source"],
            "active": civic_alert["active"],
            "severity": civic_alert["severity"],
            "impact": "Mock civic bulletins simulate closures, accidents, or disaster advisories.",
        },
    ]

    active_triggers = [trigger for trigger in triggers if trigger["active"]]
    return {
        "environment": environment,
        "historical_profile": profile,
        "waterlogging_risk": waterlogging_risk,
        "forecast_disruption_hours": forecast["predicted_disruption_hours"],
        "civic_alert": civic_alert,
        "monitored_trigger_count": len(triggers),
        "automated_triggers": active_triggers,
    }

