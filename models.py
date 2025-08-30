from extensions import db
from flask_login import UserMixin
from datetime import datetime, timezone
from sqlalchemy.orm import validates
import re

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50))  # Added for personalization
    last_name = db.Column(db.String(50))   # Added for personalization
    is_premium = db.Column(db.Boolean, default=False, nullable=False)
    premium_since = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime)  # Track last login for analytics
    login_count = db.Column(db.Integer, default=0)  # Track engagement

    # Relationships
    journal_entries = db.relationship(
        'JournalEntry',
        backref='user',  # Changed from 'author' to 'user' for consistency
        lazy='dynamic',  # Use 'dynamic' for large collections for better performance
        cascade='all, delete-orphan',
        order_by='desc(JournalEntry.created_at)'  # Default ordering
    )

    # Validation
    @validates('email')
    def validate_email(self, key, email):
        if not email:
            raise ValueError("Email cannot be empty")
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValueError("Invalid email format")
        return email.lower()  # Store emails in lowercase

    @validates('username')
    def validate_username(self, key, username):
        if not username or len(username.strip()) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValueError("Username can only contain letters, numbers, and underscores")
        return username

    # Helper methods
    def get_recent_entries(self, limit=10):
        """Get recent journal entries with default limit"""
        return self.journal_entries.limit(limit).all()

    def get_mood_trend(self, days=30):
        """Get mood data for charting (used in dashboard)"""
        from datetime import timedelta
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        return JournalEntry.query.filter(
            JournalEntry.user_id == self.id,
            JournalEntry.created_at >= cutoff_date
        ).order_by(JournalEntry.created_at.asc()).all()

    def to_dict(self):
        """Serialize user data for API responses"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_premium': self.is_premium,
            'premium_since': self.premium_since.isoformat() if self.premium_since else None,
            'created_at': self.created_at.isoformat(),
            'journal_entries_count': self.journal_entries.count()
        }

    @property
    def name(self):
        """Get user's display name (first name + last name or username)"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return self.username

    def __repr__(self):
        return f"<User {self.username} ({self.email})>"


class JournalEntry(db.Model):
    __tablename__ = 'journal_entries'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    sentiment_score = db.Column(db.Float)  # 0.0 (negative) to 1.0 (positive)
    emotion = db.Column(db.String(50))     # e.g., "Positive", "Anxious", "Grateful"
    emotion_category = db.Column(db.String(20))  # Simplified: 'positive', 'neutral', 'negative'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), 
                          onupdate=lambda: datetime.now(timezone.utc))
    
    # Foreign key with proper indexing
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), 
                       nullable=False, index=True)

    # Index for common query patterns
    __table_args__ = (
        db.Index('ix_user_emotion', 'user_id', 'emotion'),
        db.Index('ix_user_date', 'user_id', 'created_at'),
        db.Index('ix_sentiment_date', 'user_id', 'sentiment_score', 'created_at'),
    )

    # Validation
    @validates('sentiment_score')
    def validate_sentiment_score(self, key, score):
        if score is not None and (score < 0 or score > 1):
            raise ValueError("Sentiment score must be between 0 and 1")
        return score

    @validates('content')
    def validate_content(self, key, content):
        if not content or len(content.strip()) < 10:
            raise ValueError("Journal entry must be at least 10 characters long")
        if len(content) > 10000:  # Reasonable limit
            raise ValueError("Journal entry is too long")
        return content.strip()

    # Helper methods
    def get_sentiment_label(self):
        """Convert numerical score to human-readable label"""
        if self.sentiment_score is None:
            return "Unknown"
        elif self.sentiment_score >= 0.7:
            return "Very Positive"
        elif self.sentiment_score >= 0.6:
            return "Positive"
        elif self.sentiment_score >= 0.5:
            return "Slightly Positive"
        elif self.sentiment_score >= 0.4:
            return "Neutral"
        elif self.sentiment_score >= 0.3:
            return "Slightly Negative"
        else:
            return "Negative"

    def to_dict(self):
        """Serialize journal entry for API responses"""
        return {
            'id': self.id,
            'content': self.content,
            'sentiment_score': self.sentiment_score,
            'sentiment_label': self.get_sentiment_label(),
            'emotion': self.emotion,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @property
    def preview(self):
        """Get a shortened preview of the content"""
        if len(self.content) <= 100:
            return self.content
        return self.content[:97] + '...'

    def __repr__(self):
        return f"<JournalEntry {self.id} - {self.emotion} ({self.sentiment_score})>"