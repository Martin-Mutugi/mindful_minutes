import os
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load environment variables from .env file
load_dotenv()

class Config:
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("No SECRET_KEY set for Flask application. Set SECRET_KEY environment variable.")
    
    # Ensure the secret key is strong in production
    if os.getenv('FLASK_ENV') == 'production' and SECRET_KEY == 'dev':
        raise ValueError("Cannot use default 'dev' secret key in production. Set a strong SECRET_KEY.")

    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("No DATABASE_URL set. Set DATABASE_URL environment variable.")
    
    # Fix common Heroku/Render PostgreSQL URL issue
    if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,  # Recycle connections after 5 minutes
        'pool_pre_ping': True,  # Check connection health before using
    }

    # Hugging Face API
    HUGGING_FACE_API_KEY = os.getenv('HUGGING_FACE_API_KEY')
    HUGGING_FACE_API_TIMEOUT = int(os.getenv('HUGGING_FACE_API_TIMEOUT', '30'))

    # IntaSend API (Payments)
    INTASEND_PUBLIC_KEY = os.getenv('INTASEND_PUBLIC_KEY')
    INTASEND_SECRET_KEY = os.getenv('INTASEND_SECRET_KEY')
    INTASEND_TEST_MODE = os.getenv('INTASEND_TEST_MODE', 'true').lower() == 'true'
    
    # Check if payment is configured (useful for templates)
    PAYMENT_CONFIGURED = bool(INTASEND_PUBLIC_KEY and INTASEND_SECRET_KEY and 
                             not INTASEND_PUBLIC_KEY.startswith(('your_actual', 'test_')) and
                             not INTASEND_SECRET_KEY.startswith(('your_actual', 'test_')))

    # Application Settings
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', '0').lower() in ('1', 'true', 'yes')
    
    # Security Headers (for production)
    if FLASK_ENV == 'production':
        SESSION_COOKIE_SECURE = True
        SESSION_COOKIE_HTTPONLY = True
        REMEMBER_COOKIE_SECURE = True
        REMEMBER_COOKIE_HTTPONLY = True

    # File Upload Settings
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', '16777216'))  # 16MB max file upload

    # Email Configuration (for future features)
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@mindfulminutes.com')

    # Performance and Caching
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', '300'))

    # Analytics (for future features)
    GOOGLE_ANALYTICS_ID = os.getenv('GOOGLE_ANALYTICS_ID')

    # Custom Application Settings
    APP_NAME = "Mindful Minutes"
    APP_VERSION = "1.0.0"
    SUPPORT_EMAIL = os.getenv('SUPPORT_EMAIL', 'support@mindfulminutes.com')

    # Rate Limiting (for future API protection)
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')
    RATELIMIT_STRATEGY = 'fixed-window'

    @classmethod
    def init_app(cls, app):
        """Initialize application with this configuration"""
        # Add custom template global for config access
        app.jinja_env.globals['config'] = cls
        
        # Log configuration summary (without sensitive data)
        app.logger.info(f"Starting {cls.APP_NAME} v{cls.APP_VERSION}")
        app.logger.info(f"Environment: {cls.FLASK_ENV}")
        app.logger.info(f"Debug mode: {cls.DEBUG}")
        
        # Log database info without credentials
        if cls.SQLALCHEMY_DATABASE_URI:
            parsed_db = urlparse(cls.SQLALCHEMY_DATABASE_URI)
            app.logger.info(f"Database: {parsed_db.hostname}/{parsed_db.path[1:]}")
        
        app.logger.info(f"Payment configured: {cls.PAYMENT_CONFIGURED}")
        app.logger.info(f"Hugging Face API configured: {bool(cls.HUGGING_FACE_API_KEY)}")


class DevelopmentConfig(Config):
    """Development-specific configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Log SQL queries


class TestingConfig(Config):
    """Testing-specific configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL', 'sqlite:///:memory:')
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing
    SERVER_NAME = 'localhost:5000'  # For URL generation in tests


class ProductionConfig(Config):
    """Production-specific configuration"""
    DEBUG = False
    
    # Additional production security
    PREFERRED_URL_SCHEME = 'https'
    
    # Production-specific database pool settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'pool_size': 20,
        'max_overflow': 30,
    }


# Configuration registry
config_dict = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get appropriate configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'development')
    return config_dict.get(env, config_dict['default'])