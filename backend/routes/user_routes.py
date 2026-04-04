from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from services.auth_service import build_movement_profile, get_current_user
from services.geo_utils import normalize_location


user_bp = Blueprint("users", __name__)


@user_bp.get("/profile")
@jwt_required()
def get_profile():
    return jsonify({"user": get_current_user().to_public_json()})


@user_bp.put("/profile")
@jwt_required()
def update_profile():
    payload = request.get_json() or {}
    user = get_current_user()

    try:
        if "name" in payload:
            user.name = (payload.get("name") or "").strip() or user.name
        if "location" in payload:
            user.location = normalize_location(payload.get("location"))
        if "work_type" in payload:
            user.work_type = (payload.get("work_type") or user.work_type).strip().lower()
            user.movement_profile = build_movement_profile(user.work_type)
        if "weekly_earnings_estimate" in payload:
            user.weekly_earnings_estimate = float(payload.get("weekly_earnings_estimate") or user.weekly_earnings_estimate)

        user.save()
        return jsonify({"user": user.to_public_json()})
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400

