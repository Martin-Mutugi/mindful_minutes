from flask import Flask
from datetime import datetime, timezone
from flask_wtf.csrf import generate_csrf

# Import the init_extensions helper
from extensions import init_extensions

# Import blueprints
from auth.routes import auth_bp
from dashboard.routes import dashboard_bp
from main.routes import main_bp


def create_app():
    app = Flask(__name__)

    # --- Configuration ---
    app.config['SECRET_KEY'] = "your-secret-key"   # Change this in production
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///site.db"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # --- Initialize Extensions ---
    init_extensions(app)

    # --- Register Blueprints ---
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(main_bp)

    # --- Context Processors ---
    register_context_processors(app)

    return app


def register_context_processors(app):
    """Inject global template variables"""

    @app.context_processor
    def inject_current_year():
        return {"current_year": datetime.now(timezone.utc).year}

    @app.context_processor
    def inject_config():
        return {"config": app.config}

    @app.context_processor
    def inject_debug():
        return {"debug": app.debug}

    @app.context_processor
    def inject_environment():
        return {"environment": app.config.get("FLASK_ENV", "production")}

    @app.context_processor
    def inject_csrf():
        """Make {{ csrf_token() }} available in templates"""
        return dict(csrf_token=generate_csrf)


# --- Run Server ---
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
