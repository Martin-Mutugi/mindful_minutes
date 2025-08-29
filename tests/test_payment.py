import pytest
from app import create_app
from extensions import db
from models import User
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

def test_premium_page_access(client):
    response = client.get('/premium')
    assert response.status_code == 302
    assert '/login' in response.location

    login(client)
    response = client.get('/premium')
    assert response.status_code == 200
    assert b'Premium Membership' in response.data

def test_premium_upgrade_simulated(client):
    login(client)

    user = User.query.filter_by(email='test@example.com').first()
    assert not user.is_premium

    # Simulate upgrade manually (bypassing external API)
    user.is_premium = True
    db.session.commit()

    upgraded_user = User.query.filter_by(email='test@example.com').first()
    assert upgraded_user.is_premium
