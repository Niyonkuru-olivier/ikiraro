# ---------------- Standard Library ----------------
from io import BytesIO
from datetime import datetime
from pathlib import Path
from flask import send_from_directory, render_template, jsonify, g
from flask import Flask, request, jsonify
from sqlalchemy import desc
from datetime import date

# ------------------ allow the Flutter for the development of app------
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

# ---------------- Third-party Packages ----------------
import pandas as pd
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, send_file
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, login_user, login_required,
    logout_user, current_user, UserMixin
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

# ---------------- Standard Library ----------------
import os
try:
    import jwt
except ModuleNotFoundError:
    import subprocess, sys
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'PyJWT'])
    import jwt
import functools
from dotenv import load_dotenv

from services.weather import weather_service

from services.chatbot import (
    generate_response_with_session as generate_chat_response,
    MissingAPIKeyError,
    RateLimitExceededError,
)

load_dotenv()

# ====================================================
# Flask App & Config
# ====================================================
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.environ.get('SECRET_KEY', 'supersecretkey-change-in-production')
app.config['PROFILE_UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads', 'profile_photos')
app.config['PROFILE_ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['PROFILE_MAX_FILE_SIZE_MB'] = int(os.environ.get('PROFILE_MAX_FILE_SIZE_MB', 4))
os.makedirs(app.config['PROFILE_UPLOAD_FOLDER'], exist_ok=True)

DATASETS_DIR = Path(app.root_path) / "datasets"

# ---------------- Database Config ----------------
database_url = os.environ.get('DATABASE_URL')
if database_url:
    if database_url.startswith('mysql://'):
        database_url = database_url.replace('mysql://', 'mysql+pymysql://', 1)
        try:
            from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
            parts = urlsplit(database_url)
            query_pairs = parse_qsl(parts.query, keep_blank_values=True)
            filtered_pairs = [(k, v) for k, v in query_pairs if k.lower() not in ('ssl-mode', 'ssl_mode', 'sslmode')]
            new_query = urlencode(filtered_pairs)
            database_url = urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))
        except Exception:
            for token in ['?ssl-mode=REQUIRED', '&ssl-mode=REQUIRED', '?ssl_mode=REQUIRED', '&ssl_mode=REQUIRED']:
                if token in database_url:
                    database_url = database_url.replace(token, '')
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True, 'pool_recycle': 300,
            'connect_args': {'connect_timeout': 10, 'ssl': {}}
        }
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    elif database_url.startswith('postgresql://') or database_url.startswith('postgres://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True, 'pool_recycle': 300,
            'connect_args': {'connect_timeout': 10}
        }
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:Da1wi2d$@localhost/umuhuza"
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True, 'pool_recycle': 300,
            'connect_args': {'connect_timeout': 10}
        }
else:
    local_db = os.environ.get('SQLALCHEMY_DATABASE_URI', "mysql+pymysql://root:Da1wi2d$@localhost/umuhuza")
    if local_db.startswith('mysql://'):
        local_db = local_db.replace('mysql://', 'mysql+pymysql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = local_db
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True, 'pool_recycle': 300,
        'connect_args': {'connect_timeout': 10}
    }

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
try:
    db = SQLAlchemy(app)
except Exception as e:
    app.logger.error(f"Database initialization error: {e}")
    db = SQLAlchemy(app)

# ---------------- Email Config ----------------
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', "oniyonkuru233@gmail.com")
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', "jvvd hzba fwqa jbnz")
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', "oniyonkuru233@gmail.com")
mail = Mail(app)

# ====================================================
# Helper: detect if request wants JSON
# ====================================================
def wants_json():
    """
    Returns True when the caller prefers a JSON response.
    Covers:
      - Content-Type: application/json
      - Accept: application/json
      - ?format=json query param
      - X-Requested-With: XMLHttpRequest  (AJAX)
    """
    if request.content_type and 'application/json' in request.content_type:
        return True
    if request.args.get('format') == 'json':
        return True
    accept = request.headers.get('Accept', '')
    if 'application/json' in accept:
        return True
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return True
    return False


# ====================================================
# JWT helpers (stateless token auth for API clients)
# ====================================================
JWT_SECRET = os.environ.get('JWT_SECRET', app.secret_key)
JWT_ALGORITHM = 'HS256'
JWT_EXP_SECONDS = int(os.environ.get('JWT_EXP_SECONDS', 86400))  # 24 h default


