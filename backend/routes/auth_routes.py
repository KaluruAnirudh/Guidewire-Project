from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from services.auth_service import authenticate_user, build_auth_payload, get_current_user, register_user


auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    payload = request.get_json() or {}
    try:
        user = register_user(payload)
        return jsonify(build_auth_payload(user)), 201
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400


@auth_bp.post("/login")
def login():
    payload = request.get_json() or {}
    try:
        user = authenticate_user(payload.get("email"), payload.get("password"))
        return jsonify(build_auth_payload(user))
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 401


@auth_bp.get("/me")
@jwt_required()
def me():
    try:
        return jsonify({"user": get_current_user().to_public_json()})
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 404

