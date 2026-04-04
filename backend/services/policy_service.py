from datetime import datetime, timedelta

from flask import current_app

from models import Policy
from services.risk_engine import build_zone_snapshot


def generate_policy_quote(user):
    zone_snapshot = build_zone_snapshot(user.location)
    earnings = float(user.weekly_earnings_estimate)
    risk_score = zone_snapshot["overall_risk"]

    base_premium = current_app.config["DEFAULT_WEEKLY_PREMIUM"]
    dynamic_premium = earnings * (0.018 + (risk_score * 0.024))
    weekly_premium = round(max(base_premium, base_premium + dynamic_premium), 2)
    coverage_amount = round(max(earnings * 0.75, 1500) * (1 + zone_snapshot["weather_risk"] * 0.15), 2)

    pricing_breakdown = {
        "base_premium": round(base_premium, 2),
        "weather_loading": round(weekly_premium * zone_snapshot["weather_risk"] * 0.16, 2),
        "historical_loading": round(weekly_premium * zone_snapshot["historical_risk"] * 0.12, 2),
        "location_loading": round(weekly_premium * zone_snapshot["location_risk"] * 0.1, 2),
        "zone_snapshot": zone_snapshot,
    }

    return {
        "plan_name": "Weekly Income Shield",
        "weekly_premium": weekly_premium,
        "coverage_amount": coverage_amount,
        "risk_score": risk_score,
        "weather_risk": zone_snapshot["weather_risk"],
        "historical_risk": zone_snapshot["historical_risk"],
        "zone_risk": zone_snapshot["location_risk"],
        "pricing_breakdown": pricing_breakdown,
    }


def get_latest_policy(user):
    policy = Policy.objects(user=user).order_by("-created_at").first()
    return sync_policy(policy) if policy else None


def sync_policy(policy):
    if not policy:
        return None

    now = datetime.utcnow()
    if policy.status != "active":
        return policy

    while policy.auto_renew and policy.current_term_end < now:
        quote = generate_policy_quote(policy.user)
        policy.renewal_history.append(
            {
                "renewed_at": now.isoformat(),
                "previous_term_end": policy.current_term_end.isoformat(),
                "premium": quote["weekly_premium"],
                "risk_score": quote["risk_score"],
            }
        )
        policy.current_term_start = policy.current_term_end
        policy.current_term_end = policy.current_term_end + timedelta(days=7)
        policy.renewal_count += 1
        policy.weekly_premium = quote["weekly_premium"]
        policy.coverage_amount = quote["coverage_amount"]
        policy.risk_score = quote["risk_score"]
        policy.weather_risk = quote["weather_risk"]
        policy.historical_risk = quote["historical_risk"]
        policy.zone_risk = quote["zone_risk"]
        policy.pricing_breakdown = quote["pricing_breakdown"]
        policy.save()

    if policy.current_term_end < now and not policy.auto_renew:
        policy.status = "expired"
        policy.save()

    return policy


def purchase_policy(user):
    existing_policy = get_latest_policy(user)
    now = datetime.utcnow()

    if existing_policy and existing_policy.status == "active" and existing_policy.current_term_end >= now:
        return existing_policy, False

    quote = generate_policy_quote(user)
    policy = Policy(
        user=user,
        plan_name=quote["plan_name"],
        status="active",
        weekly_premium=quote["weekly_premium"],
        coverage_amount=quote["coverage_amount"],
        risk_score=quote["risk_score"],
        weather_risk=quote["weather_risk"],
        historical_risk=quote["historical_risk"],
        zone_risk=quote["zone_risk"],
        auto_renew=True,
        current_term_start=now,
        current_term_end=now + timedelta(days=7),
        pricing_breakdown=quote["pricing_breakdown"],
    )
    policy.save()
    return policy, True


def cancel_policy(policy):
    policy.status = "cancelled"
    policy.auto_renew = False
    policy.save()
    return policy
