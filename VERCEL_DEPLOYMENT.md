# 🚀 Vercel Deployment Guide for UMUHUZA Project

This guide will help you deploy your Flask application to Vercel.

## 📋 Prerequisites

1. A GitHub account with your project pushed to a repository
2. A Vercel account (sign up at [vercel.com](https://vercel.com))
3. A cloud database (recommended options below)

## 🗄️ Database Setup

**⚠️ IMPORTANT:** Vercel serverless functions cannot connect to `localhost` databases. You need a cloud database.

### Recommended Options:

1. **PlanetScale** (MySQL-compatible, free tier available)
   - Sign up at [planetscale.com](https://planetscale.com)
   - Create a new database
   - Get the connection string (format: `mysql://user:password@host/database`)

2. **Neon** (PostgreSQL, free tier available)
   - Sign up at [neon.tech](https://neon.tech)
   - Create a new project
   - Get the connection string (format: `postgresql://user:password@host/database`)

3. **Supabase** (PostgreSQL, free tier available)
   - Sign up at [supabase.com](https://supabase.com)
   - Create a new project
   - Get the connection string from Settings > Database

## 📝 Step-by-Step Deployment

### Step 1: Install Vercel CLI (Optional)

You can deploy via the web interface, or use CLI:

```bash
npm i -g vercel
```

### Step 2: Deploy via Vercel Dashboard

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click "Add New Project"
3. Import your GitHub repository (`Niyonkuru-olivier/ikiraro`)
4. Vercel will automatically detect the configuration from `vercel.json`

### Step 3: Configure Environment Variables

In your Vercel project dashboard, go to **Settings > Environment Variables** and add:

#### Required Variables:

```
DATABASE_URL=mysql://user:password@host/database
# OR for PostgreSQL:
# DATABASE_URL=postgresql://user:password@host/database

SECRET_KEY=your-secret-key-here-change-this-to-random-string
```

#### Optional (for email functionality):

```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

**Generate a secure SECRET_KEY:**
```python
import secrets
print(secrets.token_urlsafe(32))
```

### Step 4: Initialize Database

After deployment, you'll need to create the database tables. You can:

1. **Option A:** Run a migration script locally pointing to your cloud database
2. **Option B:** Add a one-time setup route (for initial deployment only):

```python
@app.route('/setup-db', methods=['GET'])
def setup_db():
    if os.environ.get('SETUP_MODE') != 'true':
        return "Setup disabled", 403
    with app.app_context():
        db.create_all()
    return "Database initialized", 200
```

Set `SETUP_MODE=true` in Vercel, visit `/setup-db`, then remove the env var.

### Step 5: Deploy

Click **Deploy** in the Vercel dashboard. Vercel will:
1. Install dependencies from `requirements.txt`
2. Build your application
3. Deploy to production

## 🔍 Troubleshooting

### Database Connection Issues

- Verify your `DATABASE_URL` is correct
- Ensure your cloud database allows connections from Vercel IPs (most cloud databases do this automatically)
- Check database connection limits (free tiers may have limits)

### Static Files Not Loading

- Static files should be served from `/static/` route
- Verify file paths in templates use `url_for('static', filename='...')`

### Import Errors

- Ensure all dependencies are in `requirements.txt`
- Check that `api/index.py` correctly imports the Flask app

### Timeout Issues

- Current max duration is set to 30 seconds in `vercel.json`
- For longer operations, consider using background jobs or increasing the limit

## 📚 Project Structure

```
.
├── api/
│   └── index.py          # Vercel serverless function entry point
├── app.py                # Main Flask application
├── models.py             # Database models
├── requirements.txt      # Python dependencies
├── vercel.json          # Vercel configuration
├── static/              # Static files (CSS, JS, images)
├── templates/           # HTML templates
└── datasets/           # Data files
```

## ✅ Post-Deployment Checklist

- [ ] Verify database connection works
- [ ] Test user registration
- [ ] Test login functionality
- [ ] Test dashboard routes
- [ ] Verify static files load correctly
- [ ] Test email functionality (if configured)
- [ ] Check all role-based dashboards work

## 🔗 Useful Links

- [Vercel Documentation](https://vercel.com/docs)
- [Flask on Vercel](https://vercel.com/guides/deploying-python-with-vercel)
- [PlanetScale](https://planetscale.com)
- [Neon](https://neon.tech)
- [Supabase](https://supabase.com)

## 🆘 Need Help?

If you encounter issues:
1. Check Vercel deployment logs in the dashboard
2. Review environment variables are set correctly
3. Verify database connection string format
4. Ensure all dependencies are in `requirements.txt`

---

**Happy Deploying! 🎉**

