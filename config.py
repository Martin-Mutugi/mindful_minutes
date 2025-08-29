import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')  # ✅ Corrected
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Hugging Face API
    HUGGING_FACE_API_KEY = os.getenv('HUGGING_FACE_API_KEY')

    # IntaSend API
    INTASEND_PUBLIC_KEY = os.getenv('INTASEND_PUBLIC_KEY')
    INTASEND_SECRET_KEY = os.getenv('INTASEND_SECRET_KEY')
    INTASEND_TEST_MODE = os.getenv('INTASEND_TEST_MODE', 'true').lower() == 'true'
