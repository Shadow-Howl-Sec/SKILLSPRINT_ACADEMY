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
    
    # Relationships — existing
    enrollments = db.relationship('Enrollment', backref='user', lazy=True)
    payments = db.relationship('Payment', backref='user', lazy=True)
    # Relationships — CyberSec platform
    skill_profiles = db.relationship('SkillProfile', backref='user', lazy=True)
    roadmaps = db.relationship('Roadmap', backref='user', lazy=True)
    weekly_availability = db.relationship('WeeklyAvailability', backref='user', lazy=True)
    user_resources = db.relationship('UserResource', backref='user', lazy=True)
    streak_record = db.relationship('StreakRecord', backref='user', uselist=False, lazy=True)
    xp_logs = db.relationship('XPLog', backref='user', lazy=True)
    assessment_sessions = db.relationship('AssessmentSession', backref='user', lazy=True)
    chat_messages = db.relationship('ChatMessage', backref='user', lazy=True)

    @property
    def total_xp(self):
        """Compute total XP from XPLog entries."""
        return sum(log.xp_amount for log in self.xp_logs)

    @property
    def current_streak(self):
        """Return current streak from StreakRecord."""
        if self.streak_record:
            return self.streak_record.current_streak
        return 0

    @property
    def onboarding_complete(self):
        """True when user has at least one active roadmap."""
        return any(r.status == 'active' for r in self.roadmaps)
    
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


# =============================================================================
# CYBERSECURITY PLATFORM MODELS
# =============================================================================

class SkillArea(db.Model):
    """Taxonomy of cybersecurity skill areas (e.g. Networking, Linux, Web App Security)."""
    __tablename__ = 'skill_area'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    icon_class = db.Column(db.String(50))          # Bootstrap icon or emoji
    color_hex = db.Column(db.String(7), default='#6366f1')  # UI accent color
    parent_id = db.Column(db.Integer, db.ForeignKey('skill_area.id'), nullable=True)
    order_index = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    topics = db.relationship('Topic', backref='skill_area', lazy=True)
    assessment_questions = db.relationship('AssessmentQuestion', backref='skill_area', lazy=True)
    skill_profiles = db.relationship('SkillProfile', backref='skill_area', lazy=True)
    children = db.relationship('SkillArea', backref=db.backref('parent', remote_side=[id]), lazy=True)

    def __repr__(self):
        return f"<SkillArea {self.slug}>"


class Topic(db.Model):
    """A unit of learning in the curriculum DAG."""
    __tablename__ = 'topic'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text)
    skill_area_id = db.Column(db.Integer, db.ForeignKey('skill_area.id'), nullable=False)
    difficulty = db.Column(db.Integer, default=1)   # 1-5
    estimated_minutes = db.Column(db.Integer, default=60)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    prerequisites = db.relationship(
        'TopicPrerequisite',
        foreign_keys='TopicPrerequisite.topic_id',
        backref='topic', lazy=True
    )
    required_by = db.relationship(
        'TopicPrerequisite',
        foreign_keys='TopicPrerequisite.prerequisite_topic_id',
        backref='prerequisite', lazy=True
    )
    content_items = db.relationship('ContentItem', backref='topic', lazy=True)
    labs = db.relationship('Lab', backref='topic', lazy=True)

    def __repr__(self):
        return f"<Topic {self.slug}>"


class TopicPrerequisite(db.Model):
    """DAG edges: topic_id requires prerequisite_topic_id."""
    __tablename__ = 'topic_prerequisite'
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    prerequisite_topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)

    def __repr__(self):
        return f"<TopicPrerequisite {self.prerequisite_topic_id} -> {self.topic_id}>"


class JobRole(db.Model):
    """A cybersecurity job-role track (SOC Analyst, Pentester, etc.)."""
    __tablename__ = 'job_role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    avg_salary_note = db.Column(db.String(200))       # e.g. "₹6-15 LPA"
    recommended_certs = db.Column(db.Text)             # JSON list of cert names
    icon_url = db.Column(db.String(255))
    icon_emoji = db.Column(db.String(10), default='🛡️')
    color_hex = db.Column(db.String(7), default='#6366f1')
    difficulty_label = db.Column(db.String(30), default='Beginner Friendly')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    role_topics = db.relationship('JobRoleTopic', backref='job_role', lazy=True, order_by='JobRoleTopic.order_index')
    roadmaps = db.relationship('Roadmap', backref='job_role', lazy=True)

    def __repr__(self):
        return f"<JobRole {self.slug}>"


