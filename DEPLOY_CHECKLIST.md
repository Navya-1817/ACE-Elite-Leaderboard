# 🚀 Render Deployment Checklist

## Before Deploying

- [x] Code working locally ✅
- [ ] Push code to GitHub
- [ ] Create PostgreSQL database on Render
- [ ] Create Web Service on Render
- [ ] Set environment variables

---

## Required Environment Variables for Render

```bash
# Set these in Render Dashboard → Environment tab:

DATABASE_URL=<paste-internal-database-url-from-render>
SECRET_KEY=<generate-with-command-below>
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<your-secure-password>
FLASK_ENV=production
```

### Generate SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Render Configuration

**Build Command:**
```bash
./build.sh
```

**Start Command:**
```bash
gunicorn app:app --workers 4 --timeout 120 --bind 0.0.0.0:$PORT
```

**Runtime:** Python 3

**Plan:** Free (750 hours/month)

---

## Post-Deployment Steps

1. **Create Admin Account:**
   - Run `init_db.py` locally first to test, OR
   - Admin will be auto-created on first startup with credentials from environment variables

2. **Import Students:**
   - Login to admin dashboard
   - Go to "Import Students (Excel)"
   - Upload Excel file with columns: name, roll_number, email, cf_handle, lc_username, cc_username

3. **First Stats Refresh:**
   - Click "Update All Stats" button in admin dashboard
   - Stats will fetch in background (may take a few minutes)
   - Scheduler runs automatically every 24 hours after that

---

## Important Notes for Free Tier

✅ **Database:** PostgreSQL free tier (1GB storage)
✅ **Web Service:** Spins down after 15min inactivity, boots in ~30sec
✅ **Scheduler:** Runs in-process (uses web service hours, NOT separate cron job)
✅ **Sessions:** 7-day expiration configured

⚠️ **Free Tier Limits:**
- 750 hours/month for web service
- Services spin down after 15min of inactivity
- Cold starts take ~30 seconds
- Database limited to 1GB

💡 **Tips:**
- First load after inactivity will be slow (cold start)
- Stats refresh happens in background (won't timeout)
- Keep scheduler running in web service (it's already optimized)

---

## Troubleshooting

### App won't start:
- Check Render logs for errors
- Verify DATABASE_URL is set correctly
- Ensure build.sh has execute permissions (`chmod +x build.sh`)

### Students can't login:
- Check if student exists in database
- Verify password was set correctly
- Default password = roll_number (if imported via Excel)

### Stats not updating:
- Click "Update All Stats" button manually first time
- Check logs for API errors
- Scheduler runs every 24 hours automatically

### Database issues:
- Verify DATABASE_URL uses `postgresql://` (NOT `postgres://`)
- Check PostgreSQL database is running in Render
- Verify connection pool settings in config.py

---

## Support

For detailed deployment guide, see: [RENDER_DEPLOY.md](RENDER_DEPLOY.md)
