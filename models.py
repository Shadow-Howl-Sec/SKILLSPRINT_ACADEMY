from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

# Import VMConfig for type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from models import VMConfig

# Encryption for sensitive VM config fields
try:
    from cryptography.fernet import Fernet
    _FERNET_KEY = os.environ.get('VM_CONFIG_KEY') or Fernet.generate_key()
    _cipher = Fernet(_FERNET_KEY)
except Exception:
    _cipher = None

def _encrypt(val: str | None) -> bytes | None:
    """Encrypt a string value."""
    if val is None or _cipher is None:
        return None
    return _cipher.encrypt(val.encode())

def _decrypt(val: bytes | None) -> str | None:
    """Decrypt a bytes value."""
    if val is None or _cipher is None:
        return None
    return _cipher.decrypt(val).decode()

class User(db.Model):
    id = db.Column(db.Integer, db.Identity(start=1), primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email_verified = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # VM Configuration (stored per user for multi-VM setups)
    vm_config = db.relationship('VMConfig', backref='user', uselist=False, lazy=True, cascade='all, delete-orphan')
    
    # Relationships — Purple Team platform
    skill_profiles = db.relationship('SkillProfile', backref='user', lazy=True)
    roadmaps = db.relationship('Roadmap', backref='user', lazy=True)
    weekly_availability = db.relationship('WeeklyAvailability', backref='user', lazy=True)
    user_resources = db.relationship('UserResource', backref='user', lazy=True)
    streak_record = db.relationship('StreakRecord', backref='user', uselist=False, lazy=True)
    xp_logs = db.relationship('XPLog', backref='user', lazy=True)
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

    def is_authenticated(self):
        return True

    def is_active(self):
        return self.is_active

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.id}>"





