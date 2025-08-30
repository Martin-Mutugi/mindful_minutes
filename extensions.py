from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail

# Database ORM
db = SQLAlchemy()

# Database migrations (for schema changes)
migrate = Migrate()

# Login management
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'
login_manager.session_protection = 'strong'

# User loader function - Import inside function to avoid circular imports
@login_manager.user_loader
def load_user(user_id):
    """Load user from database by ID."""
    from models import User  # Import here to avoid circular import
    try:
        return db.session.get(User, int(user_id))
    except (ValueError, TypeError):
        return None
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Error loading user {user_id}: {e}")
        return None

# CSRF protection (for form security)
csrf = CSRFProtect()

# Caching (for performance optimization)
cache = Cache(config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 300
})

# Rate limiting (to prevent abuse)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Email service (for notifications, password reset, etc.)
mail = Mail()

def init_extensions(app):
    """
    Initialize all Flask extensions with the application.
    """
    extensions = [
        (db, "SQLAlchemy"),
        (migrate, "Flask-Migrate"),
        (login_manager, "Login Manager"),
        (csrf, "CSRF Protection"),
        (cache, "Caching"),
        (limiter, "Rate Limiting"),
        (mail, "Mail Service")
    ]
    
    # Initialize each extension
    for extension, name in extensions:
        try:
            extension.init_app(app)
            app.logger.info(f"✓ {name} initialized successfully")
        except Exception as e:
            app.logger.error(f"✗ Failed to initialize {name}: {e}")
            if name not in ["Mail Service", "Caching"]:
                raise
    
    app.logger.info("All extensions initialized successfully")