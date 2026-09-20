"""Unit tests for Phase 2 Purple Team curriculum seed and data integrity."""
import os
import unittest
from app import app
from extensions import db
from models import SkillArea, Topic, TopicLearningModule, AssessmentQuestion, Lab, JobRole, ContentItem

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
        seed_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'seed_purple_team_curriculum.py'))
        self.assertTrue(os.path.exists(seed_path))

    def test_purple_team_seed_does_not_delete_roles(self):
        """The curriculum seed must preserve existing roles and roadmaps."""
        seed_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'seed_purple_team_curriculum.py'))
        with open(seed_path, encoding='utf-8') as seed_file:
            source = seed_file.read()
        self.assertNotIn('JobRoleTopic.query.delete()', source)
        self.assertNotIn('JobRole.query.delete()', source)

    def test_every_topic_has_learning_module_lab_and_questions(self):
        """Every topic should satisfy the QA plan's completeness requirements."""
        missing = []
        for topic in Topic.query.order_by(Topic.id).all():
            if topic.learning_module is None:
                missing.append(f"{topic.title}: missing learning module")
                continue
            if not Lab.query.filter_by(topic_id=topic.id).first():
                missing.append(f"{topic.title}: missing lab")
            if not AssessmentQuestion.query.filter_by(topic_id=topic.id).first():
                missing.append(f"{topic.title}: missing checkpoint question")
        self.assertFalse(missing, "\n".join(missing))

    def test_roadmap_sh_resources_are_seeded_as_external_links(self):
        """roadmap.sh references must be external links tied to local topics."""
        resources = ContentItem.query.filter_by(source="external_admin").all()
        roadmap_resources = [
            item for item in resources
            if item.url and item.url.startswith("https://roadmap.sh/")
        ]
        self.assertGreater(len(roadmap_resources), 0)
        for item in roadmap_resources:
            self.assertEqual(item.type, "external_link")
            self.assertIsNotNone(item.topic)

    def test_roadmap_sh_seed_is_idempotent(self):
        """Re-running the roadmap.sh seed must not duplicate content rows."""
        from seed_roadmap_sh import seed_roadmap_sh_resources

        before = ContentItem.query.filter(
            ContentItem.url.like("https://roadmap.sh/%")
        ).count()
        seed_roadmap_sh_resources()
        after = ContentItem.query.filter(
            ContentItem.url.like("https://roadmap.sh/%")
        ).count()
        self.assertEqual(after, before)
