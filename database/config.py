import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

class Config:
    # Supabase configuration
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')

    # Flask configuration
    FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'your-secret-key')

    # Email configuration
    EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    IMAP_SERVER = os.getenv('IMAP_SERVER', 'imap.gmail.com')

    # OpenAI configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    # Database configuration
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres.hietukryntqccgvqgtj:Sxu44802376@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"
    SQLALCHEMY_TRACK_MODIFICATIONS = False 