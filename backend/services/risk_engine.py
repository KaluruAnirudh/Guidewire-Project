from datetime import datetime

from models import Claim, ZoneRisk
from services.geo_utils import clamp, normalize_location, zone_id_for_location
from services.historical_data_service import get_nearest_historical_profile, load_historical_profiles
from services.weather_service import get_environment_context


def _compose_alerts(environment, profile):
    alerts = []
    if environment["weather"]["rain_1h"] >= 3:
        alerts.append("Rainfall disruption alert")
    if environment["pollution"]["aqi"] >= 4:
        alerts.append("Pollution disruption alert")
    if profile["disaster_disruption"] >= 0.35:
        alerts.append("Historical disaster exposure")
    return alerts


def prime_zone_cache():
    for profile in load_historical_profiles():
        zone_id = zone_id_for_location(profile["lat"], profile["lon"])
        zone = ZoneRisk.objects(zone_id=zone_id).first() or ZoneRisk(
            zone_id=zone_id,
            label=profile["name"],
            centroid={"lat": profile["lat"], "lon": profile["lon"]},
        )
        zone.label = profile["name"]
        zone.centroid = {"lat": profile["lat"], "lon": profile["lon"]}
        zone.historical_risk = profile["baseline_risk"]
        zone.location_risk = profile["location_risk"]
        zone.overall_risk = clamp((profile["baseline_risk"] * 0.6) + (profile["location_risk"] * 0.4))
        zone.sources = {"seed_profile": profile}
        zone.last_updated = datetime.utcnow()
        zone.save()


def build_zone_snapshot(location, claim_reason=None):
    normalized_location = normalize_location(location)
    lat = normalized_location["lat"]
    lon = normalized_location["lon"]
    zone_id = zone_id_for_location(lat, lon)
    environment = get_environment_context(lat, lon)
    profile = get_nearest_historical_profile(lat, lon)

    total_claims = Claim.objects(zone_id=zone_id).count()
    historical_claim_density = clamp(total_claims / 20)
    historical_risk = clamp((profile["baseline_risk"] * 0.75) + (historical_claim_density * 0.25))
    location_risk = clamp(profile.get("location_risk", profile["baseline_risk"]))
    weather_risk = environment["risk_scores"]["combined"]
    overall_risk = clamp((weather_risk * 0.45) + (historical_risk * 0.35) + (location_risk * 0.2))

    zone = ZoneRisk.objects(zone_id=zone_id).first() or ZoneRisk(
        zone_id=zone_id,
        label=profile["name"],
        centroid=normalized_location,
    )
    zone.label = profile["name"]
    zone.centroid = normalized_location
    zone.weather_risk = weather_risk
    zone.historical_risk = historical_risk
    zone.location_risk = location_risk
    zone.overall_risk = overall_risk
    zone.active_alerts = _compose_alerts(environment, profile)
    zone.sources = {
        "environment_source": environment["source"],
        "historical_profile": profile["name"],
        "claim_reason": claim_reason,
    }
    zone.last_updated = datetime.utcnow()
    zone.save()

    return {
        "zone_id": zone_id,
        "label": zone.label,
        "weather_risk": weather_risk,
        "historical_risk": historical_risk,
        "location_risk": location_risk,
        "overall_risk": overall_risk,
        "weather_context": environment,
        "active_alerts": zone.active_alerts,
    }


def get_high_risk_zones(limit=5):
    zones = list(ZoneRisk.objects.order_by("-overall_risk")[:limit])
    if not zones:
        prime_zone_cache()
        zones = list(ZoneRisk.objects.order_by("-overall_risk")[:limit])
    return [zone.to_dict() for zone in zones]

