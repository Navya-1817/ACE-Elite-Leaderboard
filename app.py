import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from datetime import datetime, timedelta
from models import db, Admin, Student, StatsSnapshot, Application, Certification, Internship
from scheduler import scheduler
from config import Config
from sqlalchemy import func, and_
from services import codeforces_api, leetcode_api, codechef_api
from functools import wraps
from time import time
from werkzeug.utils import secure_filename
from auth import (
    login_required,
    is_admin_logged_in,
    logout_admin,
    authenticate_admin,
    login_admin,
    student_login_required, 
    authenticate_student, 
    login_student, 
    logout_student, 
    get_current_student,
    is_student_logged_in
)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Initialize scheduler
scheduler.init_app(app)

# File upload helper (defined after app is created)
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Simple cache decorator
def cached(timeout=300):
    """Simple cache decorator for view functions"""
    def decorator(f):
        cache = {}
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Create cache key from function name and args
            cache_key = f.__name__ + str(args) + str(sorted(kwargs.items()))
            now = time()
            
            # Check if cached and not expired
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if now - timestamp < timeout:
                    return result
            
            # Call function and cache result
            result = f(*args, **kwargs)
            cache[cache_key] = (result, now)
            return result
        return decorated_function
    return decorator


@app.route('/', methods=["GET", "HEAD"])
def health():
    return "OK", 200
def index():
    """Home page - redirect to appropriate dashboard"""
    if is_admin_logged_in():
        return redirect(url_for('admin_dashboard'))
    if is_student_logged_in():
        return redirect(url_for('student_dashboard'))
    return redirect(url_for('student_login'))


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if is_admin_logged_in():
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        admin = authenticate_admin(username, password)
        
        if admin:
            login_admin(admin)
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('admin_login.html')


@app.route('/admin/logout')
@login_required
def admin_logout():
    """Admin logout"""
    logout_admin()
    flash('Logged out successfully', 'info')
    return redirect(url_for('admin_login'))


