# 🔧 Troubleshooting Vercel Deployment

If your app shows nothing or an error at https://ikiraro1.vercel.app/, follow these steps:

## 🔍 Step 1: Check Vercel Deployment Logs

1. Go to your Vercel dashboard
2. Click on your project
3. Go to "Deployments" tab
4. Click on the latest deployment
5. Check the "Build Logs" and "Function Logs"

**Look for:**
- Import errors (missing dependencies)
- Database connection errors
- Template not found errors
- Environment variable errors

## 🛠️ Common Issues and Fixes

### Issue 1: Blank Page / Nothing Shows

**Possible Causes:**
- Database connection error (most common)
- Import error in api/index.py
- Missing environment variables

**Fix:**
1. Visit: `https://ikiraro1.vercel.app/test` - This should show a test page
2. If test page works, the issue is likely database-related
3. Check Vercel logs for specific error messages

### Issue 2: Database Connection Error

**Error Message:** "Database Connection Error" or "Could not connect to database"

**Fix:**
1. Set up a cloud database (PlanetScale, Neon, or Supabase)
2. Get the connection string
3. In Vercel dashboard → Settings → Environment Variables:
   - Add: `DATABASE_URL` with your database connection string
4. Redeploy

### Issue 3: Import Errors

**Error Message:** "No module named 'flask'" or similar

**Fix:**
1. Verify all packages are in `requirements.txt`
2. Check Vercel build logs for missing dependencies
3. Make sure `requirements.txt` is in the root directory

### Issue 4: Template Not Found

**Error Message:** "TemplateNotFound"

**Fix:**
1. Verify `templates/` folder is pushed to GitHub
2. Check that `templates/index.html` exists
3. Ensure templates are in the correct directory structure

## 🔐 Required Environment Variables

Add these in Vercel → Settings → Environment Variables:

### Minimum Required:
```
DATABASE_URL=your-database-connection-string
SECRET_KEY=your-random-secret-key
```

### Optional (for email):
```
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

## 📋 Quick Diagnostic Checklist

- [ ] Visit `/test` route - does it work?
- [ ] Check Vercel build logs - any errors?
- [ ] Check Vercel function logs - runtime errors?
- [ ] Is `DATABASE_URL` environment variable set?
- [ ] Is `SECRET_KEY` environment variable set?
- [ ] Are all files pushed to GitHub?
- [ ] Did you redeploy after adding environment variables?

## 🆘 Still Not Working?

1. **Check the test route:** Visit `https://ikiraro1.vercel.app/test`
   - If this works → Database issue
   - If this doesn't work → Import/configuration issue

2. **Share the error message** from Vercel logs for specific help

3. **Common fixes:**
   - Redeploy after adding environment variables
   - Clear Vercel cache and redeploy
   - Check that `api/index.py` exists and is correct

## 🔗 Useful Links

- Vercel Dashboard: https://vercel.com/dashboard
- Vercel Logs: Check in your project's deployment page
- Test Route: https://ikiraro1.vercel.app/test

