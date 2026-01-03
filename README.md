# ACE Elite Leaderboard - Competitive Programming Tracker & Student Career Portal

A comprehensive Flask-based platform that automatically tracks competitive programming statistics and manages student career development including applications, certifications, and internships.

## ✨ Features

### 🔐 Dual Authentication System
- **Admin Dashboard**: Secure admin panel for managing students and viewing analytics
- **Student Portal**: Individual student accounts with profile management

### 📊 Automated CP Statistics Tracking
- Real-time data fetching from Codeforces, LeetCode, and CodeChef
- Historical performance tracking with interactive charts
- Daily automated snapshots (APScheduler)
- No manual data entry required

### 💼 Student Career Management
- **Applications Tracking**: Record job/internship applications with status (Applied, Accepted, Rejected, Interview, Offer)
- **Certifications Management**: Upload and track certifications with credential URLs
- **Internship Records**: Track internships with ongoing status, stipend, work mode
- **File Uploads**: Secure upload for offer letters and certificates (PDF, images)

### 👨‍💼 Admin Features
- Bulk student import via Excel (with CGPA, attendance, semester, branch)
- Password management for students
- Activate/deactivate student accounts
- View all applications, certifications, and internships across students
- Advanced filtering and search capabilities

### 📈 Analytics & Visualization
- Interactive Chart.js graphs for rating/solving trends
- Platform-specific leaderboards (CF, LC, CC)
- Career statistics overview (applications, certifications, internships)
- Historical data comparison

## 🛠 Tech Stack

- **Backend**: Flask 3.0, SQLAlchemy 3.1, APScheduler
- **Database**: SQLite (production-ready for 2000+ students with connection pooling)
- **Frontend**: Jinja2 templates, Chart.js for visualizations
- **Security**: Werkzeug password hashing (scrypt), session-based auth
- **APIs**: Codeforces API, LeetCode GraphQL, CodeChef web scraping
- **File Handling**: Werkzeug secure_filename, configurable upload limits

## 🚀 Quick Start

### 1. Clone and Setup Environment
```bash
cd "ACE Elite Leaderboard"
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Application
```bash
copy .env.example .env
```

Edit `.env` and set:
```env
SECRET_KEY=your-super-secret-key-here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password
```

### 4. Initialize Database
```bash
python init_db.py
```

### 5. Launch Application
```bash
python app.py
```

Access at: `http://localhost:5000`

## 📖 User Guide

### Admin Workflow

1. **Login**: Navigate to `/admin/login`
2. **Import Students**: Click "📤 Import Students (Excel)" button
   - Use template: `student_import_template.xlsx`
   - Required columns: `roll_number`, `name`, `email`
   - Optional: `cgpa`, `attendance_percentage`, `semester`, `branch`, `phone`, platform usernames
3. **Manage Students**: View leaderboard, reset passwords, toggle accounts
4. **Monitor Career Progress**: View applications, certifications, internships

### Student Workflow

1. **First Login**: Use roll number as both username and password
   - Or register at `/register` with email and custom password
2. **Update Profile**: Change password, add contact info, update coding handles
3. **Track Applications**: Add companies applied to with status updates and offer letters
4. **Record Certifications**: Upload certificates with credential details
5. **Log Internships**: Track internship experiences with descriptions
6. **View Dashboard**: Monitor CP performance with interactive charts

## 📁 Project Structure

```
ACE Elite Leaderboard/
├── app.py                          # Main Flask application (all routes)
├── models.py                       # SQLAlchemy database models
├── auth.py                         # Authentication & authorization
├── scheduler.py                    # APScheduler for automated stats fetching
├── config.py                       # Configuration class
├── init_db.py                      # Database initialization script
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
├── services/                       # Platform API integrations
│   ├── codeforces.py              # Codeforces API client
│   ├── leetcode.py                # LeetCode GraphQL client
│   └── codechef.py                # CodeChef scraper
├── templates/                      # Jinja2 HTML templates
│   ├── base.html                  # Base template with navbar
│   ├── admin_login.html
│   ├── admin_dashboard.html
│   ├── admin_import_students.html
│   ├── student_login.html
│   ├── student_register.html
│   ├── student_dashboard.html
│   ├── student_profile.html
│   ├── student_edit_profile.html
│   ├── student_my_applications.html
│   ├── student_edit_application.html
│   ├── student_my_certifications.html
│   ├── student_edit_certification.html
│   ├── student_my_internships.html
│   └── student_edit_internship.html
├── static/
│   ├── css/
│   │   └── style.css              # Main stylesheet
│   └── js/                        # JavaScript files (if any)
├── uploads/                        # Student file uploads (offer letters, certificates)
├── instance/
│   └── cp_tracker.db              # SQLite database (auto-generated)
└── student_import_template.xlsx   # Excel template for bulk import

```

## 🗄 Database Schema

### Students Table
- Personal: roll_number, name, email, phone
- Academic: attendance_percentage, cgpa, semester, branch (admin-only)
- CP Platforms: cf_handle, lc_username, cc_username
- Social: linkedin_url, github_url
- Auth: password_hash, is_active

### Applications Table
- company_name, position, application_date, status
- job_type, location, package_offered
- offer_letter_url (file upload)

### Certifications Table
- name, issuing_organization, issue_date, expiry_date
- credential_id, credential_url
- certificate_file_url (file upload)

### Internships Table
- company_name, position, start_date, end_date, is_ongoing
- location, work_mode, stipend
- description, skills_used

### StatsSnapshots Table
- Historical CP data: platform, rating, solved, timestamp
- LeetCode breakdown: easy, medium, hard

## 🔒 Security

- ✅ Werkzeug password hashing (scrypt algorithm)
- ✅ Session-based authentication with secure cookies
- ✅ File upload validation (type and size limits)
- ✅ SQL injection protection via SQLAlchemy ORM
- ✅ CSRF protection ready (Flask-WTF integration recommended for production)
- ✅ Secure filename sanitization

## 📊 Excel Import Format

Required columns:
- `roll_number`: Student ID
- `name`: Full name
- `email`: Email address

Optional columns:
- `attendance_percentage`: 0-100
- `cgpa`: 0-10 scale
- `semester`: Integer (1-8)
- `branch`: e.g., "Computer Science"
- `phone`: Contact number
- `cf_handle`: Codeforces username
- `lc_username`: LeetCode username  
- `cc_username`: CodeChef username

Default password for imported students: `roll_number`

## 🔄 Automated Jobs

APScheduler runs daily at midnight:
- Fetches latest stats from all platforms
- Updates ratings, solved counts, problem breakdowns
- Stores historical snapshots for trending

## 📈 Scaling for Production

For 2000+ students:
- ✅ SQLite with connection pooling (pool_size=10, max_overflow=20)
- ✅ Efficient indexing on frequently queried columns
- ✅ Lazy loading for relationships
- 🔄 Upgrade to PostgreSQL for enterprise scale
- 🔄 Consider Redis for session management
- 🔄 Move uploads to cloud storage (AWS S3/Azure Blob)

## 🐛 Troubleshooting

**Students can't login?**
- Ensure password is set (default: roll_number)
- Check `is_active` status
- Admin can reset password from student profile

**Stats not updating?**
- Check platform usernames are correct
- Verify API connectivity
- Review scheduler logs in terminal

**File uploads failing?**
- Check `uploads/` directory exists
- Verify file size < 16MB
- Ensure allowed extensions: pdf, png, jpg, jpeg, doc, docx

## 📝 License

Educational project for ACE Elite Institution

## 🤝 Contributing

Contact admin for contribution guidelines.
- Admin-only route protection
- CSRF protection

## License

MIT
