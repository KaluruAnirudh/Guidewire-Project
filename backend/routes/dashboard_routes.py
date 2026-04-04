from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from models import Claim
from services.auth_service import get_current_user
from services.fraud_service import initialize_model_registry
from services.policy_service import get_latest_policy
from services.risk_engine import get_high_risk_zones


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/summary")
@jwt_required()
def summary():
    user = get_current_user()
    policy = get_latest_policy(user)
    model_registry = initialize_model_registry()

    total_claims = Claim.objects.count()
    approved_claims = Claim.objects(decision="APPROVED").count()
    rejected_claims = Claim.objects(decision="REJECTED").count()
    flagged_claims = Claim.objects(decision="FLAGGED").count()

    fraud_alerts = []
    for claim in Claim.objects(fraud_score__gte=0.75).order_by("-submitted_at")[:5]:
        fraud_alerts.append(
            {
                "claim_id": str(claim.id),
                "user_id": str(claim.user.id),
                "reason": claim.reason,
                "fraud_score": claim.fraud_score,
                "decision": claim.decision,
            }
        )

    my_claims = list(Claim.objects(user=user).order_by("-submitted_at")[:5])
    my_approved = sum(1 for claim in my_claims if claim.decision == "APPROVED")

    return jsonify(
        {
            "platform_metrics": {
                "total_claims": total_claims,
                "approved_claims": approved_claims,
                "rejected_claims": rejected_claims,
                "flagged_claims": flagged_claims,
                "fraud_alerts": fraud_alerts,
                "high_risk_zones": get_high_risk_zones(5),
                "fraud_model_metrics": model_registry["metrics"],
            },
            "my_metrics": {
                "recent_claims": [claim.to_dict() for claim in my_claims],
                "approved_recent_claims": my_approved,
                "active_policy": policy.to_dict() if policy else None,
                "active_disruption_triggers": (
                    policy.pricing_breakdown.get("zone_snapshot", {}).get("automated_triggers", [])
                    if policy
                    else []
                ),
            },
        }
    )
