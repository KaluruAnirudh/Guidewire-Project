from datetime import datetime, timedelta

import pandas as pd
from flask import current_app

from ml.fraud_model import FEATURE_COLUMNS, load_model_artifact, train_and_save_model
from models import Claim
from services.geo_utils import clamp, haversine_km


MODEL_REGISTRY = None


def initialize_model_registry():
    global MODEL_REGISTRY
    if MODEL_REGISTRY is not None:
        return MODEL_REGISTRY

    model_path = current_app.config["FRAUD_MODEL_PATH"]
    dataset_path = current_app.config["FRAUD_DATASET_PATH"]

    try:
        MODEL_REGISTRY = load_model_artifact(model_path)
    except Exception:
        MODEL_REGISTRY = train_and_save_model(dataset_path, model_path)

    return MODEL_REGISTRY


def _is_hour_in_shift(hour, start, end):
    if start <= end:
        return start <= hour <= end
    return hour >= start or hour <= end


def _detect_gps_spoofing(last_known_location, current_location, incident_at):
    observed_at = last_known_location.get("observed_at")
    if not observed_at:
        return 0.0

    try:
        previous_time = datetime.fromisoformat(observed_at)
    except ValueError:
        return 0.0

    elapsed_hours = max((incident_at - previous_time).total_seconds() / 3600, 0.1)
    distance = haversine_km(
        float(last_known_location["lat"]),
        float(last_known_location["lon"]),
        float(current_location["lat"]),
        float(current_location["lon"]),
    )
    implied_speed = distance / elapsed_hours
    return clamp((implied_speed - 60) / 90)


def _static_pattern_score(user, current_location):
    repeated_claims = Claim.objects(
        user=user,
        incident_at__gte=datetime.utcnow() - timedelta(days=45),
    )
    exactish_matches = 0
    for claim in repeated_claims:
        distance = haversine_km(
            float(claim.location["lat"]),
            float(claim.location["lon"]),
            float(current_location["lat"]),
            float(current_location["lon"]),
        )
        if distance <= 0.05:
            exactish_matches += 1
    return clamp(exactish_matches / 4)


def _sensor_mismatch_score(user, ai_validation):
    sensor_consistency = float(user.movement_profile.get("sensor_consistency", 0.8))
    weather_confidence = ai_validation["weather"]["confidence"]
    mismatch = (1 - sensor_consistency) + (0.25 if not ai_validation["weather"]["disruption_real"] else 0.0)
    mismatch += max(0.0, 0.45 - weather_confidence)
    return clamp(mismatch)


def extract_feature_vector(user, claim_payload, group_analysis, ai_validation):
    incident_at = claim_payload["incident_at"]
    location = claim_payload["location"]
    claims_last_30d = Claim.objects(
        user=user,
        submitted_at__gte=datetime.utcnow() - timedelta(days=30),
    ).count()

    distance_from_home = haversine_km(
        float(user.location["lat"]),
        float(user.location["lon"]),
        float(location["lat"]),
        float(location["lon"]),
    )
    typical_radius = float(user.movement_profile.get("typical_radius_km", 15))
    location_consistency = clamp(1 - (distance_from_home / max(typical_radius * 2, 5)))
    movement_variance = clamp(float(user.movement_profile.get("variance", 0.6)))

    shift_start = int(user.movement_profile.get("shift_start", 7))
    shift_end = int(user.movement_profile.get("shift_end", 22))
    time_anomaly = 0.0 if _is_hour_in_shift(incident_at.hour, shift_start, shift_end) else 1.0
    gps_spoofing = _detect_gps_spoofing(user.last_known_location or {}, location, incident_at)
    static_pattern = _static_pattern_score(user, location)
    sensor_mismatch = _sensor_mismatch_score(user, ai_validation)
    cluster_density = clamp(group_analysis["cluster_score"])

    return {
        "claim_frequency_30d": float(min(claims_last_30d, 10)),
        "location_consistency": round(location_consistency, 4),
        "movement_variance": round(movement_variance, 4),
        "time_anomaly": round(time_anomaly, 4),
        "gps_spoofing": round(gps_spoofing, 4),
        "static_pattern": round(static_pattern, 4),
        "sensor_mismatch": round(sensor_mismatch, 4),
        "cluster_density": round(cluster_density, 4),
    }


def score_claim(user, claim_payload, group_analysis, ai_validation):
    registry = initialize_model_registry()
    feature_vector = extract_feature_vector(user, claim_payload, group_analysis, ai_validation)
    frame = pd.DataFrame([[feature_vector[column] for column in FEATURE_COLUMNS]], columns=FEATURE_COLUMNS)
    base_probability = float(registry["model"].predict_proba(frame)[0][1])

    adversarial_adjustment = clamp(
        (feature_vector["gps_spoofing"] * 0.18)
        + (feature_vector["static_pattern"] * 0.12)
        + (feature_vector["sensor_mismatch"] * 0.1)
        + (feature_vector["cluster_density"] * 0.08)
    )
    fraud_probability = clamp(base_probability + adversarial_adjustment)

    return {
        "fraud_probability": round(fraud_probability, 4),
        "flagged": fraud_probability >= 0.75,
        "model_metrics": registry["metrics"],
        "feature_vector": feature_vector,
        "signals": {
            "gps_spoofing_detected": feature_vector["gps_spoofing"] >= 0.55,
            "static_pattern_detected": feature_vector["static_pattern"] >= 0.5,
            "sensor_mismatch_detected": feature_vector["sensor_mismatch"] >= 0.45,
            "group_cluster_detected": group_analysis["cluster_detected"],
            "adversarial_adjustment": round(adversarial_adjustment, 4),
        },
    }

