import unittest
from app import app
from extensions import db
from models import Topic, TopicLearningModule, AssessmentQuestion, Roadmap, User, JobRole


class TestPurpleTeamTwoPhase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_index_page_loads_with_two_phase_and_logo(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        # Check logo and apple-touch-icon
        self.assertIn(b'rel="icon" type="image/png" href="/static/img/skill_logo.png"', res.data)
        self.assertIn(b'rel="apple-touch-icon" href="/static/img/skill_logo.png"', res.data)
        # Check Phase 1 and Phase 2 branding
        self.assertIn(b'Phase 1: Zero to Job', res.data)
        self.assertIn(b'Phase 2: Purple Team Mastery', res.data)
        # Check Network Administrator emphasis
        self.assertIn(b'Network Administrator', res.data)
        # Verify no job role tracks links in nav
        self.assertNotIn(b'<a href="/job-roles" class="cmd-nav-link">', res.data)

    def test_roadmap_start_route(self):
        user = User.query.first()
        self.assertIsNotNone(user)
        existing_roadmaps = Roadmap.query.filter_by(user_id=user.id).all()
        for r in existing_roadmaps:
            for item in r.items:
                db.session.delete(item)
            db.session.delete(r)
        db.session.commit()

        # Call /roadmap/start
        res = self.client.get('/roadmap/start', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        # Verify roadmap was created
        roadmap = Roadmap.query.filter_by(user_id=user.id).first()
        self.assertIsNotNone(roadmap)
        self.assertGreater(len(roadmap.items), 0)

    def test_every_topic_has_five_components(self):
        topics = Topic.query.all()
        self.assertGreater(len(topics), 50)
        for t in topics:
            m = t.learning_module
            self.assertIsNotNone(m, f"Topic {t.id} '{t.title}' is missing TopicLearningModule")
            # 1. Theory
            self.assertTrue(bool(m.theory_md and len(m.theory_md.strip()) > 50),
                            f"Topic {t.id} '{t.title}' theory is missing or too short")
            # 2. Video Lecture
            self.assertTrue(bool(m.video_url and m.video_url.strip()),
                            f"Topic {t.id} '{t.title}' video_url is missing")
            # 3. Lab Guide
            self.assertTrue(bool(m.lab_guide_md and len(m.lab_guide_md.strip()) > 50),
                            f"Topic {t.id} '{t.title}' lab_guide is missing")
            # 4. Assessment Questions
            q_count = AssessmentQuestion.query.filter_by(topic_id=t.id, is_active=True).count()
            self.assertGreater(q_count, 0, f"Topic {t.id} '{t.title}' has 0 assessment questions")

    def test_topic_detail_page_renders_all_sections(self):
        topic = Topic.query.first()
        self.assertIsNotNone(topic)
        res = self.client.get(f'/topic/{topic.id}')
        self.assertEqual(res.status_code, 200)
        # Check all 5 jump links and sections
        self.assertIn(b'1. Theoretical Foundation', res.data)
        self.assertIn(b'2. Video Lectures', res.data)
        self.assertIn(b'3. Purple Team Practical Execution', res.data)
        self.assertIn(b'4. Real-World Applications', res.data)
        self.assertIn(b'5. Assessment', res.data)
        self.assertIn(b'Watch Video Lecture', res.data)
        self.assertIn(b'Launch Checkpoint Quiz', res.data)

    def test_topic_quiz_page_renders_and_works(self):
        topic = Topic.query.first()
        res = self.client.get(f'/topic/{topic.id}/quiz')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Checkpoint Quiz', res.data)


if __name__ == '__main__':
    unittest.main()
