from flask import Blueprint, render_template
from flask_login import current_user, login_required
from models import JournalEntry
from datetime import datetime, timedelta
from collections import defaultdict

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    entries = JournalEntry.query.filter(
        JournalEntry.user_id == current_user.id,
        JournalEntry.created_at >= seven_days_ago
    ).order_by(JournalEntry.created_at.asc()).all()

    dates = [entry.created_at.strftime('%Y-%m-%d') for entry in entries]
    scores = [entry.sentiment_score for entry in entries]

    mood_counts = defaultdict(int)
    for entry in entries:
        mood_counts[entry.emotion] += 1

    return render_template(
        'dashboard.html',
        dates=dates,
        scores=scores,
        mood_counts=dict(mood_counts),
        total_entries=len(entries)
    )
