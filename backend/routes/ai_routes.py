from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from services.ai_validation_service import validate_image_files, verify_document_text
from services.geo_utils import normalize_location
from services.storage_service import save_uploaded_files
from services.weather_service import validate_disruption


ai_bp = Blueprint("ai", __name__)


def _parse_incident_at(value):
    if not value:
        return datetime.utcnow()
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


@ai_bp.post("/verify-document")
@jwt_required()
def verify_document():
    payload = request.get_json() or {}
    result = verify_document_text(payload.get("reason"), payload.get("description", ""))
    return jsonify({"result": result})


@ai_bp.post("/verify-image")
@jwt_required()
def verify_image():
    uploaded_files = save_uploaded_files(request.files.getlist("proofs"))
    result = validate_image_files(uploaded_files)
    return jsonify({"result": result})


@ai_bp.post("/verify-weather")
@jwt_required()
def verify_weather():
    payload = request.get_json() or {}
    result = validate_disruption(
        reason=payload.get("reason"),
        location=normalize_location(payload.get("location")),
        incident_at=_parse_incident_at(payload.get("incident_at")),
    )
    return jsonify({"result": result})

