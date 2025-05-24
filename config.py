import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # Database configuration (for future implementation)
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///health_tracker.db'
    
    # Application settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'uploads'
    
    # Health tracking settings
    MIN_SLEEP_HOURS = 0
    MAX_SLEEP_HOURS = 24
    MIN_WATER_GLASSES = 0
    MAX_WATER_GLASSES = 30
    MAX_SCREEN_TIME = 24
    
    # Chat settings
    MAX_CHAT_MESSAGE_LENGTH = 500
    CHAT_HISTORY_LIMIT = 50
    
    # Analytics settings
    DEFAULT_TREND_DAYS = 30
    MIN_DATA_POINTS_FOR_INSIGHTS = 5
    
    # Security settings
    SESSION_TIMEOUT = 3600  # 1 hour
    MAX_LOGIN_ATTEMPTS = 5
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    DATABASE_URL = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}