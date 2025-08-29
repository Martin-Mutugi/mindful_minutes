from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'login'  # Redirects to login page if user not authenticated
login_manager.session_protection = 'strong'  # Adds extra security to user sessions