def generate_jwt(user):
    import time
    payload = {
        'sub': user.id,
        'email': user.email or '',
        'phone': user.phone or '',
        'role': user.role,
        'iat': int(time.time()),
        'exp': int(time.time()) + JWT_EXP_SECONDS,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt(token):
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def jwt_required(f):
    """
    Decorator that accepts EITHER a valid session cookie (Flask-Login)
    OR a Bearer JWT in the Authorization header.
    Sets flask_login's current_user when using JWT path.
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        # 1. Already authenticated via browser session
        if current_user.is_authenticated:
            return f(*args, **kwargs)

        # 2. Try Bearer token
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1]
            try:
                payload = decode_jwt(token)
                user = User.query.get(payload['sub'])
                if not user:
                    return jsonify({'error': 'User not found'}), 401
                login_user(user)
                return f(*args, **kwargs)
            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'Token expired'}), 401
            except jwt.InvalidTokenError as e:
                return jsonify({'error': f'Invalid token: {str(e)}'}), 401

        # 3. No auth at all
        if wants_json():
            return jsonify({'error': 'Authentication required'}), 401
        return redirect(url_for('login'))

    return decorated


# ====================================================
# Database Models
# ====================================================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=True)
    role = db.Column(db.String(50), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    profile_photo = db.Column(db.String(255), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email or '',
            'phone': self.phone or '',
            'role': self.role,
            'profile_photo': self.profile_photo or '',
        }


class MarketPrice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    commodity = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    province = db.Column(db.String(100), nullable=True)
    date = db.Column(db.Date, nullable=False)
    unit = db.Column(db.String(20), nullable=True)


class Inventory(db.Model):
    __tablename__ = 'inventory'
    id = db.Column(db.Integer, primary_key=True)
    dealer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_name = db.Column(db.String(150), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    unit = db.Column(db.String(20), default='kg')
    price = db.Column(db.Numeric(10, 2), nullable=True)
    last_updated = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    dealer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    processor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    product_name = db.Column(db.String(150), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit = db.Column(db.String(20), default='kg')
    status = db.Column(db.Enum('pending', 'approved', 'rejected', 'delivered', name='order_status'), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=True)


class Subsidy(db.Model):
    __tablename__ = 'subsidies'
    id = db.Column(db.Integer, primary_key=True)
    dealer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    commodity = db.Column(db.String(150), nullable=True)
    discount_percent = db.Column(db.Integer, default=0)
    valid_from = db.Column(db.Date, nullable=True)
    valid_to = db.Column(db.Date, nullable=True)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class Crop(db.Model):
    __tablename__ = 'crops'
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    crop_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=True)
    province = db.Column(db.String(100), nullable=True)


class Certification(db.Model):
    __tablename__ = 'certifications'
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(150), nullable=False)
    cert_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    processor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class DeliverySchedule(db.Model):
    __tablename__ = 'logistics'
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(150), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    destination = db.Column(db.String(200), nullable=True)
    delivery_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), default='scheduled')
    processor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


# ====================================================
# Flask-Login Config
# ====================================================
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception as e:
        app.logger.error(f"Error loading user {user_id}: {e}")
        return None


@login_manager.unauthorized_handler
def unauthorized():
    """Return JSON 401 for API clients, redirect for browsers."""
    if wants_json():
        return jsonify({'error': 'Authentication required. Send Bearer token in Authorization header.'}), 401
    return redirect(url_for('login'))


# ====================================================
# Token Serializer for Password Reset
# ====================================================
serializer = URLSafeTimedSerializer(app.secret_key)


# ====================================================
# Error Handlers
# ====================================================
@app.errorhandler(404)
def not_found(e):
    if wants_json():
        return jsonify({'error': 'Resource not found'}), 404
    return render_template('404.html'), 404


@app.errorhandler(500)
def handle_500_error(e):
    if wants_json():
        return jsonify({'error': 'Internal server error', 'detail': str(e)}), 500
    error_msg = str(e) if e else "Unknown error"
    return f"""
    <html><head><title>Error - UMUHUZA</title></head>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h1>Application Error</h1>
        <p><strong>Error:</strong> {error_msg}</p>
        <p><a href="/test">Try Test Route</a></p>
    </body></html>
    """, 500


@app.before_request
def before_request():
    pass


@app.context_processor
def inject_language_helpers():
    return {}


# ====================================================
# Profile Helpers
# ====================================================
def allowed_profile_file(filename: str) -> bool:
    return (
        bool(filename)
        and '.' in filename
        and filename.rsplit('.', 1)[1].lower() in app.config['PROFILE_ALLOWED_EXTENSIONS']
    )


def localized_weather_snapshot(force_refresh: bool = False):
    return weather_service.get_weather(force_refresh=force_refresh)


# ====================================================
# Routes — General Pages
# ====================================================
@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        return f"<h1>UMUHUZA Platform</h1><p>Template error: {str(e)}</p>", 200


# ====================================================
# *** AUTH API ENDPOINTS ***
# ====================================================

# ------------------------------------------------------------------
# POST /api/auth/login
# Body (JSON): { "email": "...", "password": "..." }
#   OR         { "phone": "...", "password": "..." }
#   OR         { "identifier": "...", "password": "..." }
# Returns: { "token": "...", "user": {...} }
# ------------------------------------------------------------------
@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """
    Pure JSON login endpoint — designed for Postman / mobile / SPA.

    Request body (JSON):
        {
            "email": "user@example.com",   // OR "phone" OR "identifier"
            "password": "yourpassword"
        }

    Success 200:
        {
            "token": "<JWT>",
            "expires_in": 86400,
            "user": { "id", "full_name", "email", "phone", "role" }
        }

    Error 400 / 401 / 500:
        { "error": "<message>" }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Request body must be JSON (Content-Type: application/json)'}), 400

    identifier = (
        data.get('identifier') or
        data.get('email') or
        data.get('phone') or ''
    ).strip()
    password = data.get('password', '')

    if not identifier or not password:
        return jsonify({'error': 'email (or phone / identifier) and password are required'}), 400

    try:
        user = User.query.filter(
            (User.email == identifier) | (User.phone == identifier)
        ).first()

        if user and user.role == 'promoter':
            user.role = 'dealer'
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()

        if not user:
            return jsonify({'error': 'No account found with that email or phone number'}), 401

        if not user.check_password(password):
            return jsonify({'error': 'Incorrect password'}), 401

        token = generate_jwt(user)
        return jsonify({
            'token': token,
            'expires_in': JWT_EXP_SECONDS,
            'token_type': 'Bearer',
            'user': user.to_dict(),
        }), 200

    except Exception as e:
        app.logger.error(f"API login error: {e}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500


# ------------------------------------------------------------------
# POST /api/auth/register
# Body (JSON): { "full_name", "email", "phone", "role", "password", "confirm_password" }
# Roles allowed: farmer, processor, researcher
# Returns: { "message": "...", "user": {...} }
# ------------------------------------------------------------------
@app.route('/api/auth/register', methods=['POST'])
def api_register():
    """
    Register a new user via JSON.

    Request body:
        {
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "+250788000000",
            "role": "farmer",          // farmer | processor | researcher
            "password": "Secret123!",
            "confirm_password": "Secret123!"
        }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400

    full_name = (data.get('full_name') or '').strip()
    email = (data.get('email') or '').strip() or None
    phone = (data.get('phone') or '').strip() or None
    role = (data.get('role') or '').strip().lower()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', password)

    if not full_name:
        return jsonify({'error': 'full_name is required'}), 400
    if not password:
        return jsonify({'error': 'password is required'}), 400
    if password != confirm_password:
        return jsonify({'error': 'Passwords do not match'}), 400

    if role == 'promoter':
        role = 'dealer'

    valid_roles = {'farmer', 'processor', 'researcher'}
    if role not in valid_roles:
        return jsonify({
            'error': f'Invalid role "{role}". Self-registration allows: {", ".join(sorted(valid_roles))}'
        }), 400

    if not email and not phone:
        return jsonify({'error': 'At least one of email or phone is required'}), 400

    try:
        existing = User.query.filter(
            (User.phone == phone) | (User.email == email)
        ).first()
        if existing:
            return jsonify({'error': 'An account with that email or phone already exists'}), 409

        new_user = User(full_name=full_name, phone=phone, email=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        token = generate_jwt(new_user)
        return jsonify({
            'message': 'Account created successfully',
            'token': token,
            'expires_in': JWT_EXP_SECONDS,
            'token_type': 'Bearer',
            'user': new_user.to_dict(),
        }), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"API register error: {e}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500


# ------------------------------------------------------------------
# GET /api/auth/me   — requires Bearer token
# ------------------------------------------------------------------
@app.route('/api/auth/me', methods=['GET'])
def api_me():
    """
    Returns the profile of the currently authenticated user.
    Pass:  Authorization: Bearer <token>
    """
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Authorization: Bearer <token> header required'}), 401
    token = auth_header.split(' ', 1)[1]
    try:
        payload = decode_jwt(token)
        user = User.query.get(payload['sub'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({'user': user.to_dict()}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError as e:
        return jsonify({'error': f'Invalid token: {str(e)}'}), 401


# ------------------------------------------------------------------
# POST /api/auth/logout   (stateless JWT — just a courtesy endpoint)
# ------------------------------------------------------------------
@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    """
    Stateless logout: the client should discard the token.
    If called from a browser session, the session cookie is also cleared.
    """
    logout_user()
    return jsonify({'message': 'Logged out successfully'}), 200


# ====================================================
# *** ORIGINAL HTML login / register routes (unchanged) ***
# ====================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles BOTH browser form POST and JSON POST.
    - Browser: redirects on success / renders template on failure
    - JSON (Postman / app): returns { token, user } or { error }
    """
    if request.method == 'POST':
        # Detect JSON vs form
        if wants_json():
            # Delegate to the pure API endpoint logic inline
            data = request.get_json(silent=True) or {}
            identifier = (
                data.get('identifier') or
                data.get('email') or
                data.get('phone') or ''
            ).strip()
            password = data.get('password', '')

            if not identifier or not password:
                return jsonify({'error': 'email (or phone) and password are required'}), 400

            try:
                user = User.query.filter(
                    (User.email == identifier) | (User.phone == identifier)
                ).first()

                if user and user.role == 'promoter':
                    user.role = 'dealer'
                    try:
                        db.session.commit()
                    except Exception:
                        db.session.rollback()

                if not user:
                    return jsonify({'error': 'No account found with that email or phone number'}), 401

                if not user.check_password(password):
                    return jsonify({'error': 'Incorrect password'}), 401

                login_user(user)
                token = generate_jwt(user)
                return jsonify({
                    'message': 'Login successful',
                    'token': token,
                    'expires_in': JWT_EXP_SECONDS,
                    'token_type': 'Bearer',
                    'user': user.to_dict(),
                }), 200

            except Exception as e:
                app.logger.error(f"Login error: {e}")
                return jsonify({'error': f'Database error: {str(e)}'}), 500

        # ---- Original HTML form path ----
        identifier = (request.form.get('identifier') or request.form.get('email') or '').strip()
        password = request.form.get('password')

        if not identifier or not password:
            flash('Email/Phone and password are required.', 'error')
            return render_template('login.html')

        try:
            user = User.query.filter(
                (User.email == identifier) | (User.phone == identifier)
            ).first()

            if user and user.role == 'promoter':
                user.role = 'dealer'
                try:
                    db.session.commit()
                except Exception as commit_err:
                    db.session.rollback()
                    app.logger.error(f"Failed to migrate promoter role: {commit_err}")

            if user:
                if user.check_password(password):
                    login_user(user)
                    flash('Login successful!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid password. Please try again.', 'error')
            else:
                flash('No user found with that email or phone number.', 'error')
        except Exception as e:
            app.logger.error(f"Login error: {str(e)}")
            import traceback
            app.logger.error(traceback.format_exc())
            flash(f'Database connection error: {str(e)}.', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


@app.route('/create-account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        # Support JSON body too
        if wants_json():
            return api_register()

        full_name = request.form.get('fullName')
        phone = request.form.get('phone')
        email = request.form.get('email')
        role = request.form.get('role')
        password = request.form.get('password')
        confirm_password = request.form.get('confirmPassword')

        if role == 'promoter':
            role = 'dealer'

        valid_roles = {'farmer', 'processor', 'researcher'}
        if role not in valid_roles:
            flash('Invalid role selected.', 'error')
            return redirect(url_for('create_account'))

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('create_account'))

        if User.query.filter((User.phone == phone) | (User.email == email)).first():
            flash('Phone or Email already registered.', 'error')
            return redirect(url_for('create_account'))

        new_user = User(full_name=full_name, phone=phone, email=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('create-account.html')


# ====================================================
# Admin Account Creation (Policy Maker Only)
# ====================================================
@app.route('/admin/create-account', methods=['GET', 'POST'])
@login_required
def admin_create_account():
    if current_user.role != 'policy':
        if wants_json():
            return jsonify({'error': 'Access denied. Only administrators can use this endpoint.'}), 403
        flash('Access denied.', 'error')
        return redirect(url_for('dash'))

    if request.method == 'POST':
        if wants_json():
            data = request.get_json(silent=True) or {}
            full_name = (data.get('full_name') or data.get('fullName') or '').strip()
            phone = (data.get('phone') or '').strip() or None
            email = (data.get('email') or '').strip() or None
            role = (data.get('role') or '').strip().lower()
            password = data.get('password', '')
            confirm_password = data.get('confirm_password', password)
        else:
            full_name = request.form.get('fullName')
            phone = request.form.get('phone')
            email = request.form.get('email')
            role = request.form.get('role')
            password = request.form.get('password')
            confirm_password = request.form.get('confirmPassword')

        valid_admin_roles = {'policy', 'dealer'}
        if role not in valid_admin_roles:
            if wants_json():
                return jsonify({'error': 'Invalid role. Only "policy" and "dealer" allowed here.'}), 400
            flash('Invalid role selected.', 'error')
            return redirect(url_for('admin_create_account'))

        if password != confirm_password:
            if wants_json():
                return jsonify({'error': 'Passwords do not match'}), 400
            flash('Passwords do not match.', 'error')
            return redirect(url_for('admin_create_account'))

        if User.query.filter((User.phone == phone) | (User.email == email)).first():
            if wants_json():
                return jsonify({'error': 'Phone or Email already registered'}), 409
            flash('Phone or Email already registered.', 'error')
            return redirect(url_for('admin_create_account'))

        new_user = User(full_name=full_name, phone=phone, email=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        if wants_json():
            return jsonify({'message': 'Account created', 'user': new_user.to_dict()}), 201
        flash('Account created successfully!', 'success')
        return redirect(url_for('admin_create_account'))

    return render_template('admin-create-account.html')


# ====================================================
# Password Reset
# ====================================================
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        if wants_json():
            data = request.get_json(silent=True) or {}
            email = (data.get('email') or '').strip()
        else:
            email = request.form.get('email')

        user = User.query.filter_by(email=email).first()

        if not user:
            if wants_json():
                return jsonify({'error': 'Email not registered'}), 404
            flash('Your email is not registered.', 'error')
            return redirect(url_for('forgot_password'))

        token = serializer.dumps(email, salt='password-reset-salt')
        reset_link = url_for('reset_password', token=token, _external=True)

        try:
            msg = Message(
                subject='Password Reset Request - UMUHUZA',
                recipients=[email],
                body=f"Hello {user.full_name},\n\nReset link: {reset_link}\n\nExpires in 30 minutes."
            )
            mail.send(msg)
            if wants_json():
                return jsonify({'message': 'Password reset link sent to your email'}), 200
            flash('Password reset link has been sent.', 'success')
        except Exception as e:
            if wants_json():
                return jsonify({'error': f'Error sending email: {str(e)}'}), 500
            flash(f'Error sending email: {str(e)}', 'error')

        return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=1800)
    except SignatureExpired:
        if wants_json():
            return jsonify({'error': 'Reset link expired'}), 400
        flash('The reset link has expired.', 'error')
        return redirect(url_for('forgot_password'))
    except BadSignature:
        if wants_json():
            return jsonify({'error': 'Invalid reset link'}), 400
        flash('Invalid reset link.', 'error')
        return redirect(url_for('forgot_password'))

    user = User.query.filter_by(email=email).first()
    if not user:
        if wants_json():
            return jsonify({'error': 'Invalid email in reset link'}), 404
        flash('Invalid email in reset link.', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        if wants_json():
            data = request.get_json(silent=True) or {}
            password = data.get('password', '')
            confirm_password = data.get('confirm_password', password)
        else:
            password = request.form.get('password')
            confirm_password = request.form.get('confirmPassword')

        if password != confirm_password:
            if wants_json():
                return jsonify({'error': 'Passwords do not match'}), 400
            flash('Passwords do not match.', 'error')
            return redirect(url_for('reset_password', token=token))

        user.set_password(password)
        db.session.commit()
        if wants_json():
            return jsonify({'message': 'Password reset successfully. Please log in.'}), 200
        flash('Password reset successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)


# ====================================================
# Profile Management
# ====================================================
@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    if wants_json():
        data = request.get_json(silent=True) or {}
        full_name = (data.get('full_name') or '').strip()
        phone = (data.get('phone') or '').strip()
        email = (data.get('email') or '').strip()
    else:
        full_name = (request.form.get('full_name') or '').strip()
        phone = (request.form.get('phone') or '').strip()
        email = (request.form.get('email') or '').strip()

    if not full_name:
        if wants_json():
            return jsonify({'error': 'full_name is required'}), 400
        flash('Full name is required.', 'error')
        return redirect(request.referrer or url_for('dashboard'))

    try:
        if email:
            if User.query.filter(User.email == email, User.id != current_user.id).first():
                if wants_json():
                    return jsonify({'error': 'Email already in use'}), 409
                flash('Email is already in use.', 'error')
                return redirect(request.referrer or url_for('dashboard'))
        if phone:
            if User.query.filter(User.phone == phone, User.id != current_user.id).first():
                if wants_json():
                    return jsonify({'error': 'Phone number already in use'}), 409
                flash('Telephone number is already in use.', 'error')
                return redirect(request.referrer or url_for('dashboard'))

        current_user.full_name = full_name
        current_user.phone = phone or None
        current_user.email = email or None
        db.session.commit()
        if wants_json():
            return jsonify({'message': 'Profile updated', 'user': current_user.to_dict()}), 200
        flash('Profile updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Profile update error: {e}")
        if wants_json():
            return jsonify({'error': str(e)}), 500
        flash('Unable to update profile right now.', 'error')

    return redirect(request.referrer or url_for('dashboard'))


@app.route('/profile/photo', methods=['POST'])
@login_required
def upload_profile_photo():
    file = request.files.get('profile_photo')
    if not file or file.filename == '':
        if wants_json():
            return jsonify({'error': 'No file provided'}), 400
        flash('Please choose a photo to upload.', 'error')
        return redirect(request.referrer or url_for('dashboard'))

    if not allowed_profile_file(file.filename):
        allowed = ', '.join(sorted(app.config['PROFILE_ALLOWED_EXTENSIONS']))
        if wants_json():
            return jsonify({'error': f'Unsupported file type. Allowed: {allowed}'}), 400
        flash(f'Unsupported file type. Allowed: {allowed}', 'error')
        return redirect(request.referrer or url_for('dashboard'))

    file.stream.seek(0, os.SEEK_END)
    size_bytes = file.stream.tell()
    file.stream.seek(0)
    max_bytes = app.config['PROFILE_MAX_FILE_SIZE_MB'] * 1024 * 1024
    if size_bytes > max_bytes:
        if wants_json():
            return jsonify({'error': f'File too large. Max {app.config["PROFILE_MAX_FILE_SIZE_MB"]}MB'}), 400
        flash(f'File is too large. Max {app.config["PROFILE_MAX_FILE_SIZE_MB"]}MB.', 'error')
        return redirect(request.referrer or url_for('dashboard'))

    ext = file.filename.rsplit('.', 1)[1].lower()
    safe_name = secure_filename(f"user_{current_user.id}_{int(datetime.utcnow().timestamp())}.{ext}")
    save_path = os.path.join(app.config['PROFILE_UPLOAD_FOLDER'], safe_name)
    try:
        file.save(save_path)
        if current_user.profile_photo:
            old_path = os.path.join(app.static_folder, current_user.profile_photo.replace('/', os.sep))
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except OSError:
                    pass
        current_user.profile_photo = os.path.join('uploads', 'profile_photos', safe_name).replace('\\', '/')
        db.session.commit()
        if wants_json():
            return jsonify({'message': 'Photo updated', 'profile_photo': current_user.profile_photo}), 200
        flash('Profile photo updated.', 'success')
    except Exception as e:
        db.session.rollback()
        if wants_json():
            return jsonify({'error': str(e)}), 500
        flash('Could not upload photo. Please try again.', 'error')

    return redirect(request.referrer or url_for('dashboard'))


# ====================================================
# Dashboard (Role-Based)
# ====================================================
@app.route('/dashboard')
@login_required
def dashboard():
    role = current_user.role
    weather_snapshot = localized_weather_snapshot()

    if role == 'farmer':
        try:
            market_prices = MarketPrice.query.order_by(MarketPrice.date.desc()).all()
        except Exception:
            market_prices = []

        try:
            inv_items = Inventory.query.order_by(Inventory.product_name.asc()).all()
            inventories = []
            for inv in inv_items:
                dealer = User.query.get(inv.dealer_id)
                inventories.append({
                    'id': inv.id, 'dealer_id': inv.dealer_id,
                    'dealer_name': dealer.full_name if dealer else f'Dealer #{inv.dealer_id}',
                    'dealer_email': dealer.email if dealer else '',
                    'dealer_phone': dealer.phone if dealer else '',
                    'product_name': inv.product_name, 'stock': inv.stock,
                    'unit': inv.unit or 'kg',
                    'price': float(inv.price) if inv.price is not None else None
                })
        except Exception:
            inventories = []

        try:
            my_orders = Order.query.filter_by(farmer_id=current_user.id).order_by(desc(Order.created_at)).all()
        except Exception:
            my_orders = []

        if wants_json():
            return jsonify({
                'role': role,
                'user': current_user.to_dict(),
                'market_prices': [{'id': p.id, 'commodity': p.commodity, 'price': p.price,
                                   'province': p.province, 'unit': p.unit,
                                   'date': p.date.isoformat()} for p in market_prices],
                'inventories': inventories,
                'my_orders': [{'id': o.id, 'product_name': o.product_name, 'quantity': o.quantity,
                               'unit': o.unit, 'status': o.status,
                               'created_at': o.created_at.isoformat() if o.created_at else None}
                              for o in my_orders],
            }), 200

        return render_template(
            'dashboards/farmer_dashboard.html',
            user=current_user, weather=weather_snapshot,
            market_prices=market_prices, inventories=inventories, my_orders=my_orders
        )

    elif role == 'dealer':
        return redirect(url_for('agro_dealer_dashboard'))

    elif role == 'processor':
        try:
            offers = Crop.query.order_by(desc(Crop.id)).all()
            crops = []
            for o in offers:
                farmer = User.query.get(o.farmer_id)
                crops.append({
                    'id': o.id, 'farmer_id': o.farmer_id,
                    'farmer_name': farmer.full_name if farmer else f'Farmer #{o.farmer_id}',
                    'farmer_email': farmer.email if farmer else '',
                    'farmer_phone': farmer.phone if farmer else '',
                    'crop_name': o.crop_name, 'quantity': o.quantity,
                    'unit': o.unit or 'kg',
                    'price': float(o.price) if o.price is not None else None,
                    'province': o.province or '-'
                })
        except Exception:
            crops = []

        try:
            certs = Certification.query.order_by(desc(Certification.cert_date)).all()
            certifications = [{'product_name': c.product_name,
                               'cert_date': c.cert_date.isoformat(),
                               'expiry_date': c.expiry_date.isoformat()} for c in certs]
        except Exception:
            certifications = []

        try:
            schedules = DeliverySchedule.query.order_by(desc(DeliverySchedule.delivery_date)).all()
            logistics = [{'product_name': s.product_name, 'quantity': s.quantity,
                          'destination': s.destination,
                          'delivery_date': s.delivery_date.isoformat(),
                          'status': s.status} for s in schedules]
        except Exception:
            logistics = []

        try:
            po = Order.query.filter(Order.processor_id.isnot(None)).order_by(desc(Order.id)).all()
            orders = [{'customer_name': (User.query.get(o.customer_id).full_name if o.customer_id else 'Customer'),
                       'product_name': o.product_name, 'quantity': o.quantity,
                       'unit': o.unit, 'status': o.status} for o in po]
        except Exception:
            orders = []

        if wants_json():
            return jsonify({
                'role': role, 'user': current_user.to_dict(),
                'crops': crops, 'certifications': certifications,
                'logistics': logistics, 'orders': orders,
            }), 200

        return render_template('dashboards/processor_dashboard.html',
                               user=current_user, weather=weather_snapshot,
                               crops=crops, certifications=certifications,
                               logistics=logistics, orders=orders)

    elif role == 'researcher':
        try:
            market_prices = MarketPrice.query.order_by(MarketPrice.date.desc()).all()
        except Exception:
            market_prices = []

        if wants_json():
            return jsonify({
                'role': role, 'user': current_user.to_dict(),
                'market_prices': [{'id': p.id, 'commodity': p.commodity, 'price': p.price,
                                   'province': p.province, 'unit': p.unit,
                                   'date': p.date.isoformat()} for p in market_prices],
            }), 200

        return render_template('dashboards/researcher_dashboard.html',
                               user=current_user, weather=weather_snapshot,
                               market_prices=market_prices, chart_data=None,
                               nisr_chart_data=None, maize_data=None)

    elif role == 'policy':
        stats = {
            'farmers': User.query.filter_by(role='farmer').count(),
            'dealers': User.query.filter(User.role.in_(['dealer', 'promoter'])).count(),
            'processors': User.query.filter_by(role='processor').count(),
            'researchers': User.query.filter_by(role='researcher').count(),
            'policymakers': User.query.filter_by(role='policy').count(),
        }
        if wants_json():
            return jsonify({'role': role, 'user': current_user.to_dict(), 'stats': stats}), 200
        return render_template('dashboards/policy_dashboard.html',
                               user=current_user, weather=weather_snapshot, stats=stats)
    else:
        if wants_json():
            return jsonify({'error': 'Role not recognized'}), 400
        flash('Role not recognized. Contact admin.', 'error')
        return redirect(url_for('login'))


# ====================================================
# Chat
# ====================================================
@app.route('/chat', methods=['POST'])
def chat():
    payload = request.get_json(silent=True) or {}
    user_message = (payload.get('message') or '').strip()
    history = payload.get('history') or []

    if not user_message:
        return jsonify({'error': 'Message is required.'}), 400

    try:
        assistant_reply = generate_chat_response(user_message, history, db.session)
    except RateLimitExceededError:
        return jsonify({'error': 'UMUHUZA is temporarily at capacity. Try again in a moment.',
                        'detail': 'Rate limit reached'}), 429
    except MissingAPIKeyError:
        return jsonify({'error': 'UMUHUZA Assistant is not configured yet.'}), 503
    except Exception as exc:
        app.logger.exception('Chatbot error: %s', exc)
        return jsonify({'error': 'UMUHUZA Assistant is currently unavailable. Try again later.'}), 500

    return jsonify({'message': assistant_reply})


# ====================================================
# Agro-Dealer Dashboard
# ====================================================
@app.route('/agro-dealer-dashboard')
@login_required
def agro_dealer_dashboard():
    if current_user.role != 'dealer':
        if wants_json():
            return jsonify({'error': 'Access denied: dealer-only area'}), 403
        flash('Access denied: dealer-only area.', 'error')
        return redirect(url_for('dashboard'))

    weather_snapshot = localized_weather_snapshot()
    inventory = Inventory.query.filter_by(dealer_id=current_user.id).order_by(Inventory.product_name).all()
    orders = Order.query.filter_by(dealer_id=current_user.id).order_by(desc(Order.created_at)).all()
    today = date.today()
    subsidies = Subsidy.query.filter(Subsidy.active == True).all()

    if wants_json():
        return jsonify({
            'user': current_user.to_dict(),
            'inventory': [{'id': i.id, 'product_name': i.product_name, 'stock': i.stock,
                           'unit': i.unit, 'price': float(i.price) if i.price else None} for i in inventory],
            'orders': [{'id': o.id, 'product_name': o.product_name, 'quantity': o.quantity,
                        'unit': o.unit, 'status': o.status,
                        'created_at': o.created_at.isoformat() if o.created_at else None} for o in orders],
            'subsidies': [{'id': s.id, 'title': s.title, 'commodity': s.commodity,
                           'discount_percent': s.discount_percent} for s in subsidies],
        }), 200

    return render_template('dashboards/dealer_dashboard.html',
                           user=current_user, weather=weather_snapshot,
                           inventory=inventory, orders=orders, subsidies=subsidies)


# ====================================================
# Dealer Order Actions
# ====================================================
@app.route('/dealer/order/<int:order_id>/action', methods=['POST'])
@login_required
def dealer_order_action(order_id):
    if current_user.role != 'dealer':
        if wants_json():
            return jsonify({'error': 'Access denied'}), 403
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))

    action = (request.form.get('action') or (request.get_json(silent=True) or {}).get('action'))
    order = Order.query.get_or_404(order_id)
    if order.dealer_id != current_user.id:
        if wants_json():
            return jsonify({'error': 'You cannot manage this order'}), 403
        flash('You cannot manage this order.', 'error')
        return redirect(url_for('agro_dealer_dashboard'))

    if action == 'approve':
        order.status = 'approved'
        order.updated_at = db.func.now()
        inv = Inventory.query.filter_by(dealer_id=current_user.id, product_name=order.product_name).first()
        if inv:
            inv.stock = inv.stock - order.quantity
    elif action == 'reject':
        order.status = 'rejected'
        order.updated_at = db.func.now()
    elif action == 'deliver':
        order.status = 'delivered'
        order.updated_at = db.func.now()
    else:
        if wants_json():
            return jsonify({'error': 'Unknown action'}), 400
        flash('Unknown action.', 'error')
        return redirect(url_for('agro_dealer_dashboard'))

    db.session.commit()
    if wants_json():
        return jsonify({'message': 'Order updated', 'status': order.status}), 200
    flash('Order updated.', 'success')
    return redirect(url_for('agro_dealer_dashboard'))


# ====================================================
# Farmer Order Create
# ====================================================
@app.route('/farmer/order/create', methods=['POST'])
@login_required
def farmer_create_order():
    if current_user.role != 'farmer':
        if wants_json():
            return jsonify({'error': 'Access denied'}), 403
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))

    if wants_json():
        data = request.get_json(silent=True) or {}
        dealer_id = data.get('dealer_id')
        product_name = data.get('product_name')
        quantity = data.get('quantity')
        unit = data.get('unit') or 'kg'
    else:
        dealer_id = request.form.get('dealer_id')
        product_name = request.form.get('product_name')
        quantity = request.form.get('quantity')
        unit = request.form.get('unit') or 'kg'

    if not all([dealer_id, product_name, quantity]):
        if wants_json():
            return jsonify({'error': 'dealer_id, product_name, and quantity are required'}), 400
        flash('Missing required fields.', 'error')
        return redirect(url_for('dashboard'))

    try:
        dealer_user = User.query.get(int(dealer_id))
        if not dealer_user or dealer_user.role != 'dealer':
            if wants_json():
                return jsonify({'error': 'Invalid dealer'}), 404
            flash('Selected dealer is invalid.', 'error')
            return redirect(url_for('dashboard'))

        order = Order(
            farmer_id=current_user.id, dealer_id=int(dealer_id),
            product_name=str(product_name).strip(), quantity=int(quantity),
            unit=str(unit).strip(), status='pending',
            created_at=db.func.now(), updated_at=None
        )
        db.session.add(order)
        db.session.commit()
        if wants_json():
            return jsonify({'message': 'Order submitted', 'order_id': order.id}), 201
        flash('Order submitted to agro-dealer.', 'success')
    except Exception as e:
        app.logger.error(f"Create order error: {e}")
        if wants_json():
            return jsonify({'error': str(e)}), 500
        flash('Could not submit order.', 'error')

    return redirect(url_for('dashboard'))


# ====================================================
# Inventory Management
# ====================================================
@app.route('/dealer/inventory/<int:inv_id>/update', methods=['POST'])
@login_required
def dealer_inventory_update(inv_id):
    if current_user.role != 'dealer':
        if wants_json():
            return jsonify({'error': 'Access denied'}), 403
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))

    inv = Inventory.query.get_or_404(inv_id)
    if inv.dealer_id != current_user.id:
        if wants_json():
            return jsonify({'error': 'You cannot edit this inventory item'}), 403
        flash('You cannot edit this inventory item.', 'error')
        return redirect(url_for('agro_dealer_dashboard'))

    if wants_json():
        data = request.get_json(silent=True) or {}
        new_stock = data.get('stock')
        new_price = data.get('price')
    else:
        new_stock = request.form.get('stock')
        new_price = request.form.get('price')

    try:
        inv.stock = int(new_stock)
        if new_price:
            inv.price = float(new_price)
        inv.last_updated = db.func.now()
        db.session.commit()
        if wants_json():
            return jsonify({'message': 'Inventory updated'}), 200
        flash('Inventory updated.', 'success')
    except Exception as e:
        app.logger.error(f"Inventory update error: {e}")
        if wants_json():
            return jsonify({'error': 'Invalid values'}), 400
        flash('Invalid values.', 'error')

    return redirect(url_for('agro_dealer_dashboard'))


@app.route('/dealer/inventory/create', methods=['POST'])
@login_required
def dealer_inventory_create():
    if current_user.role != 'dealer':
        if wants_json():
            return jsonify({'error': 'Access denied'}), 403
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))

    if wants_json():
        data = request.get_json(silent=True) or {}
        product_name = data.get('product_name')
        unit = data.get('unit') or 'kg'
        stock = data.get('stock') or 0
        price = data.get('price')
    else:
        product_name = request.form.get('product_name')
        unit = request.form.get('unit') or 'kg'
        stock = request.form.get('stock') or 0
        price = request.form.get('price') or None

    if not product_name:
        if wants_json():
            return jsonify({'error': 'product_name is required'}), 400
        flash('Product name is required.', 'error')
        return redirect(url_for('agro_dealer_dashboard'))

    try:
        inv = Inventory(
            dealer_id=current_user.id, product_name=str(product_name).strip(),
            stock=int(stock), unit=str(unit).strip(),
            price=float(price) if price else None,
        )
        db.session.add(inv)
        db.session.commit()
        if wants_json():
            return jsonify({'message': 'Inventory item created', 'id': inv.id}), 201
        flash('Inventory item created.', 'success')
    except Exception as e:
        app.logger.error(f"Inventory create error: {e}")
        if wants_json():
            return jsonify({'error': str(e)}), 500
        flash('Could not create inventory.', 'error')

    return redirect(url_for('agro_dealer_dashboard'))


