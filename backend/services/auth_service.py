from flask_jwt_extended import create_access_token, get_jwt_identity

from models import User
from services.geo_utils import normalize_location


DEFAULT_PROFILES = {
    "delivery": {"typical_radius_km": 12, "variance": 0.58, "shift_start": 7, "shift_end": 23, "sensor_consistency": 0.82},
    "driver": {"typical_radius_km": 35, "variance": 0.7, "shift_start": 6, "shift_end": 1, "sensor_consistency": 0.88},
    "courier": {"typical_radius_km": 18, "variance": 0.6, "shift_start": 8, "shift_end": 22, "sensor_consistency": 0.84},
}


def build_movement_profile(work_type):
    normalized = (work_type or "delivery").strip().lower()
    return DEFAULT_PROFILES.get(
        normalized,
        {"typical_radius_km": 15, "variance": 0.62, "shift_start": 7, "shift_end": 22, "sensor_consistency": 0.8},
    )


def build_auth_payload(user):
    token = create_access_token(identity=str(user.id))
    return {"token": token, "user": user.to_public_json()}


def register_user(payload):
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    name = (payload.get("name") or "").strip()
    weekly_earnings = float(payload.get("weekly_earnings_estimate") or 0)

    if not email or not password:
        raise ValueError("Email and password are required.")
    if not name:
        raise ValueError("Name is required.")
    if weekly_earnings <= 0:
        raise ValueError("Weekly earnings estimate must be greater than zero.")

    if User.objects(email=email).first():
        raise ValueError("A user with this email already exists.")

    user = User(
        email=email,
        name=name,
        location=normalize_location(payload.get("location")),
        work_type=(payload.get("work_type") or "delivery").strip().lower(),
        weekly_earnings_estimate=weekly_earnings,
        movement_profile=build_movement_profile(payload.get("work_type")),
    )
    user.last_known_location = dict(user.location)
    user.set_password(password)
    user.save()
    return user


def authenticate_user(email, password):
    user = User.objects(email=(email or "").strip().lower()).first()
    if not user or not user.check_password(password or ""):
        raise ValueError("Invalid email or password.")
    return user


def get_current_user():
    identity = get_jwt_identity()
    user = User.objects(id=identity).first()
    if not user:
        raise ValueError("User not found.")
    return user