class MiniProject(db.Model):
    id = db.Column(db.Integer, db.Identity(start=1), primary_key=True)
    # course_id nullable since capstone projects (plan §3, Tier 4) are tied
    # to a JobRole, not a legacy Course row.
    # Legacy FK to 'course' table removed - table doesn't exist in this build
    course_id = db.Column(db.Integer, nullable=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    project_brief = db.Column(db.Text)  # Detailed project requirements
    deliverables = db.Column(db.Text)  # JSON string of expected deliverables
    difficulty_level = db.Column(db.String(20))  # easy, medium, hard
    estimated_hours = db.Column(db.Integer)
    # Capstone grading strategy (plan §3): "flag_submission" | "ioc_checklist"
    # | "self_grade_checklist".  When non-null, this is a Tier-4 capstone.
    grading_method = db.Column(db.String(30), nullable=True)
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
    # Gap 3 optional: Curriculum week assignment
    week_id = db.Column(db.Integer, db.ForeignKey('curriculum_week.id'), nullable=True)

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


# =============================================================================
# CURRICULUM WEEKS (Optional - Gap 3 polish)
# =============================================================================

class CurriculumWeek(db.Model):
    """A week in the structured curriculum (e.g., 12-week program).
    
    Allows the dashboard to show "Week 7 of 12: Detecting AD Attacks" 
    instead of just a generic progress percentage.
    """
    __tablename__ = 'curriculum_week'
    id = db.Column(db.Integer, primary_key=True)
    week_number = db.Column(db.Integer, nullable=False)  # 1-12, or 0 for ongoing-mastery
    title = db.Column(db.String(200), nullable=False)
    phase = db.Column(db.String(20), nullable=False)  # 'month1' | 'month2' | 'month3' | 'ongoing'
    goal_description = db.Column(db.Text, nullable=False)
    order_index = db.Column(db.Integer, default=0)

    # Relationships
    topics = db.relationship('Topic', backref='curriculum_week', lazy=True)

    def __repr__(self):
        return f"<CurriculumWeek {self.week_number}: {self.title}>"


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
    # Tier 4 capstone project (plan §3, §11 Phase B4) — nullable so existing
    # rows don't break; points at a MiniProject row carrying the role's final
    # graded project (mock OSCP, IR tabletop, etc.).
    capstone_project_id = db.Column(db.Integer, db.ForeignKey('mini_project.id'),
                                    nullable=True)
    # Gap 3: Purple Team as default track
    is_default = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    role_topics = db.relationship('JobRoleTopic', backref='job_role', lazy=True,
                                  order_by='JobRoleTopic.order_index')
    roadmaps = db.relationship('Roadmap', backref='job_role', lazy=True)
    capstone_project = db.relationship('MiniProject', foreign_keys=[capstone_project_id])

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
    #        | interactive_exercise  (offline, plan §4)
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

    # Interactive exercise spec (plan §4) — JSON blob describing the exercise
    # (kind ∈ {code_py, code_js, pcap_challenge, cipher_lab, regex_lab,
    # quiz_interactive, binary_inspector}, plus kind-specific fields like unit
    # tests, expected answers, bundled-file pointers). MVP stores this as JSON
    # text so no migration is needed; a future column split is fine too.
    exercise_spec = db.Column(db.Text)

    def __repr__(self):
        return f"<ContentItem {self.title[:40]}>"


class TopicHint(db.Model):
    """Authored hints for the rules-based AI-tutor fallback (plan §7.2).

    Every Topic can have several `TopicHint` rows keyed to trigger keywords
    and a 1-3 hint level so the tutor escalates without ever leaking a flag.
    """
    __tablename__ = 'topic_hint'
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    trigger_keywords = db.Column(db.Text)    # JSON list of lowercase keywords
    hint_text = db.Column(db.Text, nullable=False)  # Markdown
    hint_level = db.Column(db.Integer, default=1)  # 1..3 (progressive)
    is_active = db.Column(db.Boolean, default=True)

    topic = db.relationship('Topic', backref='hints', lazy=True)

    def __repr__(self):
        return f"<TopicHint topic={self.topic_id} lvl={self.hint_level}>"


class CachedResource(db.Model):
    """One-time-synced offline copy of an external page/PDF (plan §6.2).

    Populated by `scripts/sync_resource_cache.ps1`. The link_metadata_service
    reads from this table instead of fetching live URLs when OFFLINE_MODE.
    """
    __tablename__ = 'cached_resource'
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(500), nullable=False, unique=True)
    local_path = db.Column(db.String(500), nullable=False)  # relative under instance/resource_cache
    title = db.Column(db.String(300))
    resource_type = db.Column(db.String(20))   # article | pdf | video | github | course
    fetched_at = db.Column(db.DateTime, default=datetime.utcnow)
    content_hash = db.Column(db.String(64))    # sha-256 of cached body

    def __repr__(self):
        return f"<CachedResource {self.original_url[:60]}>"


class LocalInbox(db.Model):
    """In-app replacement for the SMTP contact form (plan §9)."""
    __tablename__ = 'local_inbox'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    subject = db.Column(db.String(200))
    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='local_inbox', lazy=True)

    def __repr__(self):
        return f"<LocalInbox id={self.id} subject={self.subject}>"