@app.route('/dealer/subsidy/create', methods=['POST'])
@login_required
def dealer_create_subsidy():
    if current_user.role != 'dealer':
        if wants_json():
            return jsonify({'error': 'Access denied'}), 403
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))

    if wants_json():
        data = request.get_json(silent=True) or {}
        title = data.get('title')
        commodity = data.get('commodity')
        discount = data.get('discount_percent') or 0
        valid_from = data.get('valid_from')
        valid_to = data.get('valid_to')
    else:
        title = request.form.get('title')
        commodity = request.form.get('commodity')
        discount = request.form.get('discount_percent') or 0
        valid_from = request.form.get('valid_from') or None
        valid_to = request.form.get('valid_to') or None

    try:
        s = Subsidy(
            title=title, commodity=commodity, discount_percent=int(discount),
            valid_from=date.fromisoformat(valid_from) if valid_from else None,
            valid_to=date.fromisoformat(valid_to) if valid_to else None,
            active=True
        )
        db.session.add(s)
        db.session.commit()
        if wants_json():
            return jsonify({'message': 'Subsidy created', 'id': s.id}), 201
        flash('Subsidy proposal created.', 'success')
    except Exception as e:
        app.logger.error(f"Error creating subsidy: {e}")
        if wants_json():
            return jsonify({'error': str(e)}), 500
        flash('Could not create subsidy.', 'error')

    return redirect(url_for('agro_dealer_dashboard'))


