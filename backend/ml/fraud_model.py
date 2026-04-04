import os
from datetime import datetime

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split


FEATURE_COLUMNS = [
    "claim_frequency_30d",
    "location_consistency",
    "movement_variance",
    "time_anomaly",
    "gps_spoofing",
    "static_pattern",
    "sensor_mismatch",
    "cluster_density",
]


def train_and_save_model(dataset_path, artifact_path):
    dataframe = pd.read_csv(dataset_path)
    features = dataframe[FEATURE_COLUMNS]
    labels = dataframe["is_fraud"]

    model = RandomForestClassifier(
        n_estimators=180,
        max_depth=6,
        random_state=42,
        class_weight="balanced",
    )

    metrics = {"rows": int(len(dataframe))}
    if len(dataframe) >= 12 and labels.nunique() > 1:
        x_train, x_test, y_train, y_test = train_test_split(
            features,
            labels,
            test_size=0.25,
            random_state=42,
            stratify=labels,
        )
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        probabilities = model.predict_proba(x_test)[:, 1]
        metrics.update(
            {
                "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
                "roc_auc": round(float(roc_auc_score(y_test, probabilities)), 4),
            }
        )
    else:
        model.fit(features, labels)

    artifact = {
        "model": model,
        "features": FEATURE_COLUMNS,
        "trained_at": datetime.utcnow().isoformat(),
        "metrics": metrics,
    }

    os.makedirs(os.path.dirname(artifact_path), exist_ok=True)
    joblib.dump(artifact, artifact_path)
    return artifact


def load_model_artifact(artifact_path):
    return joblib.load(artifact_path)

