import pytest
from app import create_app
from extensions import db
from models import User

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

def test_register(client):
    response = client.post('/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    user = User.query.filter_by(email='test@example.com').first()
    assert user is not None
    assert user.username == 'testuser'

def test_login_success(client):
    client.post('/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass'
    })

    response = client.post('/login', data={
        'email': 'test@example.com',
        'password': 'testpass'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Dashboard" in response.data  # Optional: check content

def test_login_failure(client):
    response = client.post('/login', data={
        'email': 'wrong@example.com',
        'password': 'wrongpass'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Invalid credentials" in response.data