@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard with leaderboard and navigation - Optimized for 2000+ students"""
    # Get filter parameters
    platform = request.args.get('platform', 'all')
    search = request.args.get('search', '').strip()
    sort_by = request.args.get('sort', 'rating')
    page = request.args.get('page', 1, type=int)
    per_page = 100  # Increased for better performance
    
    # Get career tracking stats (cached for 5 minutes)
    total_applications = Application.query.count()
    total_accepted = Application.query.filter_by(status='accepted').count()
    total_certifications = Certification.query.count()
    total_internships = Internship.query.count()
    
    # Get all students with optimized query
    students_query = Student.query
    
    # Apply search filter
    if search:
        students_query = students_query.filter(
            (Student.name.ilike(f'%{search}%')) |
            (Student.roll_number.ilike(f'%{search}%'))
        )
    
    # Get total count before pagination
    total_students = students_query.count()
    
    # Apply pagination - fetch only needed students
    students = students_query.limit(per_page).offset((page - 1) * per_page).all()
    
    # Optimized: Get all latest stats in bulk queries instead of N+1
    student_ids = [s.id for s in students]
    
    # Get latest stats for each platform in single queries
    cf_stats_subquery = db.session.query(
        StatsSnapshot.student_id,
        func.max(StatsSnapshot.timestamp).label('max_timestamp')
    ).filter(
        StatsSnapshot.platform == 'CF',
        StatsSnapshot.student_id.in_(student_ids)
    ).group_by(StatsSnapshot.student_id).subquery()
    
    cf_stats = db.session.query(StatsSnapshot).join(
        cf_stats_subquery,
        and_(
            StatsSnapshot.student_id == cf_stats_subquery.c.student_id,
            StatsSnapshot.timestamp == cf_stats_subquery.c.max_timestamp,
            StatsSnapshot.platform == 'CF'
        )
    ).all()
    cf_stats_dict = {s.student_id: s for s in cf_stats}
    
    lc_stats_subquery = db.session.query(
        StatsSnapshot.student_id,
        func.max(StatsSnapshot.timestamp).label('max_timestamp')
    ).filter(
        StatsSnapshot.platform == 'LC',
        StatsSnapshot.student_id.in_(student_ids)
    ).group_by(StatsSnapshot.student_id).subquery()
    
    lc_stats = db.session.query(StatsSnapshot).join(
        lc_stats_subquery,
        and_(
            StatsSnapshot.student_id == lc_stats_subquery.c.student_id,
            StatsSnapshot.timestamp == lc_stats_subquery.c.max_timestamp,
            StatsSnapshot.platform == 'LC'
        )
    ).all()
    lc_stats_dict = {s.student_id: s for s in lc_stats}
    
    cc_stats_subquery = db.session.query(
        StatsSnapshot.student_id,
        func.max(StatsSnapshot.timestamp).label('max_timestamp')
    ).filter(
        StatsSnapshot.platform == 'CC',
        StatsSnapshot.student_id.in_(student_ids)
    ).group_by(StatsSnapshot.student_id).subquery()
    
    cc_stats = db.session.query(StatsSnapshot).join(
        cc_stats_subquery,
        and_(
            StatsSnapshot.student_id == cc_stats_subquery.c.student_id,
            StatsSnapshot.timestamp == cc_stats_subquery.c.max_timestamp,
            StatsSnapshot.platform == 'CC'
        )
    ).all()
    cc_stats_dict = {s.student_id: s for s in cc_stats}
    
    # Build leaderboard data using bulk-fetched stats
    leaderboard_data = []
    
    for student in students:
        student_data = {
            'id': student.id,
            'name': student.name,
            'roll_number': student.roll_number,
            'cf_handle': student.cf_handle,
            'lc_username': student.lc_username,
            'cc_username': student.cc_username,
            'cf_stats': None,
            'lc_stats': None,
            'cc_stats': None
        }
        
        # Get stats from bulk-fetched dictionaries
        if student.cf_handle and student.id in cf_stats_dict:
            cf_stat = cf_stats_dict[student.id]
            if cf_stat.fetch_status == 'success':
                student_data['cf_stats'] = {
                    'rating': cf_stat.rating,
                    'max_rating': cf_stat.max_rating,
                    'solved': cf_stat.solved
                }
        
        if student.lc_username and student.id in lc_stats_dict:
            lc_stat = lc_stats_dict[student.id]
            if lc_stat.fetch_status == 'success':
                student_data['lc_stats'] = {
                    'solved': lc_stat.solved,
                    'easy': lc_stat.easy,
                    'medium': lc_stat.medium,
                    'hard': lc_stat.hard
                }
        
        if student.cc_username and student.id in cc_stats_dict:
            cc_stat = cc_stats_dict[student.id]
            if cc_stat.fetch_status == 'success':
                student_data['cc_stats'] = {
                    'rating': cc_stat.rating,
                    'solved': cc_stat.solved
                }
        
        leaderboard_data.append(student_data)
    
    # Apply platform filter and sorting
    if platform == 'CF':
        leaderboard_data = [s for s in leaderboard_data if s['cf_stats']]
        if sort_by == 'rating':
            leaderboard_data.sort(key=lambda x: x['cf_stats']['rating'], reverse=True)
        elif sort_by == 'solved':
            leaderboard_data.sort(key=lambda x: x['cf_stats']['solved'], reverse=True)
    
    elif platform == 'LC':
        leaderboard_data = [s for s in leaderboard_data if s['lc_stats']]
        if sort_by == 'solved':
            leaderboard_data.sort(key=lambda x: x['lc_stats']['solved'], reverse=True)
        elif sort_by == 'hard':
            leaderboard_data.sort(key=lambda x: x['lc_stats']['hard'], reverse=True)
    
    elif platform == 'CC':
        leaderboard_data = [s for s in leaderboard_data if s['cc_stats']]
        if sort_by == 'rating':
            leaderboard_data.sort(key=lambda x: x['cc_stats']['rating'], reverse=True)
        elif sort_by == 'solved':
            leaderboard_data.sort(key=lambda x: x['cc_stats']['solved'], reverse=True)
    
    # Calculate pagination
    total_pages = (total_students + per_page - 1) // per_page
    
    return render_template(
        'admin_dashboard.html',
        leaderboard=leaderboard_data,
        platform=platform,
        search=search,
        sort_by=sort_by,
        total_students=total_students,
        page=page,
        total_pages=total_pages,
        per_page=per_page,
        total_applications=total_applications,
        total_accepted=total_accepted,
        total_certifications=total_certifications,
        total_internships=total_internships
    )


@app.route('/admin/applications')
@login_required
def admin_applications():
    """View all student applications"""
    status_filter = request.args.get('status', 'all')
    search = request.args.get('search', '').strip()
    
    query = db.session.query(Application, Student).join(Student)
    
    if status_filter != 'all':
        query = query.filter(Application.status == status_filter)
    
    if search:
        query = query.filter(
            (Student.name.ilike(f'%{search}%')) |
            (Application.company_name.ilike(f'%{search}%')) |
            (Application.position.ilike(f'%{search}%'))
        )
    
    applications = query.order_by(Application.application_date.desc()).all()
    
    # Get statistics
    stats = {
        'total': Application.query.count(),
        'applied': Application.query.filter_by(status='applied').count(),
        'pending': Application.query.filter_by(status='pending').count(),
        'accepted': Application.query.filter_by(status='accepted').count(),
        'rejected': Application.query.filter_by(status='rejected').count()
    }
    
    return render_template('admin_applications.html', 
                         applications=applications, 
                         status_filter=status_filter,
                         search=search,
                         stats=stats)


@app.route('/admin/certifications')
@login_required
def admin_certifications():
    """View all student certifications"""
    search = request.args.get('search', '').strip()
    
    query = db.session.query(Certification, Student).join(Student)
    
    if search:
        query = query.filter(
            (Student.name.ilike(f'%{search}%')) |
            (Certification.name.ilike(f'%{search}%')) |
            (Certification.issuing_organization.ilike(f'%{search}%'))
        )
    
    certifications = query.order_by(Certification.issue_date.desc()).all()
    
    # Get popular certifications
    from sqlalchemy import func
    popular_certs = db.session.query(
        Certification.issuing_organization, 
        func.count(Certification.id).label('count')
    ).group_by(Certification.issuing_organization).order_by(func.count(Certification.id).desc()).limit(10).all()
    
    return render_template('admin_certifications.html', 
                         certifications=certifications,
                         search=search,
                         popular_certs=popular_certs,
                         total_count=Certification.query.count())


@app.route('/admin/internships')
@login_required
def admin_internships():
    """View all student internships"""
    status_filter = request.args.get('status', 'all')
    search = request.args.get('search', '').strip()
    
    query = db.session.query(Internship, Student).join(Student)
    
    if status_filter == 'ongoing':
        query = query.filter(Internship.is_ongoing == True)
    elif status_filter == 'completed':
        query = query.filter(Internship.is_ongoing == False)
    
    if search:
        query = query.filter(
            (Student.name.ilike(f'%{search}%')) |
            (Internship.company_name.ilike(f'%{search}%')) |
            (Internship.position.ilike(f'%{search}%'))
        )
    
    internships = query.order_by(Internship.start_date.desc()).all()
    
    # Get statistics
    stats = {
        'total': Internship.query.count(),
        'ongoing': Internship.query.filter_by(is_ongoing=True).count(),
        'completed': Internship.query.filter_by(is_ongoing=False).count()
    }
    
    # Get top companies
    top_companies = db.session.query(
        Internship.company_name, 
        func.count(Internship.id).label('count')
    ).group_by(Internship.company_name).order_by(func.count(Internship.id).desc()).limit(10).all()
    
    return render_template('admin_internships.html', 
                         internships=internships,
                         status_filter=status_filter,
                         search=search,
                         stats=stats,
                         top_companies=top_companies)


# ============ ADMIN EDIT ROUTES ============
@app.route('/admin/application/<int:app_id>/edit', methods=['POST'])
@login_required
def admin_edit_application(app_id):
    """Admin edit application"""
    application = Application.query.get_or_404(app_id)
    
    try:
        application.company_name = request.form.get('company_name', '').strip()
        application.position = request.form.get('position', '').strip()
        application.application_date = datetime.strptime(request.form.get('application_date'), '%Y-%m-%d').date()
        application.status = request.form.get('status', 'applied')
        application.job_type = request.form.get('job_type', '').strip() or None
        application.location = request.form.get('location', '').strip() or None
        application.package_offered = request.form.get('package_offered', '').strip() or None
        application.notes = request.form.get('notes', '').strip() or None
        
        db.session.commit()
        flash('Application updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating application: {str(e)}', 'error')
    
    return redirect(url_for('admin_applications'))


@app.route('/admin/application/<int:app_id>/delete', methods=['POST'])
@login_required
def admin_delete_application(app_id):
    """Admin delete application"""
    application = Application.query.get_or_404(app_id)
    
    try:
        db.session.delete(application)
        db.session.commit()
        flash('Application deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting application: {str(e)}', 'error')
    
    return redirect(url_for('admin_applications'))


@app.route('/admin/certification/<int:cert_id>/delete', methods=['POST'])
@login_required
def admin_delete_certification(cert_id):
    """Admin delete certification"""
    certification = Certification.query.get_or_404(cert_id)
    
    try:
        db.session.delete(certification)
        db.session.commit()
        flash('Certification deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting certification: {str(e)}', 'error')
    
    return redirect(url_for('admin_certifications'))


@app.route('/admin/internship/<int:internship_id>/delete', methods=['POST'])
@login_required
def admin_delete_internship(internship_id):
    """Admin delete internship"""
    internship = Internship.query.get_or_404(internship_id)
    
    try:
        db.session.delete(internship)
        db.session.commit()
        flash('Internship deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting internship: {str(e)}', 'error')
    
    return redirect(url_for('admin_internships'))


@app.route('/student/<int:student_id>')
def student_profile(student_id):
    """Student profile page with graphs"""
    student = Student.query.get_or_404(student_id)
    
    # Get stats history for charts (last 30 days)
    days = int(request.args.get('days', 30))
    
    cf_history = student.get_stats_history('CF', days) if student.cf_handle else []
    lc_history = student.get_stats_history('LC', days) if student.lc_username else []
    cc_history = student.get_stats_history('CC', days) if student.cc_username else []
    
    # Convert to dictionaries for JSON serialization
    cf_history_dict = [s.to_dict() for s in cf_history]
    lc_history_dict = [s.to_dict() for s in lc_history]
    cc_history_dict = [s.to_dict() for s in cc_history]
    
    return render_template(
        'student_profile.html',
        student=student,
        cf_history=cf_history_dict,
        lc_history=lc_history_dict,
        cc_history=cc_history_dict,
        days=days
    )


@app.route('/register', methods=['GET', 'POST'])
def student_register():
    """Student registration page"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        roll_number = request.form.get('roll_number', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        cf_handle = request.form.get('cf_handle', '').strip() or None
        lc_username = request.form.get('lc_username', '').strip() or None
        cc_username = request.form.get('cc_username', '').strip() or None
        
        # Validation
        if not name or not roll_number or not email or not password:
            flash('Name, Roll Number, Email, and Password are required', 'error')
            return render_template('student_register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('student_register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('student_register.html')
        
        if not cf_handle and not lc_username and not cc_username:
            flash('Please provide at least one platform username', 'error')
            return render_template('student_register.html')
        
        # Check if roll number already exists
        if Student.query.filter_by(roll_number=roll_number).first():
            flash('Roll number already registered', 'error')
            return render_template('student_register.html')
        
        # Check if email already exists
        if Student.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('student_register.html')
        
        # Validate platform usernames
        validation_errors = []
        
        if cf_handle:
            if not codeforces_api.validate_handle(cf_handle):
                validation_errors.append(f'Codeforces handle "{cf_handle}" not found')
        
        if lc_username:
            if not leetcode_api.validate_username(lc_username):
                validation_errors.append(f'LeetCode username "{lc_username}" not found')
        
        if cc_username:
            if not codechef_api.validate_username(cc_username):
                validation_errors.append(f'CodeChef username "{cc_username}" not found')
        
        if validation_errors:
            for error in validation_errors:
                flash(error, 'error')
            return render_template('student_register.html')
        
        # Create student
        student = Student(
            name=name,
            roll_number=roll_number,
            email=email,
            cf_handle=cf_handle,
            lc_username=lc_username,
            cc_username=cc_username,
            is_active=True
        )
        student.set_password(password)
        
        db.session.add(student)
        db.session.commit()
        
        # Fetch initial stats
        scheduler.fetch_student_stats(student.id)
        
        # Auto-login the student
        login_student(student)
        
        flash(f'Registration successful! Welcome, {name}!', 'success')
        return redirect(url_for('student_dashboard'))
    
    return render_template('student_register.html')


@app.route('/api/student/<int:student_id>/stats')
def api_student_stats(student_id):
    """API endpoint for student stats (for charts)"""
    student = Student.query.get_or_404(student_id)
    days = int(request.args.get('days', 30))
    
    cf_history = student.get_stats_history('CF', days) if student.cf_handle else []
    lc_history = student.get_stats_history('LC', days) if student.lc_username else []
    cc_history = student.get_stats_history('CC', days) if student.cc_username else []
    
    return jsonify({
        'cf': [s.to_dict() for s in cf_history],
        'lc': [s.to_dict() for s in lc_history],
        'cc': [s.to_dict() for s in cc_history]
    })


# ============ APPLICATION ROUTES ============
@app.route('/student/<int:student_id>/applications', methods=['GET', 'POST'])
def student_applications(student_id):
    """Manage student applications"""
    student = Student.query.get_or_404(student_id)
    
    if request.method == 'POST':
        try:
            application = Application(
                student_id=student_id,
                company_name=request.form.get('company_name', '').strip(),
                position=request.form.get('position', '').strip(),
                application_date=datetime.strptime(request.form.get('application_date'), '%Y-%m-%d').date(),
                status=request.form.get('status', 'applied'),
                job_type=request.form.get('job_type', '').strip() or None,
                location=request.form.get('location', '').strip() or None,
                package_offered=request.form.get('package_offered', '').strip() or None,
                notes=request.form.get('notes', '').strip() or None
            )
            
            db.session.add(application)
            db.session.commit()
            flash('Application added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding application: {str(e)}', 'error')
        
        return redirect(url_for('student_applications', student_id=student_id))
    
    applications = student.applications.order_by(Application.application_date.desc()).all()
    return render_template('student_applications.html', student=student, applications=applications)


@app.route('/student/<int:student_id>/application/<int:app_id>/edit', methods=['POST'])
def edit_application(student_id, app_id):
    """Edit an application"""
    application = Application.query.get_or_404(app_id)
    
    if application.student_id != student_id:
        flash('Unauthorized', 'error')
        return redirect(url_for('student_applications', student_id=student_id))
    
    try:
        application.company_name = request.form.get('company_name', '').strip()
        application.position = request.form.get('position', '').strip()
        application.application_date = datetime.strptime(request.form.get('application_date'), '%Y-%m-%d').date()
        application.status = request.form.get('status', 'applied')
        application.job_type = request.form.get('job_type', '').strip() or None
        application.location = request.form.get('location', '').strip() or None
        application.package_offered = request.form.get('package_offered', '').strip() or None
        application.notes = request.form.get('notes', '').strip() or None
        
        db.session.commit()
        flash('Application updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating application: {str(e)}', 'error')
    
    return redirect(url_for('student_applications', student_id=student_id))


@app.route('/student/<int:student_id>/application/<int:app_id>/delete', methods=['POST'])
def delete_application(student_id, app_id):
    """Delete an application"""
    application = Application.query.get_or_404(app_id)
    
    if application.student_id != student_id:
        flash('Unauthorized', 'error')
        return redirect(url_for('student_applications', student_id=student_id))
    
    try:
        db.session.delete(application)
        db.session.commit()
        flash('Application deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting application: {str(e)}', 'error')
    
    return redirect(url_for('student_applications', student_id=student_id))


# ============ CERTIFICATION ROUTES ============
@app.route('/student/<int:student_id>/certifications', methods=['GET', 'POST'])
def student_certifications(student_id):
    """Manage student certifications"""
    student = Student.query.get_or_404(student_id)
    
    if request.method == 'POST':
        try:
            expiry_date_str = request.form.get('expiry_date', '').strip()
            certification = Certification(
                student_id=student_id,
                name=request.form.get('name', '').strip(),
                issuing_organization=request.form.get('issuing_organization', '').strip(),
                issue_date=datetime.strptime(request.form.get('issue_date'), '%Y-%m-%d').date(),
                expiry_date=datetime.strptime(expiry_date_str, '%Y-%m-%d').date() if expiry_date_str else None,
                credential_id=request.form.get('credential_id', '').strip() or None,
                credential_url=request.form.get('credential_url', '').strip() or None,
                description=request.form.get('description', '').strip() or None,
                skills=request.form.get('skills', '').strip() or None
            )
            
            db.session.add(certification)
            db.session.commit()
            flash('Certification added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding certification: {str(e)}', 'error')
        
        return redirect(url_for('student_certifications', student_id=student_id))
    
    certifications = student.certifications.order_by(Certification.issue_date.desc()).all()
    return render_template('student_certifications.html', student=student, certifications=certifications)


@app.route('/student/<int:student_id>/certification/<int:cert_id>/delete', methods=['POST'])
def delete_certification(student_id, cert_id):
    """Delete a certification"""
    certification = Certification.query.get_or_404(cert_id)
    
    if certification.student_id != student_id:
        flash('Unauthorized', 'error')
        return redirect(url_for('student_certifications', student_id=student_id))
    
    try:
        db.session.delete(certification)
        db.session.commit()
        flash('Certification deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting certification: {str(e)}', 'error')
    
    return redirect(url_for('student_certifications', student_id=student_id))


# ============ INTERNSHIP ROUTES ============
@app.route('/student/<int:student_id>/internships', methods=['GET', 'POST'])
def student_internships(student_id):
    """Manage student internships"""
    student = Student.query.get_or_404(student_id)
    
    if request.method == 'POST':
        try:
            is_ongoing = request.form.get('is_ongoing') == 'on'
            end_date_str = request.form.get('end_date', '').strip()
            
            internship = Internship(
                student_id=student_id,
                company_name=request.form.get('company_name', '').strip(),
                position=request.form.get('position', '').strip(),
                start_date=datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date(),
                end_date=datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str and not is_ongoing else None,
                is_ongoing=is_ongoing,
                location=request.form.get('location', '').strip() or None,
                work_mode=request.form.get('work_mode', '').strip() or None,
                stipend=request.form.get('stipend', '').strip() or None,
                description=request.form.get('description', '').strip() or None,
                skills_used=request.form.get('skills_used', '').strip() or None,
                certificate_url=request.form.get('certificate_url', '').strip() or None
            )
            
            db.session.add(internship)
            db.session.commit()
            flash('Internship added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding internship: {str(e)}', 'error')
        
        return redirect(url_for('student_internships', student_id=student_id))
    
    internships = student.internships.order_by(Internship.start_date.desc()).all()
    return render_template('student_internships.html', student=student, internships=internships)


@app.route('/student/<int:student_id>/internship/<int:internship_id>/delete', methods=['POST'])
def delete_internship(student_id, internship_id):
    """Delete an internship"""
    internship = Internship.query.get_or_404(internship_id)
    
    if internship.student_id != student_id:
        flash('Unauthorized', 'error')
        return redirect(url_for('student_internships', student_id=student_id))
    
    try:
        db.session.delete(internship)
        db.session.commit()
        flash('Internship deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting internship: {str(e)}', 'error')
    
    return redirect(url_for('student_internships', student_id=student_id))


# ============================================================================
# STUDENT SELF-SERVICE ROUTES (Login, Dashboard, Profile, Career Management)
# ============================================================================

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    """Student login page"""
    if is_student_logged_in():
        return redirect(url_for('student_dashboard'))
    
    if request.method == 'POST':
        roll_number = request.form.get('roll_number', '').strip()
        password = request.form.get('password', '')
        
        student = authenticate_student(roll_number, password)
        
        if student:
            login_student(student)
            flash('Login successful!', 'success')
            return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid roll number or password', 'error')
    
    return render_template('student_login.html')


@app.route('/student/logout')
@student_login_required
def student_logout():
    """Student logout"""
    logout_student()
    flash('Logged out successfully', 'info')
    return redirect(url_for('student_login'))


@app.route('/student/dashboard')
@student_login_required
def student_dashboard():
    """Student's own dashboard"""
    student = get_current_student()
    
    # Get stats history
    days = int(request.args.get('days', 30))
    cf_history_raw = student.get_stats_history('CF', days) if student.cf_handle else []
    lc_history_raw = student.get_stats_history('LC', days) if student.lc_username else []
    cc_history_raw = student.get_stats_history('CC', days) if student.cc_username else []
    
    # Format for Chart.js
    cf_history = [{'date': s.timestamp.strftime('%Y-%m-%d'), 'value': s.rating or 0} for s in cf_history_raw]
    lc_history = [{'date': s.timestamp.strftime('%Y-%m-%d'), 'value': s.solved or 0} for s in lc_history_raw]
    cc_history = [{'date': s.timestamp.strftime('%Y-%m-%d'), 'value': s.rating or 0} for s in cc_history_raw]
    
    # Get career data counts
    app_count = student.applications.count()
    cert_count = student.certifications.count()
    intern_count = student.internships.count()
    
    return render_template('student_dashboard.html',
                         student=student,
                         cf_history=cf_history,
                         lc_history=lc_history,
                         cc_history=cc_history,
                         app_count=app_count,
                         cert_count=cert_count,
                         intern_count=intern_count)


@app.route('/student/profile/edit', methods=['GET', 'POST'])
@student_login_required
def student_edit_profile():
    """Student edit their own profile"""
    student = get_current_student()
    
    if request.method == 'POST':
        try:
            # Students can only edit these fields
            student.name = request.form.get('name', '').strip()
            student.email = request.form.get('email', '').strip()
            student.phone = request.form.get('phone', '').strip() or None
            student.cf_handle = request.form.get('cf_handle', '').strip() or None
            student.lc_username = request.form.get('lc_username', '').strip() or None
            student.cc_username = request.form.get('cc_username', '').strip() or None
            student.linkedin_url = request.form.get('linkedin_url', '').strip() or None
            student.github_url = request.form.get('github_url', '').strip() or None
            
            # Handle password change
            new_password = request.form.get('new_password', '').strip()
            if new_password:
                student.set_password(new_password)
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('student_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')
    
    return render_template('student_edit_profile.html', student=student)


@app.route('/student/my/applications', methods=['GET', 'POST'])
@student_login_required
def student_my_applications():
    """Student manage their own applications"""
    student = get_current_student()
    
    if request.method == 'POST':
        try:
            # Handle file upload
            offer_letter_url = None
            if 'offer_letter' in request.files:
                file = request.files['offer_letter']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{student.roll_number}_{int(time())}_{file.filename}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    offer_letter_url = f'/uploads/{filename}'
            
            application = Application(
                student_id=student.id,
                company_name=request.form.get('company_name', '').strip(),
                position=request.form.get('position', '').strip(),
                application_date=datetime.strptime(request.form.get('application_date'), '%Y-%m-%d').date(),
                status=request.form.get('status', 'applied'),
                job_type=request.form.get('job_type', '').strip() or None,
                location=request.form.get('location', '').strip() or None,
                package_offered=request.form.get('package_offered', '').strip() or None,
                notes=request.form.get('notes', '').strip() or None,
                offer_letter_url=offer_letter_url
            )
            
            db.session.add(application)
            db.session.commit()
            flash('Application added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding application: {str(e)}', 'error')
        
        return redirect(url_for('student_my_applications'))
    
    applications = student.applications.order_by(Application.application_date.desc()).all()
    return render_template('student_my_applications.html', student=student, applications=applications)


@app.route('/student/my/certifications', methods=['GET', 'POST'])
@student_login_required
def student_my_certifications():
    """Student manage their own certifications"""
    student = get_current_student()
    
    if request.method == 'POST':
        try:
            # Handle file upload
            cert_file_url = None
            if 'certificate_file' in request.files:
                file = request.files['certificate_file']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{student.roll_number}_{int(time())}_{file.filename}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    cert_file_url = f'/uploads/{filename}'
            
            expiry_date_str = request.form.get('expiry_date', '').strip()
            certification = Certification(
                student_id=student.id,
                name=request.form.get('name', '').strip(),
                issuing_organization=request.form.get('issuing_organization', '').strip(),
                issue_date=datetime.strptime(request.form.get('issue_date'), '%Y-%m-%d').date(),
                expiry_date=datetime.strptime(expiry_date_str, '%Y-%m-%d').date() if expiry_date_str else None,
                credential_id=request.form.get('credential_id', '').strip() or None,
                credential_url=request.form.get('credential_url', '').strip() or None,
                description=request.form.get('description', '').strip() or None,
                skills=request.form.get('skills', '').strip() or None,
                certificate_file_url=cert_file_url
            )
            
            db.session.add(certification)
            db.session.commit()
            flash('Certification added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding certification: {str(e)}', 'error')
        
        return redirect(url_for('student_my_certifications'))
    
    certifications = student.certifications.order_by(Certification.issue_date.desc()).all()
    return render_template('student_my_certifications.html', student=student, certifications=certifications)


@app.route('/student/my/internships', methods=['GET', 'POST'])
@student_login_required
def student_my_internships():
    """Student manage their own internships"""
    student = get_current_student()
    
    if request.method == 'POST':
        try:
            is_ongoing = request.form.get('is_ongoing') == 'on'
            end_date_str = request.form.get('end_date', '').strip()
            
            internship = Internship(
                student_id=student.id,
                company_name=request.form.get('company_name', '').strip(),
                position=request.form.get('position', '').strip(),
                start_date=datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date(),
                end_date=datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str and not is_ongoing else None,
                is_ongoing=is_ongoing,
                location=request.form.get('location', '').strip() or None,
                work_mode=request.form.get('work_mode', '').strip() or None,
                stipend=request.form.get('stipend', '').strip() or None,
                description=request.form.get('description', '').strip() or None,
                skills_used=request.form.get('skills_used', '').strip() or None,
                certificate_url=request.form.get('certificate_url', '').strip() or None
            )
            
            db.session.add(internship)
            db.session.commit()
            flash('Internship added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding internship: {str(e)}', 'error')
        
        return redirect(url_for('student_my_internships'))
    
    internships = student.internships.order_by(Internship.start_date.desc()).all()
    return render_template('student_my_internships.html', student=student, internships=internships)


@app.route('/student/application/<int:app_id>/delete', methods=['POST'])
@student_login_required
def student_delete_application(app_id):
    """Student delete their own application"""
    student = get_current_student()
    application = Application.query.get_or_404(app_id)
    
    if application.student_id != student.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('student_my_applications'))
    
    try:
        db.session.delete(application)
        db.session.commit()
        flash('Application deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting application: {str(e)}', 'error')
    
    return redirect(url_for('student_my_applications'))


