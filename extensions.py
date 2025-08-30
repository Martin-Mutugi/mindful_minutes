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
login_manager.login_view = 'auth_bp.login'  # Updated to use blueprint naming
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'
login_manager.session_protection = 'strong'  # Basic session protection

# CSRF protection (for form security)
csrf = CSRFProtect()

# Caching (for performance optimization)
cache = Cache(config={
    'CACHE_TYPE': 'simple',  # Use 'redis' or 'memcached' in production
    'CACHE_DEFAULT_TIMEOUT': 300  # 5 minutes
})

# Rate limiting (to prevent abuse)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"  # Use Redis in production: "redis://localhost:6379"
)

# Email service (for notifications, password reset, etc.)
mail = Mail()

# Optional: Compression (for performance)
try:
    from flask_compress import Compress
    compress = Compress()
except ImportError:
    compress = None
    # We'll handle this gracefully in the init function

def init_extensions(app):
    """
    Initialize all Flask extensions with the application.
    This centralizes extension initialization and error handling.
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
            # Don't raise for optional extensions
            if name not in ["Mail Service", "Caching"]:
                raise
    
    # Initialize compression if available
    if compress:
        try:
            compress.init_app(app)
            app.logger.info("✓ Compression initialized successfully")
        except Exception as e:
            app.logger.warning(f"Compression initialization failed: {e}")
    
    # Configure rate limiting to exclude certain routes
    configure_rate_limiting(app)
    
    app.logger.info("All extensions initialized successfully")

def configure_rate_limiting(app):
    """
    Configure rate limiting rules and exemptions.
    """
    # Health check endpoint should have higher limits
    @limiter.limit("10 per minute")
    def health_check_limit():
        return "Health check limited"
    
    # Apply specific limits to authentication routes
    limiter.limit("5 per minute", error_message="Too many login attempts")(["auth_bp.login", "auth_bp.register"])
    
    # Higher limits for API endpoints (if you add them later)
    # limiter.limit("100 per hour")(["api_bp.some_endpoint"])