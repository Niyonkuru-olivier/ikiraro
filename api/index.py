"""
Vercel Serverless Function Wrapper for Flask App
This file serves as the entry point for Vercel serverless functions
"""
import sys
import os
import traceback

# Add parent directory to path to import app
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Set working directory to project root for static files
os.chdir(parent_dir)

# Import the Flask app
flask_app = None
import_error = None
error_trace = None

try:
    from app import app as flask_app
    app = flask_app
except Exception as import_error_exception:
    # Store error for later use
    import_error = import_error_exception
    error_trace = traceback.format_exc()
    
    def error_app(environ, start_response):
        """Error handler app when import fails"""
        error_msg = f"""<html><body>
            <h1>Application Import Error</h1>
            <p><strong>Error:</strong> {str(import_error)}</p>
            <pre>{error_trace}</pre>
            <p>Please check:</p>
            <ul>
                <li>All dependencies are in requirements.txt</li>
                <li>Vercel build logs for more details</li>
                <li>Environment variables are set correctly</li>
            </ul>
        </body></html>"""
        status = '500 Internal Server Error'
        headers = [('Content-Type', 'text/html; charset=utf-8')]
        start_response(status, headers)
        return [error_msg.encode('utf-8')]
    
    app = error_app

# Export for Vercel
# Vercel Python runtime will call this as a WSGI application

