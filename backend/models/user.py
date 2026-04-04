from datetime import datetime

from mongoengine import DateTimeField, DictField, Document, EmailField, FloatField, StringField
from werkzeug.security import check_password_hash, generate_password_hash


class User(Document):
    meta = {"collection": "users", "indexes": ["email", "work_type"]}

    email = EmailField(required=True, unique=True)
    password_hash = StringField(required=True)
    name = StringField(required=True, max_length=120)
    location = DictField(required=True)
    work_type = StringField(required=True, max_length=50)
    weekly_earnings_estimate = FloatField(required=True, min_value=0)
    last_known_location = DictField(default=dict)
    movement_profile = DictField(default=dict)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    def to_public_json(self):
        return {
            "id": str(self.id),
            "email": self.email,
            "name": self.name,
            "location": self.location,
            "work_type": self.work_type,
            "weekly_earnings_estimate": self.weekly_earnings_estimate,
            "last_known_location": self.last_known_location,
            "movement_profile": self.movement_profile,
            "created_at": self.created_at.isoformat(),
        }

