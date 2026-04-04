from datetime import timedelta

import numpy as np
from sklearn.cluster import DBSCAN

from models import Claim
from services.geo_utils import clamp, haversine_km


def detect_group_fraud(location, incident_at):
    start_window = incident_at - timedelta(days=3)
    recent_claims = list(Claim.objects(incident_at__gte=start_window))
    if len(recent_claims) < 2:
        return {
            "cluster_detected": False,
            "cluster_size": 1,
            "shared_coordinate_count": 0,
            "shared_timestamp_count": 0,
            "cluster_score": 0.0,
        }

    claim_vectors = []
    for claim in recent_claims:
        claim_vectors.append(
            [
                float(claim.location["lat"]) * 111,
                float(claim.location["lon"]) * 111,
                claim.incident_at.timestamp() / 1800,
            ]
        )

    candidate_vector = [
        float(location["lat"]) * 111,
        float(location["lon"]) * 111,
        incident_at.timestamp() / 1800,
    ]
    claim_vectors.append(candidate_vector)

    labels = DBSCAN(eps=0.8, min_samples=3).fit(np.array(claim_vectors)).labels_
    candidate_label = labels[-1]
    cluster_size = int(sum(label == candidate_label for label in labels)) if candidate_label != -1 else 1

    shared_coordinate_count = 0
    shared_timestamp_count = 0
    for claim in recent_claims:
        distance = haversine_km(
            float(location["lat"]),
            float(location["lon"]),
            float(claim.location["lat"]),
            float(claim.location["lon"]),
        )
        if distance <= 0.3:
            shared_coordinate_count += 1
        if abs((claim.incident_at - incident_at).total_seconds()) <= 1800:
            shared_timestamp_count += 1

    cluster_score = clamp(
        max(
            (cluster_size - 1) / 5,
            shared_coordinate_count / 5,
            shared_timestamp_count / 5,
        )
    )

    return {
        "cluster_detected": candidate_label != -1 and cluster_size >= 3,
        "cluster_size": cluster_size,
        "shared_coordinate_count": shared_coordinate_count,
        "shared_timestamp_count": shared_timestamp_count,
        "cluster_score": cluster_score,
    }

