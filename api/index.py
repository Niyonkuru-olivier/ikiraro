"""
Vercel Serverless Function Wrapper for Flask App
This file serves as the entry point for Vercel serverless functions
"""
import sys
import os

# Add parent directory to path to import app
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import the Flask app
from app import app as application

# Vercel Python runtime expects the WSGI app to be available
# Export as 'app' for Vercel to recognize it
app = application

# For compatibility, also export as handler
handler = app

