from extensions import db
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    is_premium = db.Column(db.Boolean, default=False)
    premium_since = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    journal_entries = db.relationship(
        'JournalEntry',
        backref='author',
        lazy=True,
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f"<User {self.username}>"


class JournalEntry(db.Model):
    __tablename__ = 'journal_entries'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    sentiment_score = db.Column(db.Float)
    emotion = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f"<JournalEntry {self.id} - {self.emotion}>"
