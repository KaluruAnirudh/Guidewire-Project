from services.geo_utils import clamp


def decide_claim(ai_validation, fraud_assessment, zone_snapshot, policy):
    fraud_probability = fraud_assessment["fraud_probability"]
    confidence = ai_validation["overall_confidence"]
    disruption_real = ai_validation["disruption_real"]

    composite_risk = clamp(
        (zone_snapshot["overall_risk"] * 0.4)
        + (fraud_probability * 0.4)
        + ((1 - confidence) * 0.2)
    )
    approve_threshold = 0.55 if zone_snapshot["overall_risk"] < 0.75 else 0.62

    if disruption_real and confidence >= approve_threshold and fraud_probability < 0.55:
        decision = "APPROVED"
    elif fraud_probability >= 0.85 or (not ai_validation["weather"]["disruption_real"] and confidence < 0.4):
        decision = "REJECTED"
    else:
        decision = "FLAGGED"

    payout_ratio = clamp((0.35 + (confidence * 0.3) + ((1 - fraud_probability) * 0.2)), 0.2, 0.85)
    payout_amount = round(policy.coverage_amount * payout_ratio, 2) if decision == "APPROVED" else 0.0

    reasons = []
    if ai_validation["weather"]["disruption_real"]:
        reasons.append("Environmental disruption validated.")
    else:
        reasons.append("Environmental disruption could not be strongly validated.")
    if fraud_probability >= 0.75:
        reasons.append("Fraud score crossed the review threshold.")
    if zone_snapshot["overall_risk"] >= 0.7:
        reasons.append("Claim originated in a high-risk micro-zone.")

    return {
        "decision": decision,
        "decision_reason": " ".join(reasons),
        "risk_score": round(composite_risk, 4),
        "review_required": decision == "FLAGGED",
        "payout_amount": payout_amount,
        "thresholds": {
            "approve_confidence_threshold": approve_threshold,
            "reject_fraud_threshold": 0.85,
        },
    }

