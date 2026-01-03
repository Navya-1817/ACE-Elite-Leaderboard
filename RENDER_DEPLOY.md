# 🚀 Render Deployment Guide

## ✅ Files Ready for Render

Your app is now configured for Render with:
- ✅ `runtime.txt` - Python 3.13.1
- ✅ `Procfile` - Gunicorn with 4 workers
- ✅ `build.sh` - Auto database initialization
- ✅ `requirements.txt` - Updated with gunicorn
- ✅ `config.py` - PostgreSQL auto-detection
- ✅ `app.py` - Dynamic PORT handling

---

## 📋 Deployment Steps

### Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Ready for Render deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### Step 2: Create Render Account
1. Go to https://render.com
2. Sign up with GitHub
3. Authorize Render to access your repositories

### Step 3: Create PostgreSQL Database
1. In Render Dashboard → Click "New +"
2. Select "PostgreSQL"
3. Configure:
   - **Name**: `ace-elite-db`
   - **Database**: `cptracker`
   - **User**: `cptracker_user`
   - **Region**: Choose closest to you
   - **Plan**: Free
4. Click "Create Database"
5. **IMPORTANT**: Copy the "Internal Database URL" (starts with `postgresql://`)

### Step 4: Create Web Service
1. Dashboard → "New +" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - **Name**: `ace-elite-leaderboard`
   - **Region**: Same as database
   - **Branch**: `main`
   - **Root Directory**: (leave blank)
   - **Runtime**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn app:app --workers 4 --timeout 120 --bind 0.0.0.0:$PORT`
   - **Plan**: Free

### Step 5: Add Environment Variables
In your web service, go to "Environment" tab and add:

```
DATABASE_URL = [paste Internal Database URL from Step 3]
SECRET_KEY = [generate random 50-character string]
ADMIN_USERNAME = admin
ADMIN_PASSWORD = [your secure password]
FLASK_ENV = production
```

**To generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Step 6: Deploy
1. Click "Create Web Service"
2. Render will:
   - Clone your repository
   - Run `build.sh` (installs dependencies + initializes database)
   - Start gunicorn server
3. Wait 5-10 minutes for first deploy
4. Your app will be live at: `https://ace-elite-leaderboard.onrender.com`

---

## 🎯 Post-Deployment

### Access Your App
- **Admin Login**: `https://your-app.onrender.com/admin/login`
- **Student Login**: `https://your-app.onrender.com/student/login`

### Import Students
1. Login as admin
2. Click "📤 Import Students (Excel)"
3. Upload your Excel file
4. Students created with password = roll_number

### Monitor
- Dashboard → Logs (see real-time activity)
- Dashboard → Metrics (see performance)

---

## ⚡ Important Notes

### Free Tier Limitations
- **Sleep after 15 min idle** (wakes in ~30 sec on next request)
- **750 hours/month** (enough for always-on if needed)
- **PostgreSQL**: 1GB storage (good for 10,000+ students)

### File Uploads
⚠️ **Render's free tier has ephemeral storage** - uploaded files (offer letters, certificates) will be lost on restart.

**Solutions:**
1. **Use Cloudinary** (free 25GB) for images/PDFs
2. **Use AWS S3** (free 5GB for 12 months)
3. **Upgrade Render** to persistent storage ($7/month)

For now, uploads work but may be lost on app restart.

### Performance Tips
- **First request slow?** App is waking from sleep
- **Stats not updating?** Scheduler runs daily at midnight
- **Database slow?** Check you're using PostgreSQL (not SQLite)

---

## 🔧 Troubleshooting

### Build Fails
```bash
# Check logs in Render Dashboard
# Common issues:
# 1. Missing requirements.txt - already fixed ✅
# 2. Wrong Python version - check runtime.txt
# 3. Build script not executable:
chmod +x build.sh
git add build.sh
git commit -m "Make build.sh executable"
git push
```

### Database Connection Error
```
# Verify DATABASE_URL in Environment tab
# Should start with: postgresql://
# NOT: postgres://
```

### App Not Starting
```
# Check Start Command in Settings:
gunicorn app:app --workers 4 --timeout 120 --bind 0.0.0.0:$PORT
```

---

## 📊 Scaling Beyond Free Tier

When you hit limits:
1. **Upgrade Render** ($7/month for starter)
2. **Add Redis** for caching
3. **Use CDN** for static files
4. **Add persistent storage** for uploads

---

## ✅ Quick Checklist

Before deploying, verify:
- [ ] Code pushed to GitHub
- [ ] PostgreSQL database created on Render
- [ ] Internal Database URL copied
- [ ] Environment variables set (4 total)
- [ ] Build command: `./build.sh`
- [ ] Start command: `gunicorn app:app --workers 4 --timeout 120 --bind 0.0.0.0:$PORT`

**Ready to deploy? Push to GitHub and follow Step 2!**
