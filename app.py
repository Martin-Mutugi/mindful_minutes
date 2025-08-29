from flask import Flask, redirect, url_for, render_template
from flask_login import current_user
from config import Config
from extensions import db, login_manager
from models import User
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints
    from routes.auth_routes import auth_bp
    from routes.journal_routes import journal_bp
    from routes.meditate_routes import meditate_bp
    from routes.premium_routes import premium_bp
    from routes.dashboard_routes import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(journal_bp)
    app.register_blueprint(meditate_bp)
    app.register_blueprint(premium_bp)
    app.register_blueprint(dashboard_bp)

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.dashboard'))
        return render_template('index.html')

    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
