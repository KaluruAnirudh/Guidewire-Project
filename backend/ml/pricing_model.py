import os
from datetime import datetime

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor


FEATURE_COLUMNS = [
    "weather_risk",
    "historical_risk",
    "location_risk",
    "waterlogging_risk",
    "forecast_disruption_hours",
    "active_trigger_count",
    "civic_alert_severity",
    "earnings_band",
]


def train_and_save_model(dataset_path, artifact_path):
    dataframe = pd.read_csv(dataset_path)
    features = dataframe[FEATURE_COLUMNS]
    labels = dataframe["premium_delta"]

    model = RandomForestRegressor(
        n_estimators=160,
        max_depth=6,
        random_state=42,
    )
    model.fit(features, labels)

    artifact = {
        "model": model,
        "features": FEATURE_COLUMNS,
        "trained_at": datetime.utcnow().isoformat(),
        "metrics": {
            "rows": int(len(dataframe)),
            "feature_count": len(FEATURE_COLUMNS),
        },
    }

    os.makedirs(os.path.dirname(artifact_path), exist_ok=True)
    joblib.dump(artifact, artifact_path)
    return artifact


def load_model_artifact(artifact_path):
    return joblib.load(artifact_path)

