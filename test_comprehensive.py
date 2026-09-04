"""Comprehensive end-to-end integration and sanity test suite for SkillSprint Academy / ZeroCipher.
"""
import unittest
import json
from unittest.mock import patch
from datetime import date
from app import app
from extensions import db
from models import (
    User, JobRole, SkillArea, Topic, Lab, Roadmap, RoadmapItem,
    PurpleTeamExerciseLog, UserResource, VMConfig
)

class AppComprehensiveTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_01_health_endpoints(self):
        """Test health check endpoints."""
        res = self.client.get('/health')
        self.assertEqual(res.status_code, 200)
        data = res.json
        self.assertEqual(data.get('status'), 'healthy')

        with patch('socket.create_connection', side_effect=OSError('Offline')):
            res_vm = self.client.get('/health/vm')
            self.assertEqual(res_vm.status_code, 200)
            data_vm = res_vm.json
            self.assertIn('status', data_vm)

    def test_02_static_and_base_pages(self):
        """Test home, about, and info pages."""
        for path in ['/', '/offline/about', '/offline/resource-cache', '/offline/lab-setup', '/offline/settings/ai-tutor']:
            res = self.client.get(path)
            self.assertEqual(res.status_code, 200, f"Failed at {path}")

    def test_03_job_roles_flow(self):
        """Test browsing job roles, viewing details, and starting a roadmap."""
        res = self.client.get('/job-roles')
        self.assertEqual(res.status_code, 200)

        role = JobRole.query.first()
        self.assertIsNotNone(role, "At least one JobRole should exist in DB")

        res_detail = self.client.get(f'/job-roles/{role.id}')
        self.assertEqual(res_detail.status_code, 200)

        # Start job role to generate roadmap
        res_start = self.client.get(f'/job-roles/{role.id}/start', follow_redirects=True)
        self.assertEqual(res_start.status_code, 200)

        # Verify active roadmap exists
        user = User.query.first()
        active_roadmap = Roadmap.query.filter_by(user_id=user.id, status='active').first()
        self.assertIsNotNone(active_roadmap, "Active roadmap should have been generated")
        self.assertGreater(len(active_roadmap.items), 0, "Roadmap should contain scheduled items")

    def test_04_roadmap_and_dashboard(self):
        """Test roadmap view, dashboard, calendar, and availability."""
        # Ensure active roadmap exists first
        user = User.query.first()
        active_roadmap = Roadmap.query.filter_by(user_id=user.id, status='active').first()
        if not active_roadmap:
            role = JobRole.query.first()
            self.client.get(f'/job-roles/{role.id}/start', follow_redirects=True)

        res_dash = self.client.get('/dashboard')
        self.assertEqual(res_dash.status_code, 200)

        res_prog = self.client.get('/progress')
        self.assertEqual(res_prog.status_code, 200)

        res_rm = self.client.get('/roadmap')
        self.assertEqual(res_rm.status_code, 200)

        res_cal = self.client.get('/roadmap/calendar')
        self.assertEqual(res_cal.status_code, 200)

        res_avail = self.client.get('/roadmap/availability')
        self.assertEqual(res_avail.status_code, 200)

    def test_05_item_completion(self):
        """Test marking a roadmap item complete and awarding XP."""
        user = User.query.first()
        active_roadmap = Roadmap.query.filter_by(user_id=user.id, status='active').first()
        self.assertIsNotNone(active_roadmap)
        item = RoadmapItem.query.filter_by(roadmap_id=active_roadmap.id, status='pending').first()
        self.assertIsNotNone(item, "Should have an incomplete item")

        initial_xp = user.total_xp
        res_comp = self.client.post(f'/roadmap-item/{item.id}/complete', follow_redirects=True)
        self.assertEqual(res_comp.status_code, 200)

        db.session.refresh(item)
        db.session.refresh(user)
        self.assertEqual(item.status, 'done')
        self.assertGreater(user.total_xp, initial_xp, "User XP should increase after completion")

    def test_06_labs_and_exercises(self):
        """Test browsing labs and lab details with and without VM setup."""
        res_labs = self.client.get('/labs')
        self.assertEqual(res_labs.status_code, 200)

        lab = Lab.query.first()
        self.assertIsNotNone(lab)

        # Without VM config configured, accessing vm_exercise lab redirects to lab-setup
        res_lab_redirect = self.client.get(f'/lab/{lab.id}', follow_redirects=False)
        self.assertEqual(res_lab_redirect.status_code, 302)
        self.assertIn('/offline/lab-setup', res_lab_redirect.location)

        # With mock socket connection and mock VMConfig, lab renders detail_vm_exercise.html
        user = User.query.first()
        vm = VMConfig.query.filter_by(user_id=user.id).first()
        if not vm:
            vm = VMConfig(
                user_id=user.id,
                kali_ip='192.168.56.5',
                goad_dc_ip='192.168.56.10',
                goad_win10_ip='192.168.56.11',
                metasploitable_ip='192.168.56.20',
                dvwa_ip='192.168.56.21',
                wazuh_ip='192.168.56.30',
                is_validated=True
            )
            db.session.add(vm)
            db.session.commit()

        class DummySocket:
            def close(self): pass

        with patch('socket.create_connection', return_value=DummySocket()):
            res_vm_lab = self.client.get(f'/lab/{lab.id}')
            self.assertEqual(res_vm_lab.status_code, 200)
            self.assertIn(b'Purple Team Exercise', res_vm_lab.data)

    def test_07_topic_quiz(self):
        """Test topic quiz GET and submission."""
        topic = Topic.query.first()
        self.assertIsNotNone(topic)

        res_quiz_get = self.client.get(f'/topic/{topic.id}/quiz')
        self.assertEqual(res_quiz_get.status_code, 200)

    def test_08_purple_team_logging(self):
        """Test purple team log views and creating a new exercise log."""
        res_log = self.client.get('/purple-team/log')
        self.assertEqual(res_log.status_code, 200)

        res_cov = self.client.get('/purple-team/coverage')
        self.assertEqual(res_cov.status_code, 200)

        res_exp = self.client.get('/purple-team/export')
        self.assertEqual(res_exp.status_code, 200)

        res_new_get = self.client.get('/purple-team/log/new')
        self.assertEqual(res_new_get.status_code, 200)

        user = User.query.first()
        log_data = {
            'technique_title': 'Pass the Hash Lateral Movement Drill',
            'mitre_id': 'T1550.002',
            'attack_succeeded': 'on',
            'detected': 'on',
            'rule_written': 'on',
            'notes': 'Verified Sysmon Event ID 10 with Mimikatz sekurlsa::pth',
        }
        res_post = self.client.post('/purple-team/log/new', data=log_data, follow_redirects=True)
        self.assertEqual(res_post.status_code, 200)

        created = PurpleTeamExerciseLog.query.filter_by(user_id=user.id, mitre_id='T1550.002').first()
        self.assertIsNotNone(created)
        self.assertEqual(created.technique_title, 'Pass the Hash Lateral Movement Drill')
        self.assertTrue(created.attack_succeeded)
        self.assertTrue(created.detected)

    def test_09_library(self):
        """Test user library view and adding a resource."""
        res_lib = self.client.get('/library')
        self.assertEqual(res_lib.status_code, 200)

        res_add_get = self.client.get('/library/add')
        self.assertEqual(res_add_get.status_code, 200)

        add_data = {
            'url': 'https://attack.mitre.org/techniques/T1550/002/',
            'title': 'MITRE ATT&CK: Pass the Hash',
            'resource_type': 'cheatsheet',
            'estimated_minutes': '25'
        }
        mock_meta = {
            'title': 'MITRE ATT&CK: Pass the Hash',
            'resource_type': 'cheatsheet',
            'thumbnail_url': None
        }
        with patch('blueprints.library.routes.fetch_metadata', return_value=mock_meta):
            res_add_post = self.client.post('/library/add', data=add_data, follow_redirects=True)
            self.assertEqual(res_add_post.status_code, 200)

        user = User.query.first()
        res_entry = UserResource.query.filter_by(user_id=user.id, title='MITRE ATT&CK: Pass the Hash').first()
        self.assertIsNotNone(res_entry)

    def test_10_assistant_api(self):
        """Test AI assistant chat API."""
        res_chat = self.client.post('/api/assistant/chat',
                                    json={'message': 'What is kerberoasting?'},
                                    headers={'Content-Type': 'application/json'})
        self.assertEqual(res_chat.status_code, 200)
        data = res_chat.json
        self.assertIn('reply', data)
        self.assertGreater(len(data['reply']), 0)

    def test_11_roadmap_calendar_and_move(self):
        """Test moving a roadmap item to a new date and time slot."""
        item = RoadmapItem.query.first()
        self.assertIsNotNone(item)
        new_date_str = date.today().isoformat()
        res_move = self.client.post(
            f'/roadmap/item/{item.id}/move',
            data={'new_date': new_date_str, 'time_slot': '14:00-16:30 (Afternoon Block - 2.5h)'},
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        self.assertEqual(res_move.status_code, 200)
        self.assertEqual(res_move.json.get('status'), 'success')

    def test_12_roadmap_replan(self):
        """Test recalculating roadmap."""
        res_replan = self.client.post('/roadmap/replan', follow_redirects=True)
        self.assertEqual(res_replan.status_code, 200)

    def test_13_lab_submit(self):
        """Test submitting purple team lab checklist."""
        lab = Lab.query.filter_by(provider='vm_exercise').first()
        self.assertIsNotNone(lab)

        submission_payload = json.dumps({
            'attack_succeeded': True,
            'detected': True,
            'rule_written': True,
            'notes': 'Verified attack technique execution and created detection rule.'
        })
        user = User.query.first()
        initial_xp = user.total_xp
        res_submit = self.client.post(f'/lab/{lab.id}/submit', data={'proof': submission_payload}, follow_redirects=True)
        self.assertEqual(res_submit.status_code, 200)

        db.session.refresh(user)
        self.assertGreater(user.total_xp, initial_xp)

    def test_14_purple_team_edit_and_delete(self):
        """Test editing and deleting a purple team log."""
        user = User.query.first()
        log = PurpleTeamExerciseLog.query.filter_by(user_id=user.id).first()
        self.assertIsNotNone(log)

        # GET edit form
        res_get_edit = self.client.get(f'/purple-team/log/{log.id}/edit')
        self.assertEqual(res_get_edit.status_code, 200)

        # POST edit
        res_post_edit = self.client.post(f'/purple-team/log/{log.id}/edit', data={
            'technique_title': 'Updated Pass the Hash Title',
            'notes': 'Updated notes',
            'attack_succeeded': 'on'
        }, follow_redirects=True)
        self.assertEqual(res_post_edit.status_code, 200)

        db.session.refresh(log)
        self.assertEqual(log.technique_title, 'Updated Pass the Hash Title')

        # POST delete
        res_del = self.client.post(f'/purple-team/log/{log.id}/delete', follow_redirects=True)
        self.assertEqual(res_del.status_code, 200)

        deleted = PurpleTeamExerciseLog.query.get(log.id)
        self.assertIsNone(deleted)

    def test_15_topic_quiz_evaluation(self):
        """Test submitting topic quiz answers."""
        topic = Topic.query.first()
        self.assertIsNotNone(topic)

        res_quiz_post = self.client.post(f'/topic/{topic.id}/quiz', data={'q_1': '0'}, follow_redirects=True)
        self.assertEqual(res_quiz_post.status_code, 200)

    def test_16_updates_api(self):
        """Test update status and check endpoints."""
        res_status = self.client.get('/api/update/status')
        self.assertEqual(res_status.status_code, 200)

        res_check = self.client.get('/api/update/check')
        self.assertEqual(res_check.status_code, 200)


if __name__ == '__main__':
    unittest.main()
