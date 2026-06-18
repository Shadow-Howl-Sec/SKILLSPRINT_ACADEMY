from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import uuid

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, db.Identity(start=1), primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    college = db.Column(db.String(100), nullable=False)
    year = db.Column(db.String(20), nullable=False)
    branch = db.Column(db.String(50), nullable=False)
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(100), unique=True)
    reset_password_token = db.Column(db.String(100), unique=True)
    reset_password_expires = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    enrollments = db.relationship('Enrollment', backref='user', lazy=True)
    payments = db.relationship('Payment', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_verification_token(self):
        self.email_verification_token = str(uuid.uuid4())
        return self.email_verification_token
    
    def generate_reset_token(self):
        self.reset_password_token = str(uuid.uuid4())
        self.reset_password_expires = datetime.utcnow() + timedelta(hours=24)
        return self.reset_password_token
    def __repr__(self):
        return f"<{self.__class__.__name__} {self.id}>"


class Course(db.Model):
    id = db.Column(db.Integer, db.Identity(start=1), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # IT, Computer Engineering, AI&DS, AI&ML, CS-related
    difficulty = db.Column(db.String(30), nullable=False)  # beginner, intermediate, advanced
    duration_weeks = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    discounted_price = db.Column(db.Float)
    image_url = db.Column(db.String(255))
    icon_class = db.Column(db.String(50))  # Bootstrap icon class
    features = db.Column(db.Text)  # JSON string of features
    roadmap_steps = db.Column(db.Text)  # JSON string of roadmap steps
    
    # Enhanced fields for your requirements
    video_links = db.Column(db.Text)  # JSON string of video/tutorial links
    practice_tests = db.Column(db.Text)  # JSON string of practice test configurations
    mini_projects = db.Column(db.Text)  # JSON string of mini project briefs
    course_materials = db.Column(db.Text)  # JSON string of downloadable materials
    target_branches = db.Column(db.Text)  # JSON string of target branches (IT, Computer Engineering, etc.)
    industry_relevance = db.Column(db.Text)  # Description of industry applications
    certification_info = db.Column(db.Text)  # Certification details
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    enrollments = db.relationship('Enrollment', backref='course', lazy=True)
    coupons = db.relationship('Coupon', backref='course', lazy=True)
    practice_tests_rel = db.relationship('PracticeTest', backref='course', lazy=True)
    mini_projects_rel = db.relationship('MiniProject', backref='course', lazy=True)
    def __repr__(self):
        return f"<{self.__class__.__name__} {self.id}>"


class Coupon(db.Model):
    id = db.Column(db.Integer, db.Identity(start=1), primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    discount_type = db.Column(db.String(10), nullable=False)  # percentage, fixed
    discount_value = db.Column(db.Float, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)
    max_uses = db.Column(db.Integer, default=100)
    used_count = db.Column(db.Integer, default=0)
    valid_from = db.Column(db.DateTime, nullable=False)
    valid_until = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    payments = db.relationship('Payment', backref='coupon', lazy=True)
    def __repr__(self):
        return f"<{self.__class__.__name__} {self.id}>"


class Enrollment(db.Model):
    id = db.Column(db.Integer, db.Identity(start=1), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    completion_date = db.Column(db.DateTime)
    progress = db.Column(db.Float, default=0.0)  # 0-100%
    status = db.Column(db.String(20), default='enrolled')  # enrolled, in_progress, completed, cancelled
    payment_id = db.Column(db.Integer, db.ForeignKey('payment.id'), nullable=True)
    
    # Relationships
    payment = db.relationship('Payment', backref='enrollment', lazy=True)
    def __repr__(self):
        return f"<{self.__class__.__name__} {self.id}>"


class Payment(db.Model):
    id = db.Column(db.Integer, db.Identity(start=1), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    coupon_id = db.Column(db.Integer, db.ForeignKey('coupon.id'), nullable=True)
    razorpay_order_id = db.Column(db.String(100), unique=True)
    razorpay_payment_id = db.Column(db.String(100), unique=True)
    amount = db.Column(db.Float, nullable=False)
    discount_amount = db.Column(db.Float, default=0.0)
    final_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed, refunded
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    course = db.relationship('Course', backref='payments', lazy=True)
    def __repr__(self):
        return f"<{self.__class__.__name__} {self.id}>"


class AdminLog(db.Model):
    id = db.Column(db.Integer, db.Identity(start=1), primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    table_name = db.Column(db.String(50), nullable=False)
    record_id = db.Column(db.Integer)
    old_values = db.Column(db.Text)  # JSON string
    new_values = db.Column(db.Text)  # JSON string
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    admin = db.relationship('User', backref='admin_logs', lazy=True)
    def __repr__(self):
        return f"<{self.__class__.__name__} {self.id}>"


class PracticeTest(db.Model):
    id = db.Column(db.Integer, db.Identity(start=1), primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    questions = db.Column(db.Text)  # JSON string of MCQ questions
    time_limit = db.Column(db.Integer)  # Time limit in minutes
    pass_percentage = db.Column(db.Float, default=70.0)  # Pass percentage
    max_attempts = db.Column(db.Integer, default=3)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    attempts = db.relationship('TestAttempt', backref='practice_test', lazy=True)
    def __repr__(self):
        return f"<{self.__class__.__name__} {self.id}>"


class TestAttempt(db.Model):
    id = db.Column(db.Integer, db.Identity(start=1), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('practice_test.id'), nullable=False)
    score = db.Column(db.Float)
    total_questions = db.Column(db.Integer)
    correct_answers = db.Column(db.Integer)
    time_taken = db.Column(db.Integer)  # Time taken in seconds
    passed = db.Column(db.Boolean)
    answers = db.Column(db.Text)  # JSON string of user answers
    attempt_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='test_attempts', lazy=True)
    def __repr__(self):
        return f"<{self.__class__.__name__} {self.id}>"


class MiniProject(db.Model):
    id = db.Column(db.Integer, db.Identity(start=1), primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    project_brief = db.Column(db.Text)  # Detailed project requirements
    deliverables = db.Column(db.Text)  # JSON string of expected deliverables
    difficulty_level = db.Column(db.String(20))  # easy, medium, hard
    estimated_hours = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    submissions = db.relationship('ProjectSubmission', backref='mini_project', lazy=True)
    def __repr__(self):
        return f"<{self.__class__.__name__} {self.id}>"


class ProjectSubmission(db.Model):
    id = db.Column(db.Integer, db.Identity(start=1), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('mini_project.id'), nullable=False)
    submission_file = db.Column(db.String(255))  # File path
    submission_text = db.Column(db.Text)  # Text submission
    submission_url = db.Column(db.String(500))  # GitHub/other URL
    status = db.Column(db.String(20), default='submitted')  # submitted, reviewed, approved, rejected
    feedback = db.Column(db.Text)
    score = db.Column(db.Float)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='project_submissions', lazy=True)
    reviewer = db.relationship('User', foreign_keys=[reviewed_by], backref='reviewed_submissions', lazy=True)
    def __repr__(self):
        return f"<{self.__class__.__name__} {self.id}>"


 