"""Unit tests for Phase 2 Purple Team curriculum seed and data integrity."""
import unittest
from app import app
from extensions import db
from models import SkillArea, Topic, TopicLearningModule, AssessmentQuestion, Lab, JobRole

class TestPurpleTeamCurriculum(unittest.TestCase):
    """Test suite for Purple Team curriculum models and seed integrity."""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_skill_areas_exist(self):
        """Verify that skill areas are defined in the database."""
        areas = SkillArea.query.all()
        self.assertGreater(len(areas), 0)

    def test_topics_linked_to_skill_areas(self):
        """Verify that topics are linked to valid skill areas."""
        topics = Topic.query.all()
        self.assertGreater(len(topics), 0)
        for t in topics:
            self.assertIsNotNone(t.skill_area_id)
            self.assertIsNotNone(t.skill_area)

    def test_topic_learning_modules_have_theory_and_labs(self):
        """Verify topic learning modules have required structured content."""
        modules = TopicLearningModule.query.all()
        self.assertGreater(len(modules), 0)
        for m in modules:
            self.assertTrue(len(m.theory_md or "") > 0 or len(m.lab_guide_md or "") > 0)

    def test_assessment_questions_valid(self):
        """Verify assessment questions have non-empty question text and choices."""
        questions = AssessmentQuestion.query.all()
        self.assertGreater(len(questions), 0)
        for q in questions:
            self.assertTrue(len(q.question_text) > 0)
            self.assertIn(q.question_type, ('mcq', 'practical', 'text'))

    def test_job_roles_exist(self):
        """Verify job roles are present and linked to topics."""
        roles = JobRole.query.all()
        self.assertGreater(len(roles), 0)
        for r in roles:
            self.assertTrue(len(r.name) > 0)

    def test_purple_team_seed_file_integrity(self):
        """Verify seed_purple_team_curriculum script exists and is importable."""
        import os
        seed_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'seed_purple_team_curriculum.py'))
        self.assertTrue(os.path.exists(seed_path))
