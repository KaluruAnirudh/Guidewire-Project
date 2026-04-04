from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from services.auth_service import get_current_user
from services.policy_service import cancel_policy, generate_policy_quote, get_latest_policy, purchase_policy


policy_bp = Blueprint("policies", __name__)


@policy_bp.get("/quote")
@jwt_required()
def get_quote():
    user = get_current_user()
    return jsonify({"quote": generate_policy_quote(user)})


@policy_bp.post("/buy")
@jwt_required()
def buy_policy():
    user = get_current_user()
    policy, created = purchase_policy(user)
    status_code = 201 if created else 200
    return jsonify({"policy": policy.to_dict(), "created": created}), status_code


@policy_bp.get("/current")
@jwt_required()
def get_current_policy():
    policy = get_latest_policy(get_current_user())
    if not policy:
        return jsonify({"policy": None}), 404
    return jsonify({"policy": policy.to_dict()})


@policy_bp.post("/cancel")
@jwt_required()
def cancel_current_policy():
    policy = get_latest_policy(get_current_user())
    if not policy:
        return jsonify({"message": "No policy found."}), 404

    cancelled = cancel_policy(policy)
    return jsonify({"policy": cancelled.to_dict()})

