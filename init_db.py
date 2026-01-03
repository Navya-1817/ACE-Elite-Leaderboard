from flask import Flask
from models import db, Admin
from config import Config
import os

def init_database():
    """Initialize the database with tables and default admin"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Ensure instance folder exists
    instance_path = os.path.join(os.path.dirname(__file__), 'instance')
    os.makedirs(instance_path, exist_ok=True)
    
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        
        # Create default admin if not exists
        admin_username = app.config['ADMIN_USERNAME']
        admin_password = app.config['ADMIN_PASSWORD']
        
        if not Admin.query.filter_by(username=admin_username).first():
            admin = Admin(username=admin_username)
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print(f"✓ Default admin created: {admin_username}")
        else:
            print(f"✓ Admin '{admin_username}' already exists")
        
        print("✓ Database initialized successfully!")
        print(f"✓ Database location: {app.config['SQLALCHEMY_DATABASE_URI']}")

if __name__ == '__main__':
    init_database()
