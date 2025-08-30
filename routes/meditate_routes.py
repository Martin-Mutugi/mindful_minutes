from flask import Blueprint, render_template, send_from_directory, abort, current_app
from flask_login import current_user, login_required
from models import JournalEntry
from sqlalchemy import desc
import os

meditate_bp = Blueprint('meditate_bp', __name__)  # Consistent _bp naming

# Define meditation sessions with more context for recommendations
MEDITATION_SESSIONS = {
    "free": [
        {
            "id": "breathing",
            "name": "Basic Breathing",
            "file": "breathing.mp3",
            "description": "A simple 2-minute breathing exercise to center yourself.",
            "tags": ["stress", "focus", "beginner"]
        },
        {
            "id": "focus",
            "name": "Quick Focus",
            "file": "focus.mp3",
            "description": "Regain clarity and concentration with this short meditation.",
            "tags": ["focus", "work", "study"]
        }
    ],
    "premium": [
        {
            "id": "gratitude",
            "name": "Gratitude Practice",
            "file": "gratitude.mp3",
            "description": "Cultivate a sense of thankfulness and appreciation for your life.",
            "tags": ["positive", "gratitude", "joy"]
        },
        {
            "id": "relaxation",
            "name": "Deep Relaxation",
            "file": "relaxation.mp3",
            "description": "Release physical tension and achieve a state of deep calm.",
            "tags": ["stress", "anxiety", "calm", "sleep"]
        },
        {
            "id": "stress_relief",
            "name": "Stress Relief",
            "file": "stress_relief.mp3",
            "description": "Specifically designed to melt away stress and worry.",
            "tags": ["stress", "worry", "overwhelm"]
        },
        {
            "id": "sleep",
            "name": "Sleep Meditation",
            "file": "sleep.mp3",
            "description": "Gentle guidance into a deep and restful night's sleep.",
            "tags": ["sleep", "insomnia", "rest"]
        },
        {
            "id": "anxiety_relief",
            "name": "Anxiety Relief",
            "file": "anxiety_relief.mp3",
            "description": "Calm racing thoughts and find your center.",
            "tags": ["anxiety", "panic", "calm"]
        },
        {
            "id": "morning_energy",
            "name": "Morning Energy",
            "file": "morning_energy.mp3",
            "description": "Invigorate your mind and body to start your day with purpose.",
            "tags": ["energy", "morning", "motivation"]
        }
    ]
}

@meditate_bp.route('/meditate')
@login_required
def meditate():
    """Serve the meditation page with a personalized recommendation."""
    # Determine user access
    is_premium = current_user.is_premium
    user_status = "Premium Member" if is_premium else "Free Member"
    
    # Get all sessions user has access to
    all_sessions = MEDITATION_SESSIONS['free'] + (MEDITATION_SESSIONS['premium'] if is_premium else [])
    
    # Get a personalized recommendation based on latest journal entry
    recommended_session = get_recommended_meditation(current_user.id)
    
    return render_template(
        'meditate.html',
        sessions=all_sessions,
        user_status=user_status,
        is_premium=is_premium,
        recommended_session=recommended_session  # Pass the recommendation to the template
    )


def get_recommended_meditation(user_id):
    """
    Recommends a meditation session based on the user's most recent journal sentiment.
    Returns the session ID of the recommendation.
    """
    # Get the most recent journal entry
    latest_entry = JournalEntry.query.filter_by(
        user_id=user_id
    ).order_by(
        JournalEntry.created_at.desc()
    ).first()

    if not latest_entry:
        # No journal entries yet, recommend a beginner-friendly free session
        return "breathing"

    # Simple logic: map emotions to session tags
    # You can make this much more sophisticated
    emotion = latest_entry.emotion.lower()
    score = latest_entry.sentiment_score

    if "anxiety" in emotion or "stress" in emotion or score < 0.4:
        return "anxiety_relief"
    elif "sad" in emotion or "negative" in emotion:
        return "gratitude"
    elif "tired" in emotion or "sleep" in emotion:
        return "sleep"
    elif "focus" in emotion or "concentrate" in emotion:
        return "focus"
    else:
        # Default recommendation for positive/neutral or unknown state
        return "relaxation"


@meditate_bp.route('/audio/<filename>')
@login_required
def serve_audio(filename):
    """Securely serve audio files only if user has access."""
    # Check if file exists in allowed sessions
    all_sessions = MEDITATION_SESSIONS['free'] + (MEDITATION_SESSIONS['premium'] if current_user.is_premium else [])
    allowed_files = {s["file"] for s in all_sessions}  # Use a set for O(1) lookups

    if filename not in allowed_files:
        current_app.logger.warning(f"Unauthorized audio access attempt: {current_user.id} tried to access {filename}")
        abort(403)  # Forbidden, not 404, because the file exists but they can't access it

    # Secure directory traversal prevention
    safe_path = os.path.join('static', 'audio')
    if not os.path.isfile(os.path.join(safe_path, filename)):
        abort(404)

    return send_from_directory(safe_path, filename)