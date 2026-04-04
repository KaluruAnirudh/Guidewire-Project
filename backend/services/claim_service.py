from datetime import datetime

from models import Claim, ZoneRisk
from services.ai_validation_service import run_claim_validation
from services.decision_engine import decide_claim
from services.fraud_service import score_claim
from services.geo_utils import normalize_location
from services.group_fraud_service import detect_group_fraud
from services.policy_service import get_latest_policy
from services.risk_engine import build_zone_snapshot
from services.storage_service import save_uploaded_files


def _parse_incident_at(raw_value):
    if isinstance(raw_value, datetime):
        return raw_value
    if not raw_value:
        return datetime.utcnow()
    normalized = raw_value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized).replace(tzinfo=None)


def submit_claim(user, payload, uploaded_files):
    policy = get_latest_policy(user)
    if not policy or policy.status != "active":
        raise ValueError("An active policy is required before submitting a claim.")

    incident_at = _parse_incident_at(payload.get("incident_at"))
    location = normalize_location(payload.get("location"))
    proof_files = save_uploaded_files(uploaded_files)

    zone_snapshot = build_zone_snapshot(location, payload.get("reason"))
    ai_validation = run_claim_validation(
        reason=payload.get("reason"),
        description=payload.get("description", ""),
        location=location,
        incident_at=incident_at,
        proof_files=proof_files,
    )
    group_analysis = detect_group_fraud(location, incident_at)
    fraud_assessment = score_claim(
        user=user,
        claim_payload={
            "incident_at": incident_at,
            "location": location,
            "reason": payload.get("reason"),
        },
        group_analysis=group_analysis,
        ai_validation=ai_validation,
    )
    decision = decide_claim(ai_validation, fraud_assessment, zone_snapshot, policy)

    claim = Claim(
        user=user,
        policy=policy,
        incident_at=incident_at,
        location=location,
        reason=(payload.get("reason") or "").strip().lower(),
        description=(payload.get("description") or "").strip(),
        proof_files=proof_files,
        ai_validation=ai_validation,
        fraud_score=fraud_assessment["fraud_probability"],
        fraud_signals={
            "features": fraud_assessment["feature_vector"],
            "signals": fraud_assessment["signals"],
        },
        risk_score=decision["risk_score"],
        risk_breakdown={
            "zone_snapshot": zone_snapshot,
            "thresholds": decision["thresholds"],
        },
        zone_id=zone_snapshot["zone_id"],
        group_fraud=group_analysis,
        review_required=decision["review_required"],
        decision=decision["decision"],
        decision_reason=decision["decision_reason"],
        payout_amount=decision["payout_amount"],
    )
    claim.save()

    ZoneRisk.objects(zone_id=zone_snapshot["zone_id"]).update_one(inc__claim_count=1)

    user.last_known_location = {
        "lat": location["lat"],
        "lon": location["lon"],
        "observed_at": incident_at.isoformat(),
    }
    user.save()

    return claim
