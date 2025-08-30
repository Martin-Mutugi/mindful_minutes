from flask import Blueprint, redirect, url_for, render_template
from flask_login import current_user

main_bp = Blueprint('main_bp', __name__)  # Consistent _bp naming

@main_bp.route('/')
def index():
    """
    Home page route. Redirects authenticated users to dashboard,
    unauthenticated users to a landing page or login.
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_bp.dashboard'))
    else:
        # Instead of directly redirecting to login, show a landing page
        # This is better for marketing and first-time users
        return redirect(url_for('main_bp.landing'))

@main_bp.route('/welcome')
def landing():
    """
    Landing page for unauthenticated users.
    Showcases the app's value proposition.
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_bp.dashboard'))
    
    return render_template('index.html')  # Create a proper landing page

@main_bp.route('/about')
def about():
    """About page with information about the project"""
    return render_template('about.html')

@main_bp.route('/privacy')
def privacy():
    """Privacy policy page (important for production)"""
    return render_template('privacy.html')

@main_bp.route('/terms')
def terms():
    """Terms of service page"""
    return render_template('terms.html')