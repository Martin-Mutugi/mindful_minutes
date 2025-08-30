from flask import Flask, redirect, url_for, render_template, request, jsonify
from flask_login import current_user
from config import Config, get_config
from extensions import db, login_manager, migrate, csrf, cache, init_extensions
from models import User
from dotenv import load_dotenv
import os
import logging
from datetime import datetime, timezone
from werkzeug.middleware.proxy_fix import ProxyFix

# Load environment variables from .env file
load_dotenv()

def create_app(config_class=None):
    """Application factory function"""
    app = Flask(__name__)
    
    # Configure the application
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)
    
    # Initialize configuration with app
    config_class.init_app(app)
    
    # Setup logging
    configure_logging(app)
    
    # Middleware for proxy setups (Heroku, Render, etc.)
    app.wsgi_app = ProxyFix(
        app.wsgi_app, 
        x_for=1, 
        x_proto=1, 
        x_host=1, 
        x_prefix=1
    )
    
    # Initialize extensions
    init_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register context processors
    register_context_processors(app)
    
    # Register CLI commands
    register_commands(app)
    
    # Health check and basic routes
    register_routes(app)
    
    # Create database tables (only in development)
    with app.app_context():
        if app.config.get('FLASK_ENV') == 'development':
            try:
                db.create_all()
                app.logger.info("Database tables created/verified")
            except Exception as e:
                app.logger.warning(f"db.create_all() failed: {e}")
        else:
            app.logger.info("Skipping automatic db.create_all() in production - using migrations instead")
    
    return app


def configure_logging(app):
    """Configure application logging"""
    if app.config.get('TESTING'):
        # Suppress logging during tests
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
        return
    
    # Configure logging based on environment
    if app.config.get('FLASK_ENV') == 'production':
        log_level = logging.INFO
        log_format = '%(asctime)s %(levelname)s: %(message)s [in %(name)s:%(lineno)d]'
    else:
        log_level = logging.DEBUG
        log_format = '%(asctime)s %(levelname)s %(name)s: %(message)s'
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
        ]
    )
    
    # Reduce noisy logs from some libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)


def register_blueprints(app):
    """Register all application blueprints"""
    try:
        from routes.auth_routes import auth_bp
        from routes.journal_routes import journal_bp
        from routes.meditate_routes import meditate_bp
        from routes.premium_routes import premium_bp
        from routes.dashboard_routes import dashboard_bp
        from routes.main_routes import main_bp
        
        blueprints = [
            (auth_bp, '/auth'),
            (journal_bp, '/journal'),
            (meditate_bp, '/meditate'),
            (premium_bp, '/premium'),
            (dashboard_bp, '/dashboard'),
            (main_bp, '/')  # Main routes including index
        ]
        
        for blueprint, url_prefix in blueprints:
            app.register_blueprint(blueprint, url_prefix=url_prefix)
            app.logger.info(f"Registered blueprint: {blueprint.name} at {url_prefix}")
            
    except ImportError as e:
        app.logger.error(f"Failed to import blueprints: {e}")
        raise


