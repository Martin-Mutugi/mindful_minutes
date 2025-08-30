from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from extensions import db
from models import JournalEntry
from utils import analyze_sentiment, recommend_meditation
from datetime import datetime
import logging

journal_bp = Blueprint('journal_bp', __name__)  # Consistent _bp naming
logger = logging.getLogger(__name__)

@journal_bp.route('/journal', methods=['GET', 'POST'])
@login_required
def journal():
    # Handle POST request - Form Submission
    if request.method == 'POST':
        content = request.form.get('content', '').strip()

        # Enhanced validation
        if len(content) < 10:  # Increased from 3 to encourage more meaningful entries
            flash('Please write a bit more (at least 10 characters) for a meaningful analysis.', 'warning')
            return render_template('journal.html', entries=get_user_entries(), content=content) # Preserve input

        try:
            # Analyze sentiment
            sentiment_score = analyze_sentiment(content)
            emotion = map_score_to_emotion(sentiment_score)

            # Create and save new entry
            new_entry = JournalEntry(
                content=content,
                sentiment_score=sentiment_score,
                emotion=emotion,
                user_id=current_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(new_entry)
            db.session.commit()

            # Get recommendation and flash success
            meditation = recommend_meditation(emotion, sentiment_score)  # Potential improvement
            flash(
                f"✓ Journal saved. Your mood is {emotion.lower()}."
                f" We recommend: '{meditation['name']}'",
                'success'
            )
            logger.info(f"New journal entry created for user {current_user.id}. Emotion: {emotion}")

        except Exception as e:
            # Handle potential errors from analyze_sentiment or database
            db.session.rollback()
            logger.error(f"Error creating journal entry for user {current_user.id}: {e}")
            flash("Sorry, we couldn't analyze your entry right now. Please try again.", 'danger')
            return render_template('journal.html', entries=get_user_entries(), content=content)

        # PRG Pattern (Post-Redirect-Get) to avoid form resubmission
        return redirect(url_for('journal_bp.journal'))

    # Handle GET request - Display form and entries
    entries = get_user_entries()
    return render_template('journal.html', entries=entries)


def get_user_entries():
    """Helper function to fetch the current user's entries."""
    return JournalEntry.query.filter_by(
        user_id=current_user.id
    ).order_by(
        JournalEntry.created_at.desc()
    ).all()

def map_score_to_emotion(score):
    """
    Maps a sentiment score to a more nuanced emotional label.
    Easy to extend later with more complex logic.
    """
    if score > 0.7:
        return "Very Positive"
    elif score > 0.6:
        return "Positive"
    elif score > 0.45:
        return "Slightly Positive"
    elif score > 0.4:
        return "Neutral"
    elif score > 0.3:
        return "Slightly Negative"
    elif score > 0.2:
        return "Negative"
    else:
        return "Very Negative"