import pandas as pd
from flask import current_app

from ml.pricing_model import FEATURE_COLUMNS, load_model_artifact, train_and_save_model
from services.geo_utils import clamp


MODEL_REGISTRY = None


def initialize_pricing_model_registry():
    global MODEL_REGISTRY
    if MODEL_REGISTRY is not None:
        return MODEL_REGISTRY

    model_path = current_app.config["PRICING_MODEL_PATH"]
    dataset_path = current_app.config["PRICING_DATASET_PATH"]

    try:
        MODEL_REGISTRY = load_model_artifact(model_path)
    except Exception:
        MODEL_REGISTRY = train_and_save_model(dataset_path, model_path)

    return MODEL_REGISTRY


def _earnings_band(earnings):
    if earnings < 4000:
        return 1
    if earnings < 6000:
        return 2
    if earnings < 9000:
        return 3
    if earnings < 12000:
        return 4
    return 5


def build_pricing_feature_vector(zone_snapshot, earnings):
    triggers = zone_snapshot.get("automated_triggers", [])
    civic_alert = zone_snapshot.get("civic_alert", {})
    return {
        "weather_risk": round(zone_snapshot["weather_risk"], 4),
        "historical_risk": round(zone_snapshot["historical_risk"], 4),
        "location_risk": round(zone_snapshot["location_risk"], 4),
        "waterlogging_risk": round(zone_snapshot.get("waterlogging_risk", 0.0), 4),
        "forecast_disruption_hours": float(zone_snapshot.get("forecast_disruption_hours", 0)),
        "active_trigger_count": float(len(triggers)),
        "civic_alert_severity": round(float(civic_alert.get("severity", 0.0)), 4),
        "earnings_band": float(_earnings_band(earnings)),
    }


def predict_pricing_adjustment(zone_snapshot, earnings):
    registry = initialize_pricing_model_registry()
    feature_vector = build_pricing_feature_vector(zone_snapshot, earnings)
    frame = pd.DataFrame([[feature_vector[column] for column in FEATURE_COLUMNS]], columns=FEATURE_COLUMNS)
    predicted_delta = float(registry["model"].predict(frame)[0])

    safe_zone_discount = 2.0 if zone_snapshot.get("waterlogging_risk", 0) <= 0.25 else 0.0
    trigger_pressure = len(zone_snapshot.get("automated_triggers", []))
    predicted_delta = round(predicted_delta + (trigger_pressure * 0.35), 2)

    coverage_hours = int(
        max(
            40,
            min(
                56,
                40
                + round(zone_snapshot.get("forecast_disruption_hours", 0) * 0.7)
                + min(trigger_pressure, 3),
            ),
        )
    )

    coverage_hours_boost = max(0, coverage_hours - 40)
    return {
        "predicted_premium_delta": predicted_delta,
        "safe_zone_discount": safe_zone_discount,
        "coverage_hours": coverage_hours,
        "coverage_hours_boost": coverage_hours_boost,
        "feature_vector": feature_vector,
        "model_metrics": registry["metrics"],
    }
