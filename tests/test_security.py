"""Security unit tests covering CSRF, CSP headers, HMAC validation, and input sanitization."""
import unittest
import hmac
import hashlib
from app import app
from extensions import db
from models import User, Roadmap, JobRole

class TestSecurityAudit(unittest.TestCase):
    """Test suite validating application security controls."""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_csp_header_present(self):
        """Verify Content-Security-Policy header is included in HTML responses."""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('Content-Security-Policy', res.headers)
        csp = res.headers['Content-Security-Policy']
        self.assertIn("script-src", csp)

    def test_apply_update_hmac_verification_in_online_mode(self):
        """Verify HMAC-SHA256 signature verification for apply-update in online mode."""
        self.app.config['OFFLINE_MODE'] = False
        self.app.config['UPDATE_HMAC_SECRET'] = 'secret_key_123'
        
        # Test 1: Missing signature -> 400
        res = self.client.post('/settings/apply-update', json={
            'download_url': 'https://example.com/update.zip'
        })
        self.assertEqual(res.status_code, 400)

        # Test 2: Invalid signature -> 403
        res = self.client.post('/settings/apply-update', json={
            'download_url': 'https://example.com/update.zip',
            'signature': 'invalid_signature_hex'
        })
        self.assertEqual(res.status_code, 403)

        # Test 3: Valid signature -> computes matching HMAC
        url = 'https://example.com/update.zip'
        valid_sig = hmac.new(
            b'secret_key_123',
            url.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # We mock apply_update so the process doesn't exit during test
        from unittest.mock import patch
        with patch('blueprints.settings.routes.apply_update') as mock_apply:
            res = self.client.post('/settings/apply-update', json={
                'download_url': url,
                'signature': valid_sig
            })
            self.assertEqual(res.status_code, 200)
            mock_apply.assert_called_once_with(url)

        # Restore default test mode
        self.app.config['OFFLINE_MODE'] = True

    def test_csrf_protection_on_post_routes(self):
        """Verify CSRF token is required on state-mutating POST endpoints when WTF_CSRF_ENABLED is True."""
        user = User.query.first()
        active = Roadmap.query.filter_by(user_id=user.id, status='active').first()
        if not active:
            role = JobRole.query.first()
            self.client.get(f'/job-roles/{role.id}/start', follow_redirects=True)

        # POST without CSRF token to a protected blueprint should fail with 400 Bad Request
        res = self.client.post('/roadmap/replan', data={'weekly_hours': 15})
        self.assertEqual(res.status_code, 400)

    def test_sql_injection_resilience(self):
        """Verify ORM queries handle special characters safely without SQL injection."""
        sqli_payload = "'; DROP TABLE users; --"
        user = User.query.filter_by(email=sqli_payload).first()
        self.assertIsNone(user)
        # Database table remains intact
        users_count = User.query.count()
        self.assertGreaterEqual(users_count, 1)