# ====================================================
# Farmer Crops
# ====================================================
@app.route('/farmer/crops/create', methods=['POST'])
@login_required
def farmer_create_crop():
    if current_user.role != 'farmer':
        if wants_json():
            return jsonify({'error': 'Access denied'}), 403
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))

    if wants_json():
        data = request.get_json(silent=True) or {}
        crop_name = data.get('crop_name')
        quantity = data.get('quantity')
        unit = data.get('unit') or 'kg'
        price = data.get('price')
        province = data.get('province')
    else:
        crop_name = request.form.get('crop_name')
        quantity = request.form.get('quantity')
        unit = request.form.get('unit') or 'kg'
        price = request.form.get('price')
        province = request.form.get('province')

    if not crop_name or not quantity:
        if wants_json():
            return jsonify({'error': 'crop_name and quantity are required'}), 400
        flash('Crop name and quantity are required.', 'error')
        return redirect(url_for('dashboard'))

    try:
        crop = Crop(
            farmer_id=current_user.id,
            crop_name=str(crop_name).strip(),
            quantity=float(quantity),
            unit=str(unit).strip() if unit else None,
            price=float(price) if price else None,
            province=str(province).strip() if province else None,
        )
        db.session.add(crop)
        db.session.commit()
        if wants_json():
            return jsonify({'message': 'Crop offer published', 'id': crop.id}), 201
        flash('Crop offer published for processors.', 'success')
    except Exception as e:
        app.logger.error(f"Create crop error: {e}")
        if wants_json():
            return jsonify({'error': str(e)}), 500
        flash('Could not publish crop offer.', 'error')

    return redirect(url_for('dashboard'))


