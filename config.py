import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database - automatically handles PostgreSQL for production (Render, Heroku, Railway)
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///cp_tracker.db')
    
    # Fix for Heroku/Railway postgres:// to postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    # Render uses absolute paths, SQLite uses relative - handle both
    if not DATABASE_URL.startswith(('postgresql://', 'postgres://')):
        # SQLite - ensure absolute path for production
        if not DATABASE_URL.startswith('sqlite:////'):  # Not already absolute
            db_file = DATABASE_URL.replace('sqlite:///', '')
            abs_path = os.path.join(os.path.dirname(__file__), 'instance', db_file)
            DATABASE_URL = f'sqlite:///{abs_path}'
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Database connection pooling for better performance with many students
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 20
    }
    
    # Admin credentials
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    # Scheduler settings
    SCHEDULER_API_ENABLED = True
    FETCH_INTERVAL_HOURS = 24
    
    # Performance settings
    MAX_STUDENTS_PER_PAGE = 100  # For pagination
    STATS_HISTORY_DAYS = 30  # Limit chart data
    ENABLE_QUERY_CACHING = True
    
    # File upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'}
    
    # Production settings
    DEBUG = os.getenv('FLASK_ENV', 'development') == 'development'
    PORT = int(os.getenv('PORT', 5000))
