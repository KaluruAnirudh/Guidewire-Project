import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    PORT = int(os.getenv("PORT", "5000"))
    SECRET_KEY = os.getenv("SECRET_KEY", "route-relief-secret")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "route-relief-jwt-secret")
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/route_relief")
    USE_MOCK_DB = os.getenv("USE_MOCK_DB", "false").lower() == "true"
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
    OPENWEATHER_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
    OPENWEATHER_AIR_URL = "https://api.openweathermap.org/data/2.5/air_pollution"
    OPENWEATHER_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
    UPLOAD_FOLDER = str(BASE_DIR / "uploads")
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]
    FRAUD_MODEL_PATH = str(BASE_DIR / "ml" / "artifacts" / "fraud_detector.joblib")
    FRAUD_DATASET_PATH = str(BASE_DIR / "ml" / "sample_claims.csv")
    PRICING_MODEL_PATH = str(BASE_DIR / "ml" / "artifacts" / "pricing_model.joblib")
    PRICING_DATASET_PATH = str(BASE_DIR / "ml" / "sample_pricing_features.csv")
    HISTORICAL_RISK_PATH = str(BASE_DIR / "data" / "historical_risk.json")
    DEFAULT_WEEKLY_PREMIUM = 89.0
