from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Admin(db.Model):
    """Admin user model for dashboard access"""
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<Admin {self.username}>'


class Student(db.Model):
    """Student model with platform handles and authentication"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(255))
    
    # Platform handles
    cf_handle = db.Column(db.String(100), index=True)  # Codeforces
    lc_username = db.Column(db.String(100), index=True)  # LeetCode
    cc_username = db.Column(db.String(100), index=True)  # CodeChef
    
    # Academic details (admin-only, imported from Excel)
    attendance_percentage = db.Column(db.Float)
    cgpa = db.Column(db.Float)
    semester = db.Column(db.Integer)
    branch = db.Column(db.String(100))
    
    # Contact details
    phone = db.Column(db.String(20))
    linkedin_url = db.Column(db.String(200))
    github_url = db.Column(db.String(200))
    
    # Metadata
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship to stats
    stats_snapshots = db.relationship('StatsSnapshot', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password against hash"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<Student {self.name} ({self.roll_number})>'
    
    def get_latest_stats(self, platform):
        """Get most recent stats for a platform"""
        return self.stats_snapshots.filter_by(platform=platform).order_by(StatsSnapshot.timestamp.desc()).first()
    
    def get_stats_history(self, platform, days=30):
        """Get stats history for a platform"""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        return self.stats_snapshots.filter(
            StatsSnapshot.platform == platform,
            StatsSnapshot.timestamp >= cutoff
        ).order_by(StatsSnapshot.timestamp.asc()).all()


class StatsSnapshot(db.Model):
    """Daily stats snapshot for each platform"""
    __tablename__ = 'stats_snapshots'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    
    # Platform identifier
    platform = db.Column(db.String(20), nullable=False, index=True)  # 'CF', 'LC', 'CC'
    
    # Common stats
    rating = db.Column(db.Integer)  # Nullable (LeetCode doesn't have rating)
    max_rating = db.Column(db.Integer)  # For Codeforces
    solved = db.Column(db.Integer, default=0)  # Total problems solved
    
    # LeetCode specific
    easy = db.Column(db.Integer)  # Nullable
    medium = db.Column(db.Integer)  # Nullable
    hard = db.Column(db.Integer)  # Nullable
    
    # Metadata
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    fetch_status = db.Column(db.String(20), default='success')  # success, failed, not_found
    error_message = db.Column(db.Text)  # Store error details if fetch failed
    
    # Composite index for efficient queries
    __table_args__ = (
        db.Index('idx_student_platform_timestamp', 'student_id', 'platform', 'timestamp'),
    )
    
    def __repr__(self):
        return f'<StatsSnapshot {self.platform} Student#{self.student_id} @ {self.timestamp}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'platform': self.platform,
            'rating': self.rating,
            'max_rating': self.max_rating,
            'solved': self.solved,
            'easy': self.easy,
            'medium': self.medium,
            'hard': self.hard,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'fetch_status': self.fetch_status
        }


class Application(db.Model):
    """Track job/company applications for students"""
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    
    # Application details
    company_name = db.Column(db.String(200), nullable=False)
    position = db.Column(db.String(200), nullable=False)
    application_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='applied')  # applied, accepted, rejected, pending
    
    # Optional details
    job_type = db.Column(db.String(50))  # internship, full-time, part-time
    location = db.Column(db.String(200))
    package_offered = db.Column(db.String(100))  # Salary/stipend if offered
    notes = db.Column(db.Text)  # Additional notes
    
    # File uploads
    offer_letter_url = db.Column(db.String(500))  # Uploaded offer letter
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    student = db.relationship('Student', backref=db.backref('applications', lazy='dynamic', cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<Application {self.company_name} - {self.position} ({self.status})>'


class Certification(db.Model):
    """Track certifications earned by students"""
    __tablename__ = 'certifications'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    
    # Certification details
    name = db.Column(db.String(200), nullable=False)
    issuing_organization = db.Column(db.String(200), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date)  # Optional, some certs don't expire
    credential_id = db.Column(db.String(200))
    credential_url = db.Column(db.String(500))  # Link to verify certificate
    
    # Optional details
    description = db.Column(db.Text)
    skills = db.Column(db.Text)  # Comma-separated skills
    
    # File upload
    certificate_file_url = db.Column(db.String(500))  # Uploaded certificate PDF/image
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    student = db.relationship('Student', backref=db.backref('certifications', lazy='dynamic', cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<Certification {self.name} - {self.issuing_organization}>'


class Internship(db.Model):
    """Track internships completed or ongoing by students"""
    __tablename__ = 'internships'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    
    # Internship details
    company_name = db.Column(db.String(200), nullable=False)
    position = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)  # Nullable for ongoing internships
    is_ongoing = db.Column(db.Boolean, default=False)
    
    # Optional details
    location = db.Column(db.String(200))
    work_mode = db.Column(db.String(50))  # remote, on-site, hybrid
    stipend = db.Column(db.String(100))
    description = db.Column(db.Text)  # Work done, projects, responsibilities
    skills_used = db.Column(db.Text)  # Comma-separated skills
    certificate_url = db.Column(db.String(500))  # Link to certificate if any
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    student = db.relationship('Student', backref=db.backref('internships', lazy='dynamic', cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<Internship {self.company_name} - {self.position}>'