def register_error_handlers(app):
    """Register error handlers for common HTTP errors"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify({'error': 'Resource not found'}), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        if request.accept_mimetypes.accept_json:
            return jsonify({'error': 'Access forbidden'}), 403
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()  # Rollback in case of database errors
        app.logger.error(f"Internal server error: {error}")
        if request.accept_mimetypes.accept_json:
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(413)
    def too_large_error(error):
        if request.accept_mimetypes.accept_json:
            return jsonify({'error': 'File too large'}), 413
        return render_template('errors/413.html'), 413
    
    @app.errorhandler(429)
    def too_many_requests(error):
        if request.accept_mimetypes.accept_json:
            return jsonify({'error': 'Too many requests'}), 429
        return render_template('errors/429.html'), 429


def register_context_processors(app):
    """Register context processors for template variables"""
    
    @app.context_processor
    def inject_current_year():
        return {'current_year': datetime.now(timezone.utc).year}
    
    @app.context_processor
    def inject_config():
        return {'config': app.config}
    
    @app.context_processor
    def inject_debug():
        return {'debug': app.debug}
    
    @app.context_processor
    def inject_environment():
        return {'environment': app.config.get('FLASK_ENV', 'production')}


def register_commands(app):
    """Register custom CLI commands"""
    
    @app.cli.command('init-db')
    def init_db():
        """Initialize the database with sample data"""
        try:
            db.create_all()
            app.logger.info("Database initialized successfully")
        except Exception as e:
            app.logger.error(f"Failed to initialize database: {e}")
            raise e
    
    @app.cli.command('create-admin')
    def create_admin():
        """Create an admin user (for development only)"""
        if app.config.get('FLASK_ENV') != 'development':
            app.logger.error("This command is only available in development mode")
            return
            
        from werkzeug.security import generate_password_hash
        try:
            admin = User(
                username='admin',
                email='admin@mindfulminutes.com',
                password_hash=generate_password_hash('admin123'),
                is_premium=True
            )
            db.session.add(admin)
            db.session.commit()
            app.logger.info("Admin user created successfully")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Failed to create admin user: {e}")
    
    @app.cli.command('migrate-db')
    def migrate_database():
        """Run database migrations"""
        try:
            from flask_migrate import upgrade
            upgrade()
            app.logger.info("Database migrations completed successfully")
        except Exception as e:
            app.logger.error(f"Database migration failed: {e}")
            # Provide helpful error message for common migration issues
            if "column" in str(e).lower() and "does not exist" in str(e).lower():
                app.logger.error("This is likely due to a missing column. Check your models match the database.")
    
    @app.cli.command('check-db')
    def check_database():
        """Check database connection and schema"""
        try:
            # Test connection
            db.session.execute('SELECT 1')
            app.logger.info("✓ Database connection successful")
            
            # Check if emotion_category column exists
            result = db.session.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='journal_entries' 
                AND column_name='emotion_category'
            """)
            
            if result.fetchone():
                app.logger.info("✓ emotion_category column exists")
            else:
                app.logger.warning("✗ emotion_category column missing - run migrations")
                
            # Check all tables exist
            result = db.session.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name IN ('users', 'journal_entries')
            """)
            
            tables = [row[0] for row in result.fetchall()]
            if 'users' in tables and 'journal_entries' in tables:
                app.logger.info("✓ All required tables exist")
            else:
                app.logger.warning(f"Missing tables. Found: {tables}")
                
        except Exception as e:
            app.logger.error(f"Database check failed: {e}")


def register_routes(app):
    """Register basic routes"""
    
    @app.route('/healthz')
    def health_check():
        """Health check endpoint for deployment monitoring"""
        try:
            # Test database connection
            db.session.execute('SELECT 1')
            
            # Check if we can query basic data
            user_count = db.session.query(User).count()
            
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'version': app.config.get('APP_VERSION', '1.0.0'),
                'environment': app.config.get('FLASK_ENV', 'production'),
                'database': 'connected',
                'user_count': user_count
            }), 200
        except Exception as e:
            app.logger.error(f"Health check failed: {e}")
            return jsonify({
                'status': 'unhealthy', 
                'error': str(e),
                'database': 'disconnected'
            }), 500
    
    @app.route('/robots.txt')
    def robots_txt():
        """Robots.txt for SEO"""
        robots_content = """User-agent: *
Allow: /
Disallow: /auth/
Disallow: /dashboard/
Disallow: /journal/
Disallow: /meditate/
Disallow: /premium/

Sitemap: https://yourdomain.com/sitemap.xml
"""
        return robots_content, 200, {'Content-Type': 'text/plain'}
    
    @app.route('/sitemap.xml')
    def sitemap():
        """Basic sitemap for SEO"""
        base_url = request.host_url.rstrip('/')
        urls = [
            f'{base_url}/',
            f'{base_url}/about',
            f'{base_url}/privacy',
            f'{base_url}/terms',
        ]
        
        sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    {"".join(f'<url><loc>{url}</loc><priority>0.8</priority></url>' for url in urls)}
</urlset>"""
        
        return sitemap_xml, 200, {'Content-Type': 'application/xml'}


# Expose app instance for Gunicorn and other WSGI servers
app = create_app()

# Render-compatible main guard
if __name__ == '__main__':
    # Get configuration from environment with safe defaults
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    debug = os.getenv('FLASK_DEBUG', 'false').lower() in ('1', 'true', 'yes')
    
    # Don't run in debug mode in production
    if os.getenv('FLASK_ENV') == 'production':
        debug = False
    
    app.logger.info(f"Starting Mindful Minutes on {host}:{port}")
    app.logger.info(f"Environment: {os.getenv('FLASK_ENV', 'production')}")
    app.logger.info(f"Debug mode: {debug}")
    
    app.run(host=host, port=port, debug=debug)