from flask import Flask
from flask_cors import CORS
from app.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)

    # Register blueprints (routes) — will add more each week
    from app.routes.auth_routes import auth_bp
    from app.routes.donation_routes import donation_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(donation_bp, url_prefix="/api/donations")

    @app.route("/api/health", methods=["GET"])
    def health_check():
        return {"status": "ok", "message": "SmartFood Rescue AI backend is running"}, 200

    return app