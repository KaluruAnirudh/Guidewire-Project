from datetime import datetime

from mongoengine import (
    BooleanField,
    DateTimeField,
    DictField,
    Document,
    FloatField,
    IntField,
    ListField,
    ReferenceField,
    StringField,
)

from models.user import User


class Policy(Document):
    meta = {
        "collection": "policies",
        "indexes": ["user", "status", "current_term_end", "auto_renew"],
    }

    user = ReferenceField(User, required=True)
    plan_name = StringField(required=True, default="Weekly Income Shield")
    status = StringField(required=True, default="active")
    weekly_premium = FloatField(required=True, min_value=0)
    coverage_amount = FloatField(required=True, min_value=0)
    risk_score = FloatField(required=True, min_value=0, max_value=1)
    weather_risk = FloatField(required=True, min_value=0, max_value=1)
    historical_risk = FloatField(required=True, min_value=0, max_value=1)
    zone_risk = FloatField(required=True, min_value=0, max_value=1)
    auto_renew = BooleanField(default=True)
    current_term_start = DateTimeField(required=True)
    current_term_end = DateTimeField(required=True)
    renewal_count = IntField(default=0)
    pricing_breakdown = DictField(default=dict)
    renewal_history = ListField(DictField(), default=list)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user.id),
            "plan_name": self.plan_name,
            "status": self.status,
            "weekly_premium": self.weekly_premium,
            "coverage_amount": self.coverage_amount,
            "risk_score": self.risk_score,
            "weather_risk": self.weather_risk,
            "historical_risk": self.historical_risk,
            "zone_risk": self.zone_risk,
            "auto_renew": self.auto_renew,
            "current_term_start": self.current_term_start.isoformat(),
            "current_term_end": self.current_term_end.isoformat(),
            "renewal_count": self.renewal_count,
            "pricing_breakdown": self.pricing_breakdown,
            "renewal_history": self.renewal_history,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