class Lab(db.Model):
    """A virtual lab exercise linked to a Topic."""
    __tablename__ = 'lab'
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    # Providers: self_hosted | tryhackme | htb | portswigger | overthewire
    #           | picoctf | self_hosted_offline | other | vm_exercise
    provider = db.Column(db.String(30), nullable=False, default='other')
    url_or_container_ref = db.Column(db.String(500))
    difficulty = db.Column(db.Integer, default=2)   # 1-5
    estimated_minutes = db.Column(db.Integer, default=30)
    # Proof types: flag | screenshot | writeup_url | self_report | self_report_checklist
    proof_type = db.Column(db.String(30), default='self_report')
    flag_hash = db.Column(db.String(128))          # SHA-256 hash of flag for self-hosted
    xp_reward = db.Column(db.Integer, default=25)
    mitre_techniques = db.Column(db.Text)          # JSON list of MITRE technique IDs
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # --- NEW: fields for vm_exercise provider (Gap 1) ---
    attacker_vm = db.Column(db.String(100), nullable=True)       # e.g. "Kali"
    target_vm = db.Column(db.String(100), nullable=True)         # e.g. "GOAD-DC01", "Metasploitable2"
    detection_vm = db.Column(db.String(100), nullable=True)      # e.g. "Wazuh Manager"
    instructions_md = db.Column(db.Text, nullable=True)          # step-by-step attack instructions
    detection_task_md = db.Column(db.Text, nullable=True)        # what to look for/build in Wazuh
    mitre_technique = db.Column(db.String(20), nullable=True)    # single MITRE technique for this lab
    # --- end new fields ---

    @property
    def is_offline_available(self) -> bool:
        """True when the lab can be run without external network (plan §5.4)."""
        return self.provider in ("self_hosted_offline", "vm_exercise")

    @property
    def is_vm_exercise(self) -> bool:
        return self.provider == "vm_exercise"

    def __repr__(self):
        return f"<Lab {self.title[:40]}>"


