import json
from functools import lru_cache

from flask import current_app

from services.geo_utils import haversine_km


@lru_cache(maxsize=1)
def load_historical_profiles():
    with open(current_app.config["HISTORICAL_RISK_PATH"], "r", encoding="utf-8") as file:
        return json.load(file)


def get_nearest_historical_profile(lat, lon):
    profiles = load_historical_profiles()
    return min(
        profiles,
        key=lambda profile: haversine_km(lat, lon, profile["lat"], profile["lon"]),
    )