class JobRoleTopic(db.Model):
    """Ordered mapping of Topics to a JobRole — forms the role's curriculum template."""
    __tablename__ = 'job_role_topic'
    id = db.Column(db.Integer, primary_key=True)
    job_role_id = db.Column(db.Integer, db.ForeignKey('job_role.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    order_index = db.Column(db.Integer, default=0)
    is_core = db.Column(db.Boolean, default=True)   # core vs optional/stretch

    # Relationships
    topic = db.relationship('Topic', backref='job_role_mappings', lazy=True)

    def __repr__(self):
        return f"<JobRoleTopic role={self.job_role_id} topic={self.topic_id}>"


class ContentItem(db.Model):
    """A single piece of learning content within a Topic."""
    __tablename__ = 'content_item'
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    # Types: lesson_md | video | pdf | external_link | quiz_checkpoint
    type = db.Column(db.String(30), nullable=False, default='lesson_md')
    title = db.Column(db.String(200), nullable=False)
    body_markdown = db.Column(db.Text)             # for lesson_md type
    url = db.Column(db.String(500))                # for video/pdf/external_link
    thumbnail_url = db.Column(db.String(500))
    estimated_minutes = db.Column(db.Integer, default=15)
    order_index = db.Column(db.Integer, default=0)
    # source: in_house | external_admin | external_user
    source = db.Column(db.String(20), default='in_house')
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ContentItem {self.title[:40]}>"


class Lab(db.Model):
    """A virtual lab exercise linked to a Topic."""
    __tablename__ = 'lab'
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    # Providers: self_hosted | tryhackme | htb | portswigger | overthewire | picoctf | other
    provider = db.Column(db.String(30), nullable=False, default='other')
    url_or_container_ref = db.Column(db.String(500))
    difficulty = db.Column(db.Integer, default=2)   # 1-5
    estimated_minutes = db.Column(db.Integer, default=30)
    # Proof types: flag | screenshot | writeup_url | self_report
    proof_type = db.Column(db.String(20), default='self_report')
    flag_hash = db.Column(db.String(128))          # SHA-256 hash of flag for self-hosted
    xp_reward = db.Column(db.Integer, default=25)
    mitre_techniques = db.Column(db.Text)          # JSON list of MITRE technique IDs
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Lab {self.title[:40]}>"


class AssessmentQuestion(db.Model):
    """Question bank entry for the adaptive skill assessment."""
    __tablename__ = 'assessment_question'
    id = db.Column(db.Integer, primary_key=True)
    skill_area_id = db.Column(db.Integer, db.ForeignKey('skill_area.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    # Types: mcq | short_answer | scenario
    question_type = db.Column(db.String(20), nullable=False, default='mcq')
    options = db.Column(db.Text)                   # JSON list of strings (for MCQ)
    correct_answer = db.Column(db.Text, nullable=False)  # option index (MCQ) or keyword list (short_answer)
    explanation = db.Column(db.Text)               # shown after answering
    difficulty = db.Column(db.Integer, nullable=False, default=3)  # 1-5
    mitre_technique_id = db.Column(db.String(20))  # e.g. T1110
    applicable_roles = db.Column(db.Text)          # JSON list of job_role slugs
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    responses = db.relationship('AssessmentResponse', backref='question', lazy=True)

    def __repr__(self):
        return f"<AssessmentQuestion area={self.skill_area_id} diff={self.difficulty}>"


class AssessmentSession(db.Model):
    """One adaptive assessment attempt by a user."""
    __tablename__ = 'assessment_session'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # track_type: general | job_role
    track_type = db.Column(db.String(20), nullable=False, default='general')
    job_role_id = db.Column(db.Integer, db.ForeignKey('job_role.id'), nullable=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    # status: in_progress | completed | abandoned
    status = db.Column(db.String(20), default='in_progress')
    # Stores computed skill profile as JSON after completion
    result_json = db.Column(db.Text)

    # Relationships
    responses = db.relationship('AssessmentResponse', backref='session', lazy=True)
    job_role = db.relationship('JobRole', backref='assessment_sessions', lazy=True)

    def __repr__(self):
        return f"<AssessmentSession user={self.user_id} status={self.status}>"


class AssessmentResponse(db.Model):
    """One question response within an AssessmentSession."""
    __tablename__ = 'assessment_response'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('assessment_session.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('assessment_question.id'), nullable=False)
    answer_given = db.Column(db.Text)
    is_correct = db.Column(db.Boolean)
    difficulty_at_time = db.Column(db.Integer)     # difficulty level when question was served
    time_taken_seconds = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AssessmentResponse session={self.session_id} correct={self.is_correct}>"


class SkillProfile(db.Model):
    """Latest computed skill score for a user in a specific skill area."""
    __tablename__ = 'skill_profile'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    skill_area_id = db.Column(db.Integer, db.ForeignKey('skill_area.id'), nullable=False)
    score = db.Column(db.Float, default=0.0)       # 0-100
    # confidence: low | medium | high
    confidence = db.Column(db.String(10), default='low')
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'skill_area_id', name='uq_skill_profile_user_area'),
    )

    def __repr__(self):
        return f"<SkillProfile user={self.user_id} area={self.skill_area_id} score={self.score:.0f}>"


class Roadmap(db.Model):
    """A user's personalized learning roadmap."""
    __tablename__ = 'roadmap'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_role_id = db.Column(db.Integer, db.ForeignKey('job_role.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    target_completion_date = db.Column(db.DateTime)
    # status: active | paused | completed
    status = db.Column(db.String(20), default='active')
    version = db.Column(db.Integer, default=1)     # increments on re-plan

    # Relationships
    items = db.relationship('RoadmapItem', backref='roadmap', lazy=True, order_by='RoadmapItem.scheduled_date, RoadmapItem.order_index')

    def __repr__(self):
        return f"<Roadmap user={self.user_id} status={self.status} v{self.version}>"


class RoadmapItem(db.Model):
    """One scheduled item on a user's roadmap (content, lab, quiz, or review)."""
    __tablename__ = 'roadmap_item'
    id = db.Column(db.Integer, primary_key=True)
    roadmap_id = db.Column(db.Integer, db.ForeignKey('roadmap.id'), nullable=False)
    # item_type: content_item | lab | checkpoint_quiz | review | external_resource
    item_type = db.Column(db.String(20), nullable=False)
    content_item_id = db.Column(db.Integer, db.ForeignKey('content_item.id'), nullable=True)
    lab_id = db.Column(db.Integer, db.ForeignKey('lab.id'), nullable=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=True)
    user_resource_id = db.Column(db.Integer, db.ForeignKey('user_resource.id'), nullable=True)
    scheduled_date = db.Column(db.DateTime)
    order_index = db.Column(db.Integer, default=0)
    # status: pending | in_progress | done | skipped
    status = db.Column(db.String(20), default='pending')
    estimated_minutes = db.Column(db.Integer, default=30)
    actual_minutes = db.Column(db.Integer)
    completed_at = db.Column(db.DateTime)

    # Relationships
    content_item = db.relationship('ContentItem', backref='roadmap_items', lazy=True)
    lab = db.relationship('Lab', backref='roadmap_items', lazy=True)
    topic = db.relationship('Topic', backref='roadmap_items', lazy=True)

    def __repr__(self):
        return f"<RoadmapItem type={self.item_type} date={self.scheduled_date} status={self.status}>"


class WeeklyAvailability(db.Model):
    """How many minutes per day a user is available to study."""
    __tablename__ = 'weekly_availability'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Mon … 6=Sun
    available_minutes = db.Column(db.Integer, default=60)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'day_of_week', name='uq_availability_user_day'),
    )

    def __repr__(self):
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        return f"<WeeklyAvailability user={self.user_id} {days[self.day_of_week]}={self.available_minutes}m>"


class UserResource(db.Model):
    """External resource a user has added to their personal library."""
    __tablename__ = 'user_resource'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    # resource_type: video | article | course | pdf | github | other
    resource_type = db.Column(db.String(20), default='other')
    thumbnail_url = db.Column(db.String(500))
    estimated_minutes = db.Column(db.Integer, default=30)
    skill_area_id = db.Column(db.Integer, db.ForeignKey('skill_area.id'), nullable=True)
    notes = db.Column(db.Text)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    # v2: community sharing
    is_shared_to_community = db.Column(db.Boolean, default=False)

    # Relationships
    skill_area = db.relationship('SkillArea', backref='user_resources', lazy=True)

    def __repr__(self):
        return f"<UserResource user={self.user_id} title={self.title[:40]}>"


class XPLog(db.Model):
    """Audit log of all XP earned by a user."""
    __tablename__ = 'xp_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # source_type: roadmap_item | lab | streak_bonus | assessment | badge
    source_type = db.Column(db.String(30), nullable=False)
    source_id = db.Column(db.Integer)              # FK to relevant record
    xp_amount = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<XPLog user={self.user_id} +{self.xp_amount}xp [{self.source_type}]>"


class StreakRecord(db.Model):
    """Per-user streak tracking."""
    __tablename__ = 'streak_record'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    last_active_date = db.Column(db.DateTime)
    freezes_available = db.Column(db.Integer, default=1)  # resets weekly

    def __repr__(self):
        return f"<StreakRecord user={self.user_id} streak={self.current_streak}>"


class ChatMessage(db.Model):
    """AI tutor conversation history."""
    __tablename__ = 'chat_message'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_id = db.Column(db.String(36), nullable=False)   # UUID grouping messages into one chat session
    # role: user | assistant
    role = db.Column(db.String(10), nullable=False)
    content = db.Column(db.Text, nullable=False)
    related_topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    related_topic = db.relationship('Topic', backref='chat_messages', lazy=True)

    def __repr__(self):
        return f"<ChatMessage user={self.user_id} role={self.role}>"