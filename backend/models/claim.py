from datetime import datetime

from mongoengine import (
    BooleanField,
    DateTimeField,
    DictField,
    Document,
    FloatField,
    ListField,
    ReferenceField,
    StringField,
)

from models.policy import Policy
from models.user import User


class Claim(Document):
    meta = {
        "collection": "claims",
        "indexes": ["user", "policy", "decision", "submitted_at", "zone_id"],
    }

    user = ReferenceField(User, required=True)
    policy = ReferenceField(Policy, required=True)
    incident_at = DateTimeField(required=True)
    submitted_at = DateTimeField(default=datetime.utcnow)
    location = DictField(required=True)
    reason = StringField(required=True, max_length=50)
    description = StringField(default="")
    proof_files = ListField(DictField(), default=list)
    ai_validation = DictField(default=dict)
    fraud_score = FloatField(default=0)
    fraud_signals = DictField(default=dict)
    risk_score = FloatField(default=0)
    risk_breakdown = DictField(default=dict)
    zone_id = StringField(default="")
    group_fraud = DictField(default=dict)
    review_required = BooleanField(default=False)
    decision = StringField(default="PENDING")
    decision_reason = StringField(default="")
    payout_amount = FloatField(default=0)

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user.id),
            "policy_id": str(self.policy.id),
            "incident_at": self.incident_at.isoformat(),
            "submitted_at": self.submitted_at.isoformat(),
            "location": self.location,
            "reason": self.reason,
            "description": self.description,
            "proof_files": self.proof_files,
            "ai_validation": self.ai_validation,
            "fraud_score": self.fraud_score,
            "fraud_signals": self.fraud_signals,
            "risk_score": self.risk_score,
            "risk_breakdown": self.risk_breakdown,
            "zone_id": self.zone_id,
            "group_fraud": self.group_fraud,
            "review_required": self.review_required,
            "decision": self.decision,
            "decision_reason": self.decision_reason,
            "payout_amount": self.payout_amount,
        }

