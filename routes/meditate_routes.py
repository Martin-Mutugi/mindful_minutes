from flask import Blueprint, render_template, send_from_directory, abort
from flask_login import current_user, login_required
import os

meditate_bp = Blueprint('meditate', __name__)

# Define meditation sessions
free_sessions = [
    {"name": "Basic Breathing", "file": "breathing.mp3", "description": "2-minute breathing exercise"},
    {"name": "Quick Focus", "file": "focus.mp3", "description": "Short focus meditation"}
]

premium_sessions = [
    {"name": "Gratitude Practice", "file": "gratitude.mp3", "description": "Cultivate thankfulness"},
    {"name": "Deep Relaxation", "file": "relaxation.mp3", "description": "Full body relaxation"},
    {"name": "Stress Relief", "file": "stress_relief.mp3", "description": "Release tension and anxiety"},
    {"name": "Sleep Meditation", "file": "sleep.mp3", "description": "Gentle guidance into restful sleep"},
    {"name": "Anxiety Relief", "file": "anxiety_relief.mp3", "description": "Calm anxious thoughts"},
    {"name": "Morning Energy", "file": "morning_energy.mp3", "description": "Start your day with vitality"}
]

@meditate_bp.route('/meditate')
@login_required
def meditate():
    sessions = premium_sessions if current_user.is_premium else free_sessions
    user_status = "Premium Member" if current_user.is_premium else "Free Member"
    return render_template('meditate.html', sessions=sessions, user_status=user_status)

@meditate_bp.route('/audio/<filename>')
@login_required
def serve_audio(filename):
    allowed_files = [s["file"] for s in premium_sessions + free_sessions]
    if filename not in allowed_files:
        abort(404)
    return send_from_directory(os.path.join('static', 'audio'), filename)
