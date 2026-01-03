# ⚡ Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac
```

Edit `.env`:
```env
SECRET_KEY=change-this-to-random-string
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password
```

### 3. Initialize Database
```bash
python init_db.py
```

### 4. Start Application
```bash
python app.py
```
Or double-click `start.bat` (Windows)

### 5. Access the Portal
- **Admin Login**: http://localhost:5000/admin/login
- **Student Login**: http://localhost:5000/student/login
- **Student Register**: http://localhost:5000/register

---

## 👨‍💼 Admin Workflow

### First Login
1. Go to `/admin/login`
2. Use credentials from `.env`
3. You'll see the main dashboard

### Import Students (Bulk Upload)
1. Click **"📤 Import Students (Excel)"** button
2. Download or use `student_import_template.xlsx`
3. Fill in student data:
   - **Required**: roll_number, name, email
   - **Optional**: cgpa, attendance_percentage, semester, branch, phone, platform usernames
4. Upload the Excel file
5. Students created with **default password = roll_number**

### Manage Students
- View leaderboard with CP statistics
- Click student name → View full profile
- Reset student passwords
- Activate/deactivate accounts
- View all applications, certifications, internships

---

## 🎓 Student Workflow

### Registration (Two Options)

**Option 1: Self-Registration**
1. Go to `/register`
2. Fill form with email, password, and platform usernames
3. Login immediately after registration

**Option 2: Admin Import**
1. Admin imports you via Excel
2. Login with:
   - Username: Your roll_number
   - Password: Your roll_number (change after first login!)

### First Steps
1. **Update Profile**: Click "Edit Profile"
   - Change password (recommended!)
   - Add/update email, phone, LinkedIn, GitHub
   - Update coding platform handles
2. **Track Applications**: Click "My Applications"
   - Add companies you've applied to
   - Update status (Applied → Interview → Offer → Accepted)
   - Upload offer letters (PDF/images)
3. **Record Certifications**: Click "My Certifications"
   - Add certifications with details
   - Upload certificate files
4. **Log Internships**: Click "My Internships"
   - Add internship experiences
   - Mark as ongoing or completed

### Dashboard Features
- View your CP performance charts (Codeforces, LeetCode, CodeChef)
- See career statistics (applications, certifications, internships)
- Track your coding progress over time

---

## 📊 Excel Import Template

### Required Columns
| Column | Type | Example |
|--------|------|---------|
| roll_number | Text | 23AG1A0545 |
| name | Text | John Doe |
| email | Email | john@student.edu |

### Optional Columns
| Column | Type | Example |
|--------|------|---------|
| attendance_percentage | Number | 85.5 |
| cgpa | Number | 8.5 |
| semester | Integer | 6 |
| branch | Text | Computer Science |
| phone | Text | +91-9876543210 |
| cf_handle | Text | tourist |
| lc_username | Text | leetcode_user |
| cc_username | Text | codechef_user |

**Note**: Download `student_import_template.xlsx` for a pre-formatted example.

---

## 🔄 Automated Features

### Daily Statistics Fetch
- **Schedule**: Runs automatically at midnight
- **What it does**: Fetches latest ratings and solved counts from all CP platforms
- **Historical Data**: Stores daily snapshots for trending charts

### On-Demand Fetch
Restart the application to trigger immediate stats fetch for all students.

---

## 🐛 Troubleshooting

### Students Can't Login
**Problem**: "Invalid roll number or password"

**Solutions**:
- Check if student exists in system (Admin → Dashboard → Search)
- Verify roll number is correct (case-sensitive)
- Try default password = roll_number
- Admin can reset password from student profile

### Stats Not Showing
**Problem**: Dashboard shows no CP data

**Solutions**:
- Ensure platform usernames are added in profile
- Wait for scheduled fetch (midnight) or restart app
- Verify usernames exist on platforms (try manual search)
- Check terminal for API errors

### File Upload Fails
**Problem**: "Error uploading file"

**Solutions**:
- Check file size < 16MB
- Use allowed formats: PDF, PNG, JPG, JPEG, DOC, DOCX
- Ensure `uploads/` directory exists
- Check disk space

### Import Excel Errors
**Problem**: "Missing required columns"

**Solutions**:
- Use template: `student_import_template.xlsx`
- Ensure columns: roll_number, name, email (exact names, lowercase)
- Check for empty rows
- Verify email format is valid

---

## 🎯 Quick Reference

### Default Credentials
- **Admin**: Set in `.env` file
- **Students (imported)**: roll_number / roll_number
- **Students (registered)**: email / custom password

### Important URLs
- Admin Dashboard: `/admin/dashboard`
- Student Dashboard: `/student/dashboard`
- Import Students: `/admin/import_students`
- Register: `/register`

### File Upload Limits
- Maximum size: 16MB per file
- Allowed types: PDF, PNG, JPG, JPEG, DOC, DOCX
- Storage location: `uploads/` directory

### Admin-Only Fields
Students **cannot edit** these (set via Excel import only):
- Attendance percentage
- CGPA
- Semester
- Branch

### Student-Editable Fields
- Name, Email, Phone
- Password
- LinkedIn URL, GitHub URL
- Coding platform handles (cf_handle, lc_username, cc_username)
- Applications, Certifications, Internships (all fields)

---

## 📚 Next Steps

- Read [README.md](README.md) for comprehensive documentation
- See [PRODUCTION.md](PRODUCTION.md) for deployment guide
- Check terminal logs for real-time API fetch status

---

## ⚡ Pro Tips

1. **Change default admin password** in `.env` before deployment
2. **Import students in batches** if you have 1000+ students
3. **Validate platform usernames** before import (they must exist on platforms)
4. **Backup database** regularly: Copy `instance/cp_tracker.db`
5. **Students should change password** on first login for security
6. **Check logs** if stats aren't updating (terminal output shows API calls)

---

**Need help?** Check the troubleshooting section or review application logs in terminal.