class VMConfig(db.Model):
    """User's VM configuration for offline purple team labs.
    
    Stores connection details for attacker, target, and detection VMs.
    All connections are local/host-only network — no internet required.
    Sensitive credentials are encrypted at rest using Fernet (AES-256-GCM).
    """
    __tablename__ = 'vm_config'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    
    # Attacker VM (Kali Linux)
    kali_ip = db.Column(db.String(45), nullable=True)  # IPv4 or IPv6
    kali_ssh_user = db.Column(db.String(50), default='kali')
    kali_ssh_key_path = db.Column(db.String(500), nullable=True)
    kali_ssh_port = db.Column(db.Integer, default=22)
    
    # Target VMs
    goad_dc_ip = db.Column(db.String(45), nullable=True)      # GOAD Domain Controller
    goad_dc_winrm_user = db.Column(db.String(50), default='Administrator')
    goad_dc_winrm_pass_enc = db.Column(db.LargeBinary, nullable=True)
    goad_dc_winrm_port = db.Column(db.Integer, default=5985)
    
    goad_win10_ip = db.Column(db.String(45), nullable=True)   # GOAD Windows 10
    goad_win10_winrm_user = db.Column(db.String(50), default='Administrator')
    goad_win10_winrm_pass_enc = db.Column(db.LargeBinary, nullable=True)
    goad_win10_winrm_port = db.Column(db.Integer, default=5985)
    
    metasploitable_ip = db.Column(db.String(45), nullable=True)
    metasploitable_ssh_user = db.Column(db.String(50), default='msfadmin')
    metasploitable_ssh_pass_enc = db.Column(db.LargeBinary, nullable=True)
    metasploitable_ssh_port = db.Column(db.Integer, default=22)
    
    dvwa_ip = db.Column(db.String(45), nullable=True)
    dvwa_port = db.Column(db.Integer, default=80)
    
    # Detection VM (Wazuh Manager)
    wazuh_ip = db.Column(db.String(45), nullable=True)
    wazuh_api_url = db.Column(db.String(500), nullable=True)  # e.g., https://192.168.56.30:55000
    wazuh_api_user = db.Column(db.String(50), default='wazuh')
    wazuh_api_pass_enc = db.Column(db.LargeBinary, nullable=True)
    
    # Network configuration
    network_cidr = db.Column(db.String(20), default='192.168.56.0/24')  # Host-only network
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_validated = db.Column(db.Boolean, default=False)  # Set true after connection test passes
    
    def __repr__(self):
        return f"<VMConfig user={self.user_id} kali={self.kali_ip}>"
    
    # Property accessors for encrypted fields
    @property
    def goad_dc_winrm_pass(self) -> str | None:
        return _decrypt(self.goad_dc_winrm_pass_enc)
    
    @goad_dc_winrm_pass.setter
    def goad_dc_winrm_pass(self, val: str | None):
        self.goad_dc_winrm_pass_enc = _encrypt(val)
    
    @property
    def goad_win10_winrm_pass(self) -> str | None:
        return _decrypt(self.goad_win10_winrm_pass_enc)
    
    @goad_win10_winrm_pass.setter
    def goad_win10_winrm_pass(self, val: str | None):
        self.goad_win10_winrm_pass_enc = _encrypt(val)
    
    @property
    def metasploitable_ssh_pass(self) -> str | None:
        return _decrypt(self.metasploitable_ssh_pass_enc)
    
    @metasploitable_ssh_pass.setter
    def metasploitable_ssh_pass(self, val: str | None):
        self.metasploitable_ssh_pass_enc = _encrypt(val)
    
    @property
    def wazuh_api_pass(self) -> str | None:
        return _decrypt(self.wazuh_api_pass_enc)
    
    @wazuh_api_pass.setter
    def wazuh_api_pass(self, val: str | None):
        self.wazuh_api_pass_enc = _encrypt(val)
    
    def get_vm_dict(self) -> dict:
        """Return VM config as dictionary for lab use (with decrypted secrets)."""
        return {
            'kali': {'ip': self.kali_ip, 'ssh_user': self.kali_ssh_user, 'ssh_key': self.kali_ssh_key_path, 'ssh_port': self.kali_ssh_port},
            'goad_dc': {'ip': self.goad_dc_ip, 'winrm_user': self.goad_dc_winrm_user, 'winrm_pass': self.goad_dc_winrm_pass, 'winrm_port': self.goad_dc_winrm_port},
            'goad_win10': {'ip': self.goad_win10_ip, 'winrm_user': self.goad_win10_winrm_user, 'winrm_pass': self.goad_win10_winrm_pass, 'winrm_port': self.goad_win10_winrm_port},
            'metasploitable': {'ip': self.metasploitable_ip, 'ssh_user': self.metasploitable_ssh_user, 'ssh_pass': self.metasploitable_ssh_pass, 'ssh_port': self.metasploitable_ssh_port},
            'dvwa': {'ip': self.dvwa_ip, 'port': self.dvwa_port},
            'wazuh': {'ip': self.wazuh_ip, 'api_url': self.wazuh_api_url, 'api_user': self.wazuh_api_user, 'api_pass': self.wazuh_api_pass},
            'network_cidr': self.network_cidr,
        }


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
    roadmap_id = db.Column(db.Integer, db.ForeignKey('roadmap.id'), nullable=False, index=True)
    # item_type: content_item | lab | checkpoint_quiz | review | external_resource
    item_type = db.Column(db.String(20), nullable=False)
    content_item_id = db.Column(db.Integer, db.ForeignKey('content_item.id'), nullable=True)
    lab_id = db.Column(db.Integer, db.ForeignKey('lab.id'), nullable=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=True)
    user_resource_id = db.Column(db.Integer, db.ForeignKey('user_resource.id'), nullable=True)
    scheduled_date = db.Column(db.DateTime, index=True)
    time_slot = db.Column(db.String(100), nullable=True)  # e.g. "09:00-11:00 (Block 1)"
    order_index = db.Column(db.Integer, default=0)
    # status: pending | in_progress | done | skipped
    status = db.Column(db.String(20), default='pending', index=True)
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
    available_minutes = db.Column(db.Integer, default=120)
    time_blocks = db.Column(db.Text, nullable=True)  # JSON list of block dicts e.g. [{"name":"Block 1","start":"09:00","end":"11:00","duration":120}]

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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    # source_type: roadmap_item | lab | streak_bonus | badge | purple_team_exercise
    source_type = db.Column(db.String(30), nullable=False)
    source_id = db.Column(db.Integer)              # FK to relevant record
    xp_amount = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

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


