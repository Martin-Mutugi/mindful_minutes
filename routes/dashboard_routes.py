from flask import Blueprint, render_template
from flask_login import current_user, login_required
from models import JournalEntry
from datetime import datetime, timedelta
from collections import defaultdict
import json  # Import json for safe data serialization

dashboard_bp = Blueprint('dashboard_bp', __name__)  # Naming consistency: use _bp suffix

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Fetches the user's journal entries and prepares data for the dashboard.
    Efficiently handles data for the Chart.js graph and stats.
    """
    # Calculate the date for one week ago
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    # 1. Query for ALL user entries for the main chart (or just 7 days? See note below)
    all_entries = JournalEntry.query.filter_by(
        user_id=current_user.id
    ).order_by(
        JournalEntry.created_at.asc()
    ).all()

    # 2. Query specifically for recent entries (last 7 days) for the stats card
    recent_entries = JournalEntry.query.filter(
        JournalEntry.user_id == current_user.id,
        JournalEntry.created_at >= seven_days_ago
    ).all()

    # Prepare data for the Chart.js graph
    # Using .strftime('%b %d') for a cleaner X-axis (e.g., "Jan 31")
    dates = [entry.created_at.strftime('%b %d') for entry in all_entries]
    scores = [float(entry.sentiment_score) for entry in all_entries]  # Ensure type is float

    # Prepare data for the mood statistics
    mood_counts = defaultdict(int)
    for entry in recent_entries:  # Count moods from the last 7 days
        mood_counts[entry.emotion] += 1

    # Get the total count of ALL journal entries, not just recent ones
    total_entries = len(all_entries)

    # Convert lists to JSON strings for safe embedding in the HTML data attributes
    dates_json = json.dumps(dates)
    scores_json = json.dumps(scores)

    return render_template(
        'dashboard.html',
        dates=dates_json,        # Pass the JSON string
        scores=scores_json,      # Pass the JSON string
        mood_counts=dict(mood_counts),
        entry_count=total_entries,  # Renamed for clarity in template
        recent_entries=len(recent_entries) # Pass the count of recent entries
    )