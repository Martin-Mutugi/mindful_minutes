from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from extensions import db
from models import JournalEntry
from utils import analyze_sentiment, recommend_meditation
from datetime import datetime

journal_bp = Blueprint('journal', __name__)

@journal_bp.route('/journal', methods=['GET', 'POST'])
@login_required
def journal():
    if request.method == 'POST':
        content = request.form.get('content')
        if not content or len(content.strip()) < 3:
            flash('Journal entry is too short. Please write more.', 'warning')
            return redirect(url_for('journal.journal'))

        sentiment_score = analyze_sentiment(content)
        emotion = (
            "Positive" if sentiment_score > 0.6 else
            "Negative" if sentiment_score < 0.4 else
            "Neutral"
        )

        new_entry = JournalEntry(
            content=content,
            sentiment_score=sentiment_score,
            emotion=emotion,
            user_id=current_user.id,
            created_at=datetime.utcnow()
        )

        db.session.add(new_entry)
        db.session.commit()

        meditation = recommend_meditation(sentiment_score)
        flash(
            f"Mood analyzed: {emotion} (Score: {sentiment_score:.2f}). "
            f"Recommended: {meditation['name']}",
            'success'
        )

        return redirect(url_for('journal.journal'))

    entries = JournalEntry.query.filter_by(user_id=current_user.id)\
        .order_by(JournalEntry.created_at.desc()).all()

    return render_template('journal.html', entries=entries)
