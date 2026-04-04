from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from models import Claim
from services.auth_service import get_current_user
from services.claim_service import submit_claim


claim_bp = Blueprint("claims", __name__)


def _build_claim_payload():
    if request.content_type and "multipart/form-data" in request.content_type:
        form = request.form
        return {
            "incident_at": form.get("incident_at"),
            "reason": form.get("reason"),
            "description": form.get("description"),
            "location": {
                "lat": form.get("lat") or form.get("latitude"),
                "lon": form.get("lon") or form.get("lng") or form.get("longitude"),
            },
        }

    payload = request.get_json() or {}
    location = payload.get("location") or {}
    return {
        "incident_at": payload.get("incident_at"),
        "reason": payload.get("reason"),
        "description": payload.get("description"),
        "location": {
            "lat": location.get("lat", location.get("latitude")),
            "lon": location.get("lon", location.get("lng", location.get("longitude"))),
        },
    }


@claim_bp.post("/submit")
@jwt_required()
def create_claim():
    user = get_current_user()
    uploaded_files = request.files.getlist("proofs")

    try:
        claim = submit_claim(user, _build_claim_payload(), uploaded_files)
        return jsonify({"claim": claim.to_dict()}), 201
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400


@claim_bp.get("/mine")
@jwt_required()
def list_claims():
    user = get_current_user()
    claims = [claim.to_dict() for claim in Claim.objects(user=user).order_by("-submitted_at")]
    return jsonify({"claims": claims})


@claim_bp.get("/<claim_id>")
@jwt_required()
def get_claim(claim_id):
    user = get_current_user()
    claim = Claim.objects(id=claim_id, user=user).first()
    if not claim:
        return jsonify({"message": "Claim not found."}), 404
    return jsonify({"claim": claim.to_dict()})

