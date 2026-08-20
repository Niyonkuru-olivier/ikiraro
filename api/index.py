"""
api/index.py
Vercel serverless entry point for the UMUHUZA Flask app.
Place this file at:  api/index.py
"""

import os
import sys

# Make the project root importable from /var/task/api/index.py
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Set working directory so relative paths (templates, static, datasets) work
os.chdir(parent_dir)

# Import the Flask app for Vercel
from app import app

if __name__ == "__main__":
    app.run()