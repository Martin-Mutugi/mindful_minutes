# test_db.py
from app import create_app, db

app = create_app()

with app.app_context():
    try:
        db.engine.connect()
        print("✅ Successfully connected to MySQL database!")
    except Exception as e:
        print(f"❌ Connection failed: {e}")