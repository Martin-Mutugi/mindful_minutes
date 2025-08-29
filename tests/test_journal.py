import pytest
from app import create_app
from extensions import db
from models import User, JournalEntry
from werkzeug.security import generate_password_hash

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            user = User(
                username='testuser',
                email='test@example.com',
                password_hash=generate_password_hash('testpass')
            )
            db.session.add(user)
            db.session.commit()
            yield client
            db.session.remove()
            db.drop_all()

def login(client):
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'testpass'
    }, follow_redirects=True)

def test_journal_entry_success(client):
    login(client)
    response = client.post('/journal', data={
        'content': 'I feel great today!'
    }, follow_redirects=True)

    assert response.status_code == 200
    entry = JournalEntry.query.first()
    assert entry is not None
    assert entry.content == 'I feel great today!'
    assert entry.sentiment_score is not None
    assert entry.emotion in ['Positive', 'Neutral', 'Negative']

def test_journal_entry_too_short(client):
    login(client)
    response = client.post('/journal', data={
        'content': 'Hi'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Journal entry is too short" in response.data
    assert JournalEntry.query.count() == 0