class AssessmentQuestion(db.Model):
    """Checkpoint quiz questions tied to topics and skill areas."""
    __tablename__ = 'assessment_question'
    id = db.Column(db.Integer, primary_key=True)
    skill_area_id = db.Column(db.Integer, db.ForeignKey('skill_area.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=True)
    question_text = db.Column(db.Text, nullable=False)
    # Types: mcq | true_false | short_answer | interactive_exercise
    question_type = db.Column(db.String(20), default='mcq')
    options = db.Column(db.Text)  # JSON list for MCQ
    correct_answer = db.Column(db.Text, nullable=False)  # JSON or string
    explanation = db.Column(db.Text)
    difficulty = db.Column(db.Integer, default=1)  # 1-5
    applicable_roles = db.Column(db.Text)  # JSON list of role slugs
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    skill_area = db.relationship('SkillArea', backref='assessment_questions', lazy=True)
    topic = db.relationship('Topic', backref='checkpoint_questions', lazy=True)

    def __repr__(self):
        return f"<AssessmentQuestion {self.id}: {self.question_text[:50]}>"


class ChatMessage(db.Model):
    """AI tutor conversation history."""
    __tablename__ = 'chat_message'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    session_id = db.Column(db.String(36), nullable=False, index=True)   # UUID grouping messages into one chat session
    # role: user | assistant
    role = db.Column(db.String(10), nullable=False)
    content = db.Column(db.Text, nullable=False)
    related_topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Relationships
    related_topic = db.relationship('Topic', backref='chat_messages', lazy=True)

    def __repr__(self):
        return f"<ChatMessage user={self.user_id} role={self.role}>"


# =============================================================================
# PURPLE TEAM EXERCISE LOG & COVERAGE (Gap 2)
# =============================================================================

class PurpleTeamExerciseLog(db.Model):
    """Log of a completed purple-team exercise (attack → detect → document).
    
    Auto-created when a vm_exercise lab is completed, or added manually
    for ad-hoc practice (e.g., Atomic Red Team tests run outside curriculum).
    """
    __tablename__ = 'purple_team_exercise_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    lab_id = db.Column(db.Integer, db.ForeignKey('lab.id'), nullable=True)
    technique_title = db.Column(db.String(200), nullable=False)
    mitre_id = db.Column(db.String(20), nullable=True, index=True)
    date_completed = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    attack_succeeded = db.Column(db.Boolean, default=False)
    detected = db.Column(db.Boolean, default=False)
    rule_written = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text, nullable=True)          # your own write-up
    writeup_path = db.Column(db.String(300), nullable=True)  # link to a local file if you keep longer notes elsewhere

    # Relationships
    user = db.relationship('User', backref='purple_team_logs', lazy=True)
    lab = db.relationship('Lab', backref='purple_team_logs', lazy=True)

    def __repr__(self):
        return f"<PurpleTeamExerciseLog user={self.user_id} technique={self.technique_title}>"


class AttackCoverage(db.Model):
    """Tracks which MITRE ATT&CK techniques you've attacked/detected/written rules for.
    
    This forms your skill-coverage map and portfolio visual.
    """
    __tablename__ = 'attack_coverage'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mitre_tactic = db.Column(db.String(100), nullable=False)
    mitre_technique_id = db.Column(db.String(20), nullable=False)
    first_attacked_date = db.Column(db.DateTime, nullable=True)
    first_detected_date = db.Column(db.DateTime, nullable=True)
    detection_rule_written = db.Column(db.Boolean, default=False)
    last_reviewed_date = db.Column(db.DateTime, nullable=True)

    # Relationships
    user = db.relationship('User', backref='attack_coverage', lazy=True)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'mitre_technique_id', name='uq_attack_coverage_user_technique'),
    )

    def __repr__(self):
        return f"<AttackCoverage user={self.user_id} {self.mitre_tactic}:{self.mitre_technique_id}>"