# ====================================================
# All existing /api/* routes (unchanged — already JSON)
# ====================================================
@app.route('/api/processor-orders', methods=['GET'])
@login_required
def api_get_processor_orders():
    try:
        if current_user.role == 'farmer':
            orders = Order.query.filter(
                Order.farmer_id == current_user.id,
                Order.processor_id.isnot(None)
            ).order_by(desc(Order.created_at)).all()
            result = []
            for o in orders:
                processor = User.query.get(o.processor_id)
                result.append({
                    'id': o.id, 'processor_id': o.processor_id,
                    'customer_name': processor.full_name if processor else f'Processor #{o.processor_id}',
                    'farmer_id': o.farmer_id, 'farmer_name': current_user.full_name,
                    'farmer_email': current_user.email or '', 'farmer_phone': current_user.phone or '',
                    'product_name': o.product_name, 'quantity': o.quantity, 'unit': o.unit or 'kg',
                    'status': o.status,
                    'created_at': o.created_at.isoformat() if o.created_at else None
                })
            return jsonify(result)
        elif current_user.role == 'processor':
            orders = Order.query.filter_by(processor_id=current_user.id).order_by(desc(Order.created_at)).all()
            result = []
            for o in orders:
                farmer = User.query.get(o.farmer_id)
                result.append({
                    'id': o.id, 'processor_id': o.processor_id,
                    'customer_name': current_user.full_name,
                    'farmer_id': o.farmer_id,
                    'farmer_name': farmer.full_name if farmer else f'Farmer #{o.farmer_id}',
                    'farmer_email': farmer.email if farmer else '', 'farmer_phone': farmer.phone if farmer else '',
                    'product_name': o.product_name, 'quantity': o.quantity, 'unit': o.unit or 'kg',
                    'status': o.status,
                    'created_at': o.created_at.isoformat() if o.created_at else None
                })
            return jsonify(result)
        return jsonify([])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/processor-orders', methods=['POST'])
