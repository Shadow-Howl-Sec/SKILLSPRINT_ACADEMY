"""Unit tests for Phase 1 UI fixes and API endpoint resolutions."""
import unittest
import re
from unittest.mock import patch
from app import app
from extensions import db
from models import User, Topic, AssessmentQuestion

class TestUIFixes(unittest.TestCase):
    """Test suite covering the 6 Phase 1 UI & API bug fixes."""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_update_status_accepts_post(self):
        """Fix 1 & 3: Ensure /api/update/status handles POST without 405 Method Not Allowed."""
        res = self.client.post('/api/update/status', json={'force': False})
        self.assertIn(res.status_code, (200, 404))
        self.assertNotEqual(res.status_code, 405)

    def test_update_status_accepts_get(self):
        """Ensure /api/update/status also handles GET requests."""
        res = self.client.get('/api/update/status')
        self.assertIn(res.status_code, (200, 404))
        self.assertNotEqual(res.status_code, 405)

    def test_apply_update_offline_mode_returns_400(self):
        """Fix 2 & 4: Ensure /settings/apply-update returns HTTP 400 when in OFFLINE_MODE."""
        self.app.config['OFFLINE_MODE'] = True
        res = self.client.post('/settings/apply-update', json={
            'download_url': 'https://example.com/update.zip'
        })
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn('error', data)
        self.assertIn('offline mode', data['error'].lower())

    def test_offline_mode_injected_in_base_cybersec(self):
        """Fix 2: Ensure base_cybersec.html injects window.OFFLINE_MODE before main.js."""
        res = self.client.get('/roadmap')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn('window.OFFLINE_MODE =', html)
        self.assertIn('/static/js/update_checker.js', html)
        self.assertIn('/static/js/main.js', html)
        self.assertNotIn('nonce="None"', html)
        nonce = re.search(r'nonce="([^"]+)" src="/static/js/main.js"', html).group(1)
        self.assertRegex(res.headers['Content-Security-Policy'], rf"'nonce-{re.escape(nonce)}'")

    def test_offline_mode_injected_in_index(self):
        """Fix 5: Ensure index.html includes scripts and window.OFFLINE_MODE runtime injection."""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn('window.OFFLINE_MODE =', html)
        self.assertIn('/static/js/update_checker.js', html)
        self.assertIn('/static/js/main.js', html)

    def test_bootstrap_icons_font_is_served(self):
        """The vendored Bootstrap Icons stylesheet must resolve its relative fonts."""
        res = self.client.get('/static/vendor/bootstrap-icons/fonts/bootstrap-icons.woff2')
        self.assertEqual(res.status_code, 200)

    def test_roadmap_without_plan_starts_onboarding(self):
        """A missing roadmap must not bounce the user back to the home page."""
        with patch('blueprints.roadmap.routes._active_roadmap', return_value=None):
            res = self.client.get('/roadmap')

        self.assertEqual(res.status_code, 302)
        self.assertTrue(res.location.endswith('/roadmap/start'))

    def test_roadmap_start_without_curriculum_has_no_home_loop(self):
        """Missing curriculum data must land on the role-selection page."""
        with patch('blueprints.roadmap.routes._active_roadmap', return_value=None), patch('models.JobRole') as job_role:
            job_role.query.filter_by.return_value.first.return_value = None
            res = self.client.get('/roadmap/start', follow_redirects=False)

        self.assertEqual(res.status_code, 302)
        self.assertTrue(res.location.endswith('/job-roles'))

        role_page = self.client.get('/job-roles')
        self.assertEqual(role_page.status_code, 200)

    def test_dashboard_without_plan_starts_onboarding(self):
        """The dashboard should use the same onboarding entry point."""
        with patch('blueprints.dashboard.routes.Roadmap.query') as roadmap_query:
            roadmap_query.filter_by.return_value.first.return_value = None
            res = self.client.get('/dashboard')

        self.assertEqual(res.status_code, 302)
        self.assertTrue(res.location.endswith('/roadmap/start'))

    def test_update_actions_are_available_in_navigation(self):
        res = self.client.get('/roadmap')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn('data-action="check-update"', html)
        self.assertIn('Download latest release', html)

    def test_quiz_has_client_side_validation_script(self):
        """Fix 6: Ensure checkpoint_quiz.html includes client-side validation script for MCQs."""
        topic = Topic.query.first()
        self.assertIsNotNone(topic)
        res = self.client.get(f'/topic/{topic.id}/quiz')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn('js-question-group', html)
        self.assertIn('js-choice', html)
        self.assertIn('Please answer all questions before submitting', html)
