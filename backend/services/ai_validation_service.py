import os
import re

from PIL import Image

from services.geo_utils import clamp, normalize_location
from services.weather_service import validate_disruption


KEYWORDS = {
    "rain": {"rain", "wet", "storm", "water", "slippery"},
    "flood": {"flood", "waterlogged", "submerged", "blocked", "drainage"},
    "pollution": {"smog", "aqi", "pollution", "air", "breathing"},
    "disaster": {"hazard", "closure", "accident", "landslide", "evacuation"},
}


def verify_document_text(reason, description):
    normalized_reason = (reason or "").strip().lower()
    normalized_text = (description or "").strip().lower()
    tokens = re.findall(r"\w+", normalized_text)
    matching_keywords = sorted(KEYWORDS.get(normalized_reason, set()).intersection(tokens))
    suspicious_phrases = [
        phrase
        for phrase in ["same as last time", "n/a", "dummy", "test proof"]
        if phrase in normalized_text
    ]

    confidence = 0.2
    confidence += min(len(tokens) / 30, 0.25)
    confidence += 0.35 if matching_keywords else 0.08
    confidence -= 0.12 * len(suspicious_phrases)
    confidence = clamp(confidence)

    return {
        "valid": bool(matching_keywords) or confidence >= 0.45,
        "confidence": confidence,
        "matching_keywords": matching_keywords,
        "suspicious_phrases": suspicious_phrases,
    }


def validate_image_files(proof_files):
    if not proof_files:
        return {
            "valid": True,
            "confidence": 0.5,
            "model": "placeholder-cnn",
            "files": [],
            "notes": ["No proof uploaded; auto-decision relies on environmental signals."],
        }

    file_results = []
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov"}

    for proof in proof_files:
        extension = os.path.splitext(proof["stored_name"])[1].lower()
        confidence = 0.25
        notes = []

        if extension in allowed_extensions:
            confidence += 0.3
        else:
            notes.append("Unsupported file type.")

        if proof["size_bytes"] >= 50_000:
            confidence += 0.1
        else:
            notes.append("Small file size reduces evidence quality.")

        if extension in {".jpg", ".jpeg", ".png", ".webp"}:
            try:
                with Image.open(proof["path"]) as image:
                    width, height = image.size
                if width >= 320 and height >= 240:
                    confidence += 0.15
                else:
                    notes.append("Low image resolution.")
            except Exception:
                notes.append("Image metadata could not be parsed.")

        if extension in {".mp4", ".mov"}:
            confidence += 0.1

        file_results.append(
            {
                "name": proof["original_name"],
                "confidence": clamp(confidence),
                "notes": notes,
            }
        )

    overall_confidence = clamp(sum(item["confidence"] for item in file_results) / max(len(file_results), 1))
    return {
        "valid": overall_confidence >= 0.45,
        "confidence": overall_confidence,
        "model": "placeholder-cnn",
        "files": file_results,
        "notes": [],
    }


def run_claim_validation(reason, description, location, incident_at, proof_files):
    normalized_location = normalize_location(location)
    document_result = verify_document_text(reason, description)
    image_result = validate_image_files(proof_files)
    weather_result = validate_disruption(reason, normalized_location, incident_at)

    disruption_real = weather_result["disruption_real"] and (document_result["valid"] or image_result["valid"])
    overall_confidence = clamp(
        (document_result["confidence"] * 0.25)
        + (image_result["confidence"] * 0.15)
        + (weather_result["confidence"] * 0.6)
    )

    return {
        "document": document_result,
        "image": image_result,
        "weather": weather_result,
        "disruption_real": disruption_real,
        "overall_confidence": overall_confidence,
        "review_recommended": overall_confidence < 0.45 or not disruption_real,
    }