@login_required
def api_create_processor_order():
    if current_user.role != 'processor':
        return jsonify({'error': 'Only processors can create these orders'}), 403
    try:
        data = request.get_json()
        crop_id = data.get('crop_id')
        quantity = float(data.get('quantity', 0))
        if not crop_id or quantity <= 0:
            return jsonify({'error': 'crop_id and valid quantity required'}), 400
        crop = Crop.query.get(crop_id)
        if not crop:
            return jsonify({'error': 'Crop not found'}), 404
        if quantity > crop.quantity:
            return jsonify({'error': f'Cannot order more than available ({crop.quantity})'}), 400
        order = Order(
            farmer_id=crop.farmer_id, dealer_id=crop.farmer_id,
            processor_id=current_user.id, product_name=crop.crop_name,
            quantity=int(quantity), unit=crop.unit or 'kg', status='pending'
        )
        db.session.add(order)
        db.session.commit()
        farmer = User.query.get(crop.farmer_id)
        return jsonify({'success': True, 'order': {
            'id': order.id, 'processor_id': order.processor_id,
            'customer_name': current_user.full_name, 'farmer_id': order.farmer_id,
            'farmer_name': farmer.full_name if farmer else '',
            'product_name': order.product_name, 'quantity': order.quantity,
            'unit': order.unit, 'status': order.status
        }})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/processor-orders/<int:order_id>/action', methods=['POST'])
@login_required
def api_processor_order_action(order_id):
    if current_user.role != 'farmer':
        return jsonify({'error': 'Only farmers can approve/reject these orders'}), 403
    try:
        data = request.get_json()
        action = data.get('action')
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        if order.farmer_id != current_user.id:
            return jsonify({'error': 'You can only manage orders for your crops'}), 403
        previous_status = order.status
        crop = Crop.query.filter_by(farmer_id=current_user.id, crop_name=order.product_name).first()
        if action == 'approve':
            if previous_status != 'approved':
                if crop:
                    if crop.quantity >= order.quantity:
                        crop.quantity -= order.quantity
                    else:
                        return jsonify({'error': f'Not enough quantity. Only {crop.quantity} left.'}), 400
            order.status = 'approved'
        elif action == 'reject':
            if previous_status == 'approved' and crop:
                crop.quantity += order.quantity
            order.status = 'rejected'
        else:
            return jsonify({'error': 'Invalid action'}), 400
        order.updated_at = db.func.now()
        db.session.commit()
        return jsonify({'success': True, 'status': order.status})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/crop/update-quantity', methods=['POST'])
