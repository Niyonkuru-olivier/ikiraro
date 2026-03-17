"""
api/index.py
Vercel serverless entry point for the UMUHUZA Flask app.
Place this file at:  api/index.py
"""

import sys
import os
import traceback

# ---------------------------------------------------------------------------
# Make the project root importable from /var/task/api/index.py
# ---------------------------------------------------------------------------
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Set working directory so relative paths (templates, static, datasets) work
os.chdir(parent_dir)

# ---------------------------------------------------------------------------
# Try to import the Flask app
# ---------------------------------------------------------------------------
flask_app      = None
import_error   = None
error_trace    = None

try:
    from app import app as flask_app
    app = flask_app  # Vercel looks for `app`

except Exception as import_error_exception:
    import_error = import_error_exception
    error_trace  = traceback.format_exc()

    # -----------------------------------------------------------------------
    # Build a helpful diagnostic page so you can see exactly what failed
    # -----------------------------------------------------------------------
    _COMMON_FIXES = {
        "flask_cors":     "Flask-Cors==4.0.1",
        "flask_sqlalchemy": "Flask-SQLAlchemy==3.1.1",
        "flask_login":    "Flask-Login==0.6.3",
        "flask_mail":     "Flask-Mail==0.10.0",
        "sqlalchemy":     "SQLAlchemy==2.0.36",
        "jwt":            "PyJWT==2.9.0",
        "requests":       "requests==2.32.3",
        "pandas":         "pandas==2.2.3",
        "openpyxl":       "openpyxl==3.1.5",
        "reportlab":      "reportlab==4.2.5",
        "dotenv":         "python-dotenv==1.0.1",
        "pymysql":        "PyMySQL==1.1.1",
        "psycopg2":       "psycopg2-binary==2.9.10",
        "itsdangerous":   "itsdangerous==2.2.0",
        "werkzeug":       "Werkzeug==3.0.6",
        "numpy":          "numpy==1.26.4",
        "pytz":           "pytz==2024.1",
    }

    def _missing_package_hint(err_str: str) -> str:
        """Return a suggested requirements.txt line for the missing module."""
        err_lower = err_str.lower()
        for key, package in _COMMON_FIXES.items():
            if key in err_lower:
                return package
        return ""

    hint = _missing_package_hint(str(import_error))

    def error_app(environ, start_response):
        """WSGI fallback that renders a diagnostic HTML page."""
        hint_html = (
            f"""
            <div class="hint">
                <strong>Quick fix — add this line to <code>requirements.txt</code>:</strong>
                <pre>{hint}</pre>
                Then commit &amp; push to trigger a Vercel redeploy.
            </div>
            """
            if hint
            else ""
        )

        env_vars = {
            "DATABASE_URL":      "✅ Set" if os.environ.get("DATABASE_URL")      else "❌ NOT SET",
            "SECRET_KEY":        "✅ Set" if os.environ.get("SECRET_KEY")        else "❌ NOT SET",
            "WEATHER_API":       "✅ Set" if os.environ.get("WEATHER_API")       else "❌ NOT SET",
            "MAIL_USERNAME":     "✅ Set" if os.environ.get("MAIL_USERNAME")     else "❌ NOT SET",
            "MAIL_PASSWORD":     "✅ Set" if os.environ.get("MAIL_PASSWORD")     else "❌ NOT SET",
            "JWT_SECRET":        "✅ Set" if os.environ.get("JWT_SECRET")        else "⚠️  Not set (uses SECRET_KEY)",
        }
        env_rows = "".join(
            f"<tr><td><code>{k}</code></td><td>{v}</td></tr>"
            for k, v in env_vars.items()
        )

        body = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>UMUHUZA — Import Error</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Segoe UI', Arial, sans-serif;
      background: #0f1923;
      color: #e2e8f0;
      padding: 40px 20px;
      min-height: 100vh;
    }}
    .card {{
      max-width: 860px;
      margin: 0 auto;
      background: #1a2535;
      border-radius: 12px;
      padding: 36px 40px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    }}
    h1 {{ color: #fc8181; font-size: 1.6rem; margin-bottom: 8px; }}
    h2 {{ color: #90cdf4; font-size: 1.1rem; margin: 24px 0 10px; }}
    .badge {{
      display: inline-block;
      background: #fc8181;
      color: #1a202c;
      font-size: 0.75rem;
      font-weight: 700;
      padding: 2px 10px;
      border-radius: 20px;
      margin-bottom: 16px;
    }}
    .error-box {{
      background: #2d1f1f;
      border-left: 4px solid #fc8181;
      padding: 14px 18px;
      border-radius: 6px;
      font-family: monospace;
      font-size: 0.95rem;
      color: #fed7d7;
      word-break: break-all;
    }}
    .hint {{
      background: #1a3a2a;
      border-left: 4px solid #68d391;
      padding: 14px 18px;
      border-radius: 6px;
      margin-top: 16px;
      color: #c6f6d5;
    }}
    .hint pre {{
      margin-top: 8px;
      font-family: monospace;
      font-size: 1rem;
      background: #0f2a1a;
      padding: 8px 12px;
      border-radius: 4px;
      color: #9ae6b4;
    }}
    pre.trace {{
      background: #0d1b2a;
      border: 1px solid #2d3748;
      padding: 16px;
      border-radius: 6px;
      font-family: monospace;
      font-size: 0.8rem;
      color: #a0aec0;
      overflow-x: auto;
      white-space: pre-wrap;
      word-break: break-word;
      max-height: 320px;
      overflow-y: auto;
    }}
    table {{ width: 100%; border-collapse: collapse; }}
    td {{ padding: 8px 12px; border-bottom: 1px solid #2d3748; font-size: 0.9rem; }}
    td:first-child {{ color: #a0aec0; width: 220px; }}
    ol {{ padding-left: 20px; }}
    ol li {{ margin: 8px 0; color: #cbd5e0; font-size: 0.95rem; }}
    ol li code {{ background: #2d3748; padding: 2px 6px; border-radius: 3px; font-size: 0.9rem; }}
    a {{ color: #63b3ed; }}
  </style>
</head>
<body>
  <div class="card">
    <span class="badge">500 Import Error</span>
    <h1>Application failed to start</h1>

    <h2>Error</h2>
    <div class="error-box">{str(import_error)}</div>
    {hint_html}

    <h2>Full traceback</h2>
    <pre class="trace">{error_trace}</pre>

    <h2>Environment variables</h2>
    <table>{env_rows}</table>

    <h2>How to fix</h2>
    <ol>
      <li>Add any missing package to <code>requirements.txt</code> in your repo root.</li>
      <li>Make sure all environment variables above are set in
          <strong>Vercel → Project → Settings → Environment Variables</strong>.</li>
      <li>Commit and push — Vercel will rebuild automatically.</li>
      <li>Check <strong>Vercel → Deployments → Build logs</strong> for pip install errors.</li>
    </ol>
  </div>
</body>
</html>"""

        status  = "500 Internal Server Error"
        headers = [("Content-Type", "text/html; charset=utf-8"),
                   ("Content-Length", str(len(body.encode("utf-8"))))]
        start_response(status, headers)
        return [body.encode("utf-8")]

    app = error_app


# ---------------------------------------------------------------------------
# Vercel Python runtime calls this module-level `app` as a WSGI application.
# No extra handler wrapping needed.
# ---------------------------------------------------------------------------