@app.route('/student/application/<int:app_id>/edit', methods=['GET', 'POST'])
@student_login_required
def student_edit_application(app_id):
    """Student edit their own application"""
    student = get_current_student()
    application = Application.query.get_or_404(app_id)
    
    if application.student_id != student.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('student_my_applications'))
    
    if request.method == 'POST':
        try:
            application.company_name = request.form.get('company_name', '').strip()
            application.position = request.form.get('position', '').strip()
            application.application_date = datetime.strptime(request.form.get('application_date'), '%Y-%m-%d').date()
            application.status = request.form.get('status', 'applied')
            application.job_type = request.form.get('job_type', '').strip() or None
            application.location = request.form.get('location', '').strip() or None
            application.package_offered = request.form.get('package_offered', '').strip() or None
            application.notes = request.form.get('notes', '').strip() or None
            
            # Handle file upload
            if 'offer_letter' in request.files:
                file = request.files['offer_letter']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{student.roll_number}_{int(time())}_{file.filename}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    application.offer_letter_url = f'/uploads/{filename}'
            
            db.session.commit()
            flash('Application updated successfully!', 'success')
            return redirect(url_for('student_my_applications'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating application: {str(e)}', 'error')
    
    return render_template('student_edit_application.html', student=student, application=application)


@app.route('/student/certification/<int:cert_id>/delete', methods=['POST'])
@student_login_required
def student_delete_certification(cert_id):
    """Student delete their own certification"""
    student = get_current_student()
    certification = Certification.query.get_or_404(cert_id)
    
    if certification.student_id != student.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('student_my_certifications'))
    
    try:
        db.session.delete(certification)
        db.session.commit()
        flash('Certification deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting certification: {str(e)}', 'error')
    
    return redirect(url_for('student_my_certifications'))


@app.route('/student/certification/<int:cert_id>/edit', methods=['GET', 'POST'])
@student_login_required
def student_edit_certification(cert_id):
    """Student edit their own certification"""
    student = get_current_student()
    certification = Certification.query.get_or_404(cert_id)
    
    if certification.student_id != student.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('student_my_certifications'))
    
    if request.method == 'POST':
        try:
            certification.name = request.form.get('name', '').strip()
            certification.issuing_organization = request.form.get('issuing_organization', '').strip()
            certification.issue_date = datetime.strptime(request.form.get('issue_date'), '%Y-%m-%d').date()
            
            expiry_date_str = request.form.get('expiry_date', '').strip()
            certification.expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date() if expiry_date_str else None
            
            certification.credential_id = request.form.get('credential_id', '').strip() or None
            certification.credential_url = request.form.get('credential_url', '').strip() or None
            certification.description = request.form.get('description', '').strip() or None
            certification.skills = request.form.get('skills', '').strip() or None
            
            # Handle file upload
            if 'certificate_file' in request.files:
                file = request.files['certificate_file']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{student.roll_number}_{int(time())}_{file.filename}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    certification.certificate_file_url = f'/uploads/{filename}'
            
            db.session.commit()
            flash('Certification updated successfully!', 'success')
            return redirect(url_for('student_my_certifications'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating certification: {str(e)}', 'error')
    
    return render_template('student_edit_certification.html', student=student, certification=certification)


@app.route('/student/internship/<int:internship_id>/delete', methods=['POST'])
@student_login_required
def student_delete_internship(internship_id):
    """Student delete their own internship"""
    student = get_current_student()
    internship = Internship.query.get_or_404(internship_id)
    
    if internship.student_id != student.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('student_my_internships'))
    
    try:
        db.session.delete(internship)
        db.session.commit()
        flash('Internship deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting internship: {str(e)}', 'error')
    
    return redirect(url_for('student_my_internships'))


@app.route('/student/internship/<int:internship_id>/edit', methods=['GET', 'POST'])
@student_login_required
def student_edit_internship(internship_id):
    """Student edit their own internship"""
    student = get_current_student()
    internship = Internship.query.get_or_404(internship_id)
    
    if internship.student_id != student.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('student_my_internships'))
    
    if request.method == 'POST':
        try:
            internship.company_name = request.form.get('company_name', '').strip()
            internship.position = request.form.get('position', '').strip()
            internship.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
            
            is_ongoing = request.form.get('is_ongoing') == 'on'
            internship.is_ongoing = is_ongoing
            
            end_date_str = request.form.get('end_date', '').strip()
            internship.end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str and not is_ongoing else None
            
            internship.location = request.form.get('location', '').strip() or None
            internship.work_mode = request.form.get('work_mode', '').strip() or None
            internship.stipend = request.form.get('stipend', '').strip() or None
            internship.description = request.form.get('description', '').strip() or None
            internship.skills_used = request.form.get('skills_used', '').strip() or None
            internship.certificate_url = request.form.get('certificate_url', '').strip() or None
            
            db.session.commit()
            flash('Internship updated successfully!', 'success')
            return redirect(url_for('student_my_internships'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating internship: {str(e)}', 'error')
    
    return render_template('student_edit_internship.html', student=student, internship=internship)


# ============================================================================
# ADMIN EXCEL IMPORT & STUDENT MANAGEMENT ROUTES
# ============================================================================

@app.route('/admin/import_students', methods=['GET', 'POST'])
@login_required
def admin_import_students():
    """Admin import students data from Excel"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            flash('Invalid file format. Please upload an Excel file (.xlsx or .xls)', 'error')
            return redirect(request.url)
        
        try:
            # Read Excel file
            df = pd.read_excel(file)
            
            # Required columns
            required_columns = ['roll_number', 'name', 'email']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                flash(f'Missing required columns: {", ".join(missing_columns)}', 'error')
                return redirect(request.url)
            
            # Process each row
            created_count = 0
            updated_count = 0
            error_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    roll_number = str(row['roll_number']).strip()
                    name = str(row['name']).strip()
                    email = str(row['email']).strip()
                    
                    if not roll_number or not name or not email:
                        error_count += 1
                        errors.append(f"Row {index+2}: Missing required data")
                        continue
                    
                    # Check if student exists
                    student = Student.query.filter_by(roll_number=roll_number).first()
                    
                    if student:
                        # Update existing student (only admin-controlled fields)
                        if 'attendance_percentage' in row and pd.notna(row['attendance_percentage']):
                            student.attendance_percentage = float(row['attendance_percentage'])
                        
                        if 'cgpa' in row and pd.notna(row['cgpa']):
                            student.cgpa = float(row['cgpa'])
                        
                        if 'semester' in row and pd.notna(row['semester']):
                            student.semester = int(row['semester'])
                        
                        if 'branch' in row and pd.notna(row['branch']):
                            student.branch = str(row['branch']).strip()
                        
                        # Update name and email if different
                        student.name = name
                        student.email = email
                        
                        updated_count += 1
                    else:
                        # Create new student
                        student = Student(
                            roll_number=roll_number,
                            name=name,
                            email=email,
                            attendance_percentage=float(row['attendance_percentage']) if 'attendance_percentage' in row and pd.notna(row['attendance_percentage']) else None,
                            cgpa=float(row['cgpa']) if 'cgpa' in row and pd.notna(row['cgpa']) else None,
                            semester=int(row['semester']) if 'semester' in row and pd.notna(row['semester']) else None,
                            branch=str(row['branch']).strip() if 'branch' in row and pd.notna(row['branch']) else None,
                            phone=str(row['phone']).strip() if 'phone' in row and pd.notna(row['phone']) else None,
                            cf_handle=str(row['cf_handle']).strip() if 'cf_handle' in row and pd.notna(row['cf_handle']) else None,
                            lc_username=str(row['lc_username']).strip() if 'lc_username' in row and pd.notna(row['lc_username']) else None,
                            cc_username=str(row['cc_username']).strip() if 'cc_username' in row and pd.notna(row['cc_username']) else None
                        )
                        
                        # Set default password (roll_number)
                        student.set_password(roll_number)
                        
                        db.session.add(student)
                        created_count += 1
                
                except Exception as e:
                    error_count += 1
                    errors.append(f"Row {index+2}: {str(e)}")
            
            # Commit all changes
            db.session.commit()
            
            # Show summary
            flash(f'Import completed! Created: {created_count}, Updated: {updated_count}, Errors: {error_count}', 
                  'success' if error_count == 0 else 'warning')
            
            if errors:
                flash(f'Errors encountered: {"; ".join(errors[:5])}', 'error')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error processing file: {str(e)}', 'error')
        
        return redirect(url_for('admin_import_students'))
    
    # GET request - show import form
    total_students = Student.query.count()
    return render_template('admin_import_students.html', total_students=total_students)


@app.route('/admin/students/<int:student_id>/set_password', methods=['POST'])
@login_required
def admin_set_student_password(student_id):
    """Admin reset student password"""
    student = Student.query.get_or_404(student_id)
    
    new_password = request.form.get('new_password', '').strip()
    if not new_password:
        flash('Password cannot be empty', 'error')
        return redirect(request.referrer or url_for('admin_dashboard'))
    
    try:
        student.set_password(new_password)
        db.session.commit()
        flash(f'Password updated for {student.name}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating password: {str(e)}', 'error')
    
    return redirect(request.referrer or url_for('admin_dashboard'))


@app.route('/admin/students/<int:student_id>/toggle_active', methods=['POST'])
@login_required
def admin_toggle_student_active(student_id):
    """Admin activate/deactivate student account"""
    student = Student.query.get_or_404(student_id)
    
    try:
        student.is_active = not student.is_active
        db.session.commit()
        status = 'activated' if student.is_active else 'deactivated'
        flash(f'Student account {status}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error toggling status: {str(e)}', 'error')
    
    return redirect(request.referrer or url_for('admin_dashboard'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Start the scheduler
    scheduler.start()
    
    try:
        # Use PORT from environment (for Render) or default to 5000
        port = int(os.getenv('PORT', 5000))
        debug = os.getenv('FLASK_ENV', 'development') == 'development'
        app.run(debug=debug, host='0.0.0.0', port=port)
    except (KeyboardInterrupt, SystemExit):
        scheduler.stop()