@login_required
def api_update_crop_quantity():
    try:
        data = request.get_json()
        crop_id = data.get('crop_id')
        quantity_reduction = float(data.get('quantity_reduction', 0))
        if not crop_id:
            return jsonify({'error': 'crop_id is required'}), 400
        crop = Crop.query.get(crop_id)
        if not crop:
            return jsonify({'error': 'Crop not found'}), 404
        if crop.farmer_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        new_quantity = max(0, crop.quantity - quantity_reduction)
        crop.quantity = new_quantity
        db.session.commit()
        return jsonify({'success': True, 'new_quantity': new_quantity, 'crop_id': crop_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/farmer-dealer-orders', methods=['GET'])
@login_required
def api_get_farmer_dealer_orders():
    if current_user.role != 'farmer':
        return jsonify({'error': 'Only farmers can access this'}), 403
    try:
        orders = Order.query.filter_by(farmer_id=current_user.id).filter(
            Order.processor_id.is_(None)
        ).order_by(desc(Order.created_at)).all()
        result = []
        for o in orders:
            dealer = User.query.get(o.dealer_id)
            result.append({
                'id': o.id, 'dealer_id': o.dealer_id,
                'dealer_name': dealer.full_name if dealer else f'Dealer #{o.dealer_id}',
                'dealer_email': dealer.email if dealer else '', 'dealer_phone': dealer.phone if dealer else '',
                'product_name': o.product_name, 'quantity': o.quantity, 'unit': o.unit or 'kg',
                'status': o.status,
                'created_at': o.created_at.isoformat() if o.created_at else None
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/farmer-dealer-orders', methods=['POST'])
@login_required
def api_create_farmer_dealer_order():
    if current_user.role != 'farmer':
        return jsonify({'error': 'Only farmers can create these orders'}), 403
    try:
        data = request.get_json()
        dealer_id = data.get('dealer_id')
        product_name = data.get('product_name', '').strip()
        quantity = float(data.get('quantity', 0))
        unit = data.get('unit', 'kg').strip()
        if not dealer_id or not product_name or quantity <= 0:
            return jsonify({'error': 'dealer_id, product_name, and valid quantity required'}), 400
        dealer = User.query.get(dealer_id)
        if not dealer or dealer.role != 'dealer':
            return jsonify({'error': 'Invalid dealer'}), 404
        inv = Inventory.query.filter_by(dealer_id=dealer_id, product_name=product_name).first()
        if inv and quantity > inv.stock:
            return jsonify({'error': f'Not enough stock. Only {inv.stock} {inv.unit or "units"} left.'}), 400
        order = Order(
            farmer_id=current_user.id, dealer_id=int(dealer_id),
            product_name=product_name, quantity=int(quantity), unit=unit, status='pending'
        )
        db.session.add(order)
        db.session.commit()
        return jsonify({'success': True, 'order': {
            'id': order.id, 'dealer_id': order.dealer_id, 'product_name': order.product_name,
            'quantity': order.quantity, 'unit': order.unit, 'status': order.status
        }})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/dealer-orders', methods=['GET'])
@login_required
def api_get_dealer_orders():
    if current_user.role != 'dealer':
        return jsonify({'error': 'Only dealers can access this'}), 403
    try:
        orders = Order.query.filter_by(dealer_id=current_user.id).order_by(desc(Order.created_at)).all()
        result = []
        for o in orders:
            farmer = User.query.get(o.farmer_id)
            result.append({
                'id': o.id, 'farmer_id': o.farmer_id,
                'farmer_name': farmer.full_name if farmer else f'Farmer #{o.farmer_id}',
                'farmer_email': farmer.email if farmer else '', 'farmer_phone': farmer.phone if farmer else '',
                'product_name': o.product_name, 'quantity': o.quantity, 'unit': o.unit or 'kg',
                'status': o.status,
                'created_at': o.created_at.isoformat() if o.created_at else None
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dealer-orders/<int:order_id>/action', methods=['POST'])
@login_required
def api_dealer_order_action(order_id):
    if current_user.role != 'dealer':
        return jsonify({'error': 'Only dealers can manage these orders'}), 403
    try:
        data = request.get_json()
        action = data.get('action')
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        if order.dealer_id != current_user.id:
            return jsonify({'error': 'You can only manage your own orders'}), 403
        previous_status = order.status
        inv = Inventory.query.filter_by(dealer_id=current_user.id, product_name=order.product_name).first()
        if action == 'approve':
            if previous_status != 'approved':
                if inv:
                    if inv.stock >= order.quantity:
                        inv.stock -= order.quantity
                    else:
                        return jsonify({'error': f'Not enough stock. Only {inv.stock} available.'}), 400
            order.status = 'approved'
        elif action == 'reject':
            if previous_status == 'approved' and inv:
                inv.stock += order.quantity
            order.status = 'rejected'
        elif action == 'deliver':
            order.status = 'delivered'
        else:
            return jsonify({'error': 'Invalid action'}), 400
        order.updated_at = db.func.now()
        db.session.commit()
        return jsonify({'success': True, 'status': order.status})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/announcements', methods=['GET'])
@login_required
def api_get_announcements():
    try:
        today = date.today()
        if current_user.role == 'dealer':
            announcements = Subsidy.query.filter_by(dealer_id=current_user.id).order_by(desc(Subsidy.created_at)).all()
        else:
            announcements = Subsidy.query.filter(
                Subsidy.active == True,
                db.or_(Subsidy.valid_to.is_(None), Subsidy.valid_to >= today)
            ).order_by(desc(Subsidy.created_at)).all()
        result = []
        for a in announcements:
            dealer = User.query.get(a.dealer_id) if a.dealer_id else None
            result.append({
                'id': a.id, 'dealer_id': a.dealer_id,
                'dealer_name': dealer.full_name if dealer else 'System',
                'dealer_email': dealer.email if dealer else '', 'dealer_phone': dealer.phone if dealer else '',
                'title': a.title, 'description': a.description or '', 'commodity': a.commodity or '',
                'discount_percent': a.discount_percent or 0,
                'valid_from': a.valid_from.isoformat() if a.valid_from else None,
                'valid_to': a.valid_to.isoformat() if a.valid_to else None,
                'active': a.active,
                'created_at': a.created_at.isoformat() if a.created_at else None
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/announcements', methods=['POST'])
@login_required
def api_create_announcement():
    if current_user.role != 'dealer':
        return jsonify({'error': 'Only dealers can create announcements'}), 403
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        if not title:
            return jsonify({'error': 'Title is required'}), 400
        valid_from = date.fromisoformat(data['valid_from']) if data.get('valid_from') else None
        valid_to = date.fromisoformat(data['valid_to']) if data.get('valid_to') else None
        announcement = Subsidy(
            dealer_id=current_user.id, title=title,
            description=data.get('description', '').strip() or None,
            commodity=data.get('commodity', '').strip() or None,
            discount_percent=int(data.get('discount_percent', 0) or 0),
            valid_from=valid_from, valid_to=valid_to, active=True
        )
        db.session.add(announcement)
        db.session.commit()
        return jsonify({'success': True, 'announcement': {
            'id': announcement.id, 'dealer_id': announcement.dealer_id,
            'dealer_name': current_user.full_name, 'title': announcement.title,
            'description': announcement.description or '', 'commodity': announcement.commodity or '',
            'discount_percent': announcement.discount_percent,
            'valid_from': announcement.valid_from.isoformat() if announcement.valid_from else None,
            'valid_to': announcement.valid_to.isoformat() if announcement.valid_to else None,
            'active': announcement.active
        }})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/announcements/<int:announcement_id>', methods=['PUT'])
@login_required
def api_update_announcement(announcement_id):
    if current_user.role != 'dealer':
        return jsonify({'error': 'Only dealers can update announcements'}), 403
    try:
        announcement = Subsidy.query.get(announcement_id)
        if not announcement:
            return jsonify({'error': 'Announcement not found'}), 404
        if announcement.dealer_id != current_user.id:
            return jsonify({'error': 'You can only edit your own announcements'}), 403
        data = request.get_json()
        for field in ['title', 'description', 'commodity']:
            if field in data:
                setattr(announcement, field, data[field].strip() or None)
        if 'discount_percent' in data:
            announcement.discount_percent = int(data['discount_percent'] or 0)
        if 'valid_from' in data:
            announcement.valid_from = date.fromisoformat(data['valid_from']) if data['valid_from'] else None
        if 'valid_to' in data:
            announcement.valid_to = date.fromisoformat(data['valid_to']) if data['valid_to'] else None
        if 'active' in data:
            announcement.active = bool(data['active'])
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/announcements/<int:announcement_id>', methods=['DELETE'])
@login_required
def api_delete_announcement(announcement_id):
    if current_user.role != 'dealer':
        return jsonify({'error': 'Only dealers can delete announcements'}), 403
    try:
        announcement = Subsidy.query.get(announcement_id)
        if not announcement:
            return jsonify({'error': 'Announcement not found'}), 404
        if announcement.dealer_id != current_user.id:
            return jsonify({'error': 'You can only delete your own announcements'}), 403
        db.session.delete(announcement)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/inventory/update-stock', methods=['POST'])
@login_required
def api_update_inventory_stock():
    try:
        data = request.get_json()
        inv_id = data.get('inv_id')
        quantity_reduction = float(data.get('quantity_reduction', 0))
        if not inv_id:
            return jsonify({'error': 'inv_id is required'}), 400
        inv = Inventory.query.get(inv_id)
        if not inv:
            return jsonify({'error': 'Inventory item not found'}), 404
        if inv.dealer_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        new_stock = max(0, inv.stock - quantity_reduction)
        inv.stock = new_stock
        inv.last_updated = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True, 'new_stock': new_stock, 'inv_id': inv_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ====================================================
# Weather
# ====================================================
@app.route('/api/weather')
def api_weather():
    refresh = request.args.get('refresh') == '1'
    data = localized_weather_snapshot(force_refresh=refresh)
    return jsonify(data)


@app.route('/weather')
def weather():
    return render_template('weather.html', weather=localized_weather_snapshot())


# ====================================================
# Test / Diagnostic Routes
# ====================================================
@app.route('/test')
def test():
    db_status = '❌ Not Connected'
    try:
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        db.session.commit()
        db_status = '✅ Connected'
    except Exception as e:
        db_status = f'❌ Error: {str(e)[:100]}'
    if wants_json():
        return jsonify({'flask': 'ok', 'db': db_status}), 200
    return f"<h1>Flask OK</h1><p>DB: {db_status}</p>", 200


@app.route('/test-db')
def test_db():
    results = {'connected': False, 'error': None, 'tables': [], 'users_count': 0}
    try:
        from sqlalchemy import text, inspect
        db.session.execute(text('SELECT 1'))
        results['connected'] = True
        inspector = inspect(db.engine)
        results['tables'] = inspector.get_table_names()
        try:
            results['users_count'] = User.query.count()
        except Exception:
            results['users_count'] = 'Error'
    except Exception as e:
        results['error'] = str(e)
    if wants_json():
        return jsonify(results), 200 if results['connected'] else 500
    return f"<h1>DB Test</h1><pre>{results}</pre>", 200


# ====================================================
# API Reference (GET /api)
# ====================================================
@app.route('/api')
def api_reference():
    """Quick reference of all available JSON endpoints."""
    endpoints = {
        'auth': {
            'POST /api/auth/login': 'Login — body: {email, password} → {token, user}',
            'POST /api/auth/register': 'Register — body: {full_name, email, phone, role, password} → {token, user}',
            'GET  /api/auth/me': 'Get current user — header: Authorization: Bearer <token>',
            'POST /api/auth/logout': 'Logout',
        },
        'dashboard': {
            'GET /dashboard': 'Role-based dashboard data (JSON if Accept:application/json)',
        },
        'farmer': {
            'POST /farmer/order/create': 'Create order to dealer',
            'POST /farmer/crops/create': 'Publish crop offer',
            'GET  /api/farmer-dealer-orders': 'List dealer orders',
            'POST /api/farmer-dealer-orders': 'Create dealer order',
            'GET  /api/processor-orders': 'List processor orders',
            'POST /api/processor-orders/<id>/action': 'Approve/reject processor order',
        },
        'dealer': {
            'GET  /agro-dealer-dashboard': 'Dealer dashboard',
            'POST /dealer/inventory/create': 'Add inventory item',
            'POST /dealer/inventory/<id>/update': 'Update stock/price',
            'POST /dealer/order/<id>/action': 'Approve/reject/deliver order',
            'POST /dealer/subsidy/create': 'Create subsidy',
            'GET  /api/dealer-orders': 'List incoming orders',
            'POST /api/dealer-orders/<id>/action': 'approve/reject/deliver',
            'GET  /api/announcements': 'List announcements',
            'POST /api/announcements': 'Create announcement',
            'PUT  /api/announcements/<id>': 'Update announcement',
            'DELETE /api/announcements/<id>': 'Delete announcement',
        },
        'processor': {
            'POST /api/processor-orders': 'Create order for crop',
        },
        'weather': {
            'GET /api/weather': 'Current weather snapshot',
        },
        'chat': {
            'POST /chat': 'AI chatbot — body: {message, history:[]}',
        },
        'note': (
            'For all protected endpoints send: '
            'Authorization: Bearer <token>  '
            '(token obtained from /api/auth/login)'
        ),
    }
    return jsonify(endpoints), 200


# ====================================================
# Remaining informational / HTML pages
# ====================================================
@app.route('/about-us')
def about_us():
    return render_template('about-us.html')


@app.route('/dash')
def dash():
    return render_template('dash.html')


@app.route('/market')
def market():
    return render_template('market.html')


@app.route('/input')
def input_page():
    return render_template('input.html')


@app.route('/irrigation')
def irrigation():
    return render_template('irrigation.html')


@app.route('/service')
def service():
    return render_template('service.html', youtube_id='29KDeFQIIpI')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        if wants_json():
            data = request.get_json(silent=True) or {}
            name = data.get('name')
            email = data.get('email')
            message_body = data.get('message')
        else:
            name = request.form.get('name')
            email = request.form.get('email')
            message_body = request.form.get('message')
        try:
            msg = Message(
                subject=f'New Contact Form Message from {name}',
                recipients=['oniyonkuru233@gmail.com'],
                body=f'Name: {name}\nEmail: {email}\n\nMessage:\n{message_body}'
            )
            mail.send(msg)
            if wants_json():
                return jsonify({'message': 'Message sent successfully'}), 200
            flash('Your message has been sent successfully!', 'success')
        except Exception as e:
            if wants_json():
                return jsonify({'error': str(e)}), 500
            flash(f'Error sending message: {str(e)}', 'error')
        return redirect(url_for('contact'))
    return render_template('contact.html')


@app.route('/agrodealer')
def appreciate_agrodealer():
    return render_template('appreciate-agrodealer.html')


@app.route('/customer')
def appreciate_customer():
    return render_template('appreciate-customer.html')


@app.route('/farmer')
def appreciate_farmer():
    return render_template('appreciate-farmer.html')


@app.route('/policy-maker')
def appreciate_policymaker():
    return render_template('appreciate-policymaker.html')


@app.route('/promoter')
def appreciate_promoter():
    return render_template('appreciate-promoter.html')


@app.route('/research')
def appreciate_research():
    return render_template('appreciate-research.html')


@app.route('/static/<path:filename>')
def static_files(filename):
    try:
        static_dir = app.static_folder
        if not os.path.exists(os.path.join(static_dir, filename)):
            filename_lower = filename.lower()
            if os.path.exists(static_dir):
                for file in os.listdir(static_dir):
                    if file.lower() == filename_lower:
                        filename = file
                        break
        return send_from_directory(static_dir, filename)
    except Exception as e:
        return f'Static file not found: {filename}', 404


@app.route('/download/nisr_dataset')
def download_nisr_dataset():
    try:
        return send_from_directory(directory=str(DATASETS_DIR),
                                   path='Tables_2025_Season_A.xlsx', as_attachment=True)
    except Exception as e:
        return 'Dataset not available', 500


@app.route('/download/maize_dataset')
def download_maize_dataset():
    try:
        return send_from_directory(directory=str(DATASETS_DIR),
                                   path='rwanda_maize_production_2025.csv', as_attachment=True)
    except Exception as e:
        return 'Dataset not available', 500


@app.route('/download_market_prices')
@login_required
def download_market_prices():
    if current_user.role not in ('researcher', 'policy'):
        if wants_json():
            return jsonify({'error': 'Access denied'}), 403
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    try:
        prices = MarketPrice.query.order_by(MarketPrice.date.desc()).all()
    except Exception as e:
        return 'No market price data available', 404
    if not prices:
        return 'No market price data available', 404
    df = pd.DataFrame([{'ID': p.id, 'Commodity': p.commodity, 'Price': p.price,
                        'Province': p.province, 'Unit': p.unit, 'Date': p.date} for p in prices])
    output = BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return send_file(output, mimetype='text/csv', as_attachment=True, download_name='market_prices.csv')


@app.route('/users/<role>')
@login_required
def list_users(role):
    if current_user.role != 'policy':
        if wants_json():
            return jsonify({'error': 'Access denied'}), 403
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    valid_roles = ['farmer', 'dealer', 'processor', 'researcher', 'policy']
    if role not in valid_roles:
        if wants_json():
            return jsonify({'error': 'Invalid role'}), 400
        flash('Invalid role selected.', 'error')
        return redirect(url_for('dashboard'))
    users = User.query.filter(User.role.in_(['dealer', 'promoter'])).all() if role == 'dealer' \
        else User.query.filter_by(role=role).all()
    if wants_json():
        return jsonify([u.to_dict() for u in users]), 200
    return render_template('dashboards/user_list.html', role=role.capitalize(), users=users)


@app.route('/export/<role>/<filetype>')
@login_required
def export_users(role, filetype):
    if current_user.role != 'policy':
        if wants_json():
            return jsonify({'error': 'Access denied'}), 403
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    valid_roles = ['farmer', 'dealer', 'processor', 'researcher', 'policy']
    if role not in valid_roles:
        if wants_json():
            return jsonify({'error': 'Invalid role'}), 400
        flash('Invalid role.', 'error')
        return redirect(url_for('dashboard'))
    users = User.query.filter(User.role.in_(['dealer', 'promoter'])).all() if role == 'dealer' \
        else User.query.filter_by(role=role).all()
    data = [{'ID': u.id, 'Full Name': u.full_name, 'Phone': u.phone or '-', 'Email': u.email or '-'} for u in users]
    if filetype == 'excel':
        df = pd.DataFrame(data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=f'{role.capitalize()}s')
        output.seek(0)
        return send_file(output, as_attachment=True, download_name=f'{role}_users.xlsx',
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    elif filetype == 'pdf':
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        elements.append(Paragraph(f'{role.capitalize()} Users', styles['Title']))
        table_data = [['ID', 'Full Name', 'Phone', 'Email']] + \
                     [[str(u.id), u.full_name, u.phone or '-', u.email or '-'] for u in users]
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#263238')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(table)
        doc.build(elements)
        output.seek(0)
        return send_file(output, as_attachment=True, download_name=f'{role}_users.pdf',
                         mimetype='application/pdf')
    else:
        if wants_json():
            return jsonify({'error': 'Unsupported export format'}), 400
        flash('Unsupported export format.', 'error')
        return redirect(url_for('list_users', role=role))


# ====================================================
# Researcher standalone page
# ====================================================
@app.route('/researcher_dashboard')
def researcher_dashboard():
    user = {'full_name': 'Researcher User'}
    market_prices = MarketPrice.query.order_by(MarketPrice.date.desc()).all()
    chart_data = None
    if market_prices:
        commodities = {}
        dates = sorted(set([mp.date.strftime('%Y-%m-%d') for mp in market_prices]))
        for mp in market_prices:
            if mp.commodity not in commodities:
                commodities[mp.commodity] = {}
            commodities[mp.commodity][mp.date.strftime('%Y-%m-%d')] = mp.price
        datasets = {c: [commodities[c].get(d, None) for d in dates] for c in commodities}
        avg_prices = {c: sum(v for v in vals if v) / len([v for v in vals if v])
                      for c, vals in datasets.items()}
        chart_data = {'dates': dates, 'commodities': datasets, 'avg_prices': avg_prices}
    return render_template('researcher_dashboard.html', user=user, market_prices=market_prices,
                           chart_data=chart_data, nisr_preview=None, nisr_chart_data=None, maize_data=None)


# ====================================================
# Run
# ====================================================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)