import os

from flask import Flask, jsonify

from config import Config
from extensions import cors, init_db, jwt
from routes import register_blueprints
from services.fraud_service import initialize_model_registry
from services.pricing_ai_service import initialize_pricing_model_registry
from services.risk_engine import prime_zone_cache


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    jwt.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=False,
    )
    init_db(app)

    with app.app_context():
        initialize_model_registry()
        initialize_pricing_model_registry()
        prime_zone_cache()

    register_blueprints(app)

    @app.get("/health")
    def healthcheck():
        return jsonify({"status": "ok", "service": "route-relief-api"})

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=app.config["PORT"], debug=app.config["DEBUG"])
