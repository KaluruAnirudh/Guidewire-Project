from datetime import datetime

from mongoengine import DateTimeField, DictField, Document, FloatField, IntField, ListField, StringField


class ZoneRisk(Document):
    meta = {"collection": "zone_risks", "indexes": ["zone_id", "-overall_risk", "last_updated"]}

    zone_id = StringField(required=True, unique=True)
    label = StringField(required=True)
    centroid = DictField(required=True)
    weather_risk = FloatField(default=0)
    historical_risk = FloatField(default=0)
    location_risk = FloatField(default=0)
    overall_risk = FloatField(default=0)
    claim_count = IntField(default=0)
    active_alerts = ListField(StringField(), default=list)
    sources = DictField(default=dict)
    last_updated = DateTimeField(default=datetime.utcnow)

    def to_dict(self):
        return {
            "zone_id": self.zone_id,
            "label": self.label,
            "centroid": self.centroid,
            "weather_risk": self.weather_risk,
            "historical_risk": self.historical_risk,
            "location_risk": self.location_risk,
            "overall_risk": self.overall_risk,
            "claim_count": self.claim_count,
            "active_alerts": self.active_alerts,
            "sources": self.sources,
            "last_updated": self.last_updated.isoformat(),
        }

