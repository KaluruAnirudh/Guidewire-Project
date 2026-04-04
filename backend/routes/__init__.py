from routes.ai_routes import ai_bp
from routes.auth_routes import auth_bp
from routes.claim_routes import claim_bp
from routes.dashboard_routes import dashboard_bp
from routes.policy_routes import policy_bp
from routes.user_routes import user_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(user_bp, url_prefix="/api/users")
    app.register_blueprint(policy_bp, url_prefix="/api/policies")
    app.register_blueprint(claim_bp, url_prefix="/api/claims")
    app.register_blueprint(ai_bp, url_prefix="/api/ai")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")

