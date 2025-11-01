# ---------------- Standard Library ----------------
from io import BytesIO
from datetime import datetime
from flask import send_from_directory, render_template
import requests

from sqlalchemy import desc
from datetime import date

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
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet


# ====================================================
# Flask App & Config
# ====================================================
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # ⚠️ Change in production!

# ---------------- Database Config ----------------
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://root:Da1wi2d$@localhost/umuhuza"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ---------------- Email Config ----------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = "oniyonkuru233@gmail.com"
app.config['MAIL_PASSWORD'] = "jvvd hzba fwqa jbnz"  # ⚠️ Gmail App Password
app.config['MAIL_DEFAULT_SENDER'] = "oniyonkuru233@gmail.com"
mail = Mail(app)

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

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class MarketPrice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    commodity = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    province = db.Column(db.String(100), nullable=True)  # New column
    date = db.Column(db.Date, nullable=False)
    unit = db.Column(db.String(20), nullable=True)
    
    
    # ---------------- Dealer models (paste near other models) ----------------
class Inventory(db.Model):
    __tablename__ = 'inventory'
    id = db.Column(db.Integer, primary_key=True)
    dealer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_name = db.Column(db.String(150), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    unit = db.Column(db.String(20), default='kg')
    price = db.Column(db.Numeric(10,2), nullable=True)
    last_updated = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    dealer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Extended for processor/customer workflows
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
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    commodity = db.Column(db.String(150), nullable=True)
    discount_percent = db.Column(db.Integer, default=0)
    valid_from = db.Column(db.Date, nullable=True)
    valid_to = db.Column(db.Date, nullable=True)
    active = db.Column(db.Boolean, default=True)


# ---------------- Processor models (aligned to existing DB DDL) ----------------
class Crop(db.Model):
    __tablename__ = 'crops'
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    crop_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=True)
    price = db.Column(db.Numeric(10,2), nullable=True)
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
    return User.query.get(int(user_id))

# ====================================================
# Token Serializer for Password Reset
# ====================================================
serializer = URLSafeTimedSerializer(app.secret_key)

# ====================================================
# Routes
# ====================================================

# -------- General Pages --------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about-us')
def about_us():
    return render_template('about-us.html')

# Keep legacy dash route
@app.route('/dash')
def dash():
    return render_template('dash.html')

