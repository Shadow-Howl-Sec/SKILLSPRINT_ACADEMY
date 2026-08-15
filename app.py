import os
import uuid
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_mail import Mail, Message
from flask_login import LoginManager, current_user, login_user, login_required
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
import razorpay
import oracledb
from flask_dance.contrib.google import make_google_blueprint, google
from sqlalchemy import text
from extensions import db, limiter, talisman, migrate

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config.from_object('config.Config')

# Initialize extensions
db.init_app(app)
migrate.init_app(app, db)
limiter.init_app(app)

# Basic Talisman config
talisman.init_app(
    app,
    content_security_policy={
        'default-src': "'self'",
        'script-src': [
            "'self'",
            'https://cdn.jsdelivr.net',
            'https://checkout.razorpay.com',
            "'unsafe-inline'"
        ],
        'style-src': [
            "'self'",
            'https://cdn.jsdelivr.net',
            'https://fonts.googleapis.com',
            "'unsafe-inline'"
        ],
        'font-src': [
            "'self'",
            'https://fonts.gstatic.com',
            'https://cdn.jsdelivr.net'
        ],
        'img-src': ["'self'", 'data:', 'https:']
    }
)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Initialize CSRF protection
csrf = CSRFProtect(app)

from auth import auth
from admin import admin
app.register_blueprint(auth)
app.register_blueprint(admin)

# --- CyberSec Platform Blueprints ---
from blueprints.onboarding.routes import onboarding_bp
from blueprints.assessment.routes import assessment_bp
from blueprints.roadmap.routes import roadmap_bp
from blueprints.dashboard.routes import dashboard_bp
from blueprints.labs.routes import labs_bp
from blueprints.library.routes import library_bp
from blueprints.assistant.routes import assistant_bp
from blueprints.job_roles.routes import job_roles_bp

app.register_blueprint(onboarding_bp)
app.register_blueprint(assessment_bp)
app.register_blueprint(roadmap_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(labs_bp)
app.register_blueprint(library_bp)
app.register_blueprint(assistant_bp)
app.register_blueprint(job_roles_bp)

login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'



# Razorpay credentials
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', 'rzp_test_xxxxxxxx')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', 'xxxxxxxxxxxxxx')

razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# Flask-Mail config
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'skillsprint_support@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'your_email_password')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'skillsprint_support@gmail.com')
mail = Mail(app)

# Import models after db.init_app(app)
from models import User, Course, Coupon, Enrollment, Payment, AdminLog

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Google OAuth config
GOOGLE_OAUTH_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', 'your_google_client_id_here')
GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET', 'your_google_client_secret_here')
google_bp = make_google_blueprint(
    client_id=GOOGLE_OAUTH_CLIENT_ID,
    client_secret=GOOGLE_OAUTH_CLIENT_SECRET,
    scope=["profile", "email"],
    redirect_url="/login/google/authorized"
)
app.register_blueprint(google_bp, url_prefix="/login")

@app.route('/login/google/authorized')
def google_login_authorized():
    if not google.authorized:
        flash('Google login failed or was cancelled.', 'error')
        return redirect(url_for('auth.login'))
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash('Failed to fetch user info from Google.', 'error')
        return redirect(url_for('auth.login'))
    info = resp.json()
    email = info["email"]
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User()
        user.username = info.get("name", email.split("@")[0])
        user.email = email
        user.first_name = info.get("given_name", "")
        user.last_name = info.get("family_name", "")
        user.email_verified = True
    # Do not assign to is_active if it's a property; default is True in model
    db.session.add(user)
    db.session.commit()
    login_user(user)
    flash('Logged in successfully with Google!', 'success')
    return redirect(url_for('index'))

@app.route('/')
def index():
    # Get some featured courses for the homepage
    featured_courses = Course.query.filter_by(is_active=True).limit(6).all()
    return render_template('index.html', featured_courses=featured_courses)

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connection
        db.session.execute(text('SELECT 1'))  # type: ignore[attr-defined]
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/courses')
def courses():
    # Get all active courses
    courses = Course.query.filter_by(is_active=True).all()
    
    # Group courses by category for better organization
    categories = {}
    for course in courses:
        if course.category not in categories:
            categories[course.category] = []
        categories[course.category].append(course)
    
    return render_template('courses.html', courses=courses, categories=categories)

@csrf.exempt
@app.route('/create_order', methods=['POST'])
def create_order():
    data = request.get_json()
    amount = int(data.get('amount', 2499)) * 100  # INR to paise
    # The following is correct for razorpay, ignore Pylance warning
    order = razorpay_client.order.create({
        'amount': amount,
        'currency': 'INR',
        'payment_capture': 1
    })
    return jsonify({'order_id': order['id'], 'key_id': RAZORPAY_KEY_ID, 'amount': amount})

@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET'])
def contact():
    return render_template('contact.html')

@app.route('/contact', methods=['POST'])
def contact_submit():
    name    = request.form.get('name', '').strip()
    email   = request.form.get('email', '').strip()
    phone   = request.form.get('phone', '').strip()
    subject = request.form.get('subject', '').strip()
    message = request.form.get('message', '').strip()

    if not name or not email or not message:
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('contact'))

    try:
        msg = Message(
            subject=f'[SkillSprint Contact] {subject} — from {name}',
            recipients=['skillsprint_support@gmail.com'],
            reply_to=email
        )
        msg.body = f"""New contact form submission:\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nSubject: {subject}\n\nMessage:\n{message}"""
        mail.send(msg)
    except Exception as e:
        print('Contact mail error:', e)

    flash('Message sent! We will get back to you within 24 hours.', 'success')
    return redirect(url_for('contact'))

@app.route('/dashboard')
@login_required
def student_dashboard():
    """Redirect legacy dashboard to new cybersecurity dashboard."""
    return redirect(url_for('dashboard.today'))

@app.route('/profile')
@login_required
def profile():
    return redirect(url_for('student_dashboard'))

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/course/<int:course_id>')
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    if not course.is_active:
        flash('This course is not available.', 'error')
        return redirect(url_for('courses'))
    
    # Get related courses in the same category
    related_courses = Course.query.filter(
        Course.category == course.category,
        Course.id != course.id,
        Course.is_active == True
    ).limit(3).all()
    
    return render_template('course_detail.html', course=course, related_courses=related_courses)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    try:
        db.session.rollback()
    except Exception:
        pass
    return render_template('errors/500.html'), 500

# Create database tables
def create_tables():
    with app.app_context():
        try:
            db.create_all()
            print("[OK] Database tables created successfully!")
        except Exception as e:
            print(f"[ERR] Error creating database tables: {e}")
            return
        
        # Create or update admin user
        admin_email = app.config.get('ADMIN_EMAIL')
        admin_password = app.config.get('ADMIN_PASSWORD')

        admin_user = User.query.filter_by(email=admin_email).first()
        
        print("Database initialized successfully!")
        print("Admin can now add courses through the admin panel at /admin/courses")

if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        create_tables()
        print(" SkillSprint Academy is starting up...")
        print(" Website: http://127.0.0.1:5000")
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n SkillSprint Academy stopped by user")
    except Exception as e:
        print(f"Error starting application: {e}")