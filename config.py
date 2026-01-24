import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DATABASE = os.environ.get('DATABASE') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tickets.db')
    WTF_CSRF_ENABLED = True

    # Session cookie configuration - 1 year lifetime
    REMEMBER_COOKIE_DURATION = timedelta(days=365)
    REMEMBER_COOKIE_SECURE = os.environ.get('COOKIE_SECURE', 'true').lower() == 'true'
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'

    # AWS SES Email Configuration
    MAIL_ENABLED = os.environ.get('MAIL_ENABLED', 'false').lower() == 'true'
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    SES_SENDER_EMAIL = os.environ.get('SES_SENDER_EMAIL', 'noreply@example.com')
    APP_NAME = os.environ.get('APP_NAME', 'Ticket Allocation')
    APP_URL = os.environ.get('APP_URL', 'http://localhost:5000')
