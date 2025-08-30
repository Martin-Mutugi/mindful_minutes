from flask import Blueprint, render_template
from flask_login import current_user, login_required
from models import JournalEntry
from datetime import datetime, timedelta
from collections import defaultdict
import json
from extensions import db  # Add this import

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Fetches the user's journal entries and prepares data for the dashboard.
    Efficiently handles data for the Chart.js graph and stats.
    """
    # Calculate the date for one week ago
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    # FIXED: Explicitly select only existing columns
    all_entries = db.session.query(
        JournalEntry.id,
        JournalEntry.content,
        JournalEntry.sentiment_score,
        JournalEntry.emotion,
        JournalEntry.created_at,
        JournalEntry.updated_at,
        JournalEntry.user_id
    ).filter_by(
        user_id=current_user.id
    ).order_by(
        JournalEntry.created_at.asc()
    ).all()

    # FIXED: Also fix the recent entries query
    recent_entries = db.session.query(
        JournalEntry.id,
        JournalEntry.content,
        JournalEntry.sentiment_score,
        JournalEntry.emotion,
        JournalEntry.created_at,
        JournalEntry.updated_at,
        JournalEntry.user_id
    ).filter(
        JournalEntry.user_id == current_user.id,
        JournalEntry.created_at >= seven_days_ago
    ).all()

    # Prepare data for the Chart.js graph
    dates = [entry.created_at.strftime('%b %d') for entry in all_entries]
    scores = [float(entry.sentiment_score) for entry in all_entries if entry.sentiment_score is not None]

    # Prepare data for the mood statistics
    mood_counts = defaultdict(int)
    for entry in recent_entries:
        if entry.emotion:  # Add null check
            mood_counts[entry.emotion] += 1

    total_entries = len(all_entries)

    # Convert lists to JSON strings for safe embedding
    dates_json = json.dumps(dates)
    scores_json = json.dumps(scores)

    return render_template(
        'dashboard.html',
        dates=dates_json,
        scores=scores_json,
        mood_counts=dict(mood_counts),
        entry_count=total_entries,
        recent_entries=len(recent_entries)
    )