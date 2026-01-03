from functools import wraps
from flask import session, redirect, url_for, flash
from models import Admin, Student


def login_required(f):
    """Decorator to protect admin-only routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


def student_login_required(f):
    """Decorator to protect student-only routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'student_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('student_login'))
        return f(*args, **kwargs)
    return decorated_function


def authenticate_admin(username, password):
    """
    Authenticate admin credentials
    Returns Admin object if valid, None otherwise
    """
    admin = Admin.query.filter_by(username=username).first()
    
    if admin and admin.check_password(password):
        return admin
    return None


def authenticate_student(roll_number, password):
    """
    Authenticate student credentials
    Returns Student object if valid, None otherwise
    """
    student = Student.query.filter_by(roll_number=roll_number).first()
    
    if student and student.check_password(password) and student.is_active:
        return student
    return None


def login_admin(admin):
    """Store admin session data"""
    session['admin_id'] = admin.id
    session['admin_username'] = admin.username
    session.permanent = True  # Use permanent session


def logout_admin():
    """Clear admin session data"""
    session.pop('admin_id', None)
    session.pop('admin_username', None)


def login_student(student):
    """Store student session data"""
    session['student_id'] = student.id
    session['student_name'] = student.name
    session['student_roll'] = student.roll_number


def logout_student():
    """Clear student session data"""
    session.pop('student_id', None)
    session.pop('student_name', None)
    session.pop('student_roll', None)


def is_admin_logged_in():
    """Check if admin is logged in"""
    return 'admin_id' in session


def is_student_logged_in():
    """Check if student is logged in"""
    return 'student_id' in session


def get_current_student():
    """Get currently logged in student"""
    if 'student_id' in session:
        return Student.query.get(session['student_id'])
    return None


def get_current_admin():
    """Get currently logged in admin or None"""
    if 'admin_id' in session:
        return Admin.query.get(session['admin_id'])
    return None