# ====================================================
# Authentication
# ====================================================
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        phone = request.form.get("phone")
        email = request.form.get("email")
        role = request.form.get("role")
        password = request.form.get("password")

        user = None
        if phone:
            user = User.query.filter_by(phone=phone, role=role).first()
        elif email:
            user = User.query.filter_by(email=email, role=role).first()

        if user and user.check_password(password):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials. Please try again.", "error")

    return render_template("login.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

@app.route('/create-account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        full_name = request.form.get('fullName')
        phone = request.form.get('phone')
        email = request.form.get('email')
        role = request.form.get('role')
        password = request.form.get('password')
        confirm_password = request.form.get('confirmPassword')

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for('create_account'))

        if User.query.filter((User.phone == phone) | (User.email == email)).first():
            flash("Phone or Email already registered.", "error")
            return redirect(url_for('create_account'))

        new_user = User(full_name=full_name, phone=phone, email=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('create-account.html')

# ====================================================
# Password Reset
# ====================================================
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("Your email is not registered.", "error")
            return redirect(url_for("forgot_password"))

        token = serializer.dumps(email, salt="password-reset-salt")
        reset_link = url_for("reset_password", token=token, _external=True)

        try:
            msg = Message(
                subject="Password Reset Request - UMUHUZA",
                recipients=[email],
                body=f"""
Hello {user.full_name},

You requested a password reset for your UMUHUZA account.
Click the link below to reset your password:

{reset_link}

This link will expire in 30 minutes.

If you did not request this, please ignore this email.

- UMUHUZA Team
"""
            )
            mail.send(msg)
            flash("Password reset link has been sent to your email.", "success")
        except Exception as e:
            flash(f"Error sending email: {str(e)}", "error")

        return redirect(url_for("forgot_password"))

    return render_template("forgot_password.html")

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        email = serializer.loads(token, salt="password-reset-salt", max_age=1800)
    except SignatureExpired:
        flash("The reset link has expired. Please try again.", "error")
        return redirect(url_for("forgot_password"))
    except BadSignature:
        flash("Invalid reset link.", "error")
        return redirect(url_for("forgot_password"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Invalid email in reset link.", "error")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        password = request.form.get("password")
        confirm_password = request.form.get("confirmPassword")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("reset_password", token=token))

        user.set_password(password)
        db.session.commit()
        flash("Your password has been reset successfully! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("reset_password.html", token=token)

# ====================================================
# Dashboard (Role-Based)
# ====================================================
@app.route('/dashboard')
@login_required
def dashboard():
    role = current_user.role

    if role == "farmer":
        # ---- Weather API (Open-Meteo) ----
        lat, lon = -1.94, 30.06  # Kigali coordinates
        weather_data = {}
        try:
            url = (
                "https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}"
                "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
                "&timezone=Africa%2FKigali"
            )
            resp = requests.get(url, timeout=5)
            json_data = resp.json()
            weather_data = json_data.get("daily", {})
        except Exception as e:
            weather_data = {
                "temperature_2m_max": [],
                "temperature_2m_min": [],
                "precipitation_sum": [],
                "time": [],
                "error": str(e)
            }

        # ---- Market Prices (from DB) ----
        try:
            market_prices = MarketPrice.query.order_by(MarketPrice.date.desc()).all()
        except Exception as e:
            market_prices = []
            app.logger.error(f"Error fetching market prices: {e}")

        # ---- Available Dealer Inventories (simple list across dealers) ----
        try:
            inventories = Inventory.query.order_by(Inventory.product_name.asc()).all()
        except Exception as e:
            inventories = []
            app.logger.error(f"Error fetching inventories: {e}")

        # ---- Farmer's Orders ----
        try:
            my_orders = Order.query.filter_by(farmer_id=current_user.id).order_by(desc(Order.created_at)).all()
        except Exception as e:
            my_orders = []
            app.logger.error(f"Error fetching farmer orders: {e}")

        return render_template(
            "dashboards/farmer_dashboard.html",
            user=current_user,
            weather_data=weather_data,
            market_prices=market_prices,
            inventories=inventories,
            my_orders=my_orders
        )

    # ... other roles unchanged ...


    elif role == "promoter":
        return render_template("dashboards/promoter_dashboard.html", user=current_user)
    elif role == "dealer":
        return redirect(url_for('agro_dealer_dashboard'))
    elif role == "processor":
        # Pull processor-facing datasets
        try:
            offers = Crop.query.order_by(desc(Crop.id)).all()
            crops = [{
                "farmer_name": (User.query.get(o.farmer_id).full_name if User.query.get(o.farmer_id) else f"Farmer #{o.farmer_id}"),
                "crop_name": o.crop_name,
                "quantity": o.quantity,
                "unit": o.unit or 'kg',
                "price": float(o.price) if o.price is not None else None,
                "province": o.province or "-"
            } for o in offers]
        except Exception as e:
            app.logger.error(f"Processor crops fetch error: {e}")
            crops = []

        try:
            certs = Certification.query.order_by(desc(Certification.cert_date)).all()
            certifications = [{
                "product_name": c.product_name,
                "cert_date": c.cert_date,
                "expiry_date": c.expiry_date
            } for c in certs]
        except Exception as e:
            app.logger.error(f"Processor certifications fetch error: {e}")
            certifications = []

        try:
            schedules = DeliverySchedule.query.order_by(desc(DeliverySchedule.delivery_date)).all()
            logistics = [{
                "product_name": s.product_name,
                "quantity": s.quantity,
                "destination": s.destination,
                "delivery_date": s.delivery_date,
                "status": s.status
            } for s in schedules]
        except Exception as e:
            app.logger.error(f"Processor logistics fetch error: {e}")
            logistics = []

        try:
            po = Order.query.filter(Order.processor_id.isnot(None)).order_by(desc(Order.id)).all()
            orders = [{
                "customer_name": (User.query.get(o.customer_id).full_name if o.customer_id else 'Customer'),
                "product_name": o.product_name,
                "quantity": o.quantity,
                "unit": o.unit,
                "status": o.status
            } for o in po]
        except Exception as e:
            app.logger.error(f"Processor orders fetch error: {e}")
            orders = []

        return render_template("dashboards/processor_dashboard.html",
                               user=current_user,
                               crops=crops,
                               certifications=certifications,
                               logistics=logistics,
                               orders=orders)
    # ---------------- Researcher ----------------
    elif role == "researcher":
        try:
            # Fetch market prices from DB
            market_prices = MarketPrice.query.order_by(MarketPrice.date.desc()).all()

            # Prepare chart data
            chart_data = {"dates": [], "commodities": {}, "avg_prices": {}}

            if market_prices:
                # Extract unique sorted dates
                unique_dates = sorted(set([mp.date.strftime("%Y-%m-%d") for mp in market_prices]))
                chart_data["dates"] = unique_dates

                # Group by commodity
                commodity_prices = {}
                for mp in market_prices:
                    if mp.commodity not in commodity_prices:
                        commodity_prices[mp.commodity] = {}
                    commodity_prices[mp.commodity][mp.date.strftime("%Y-%m-%d")] = mp.price

                # Build datasets aligned with dates
                for commodity, prices_by_date in commodity_prices.items():
                    values = [prices_by_date.get(d, None) for d in unique_dates]
                    chart_data["commodities"][commodity] = values

                    # Average price
                    valid_prices = [p for p in prices_by_date.values() if p is not None]
                    chart_data["avg_prices"][commodity] = (
                        sum(valid_prices) / len(valid_prices) if valid_prices else 0
                    )
            else:
                chart_data = None

            # -------- Load NISR dataset for charts (robust parsing) --------
            nisr_chart_data = None
            try:
                df = pd.read_excel("datasets/Tables_2025_Season_A.xlsx")
                # Normalize column names for flexible matching
                normalized = {c: str(c).strip() for c in df.columns}
                df.columns = list(normalized.values())
                lower_map = {c.lower(): c for c in df.columns}

                # Try to find commodity-like and value-like columns
                commodity_candidates = [k for k in lower_map if any(x in k for x in ["commodity", "crop", "product", "item", "name"])]
                value_candidates = [k for k in lower_map if any(x in k for x in ["price", "value", "amount", "yield", "production", "qty", "quantity"]) ]

                commodity_col = lower_map.get(commodity_candidates[0]) if commodity_candidates else None

                value_col = None
                if value_candidates:
                    # Pick the first numeric-capable candidate
                    for vk in value_candidates:
                        col = lower_map[vk]
                        series = pd.to_numeric(df[col], errors="coerce")
                        if series.notna().sum() > 0:
                            value_col = col
                            break
                if value_col is None:
                    # Fallback to first numeric column in the dataset
                    for col in df.columns:
                        series = pd.to_numeric(df[col], errors="coerce")
                        if series.notna().sum() > 0:
                            value_col = col
                            break

                if commodity_col and value_col:
                    numeric_series = pd.to_numeric(df[value_col], errors="coerce")
                    tmp = df[[commodity_col]].copy()
                    tmp[value_col] = numeric_series
                    tmp = tmp.dropna(subset=[value_col])
                    if not tmp.empty:
                        avg_values = tmp.groupby(commodity_col)[value_col].mean().sort_values(ascending=False)
                        nisr_chart_data = {
                            "commodities": avg_values.index.tolist(),
                            "avg_prices": [float(v) for v in avg_values.values]
                        }
                        # Histogram
                        hist_series = numeric_series.dropna()
                        if not hist_series.empty:
                            bins = pd.cut(hist_series, bins=10)
                            counts = bins.value_counts(sort=False)
                            bin_labels = [f"{interval.left:.0f}-{interval.right:.0f}" for interval in counts.index]
                            nisr_chart_data.update({
                                "histogram_bins": bin_labels,
                                "histogram_counts": counts.tolist()
                            })
                else:
                    app.logger.warning("NISR dataset: could not detect commodity/value columns; charts skipped.")
            except Exception as e:
                app.logger.error(f"Error reading NISR dataset for researcher: {e}")

            # -------- Load Maize production dataset (CSV) --------
            maize_data = None
            try:
                maize_df = pd.read_csv("datasets/rwanda_maize_production_2025.csv")
                # Normalize column names
                col_prov = "Provinces"
                col_dist = "Districts"
                col_2025 = "2025 Production (MT)"
                col_2024 = "2024 Production (MT)"
                col_diff = "Difference (MT)"
                col_pct = "Change (%)"

                # Aggregate by province for bar/pie charts
                by_prov = maize_df.groupby(col_prov, dropna=False)[[col_2025, col_2024]].sum().reset_index()
                provinces = by_prov[col_prov].tolist()
                prod_2025 = by_prov[col_2025].tolist()
                prod_2024 = by_prov[col_2024].tolist()

                # Histogram on district-level change percentage
                # Coerce inf/strings to NaN then drop
                change_pct_series = pd.to_numeric(maize_df[col_pct].replace([float('inf'), 'inf', 'Inf', 'INF'], pd.NA), errors="coerce").dropna()
                # Use pandas cut for bins
                hist_bins = None
                hist_counts = None
                if not change_pct_series.empty:
                    bins = pd.cut(change_pct_series, bins=10)
                    counts = bins.value_counts(sort=False)
                    hist_bins = [f"{interval.left:.1f}-{interval.right:.1f}%" for interval in counts.index]
                    hist_counts = counts.tolist()

                maize_data = {
                    "provinces": provinces,
                    "prod_2025": prod_2025,
                    "prod_2024": prod_2024,
                    "histogram_bins": hist_bins,
                    "histogram_counts": hist_counts,
                    # For preview table
                    "preview": maize_df.head(10).to_dict(orient="records")
                }
            except Exception as e:
                app.logger.error(f"Error reading Maize production dataset: {e}")

        except Exception as e:
            app.logger.error(f"Error preparing researcher data: {e}")
            market_prices, chart_data, nisr_chart_data, maize_data = [], None, None, None

        return render_template(
            "dashboards/researcher_dashboard.html",
            user=current_user,
            market_prices=market_prices,
            chart_data=chart_data,
            nisr_chart_data=nisr_chart_data,
            maize_data=maize_data
        )

    elif role == "policy":
        stats = {
            "farmers": User.query.filter_by(role="farmer").count(),
            "promoters": User.query.filter_by(role="promoter").count(),
            "dealers": User.query.filter_by(role="dealer").count(),
            "processors": User.query.filter_by(role="processor").count(),
            "researchers": User.query.filter_by(role="researcher").count(),
            "policymakers": User.query.filter_by(role="policy").count(),
        }
        return render_template("dashboards/policy_dashboard.html",
                               user=current_user, stats=stats)
    else:
        flash("Role not recognized. Contact admin.", "error")
        return redirect(url_for("login"))
    
    # ====================================================
# Researcher Dataset Download
# ====================================================

# Download route for NISR dataset
@app.route('/download/nisr_dataset')
def download_nisr_dataset():
    try:
        return send_from_directory(
            directory="datasets",
            path="Tables_2025_Season_A.xlsx",
            as_attachment=True
        )
    except Exception as e:
        app.logger.error(f"Error downloading NISR dataset: {e}")
        return "Dataset not available", 500


# Download route for Maize production dataset
@app.route('/download/maize_dataset')
def download_maize_dataset():
    try:
        return send_from_directory(
            directory="datasets",
            path="rwanda_maize_production_2025.csv",
            as_attachment=True
        )
    except Exception as e:
        app.logger.error(f"Error downloading Maize dataset: {e}")
        return "Dataset not available", 500
@app.route('/agro-dealer-dashboard')
@login_required
def agro_dealer_dashboard():
    # Only dealers should access
    if current_user.role != 'dealer':
        flash("Access denied: dealer-only area.", "error")
        return redirect(url_for('dashboard'))

    # Inventory for this dealer
    inventory = Inventory.query.filter_by(dealer_id=current_user.id).order_by(Inventory.product_name).all()

    # Orders where this dealer is recipient (latest first)
    orders = Order.query.filter_by(dealer_id=current_user.id).order_by(desc(Order.created_at)).all()

    # Active subsidies
    today = date.today()
    subsidies = Subsidy.query.filter(Subsidy.active == True).all()

    return render_template('dashboards/dealer_dashboard.html',
                           user=current_user,
                           inventory=inventory,
                           orders=orders,
                           subsidies=subsidies)

# Approve or reject an order
@app.route('/dealer/order/<int:order_id>/action', methods=['POST'])
@login_required
def dealer_order_action(order_id):
    if current_user.role != 'dealer':
        flash("Access denied.", "error")
        return redirect(url_for('dashboard'))

    action = request.form.get('action')  # 'approve' or 'reject' or 'deliver'
    order = Order.query.get_or_404(order_id)
    if order.dealer_id != current_user.id:
        flash("You cannot manage this order.", "error")
        return redirect(url_for('agro_dealer_dashboard'))

    if action == 'approve':
        order.status = 'approved'
        order.updated_at = db.func.now()
        # Optionally: subtract stock if matching inventory exists
        inv = Inventory.query.filter_by(dealer_id=current_user.id, product_name=order.product_name).first()
        if inv:
            if inv.stock >= order.quantity:
                inv.stock = inv.stock - order.quantity
            else:
                flash("Warning: stock is lower than ordered quantity. Stock will go negative.", "error")
                inv.stock = inv.stock - order.quantity
    elif action == 'reject':
        order.status = 'rejected'
        order.updated_at = db.func.now()
    elif action == 'deliver':
        order.status = 'delivered'
        order.updated_at = db.func.now()
    else:
        flash("Unknown action.", "error")
        return redirect(url_for('agro_dealer_dashboard'))

    db.session.commit()
    flash("Order updated.", "success")
    return redirect(url_for('agro_dealer_dashboard'))


# Farmer creates an order
@app.route('/farmer/order/create', methods=['POST'])
@login_required
def farmer_create_order():
    if current_user.role != 'farmer':
        flash("Access denied.", "error")
        return redirect(url_for('dashboard'))

    dealer_id = request.form.get('dealer_id')
    product_name = request.form.get('product_name')
    quantity = request.form.get('quantity')
    unit = request.form.get('unit') or 'kg'

    if not all([dealer_id, product_name, quantity]):
        flash("Missing required fields.", "error")
        return redirect(url_for('dashboard'))

    try:
        # Validate dealer exists and is a dealer
        dealer_user = User.query.get(int(dealer_id))
        if not dealer_user or dealer_user.role != 'dealer':
            flash("Selected dealer is invalid.", "error")
            return redirect(url_for('dashboard'))

        order = Order(
            farmer_id=current_user.id,
            dealer_id=int(dealer_id),
            product_name=product_name.strip(),
            quantity=int(quantity),
            unit=unit.strip(),
            status='pending',
            created_at=db.func.now(),
            updated_at=None
        )
        db.session.add(order)
        db.session.commit()
        flash("Order submitted to agro-dealer.", "success")
    except Exception as e:
        app.logger.error(f"Create order error: {e}")
        flash("Could not submit order.", "error")

    return redirect(url_for('dashboard'))

# Update inventory stock inline
@app.route('/dealer/inventory/<int:inv_id>/update', methods=['POST'])
@login_required
def dealer_inventory_update(inv_id):
    if current_user.role != 'dealer':
        flash("Access denied.", "error")
        return redirect(url_for('dashboard'))

    inv = Inventory.query.get_or_404(inv_id)
    if inv.dealer_id != current_user.id:
        flash("You cannot edit this inventory item.", "error")
        return redirect(url_for('agro_dealer_dashboard'))

    try:
        new_stock = int(request.form.get('stock'))
        new_price = request.form.get('price')
        inv.stock = new_stock
        if new_price:
            inv.price = float(new_price)
        inv.last_updated = db.func.now()
        db.session.commit()
        flash("Inventory updated.", "success")
    except Exception as e:
        app.logger.error(f"Inventory update error: {e}")
        flash("Invalid values.", "error")

    return redirect(url_for('agro_dealer_dashboard'))


# Create inventory item
@app.route('/dealer/inventory/create', methods=['POST'])
@login_required
def dealer_inventory_create():
    if current_user.role != 'dealer':
        flash("Access denied.", "error")
        return redirect(url_for('dashboard'))

    product_name = request.form.get('product_name')
    unit = request.form.get('unit') or 'kg'
    stock = request.form.get('stock') or 0
    price = request.form.get('price') or None

    if not product_name:
        flash("Product name is required.", "error")
        return redirect(url_for('agro_dealer_dashboard'))

    try:
        inv = Inventory(
            dealer_id=current_user.id,
            product_name=product_name.strip(),
            stock=int(stock),
            unit=unit.strip(),
            price=float(price) if price else None,
        )
        db.session.add(inv)
        db.session.commit()
        flash("Inventory item created.", "success")
    except Exception as e:
        app.logger.error(f"Inventory create error: {e}")
        flash("Could not create inventory.", "error")

    return redirect(url_for('agro_dealer_dashboard'))

# Create a new subsidy (dealer can propose; admin/policy maker usually creates -- simple form here)
@app.route('/dealer/subsidy/create', methods=['POST'])
@login_required
def dealer_create_subsidy():
    if current_user.role != 'dealer':
        flash("Access denied.", "error")
        return redirect(url_for('dashboard'))

    title = request.form.get('title')
    commodity = request.form.get('commodity')
    discount = request.form.get('discount_percent') or 0
    valid_from = request.form.get('valid_from') or None
    valid_to = request.form.get('valid_to') or None

    try:
        s = Subsidy(
            title=title,
            commodity=commodity,
            discount_percent=int(discount),
            valid_from=date.fromisoformat(valid_from) if valid_from else None,
            valid_to=date.fromisoformat(valid_to) if valid_to else None,
            active=True
        )
        db.session.add(s)
        db.session.commit()
        flash("Subsidy proposal created.", "success")
    except Exception as e:
        app.logger.error(f"Error creating subsidy: {e}")
        flash("Could not create subsidy.", "error")

    return redirect(url_for('agro_dealer_dashboard'))


# Researcher Dashboard
@app.route('/researcher_dashboard')
def researcher_dashboard():
    user = {"full_name": "Researcher User"}  # Replace with actual logged-in user

    market_prices = MarketPrice.query.order_by(MarketPrice.date.desc()).all()

    # ✅ Load NISR dataset (preview + robust chart data)
    nisr_preview, nisr_chart_data = None, None
    try:
        df = pd.read_excel("datasets/Tables_2025_Season_A.xlsx")
        nisr_preview = df.head(10).to_dict(orient="records")

        normalized = {c: str(c).strip() for c in df.columns}
        df.columns = list(normalized.values())
        lower_map = {c.lower(): c for c in df.columns}

        commodity_candidates = [k for k in lower_map if any(x in k for x in ["commodity", "crop", "product", "item", "name"])]
        value_candidates = [k for k in lower_map if any(x in k for x in ["price", "value", "amount", "yield", "production", "qty", "quantity"]) ]

        commodity_col = lower_map.get(commodity_candidates[0]) if commodity_candidates else None

        value_col = None
        if value_candidates:
            for vk in value_candidates:
                col = lower_map[vk]
                series = pd.to_numeric(df[col], errors="coerce")
                if series.notna().sum() > 0:
                    value_col = col
                    break
        if value_col is None:
            for col in df.columns:
                series = pd.to_numeric(df[col], errors="coerce")
                if series.notna().sum() > 0:
                    value_col = col
                    break

        if commodity_col and value_col:
            numeric_series = pd.to_numeric(df[value_col], errors="coerce")
            tmp = df[[commodity_col]].copy()
            tmp[value_col] = numeric_series
            tmp = tmp.dropna(subset=[value_col])
            if not tmp.empty:
                avg_values = tmp.groupby(commodity_col)[value_col].mean().sort_values(ascending=False)
                nisr_chart_data = {
                    "commodities": avg_values.index.tolist(),
                    "avg_prices": [float(v) for v in avg_values.values]
                }
                hist_series = numeric_series.dropna()
                if not hist_series.empty:
                    bins = pd.cut(hist_series, bins=10)
                    counts = bins.value_counts(sort=False)
                    bin_labels = [f"{interval.left:.0f}-{interval.right:.0f}" for interval in counts.index]
                    nisr_chart_data.update({
                        "histogram_bins": bin_labels,
                        "histogram_counts": counts.tolist()
                    })
        else:
            app.logger.warning("NISR dataset (standalone): could not detect commodity/value columns; charts skipped.")
    except Exception as e:
        app.logger.error(f"Error reading NISR dataset: {e}")

    # ✅ Load Maize dataset (preview + chart data)
    maize_data = None
    try:
        maize_df = pd.read_csv("datasets/rwanda_maize_production_2025.csv")
        col_prov = "Provinces"
        col_dist = "Districts"
        col_2025 = "2025 Production (MT)"
        col_2024 = "2024 Production (MT)"
        col_diff = "Difference (MT)"
        col_pct = "Change (%)"

        by_prov = maize_df.groupby(col_prov, dropna=False)[[col_2025, col_2024]].sum().reset_index()
        provinces = by_prov[col_prov].tolist()
        prod_2025 = by_prov[col_2025].tolist()
        prod_2024 = by_prov[col_2024].tolist()

        change_pct_series = pd.to_numeric(maize_df[col_pct].replace([float('inf'), 'inf', 'Inf', 'INF'], pd.NA), errors="coerce").dropna()
        hist_bins = None
        hist_counts = None
        if not change_pct_series.empty:
            bins = pd.cut(change_pct_series, bins=10)
            counts = bins.value_counts(sort=False)
            hist_bins = [f"{interval.left:.1f}-{interval.right:.1f}%" for interval in counts.index]
            hist_counts = counts.tolist()

        maize_data = {
            "provinces": provinces,
            "prod_2025": prod_2025,
            "prod_2024": prod_2024,
            "histogram_bins": hist_bins,
            "histogram_counts": hist_counts,
            "preview": maize_df.head(10).to_dict(orient="records")
        }
    except Exception as e:
        app.logger.error(f"Error reading Maize dataset: {e}")

    # Existing DB chart data
    chart_data = None
    if market_prices:
        commodities = {}
        dates = sorted(set([mp.date.strftime("%Y-%m-%d") for mp in market_prices]))
        for mp in market_prices:
            if mp.commodity not in commodities:
                commodities[mp.commodity] = {}
            commodities[mp.commodity][mp.date.strftime("%Y-%m-%d")] = mp.price

        datasets = {c: [commodities[c].get(d, None) for d in dates] for c in commodities}
        avg_prices = {c: sum(v for v in vals if v) / len([v for v in vals if v]) for c, vals in datasets.items()}
        chart_data = {"dates": dates, "commodities": datasets, "avg_prices": avg_prices}

    return render_template(
        "researcher_dashboard.html",
        user=user,
        market_prices=market_prices,
        chart_data=chart_data,
        nisr_preview=nisr_preview,
        nisr_chart_data=nisr_chart_data,
        maize_data=maize_data
    )
    
    
@app.route("/download_market_prices")
@login_required
def download_market_prices():
    if current_user.role != "researcher" and current_user.role != "policy":
        flash("Access denied. Only researchers and policymakers can download datasets.", "error")
        return redirect(url_for("dashboard"))

    try:
        prices = MarketPrice.query.order_by(MarketPrice.date.desc()).all()
    except Exception as e:
        app.logger.error(f"Error fetching market prices: {e}")
        return "No market price data available", 404

    if not prices:
        return "No market price data available", 404

    # Convert to DataFrame
    df = pd.DataFrame([{
        "ID": p.id,
        "Commodity": p.commodity,
        "Price": p.price,
        "Province": p.province,
        "Unit": p.unit,
        "Date": p.date
    } for p in prices])

    # Save to memory as CSV
    output = BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)

    return send_file(
        output,
        mimetype="text/csv",
        as_attachment=True,
        download_name="market_prices.csv"
    )

# -------- User Listing for Policy Maker --------
@app.route('/users/<role>')
@login_required
def list_users(role):
    if current_user.role != "policy":
        flash("Access denied. Only policy makers can view user lists.", "error")
        return redirect(url_for("dashboard"))

    valid_roles = ["farmer", "promoter", "dealer", "processor", "researcher", "policy"]
    if role not in valid_roles:
        flash("Invalid role selected.", "error")
        return redirect(url_for("dashboard"))

    users = User.query.filter_by(role=role).all()
    return render_template("dashboards/user_list.html",
                           role=role.capitalize(), users=users)

# -------- Export Users (Excel & PDF) --------
@app.route('/export/<role>/<filetype>')
@login_required
def export_users(role, filetype):
    if current_user.role != "policy":
        flash("Access denied. Only policy makers can export data.", "error")
        return redirect(url_for("dashboard"))

    valid_roles = ["farmer", "promoter", "dealer", "processor", "researcher", "policy"]
    if role not in valid_roles:
        flash("Invalid role.", "error")
        return redirect(url_for("dashboard"))

    users = User.query.filter_by(role=role).all()
    data = [{
        "ID": u.id,
        "Full Name": u.full_name,
        "Phone": u.phone or "-",
        "Email": u.email or "-"
    } for u in users]

    # Excel
    if filetype == "excel":
        df = pd.DataFrame(data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name=f"{role.capitalize()}s")
        output.seek(0)
        return send_file(output, as_attachment=True,
                         download_name=f"{role}_users.xlsx",
                         mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # PDF
    elif filetype == "pdf":
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        elements.append(Paragraph(f"{role.capitalize()} Users", styles['Title']))

        table_data = [["ID", "Full Name", "Phone", "Email"]] + [
            [str(u.id), u.full_name, u.phone or "-", u.email or "-"] for u in users
        ]
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#263238")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(table)

        doc.build(elements)
        output.seek(0)
        return send_file(output, as_attachment=True,
                         download_name=f"{role}_users.pdf",
                         mimetype="application/pdf")

    else:
        flash("Unsupported export format.", "error")
        return redirect(url_for("list_users", role=role))

# ====================================================
# Contact
# ====================================================
@app.route('/contact', methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message_body = request.form.get("message")

        try:
            msg = Message(
                subject=f"New Contact Form Message from {name}",
                recipients=["oniyonkuru233@gmail.com"],
                body=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message_body}"
            )
            mail.send(msg)
            flash("Your message has been sent successfully!", "success")
        except Exception as e:
            flash(f"Error sending message: {str(e)}", "error")

        return redirect(url_for("contact"))

    return render_template('contact.html')

# ====================================================
# Other Informational Pages
# ====================================================
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
    youtube_id = "29KDeFQIIpI"
    return render_template('service.html', youtube_id=youtube_id)

@app.route('/weather')
def weather():
    return render_template('weather.html')

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

# ====================================================
# Run
# ====================================================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
    
    
    
@app.route('/farmer/crops/create', methods=['POST'])
@login_required
def farmer_create_crop():
    if current_user.role != 'farmer':
        flash("Access denied.", "error")
        return redirect(url_for('dashboard'))

    crop_name = request.form.get('crop_name')
    quantity = request.form.get('quantity')
    unit = request.form.get('unit') or 'kg'
    price = request.form.get('price')
    province = request.form.get('province')

    if not crop_name or not quantity:
        flash("Crop name and quantity are required.", "error")
        return redirect(url_for('dashboard'))

    try:
        crop = Crop(
            farmer_id=current_user.id,
            crop_name=crop_name.strip(),
            quantity=float(quantity),
            unit=unit.strip() if unit else None,
            price=float(price) if price else None,
            province=province.strip() if province else None,
        )
        db.session.add(crop)
        db.session.commit()
        flash("Crop offer published for processors.", "success")
    except Exception as e:
        app.logger.error(f"Create crop error: {e}")
        flash("Could not publish crop offer.", "error")

    return redirect(url_for('dashboard'))