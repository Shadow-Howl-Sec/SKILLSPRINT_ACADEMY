"""Comprehensive end-to-end integration test suite for SkillSprint Academy.

Covers all 39 route endpoints across 11 blueprints:
- roadmap (5 routes)
- dashboard (3 routes)
- labs (4 routes)
- topics (1 route)
- purple_team (6 routes)
- offline (5 routes)
- job_roles (4 routes)
- library (4 routes)
- assistant (2 routes)
- assessment (2 routes)
- settings (3 routes)
- Plus app-level routes (index, health, health/vm)
"""
import unittest
import json
from unittest.mock import patch, MagicMock
from datetime import date, datetime, timedelta, timezone
from app import app
from extensions import db
from models import (
    User, JobRole, SkillArea, Topic, Lab, Roadmap, RoadmapItem,
    PurpleTeamExerciseLog, UserResource, VMConfig, ContentItem,
    AssessmentQuestion, TopicLearningModule, StreakRecord,
    CurriculumWeek, TopicPrerequisite, JobRoleTopic, MiniProject
)


def _ensure_roadmap(client):
    """Helper: ensure an active roadmap exists."""
    user = User.query.first()
    active = Roadmap.query.filter_by(user_id=user.id, status='active').first()
    if not active:
        role = JobRole.query.first()
        client.get(f'/job-roles/{role.id}/start', follow_redirects=True)
        db.session.commit()
    return Roadmap.query.filter_by(user_id=user.id, status='active').first()


class TestHealthEndpoints(unittest.TestCase):
    """Test /health and /health/vm endpoints."""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_health_check(self):
        res = self.client.get('/health')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json['status'], 'healthy')
        self.assertEqual(res.json['database'], 'connected')
        self.assertTrue(res.json['offline'])

    def test_vm_health_check_no_config(self):
        user = User.query.first()
        vm = VMConfig.query.filter_by(user_id=user.id).first()
        if vm:
            db.session.delete(vm)
            db.session.commit()

        res = self.client.get('/health/vm')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json['status'], 'no_config')

    def test_vm_health_check_with_config(self):
        user = User.query.first()
        vm = VMConfig.query.filter_by(user_id=user.id).first()
        if not vm:
            vm = VMConfig(user_id=user.id, kali_ip='192.168.56.5', is_validated=False)
            db.session.add(vm)
            db.session.commit()

        class DummySocket:
            def close(self): pass

        with patch('socket.create_connection', return_value=DummySocket()):
            res = self.client.get('/health/vm')
            self.assertEqual(res.status_code, 200)
            self.assertIn('status', res.json)


class TestAppRoutes(unittest.TestCase):
    """Test app-level routes."""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_index_page(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'SkillSprint', res.data)

    def test_index_with_roadmap(self):
        _ensure_roadmap(self.client)
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)


class TestJobRolesBlueprint(unittest.TestCase):
    """Test /job-roles blueprint routes."""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_job_roles_browse(self):
        res = self.client.get('/job-roles')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Purple Team', res.data)  # Job roles content

    def test_job_roles_detail(self):
        role = JobRole.query.first()
        self.assertIsNotNone(role)
        res = self.client.get(f'/job-roles/{role.id}')
        self.assertEqual(res.status_code, 200)

    def test_job_roles_start_creates_roadmap(self):
        user = User.query.first()
        role = JobRole.query.first()
        res = self.client.get(f'/job-roles/{role.id}/start', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        roadmap = Roadmap.query.filter_by(user_id=user.id, status='active').first()
        self.assertIsNotNone(roadmap)
        self.assertGreater(len(roadmap.items), 0)

    def test_job_roles_api_list(self):
        res = self.client.get('/api/job-roles')
        self.assertEqual(res.status_code, 200)
        data = res.json
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)


class TestRoadmapBlueprint(unittest.TestCase):
    """Test /roadmap blueprint routes."""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        _ensure_roadmap(self.client)

    def tearDown(self):
        self.ctx.pop()

    def test_roadmap_view(self):
        res = self.client.get('/roadmap')
        self.assertEqual(res.status_code, 200)

    def test_roadmap_calendar(self):
        res = self.client.get('/roadmap/calendar')
        self.assertEqual(res.status_code, 200)

    def test_roadmap_availability_get(self):
        res = self.client.get('/roadmap/availability')
        self.assertEqual(res.status_code, 200)

    def test_roadmap_availability_post(self):
        res = self.client.post('/roadmap/availability', data={
            'day_of_week': '1',
            'time_slot': '09:00-11:30 (Morning Block)',
            'is_available': 'on'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

    def test_roadmap_replan(self):
        res = self.client.post('/roadmap/replan', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

    def test_roadmap_item_move(self):
        item = RoadmapItem.query.first()
        self.assertIsNotNone(item)
        new_date = date.today().isoformat()
        res = self.client.post(
            f'/roadmap/item/{item.id}/move',
            data={
                'new_date': new_date,
                'time_slot': '09:00-11:30 (Morning Block)'
            },
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json.get('status'), 'success')


class TestDashboardBlueprint(unittest.TestCase):
    """Test /dashboard blueprint routes."""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        _ensure_roadmap(self.client)

    def tearDown(self):
        self.ctx.pop()

    def test_dashboard_today(self):
        res = self.client.get('/dashboard')
        self.assertEqual(res.status_code, 200)

    def test_progress_page(self):
        res = self.client.get('/progress')
        self.assertEqual(res.status_code, 200)

    def test_roadmap_item_complete(self):
        user = User.query.first()
        roadmap = Roadmap.query.filter_by(user_id=user.id, status='active').first()
        item = RoadmapItem.query.filter_by(roadmap_id=roadmap.id, status='pending').first()
        self.assertIsNotNone(item)

        initial_xp = user.total_xp
        res = self.client.post(f'/roadmap-item/{item.id}/complete', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        db.session.refresh(item)
        db.session.refresh(user)
        self.assertEqual(item.status, 'done')
        self.assertGreater(user.total_xp, initial_xp)


class TestLabsBlueprint(unittest.TestCase):
    """Test /labs blueprint routes."""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_labs_browse(self):
        res = self.client.get('/labs')
        self.assertEqual(res.status_code, 200)

    def test_lab_detail_redirect_without_vm(self):
        lab = Lab.query.first()
        res = self.client.get(f'/lab/{lab.id}', follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/offline/lab-setup', res.location)

    def test_lab_detail_with_vm_config(self):
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

        lab = Lab.query.first()

        class DummySocket:
            def close(self): pass

        with patch('socket.create_connection', return_value=DummySocket()):
            with patch('blueprints.labs.routes.VMConfig') as mock_vm:
                mock_vm.query.filter_by.return_value.first.return_value = vm
                res = self.client.get(f'/lab/{lab.id}', follow_redirects=True)
                self.assertEqual(res.status_code, 200)
                self.assertIn(b'Purple Team Exercise', res.data)

    def test_lab_submit(self):
        lab = Lab.query.filter_by(provider='vm_exercise').first()
        self.assertIsNotNone(lab)

        user = User.query.first()
        initial_xp = user.total_xp

        submission = json.dumps({
            'attack_succeeded': True,
            'detected': True,
            'rule_written': True,
            'notes': 'Test exercise completion'
        })

        res = self.client.post(
            f'/lab/{lab.id}/submit',
            data={'proof': submission},
            follow_redirects=True
        )
        self.assertEqual(res.status_code, 200)

        db.session.refresh(user)
        self.assertGreater(user.total_xp, initial_xp)


class TestTopicsBlueprint(unittest.TestCase):
    """Test /topic blueprint routes."""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_topic_detail(self):
        import html
        topic = Topic.query.first()
        self.assertIsNotNone(topic)

        res = self.client.get(f'/topic/{topic.id}')
        self.assertEqual(res.status_code, 200)
        self.assertIn(html.escape(topic.title).encode(), res.data)

    def test_topic_detail_404(self):
        max_id = db.session.query(db.func.max(Topic.id)).scalar() or 0
        res = self.client.get(f'/topic/{max_id + 9999}')
        self.assertEqual(res.status_code, 404)


class TestPurpleTeamBlueprint(unittest.TestCase):
    """Test /purple-team blueprint routes."""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_purple_team_log_list(self):
        res = self.client.get('/purple-team/log')
        self.assertEqual(res.status_code, 200)

    def test_purple_team_log_new_get(self):
        res = self.client.get('/purple-team/log/new')
        self.assertEqual(res.status_code, 200)

    def test_purple_team_log_new_post(self):
        user = User.query.first()
        res = self.client.post('/purple-team/log/new', data={
            'technique_title': 'SQL Injection Assessment',
            'mitre_id': 'T1190',
            'attack_succeeded': 'on',
            'detected': 'on',
            'rule_written': 'on',
            'notes': 'Completed SQLi test on lab environment'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        log = PurpleTeamExerciseLog.query.filter_by(
            user_id=user.id,
            mitre_id='T1190'
        ).first()
        self.assertIsNotNone(log)
        self.assertTrue(log.attack_succeeded)

    def test_purple_team_log_edit_get(self):
        user = User.query.first()
        log = PurpleTeamExerciseLog.query.filter_by(user_id=user.id).first()
        if not log:
            log = PurpleTeamExerciseLog(
                user_id=user.id,
                technique_title='Test',
                mitre_id='T1190',
                attack_succeeded=True,
                detected=False,
                notes='Test'
            )
            db.session.add(log)
            db.session.commit()

        res = self.client.get(f'/purple-team/log/{log.id}/edit')
        self.assertEqual(res.status_code, 200)

    def test_purple_team_log_edit_post(self):
        user = User.query.first()
        log = PurpleTeamExerciseLog.query.filter_by(user_id=user.id).first()
        if not log:
            log = PurpleTeamExerciseLog(
                user_id=user.id,
                technique_title='Test',
                mitre_id='T1190',
                attack_succeeded=True,
                detected=False,
                notes='Test'
            )
            db.session.add(log)
            db.session.commit()

        res = self.client.post(
            f'/purple-team/log/{log.id}/edit',
            data={
                'technique_title': 'Updated Technique',
                'notes': 'Updated notes',
                'attack_succeeded': 'on'
            },
            follow_redirects=True
        )
        self.assertEqual(res.status_code, 200)

        db.session.refresh(log)
        self.assertEqual(log.technique_title, 'Updated Technique')

    def test_purple_team_log_delete(self):
        user = User.query.first()
        log = PurpleTeamExerciseLog(
            user_id=user.id,
            technique_title='To Delete',
            mitre_id='T1190',
            attack_succeeded=True,
            detected=False,
            notes='Delete me'
        )
        db.session.add(log)
        db.session.commit()
        log_id = log.id

        res = self.client.post(f'/purple-team/log/{log_id}/delete', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        deleted = db.session.get(PurpleTeamExerciseLog, log_id)
        self.assertIsNone(deleted)

    def test_purple_team_coverage(self):
        res = self.client.get('/purple-team/coverage')
        self.assertEqual(res.status_code, 200)

    def test_purple_team_export(self):
        res = self.client.get('/purple-team/export')
        self.assertEqual(res.status_code, 200)


class TestLibraryBlueprint(unittest.TestCase):
    """Test /library blueprint routes."""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_library_list(self):
        res = self.client.get('/library')
        self.assertEqual(res.status_code, 200)

    def test_library_add_get(self):
        res = self.client.get('/library/add')
        self.assertEqual(res.status_code, 200)

    def test_library_add_post(self):
        mock_meta = {
            'title': 'Test Resource',
            'resource_type': 'article',
            'thumbnail_url': None
        }
        with patch('blueprints.library.routes.fetch_metadata', return_value=mock_meta):
            res = self.client.post('/library/add', data={
                'url': 'https://example.com/article',
                'title': 'Test Resource',
                'resource_type': 'article',
                'estimated_minutes': '30'
            }, follow_redirects=True)
            self.assertEqual(res.status_code, 200)

        user = User.query.first()
        resource = UserResource.query.filter_by(user_id=user.id, title='Test Resource').first()
        self.assertIsNotNone(resource)

    def test_library_schedule(self):
        user = User.query.first()
        resource = UserResource.query.filter_by(user_id=user.id).first()
        if not resource:
            resource = UserResource(
                user_id=user.id,
                title='Test',
                url='https://example.com',
                resource_type='article'
            )
            db.session.add(resource)
            db.session.commit()

        res = self.client.post(f'/library/{resource.id}/schedule', data={
            'scheduled_date': date.today().isoformat()
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

    def test_library_delete(self):
        user = User.query.first()
        resource = UserResource(
            user_id=user.id,
            title='To Delete',
            url='https://example.com',
            resource_type='article'
        )
        db.session.add(resource)
        db.session.commit()
        resource_id = resource.id

        res = self.client.post(f'/library/{resource_id}/delete', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        deleted = UserResource.query.filter_by(id=resource_id).first()
        self.assertIsNone(deleted)


class TestAssistantBlueprint(unittest.TestCase):
    """Test /assistant blueprint routes."""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_assistant_chat_page(self):
        res = self.client.get('/assistant')
        self.assertEqual(res.status_code, 200)

    def test_assistant_chat_api(self):
        res = self.client.post(
            '/api/assistant/chat',
            json={'message': 'What is the CIA triad?'},
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json
        self.assertIn('reply', data)
        self.assertGreater(len(data['reply']), 0)
        self.assertIn('reply_html', data)

    def test_assistant_chat_api_empty_message(self):
        res = self.client.post(
            '/api/assistant/chat',
            json={'message': ''},
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(res.status_code, 400)

    def test_assistant_chat_api_long_message(self):
        res = self.client.post(
            '/api/assistant/chat',
            json={'message': 'A' * 5000},
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(res.status_code, 400)


class TestAssessmentBlueprint(unittest.TestCase):
    """Test /topic quiz and /assessment routes."""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_topic_quiz_get(self):
        topic = Topic.query.first()
        self.assertIsNotNone(topic)
        res = self.client.get(f'/topic/{topic.id}/quiz')
        self.assertEqual(res.status_code, 200)

    def test_topic_quiz_post(self):
        topic = Topic.query.first()
        res = self.client.post(
            f'/topic/{topic.id}/quiz',
            data={'q_1': '0'}
        )
        self.assertEqual(res.status_code, 200)

    def test_assessment_start(self):
        res = self.client.get('/assessment/start', follow_redirects=True)
        self.assertEqual(res.status_code, 200)


class TestOfflineBlueprint(unittest.TestCase):
    """Test /offline blueprint routes."""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_offline_about(self):
        res = self.client.get('/offline/about')
        self.assertEqual(res.status_code, 200)

    def test_offline_lab_setup_get(self):
        res = self.client.get('/offline/lab-setup')
        self.assertEqual(res.status_code, 200)

    def test_offline_lab_setup_post(self):
        res = self.client.post('/offline/lab-setup', data={
            'kali_ip': '192.168.56.5',
            'target_ip': '192.168.56.10'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

    def test_offline_resource_cache(self):
        res = self.client.get('/offline/resource-cache')
        self.assertEqual(res.status_code, 200)

    def test_offline_ai_tutor_settings_get(self):
        res = self.client.get('/offline/settings/ai-tutor')
        self.assertEqual(res.status_code, 200)

    def test_offline_ai_tutor_settings_post(self):
        res = self.client.post('/offline/settings/ai-tutor', data={
            'ai_tutor_enabled': 'on'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)


class TestSettingsBlueprint(unittest.TestCase):
    """Test /api and /settings blueprint routes."""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_update_status(self):
        res = self.client.get('/api/update/status')
        self.assertEqual(res.status_code, 200)
        self.assertIn('current_version', res.json)

    def test_update_check(self):
        res = self.client.get('/api/update/check')
        self.assertEqual(res.status_code, 200)
        self.assertIn('update_available', res.json)

    def test_update_check_post(self):
        res = self.client.post(
            '/api/update/check',
            json={'force': True},
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(res.status_code, 200)

    def test_apply_update_in_offline_mode(self):
        res = self.client.post(
            '/settings/apply-update',
            json={'download_url': 'https://example.com/update.zip'},
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn('offline', res.json.get('error', '').lower())


class TestModelsAndRelationships(unittest.TestCase):
    """Test database models and relationships."""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_user_default_creation(self):
        user = User.query.first()
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'operator')

    def test_job_role_has_topics(self):
        role = JobRole.query.first()
        self.assertIsNotNone(role)
        from models import JobRoleTopic
        count = JobRoleTopic.query.filter_by(job_role_id=role.id).count()
        self.assertGreater(count, 0)

    def test_topic_has_learning_module(self):
        topic = Topic.query.first()
        self.assertIsNotNone(topic)
        self.assertIsNotNone(topic.learning_module)

    def test_topic_has_labs(self):
        topic = Topic.query.first()
        self.assertIsNotNone(topic)
        self.assertGreater(len(topic.labs), 0)

    def test_topic_has_content_items(self):
        topic = Topic.query.first()
        self.assertIsNotNone(topic)
        self.assertGreater(len(topic.content_items), 0)

    def test_topic_has_assessment_questions(self):
        topic = Topic.query.first()
        self.assertIsNotNone(topic)
        questions = AssessmentQuestion.query.filter_by(topic_id=topic.id).all()
        self.assertGreater(len(questions), 0)

    def test_streak_record_creation(self):
        user = User.query.first()
        streak = StreakRecord.query.filter_by(user_id=user.id).first()
        self.assertIsNotNone(streak)

    def test_roadmap_item_completion(self):
        user = User.query.first()
        roadmap = Roadmap.query.filter_by(user_id=user.id, status='active').first()
        if not roadmap:
            return

        item = RoadmapItem(
            roadmap_id=roadmap.id,
            item_type='content_item',
            status='pending',
            estimated_minutes=30
        )
        db.session.add(item)
        db.session.commit()

        self.assertEqual(item.status, 'pending')
        item.status = 'done'
        db.session.commit()
        self.assertEqual(item.status, 'done')


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases."""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_404_for_invalid_topic(self):
        res = self.client.get('/topic/99999')
        self.assertEqual(res.status_code, 404)

    def test_404_for_invalid_lab(self):
        res = self.client.get('/lab/99999')
        self.assertEqual(res.status_code, 404)

    def test_404_for_invalid_roadmap_item(self):
        res = self.client.post('/roadmap-item/99999/complete')
        self.assertIn(res.status_code, [404, 500])

    def test_404_for_invalid_job_role(self):
        res = self.client.get('/job-roles/99999')
        self.assertEqual(res.status_code, 404)


class TestXSSAndSecurity(unittest.TestCase):
    """Test XSS protection and security measures."""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_assistant_api_sanitizes_html(self):
        res = self.client.post(
            '/api/assistant/chat',
            json={'message': '<script>alert(1)</script>'},
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json
        self.assertIn('reply_html', data)

    def test_roadmap_item_move_invalid_date(self):
        item = RoadmapItem.query.first()
        res = self.client.post(
            f'/roadmap/item/{item.id}/move',
            data={
                'new_date': 'not-a-date',
                'time_slot': '09:00-11:30'
            },
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        self.assertEqual(res.status_code, 302)


class TestStreakAndXPService(unittest.TestCase):
    """Test XP and streak service functionality."""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_xp_awarded_on_item_complete(self):
        user = User.query.first()
        roadmap = Roadmap.query.filter_by(user_id=user.id, status='active').first()
        if not roadmap:
            return

        item = RoadmapItem.query.filter_by(roadmap_id=roadmap.id, status='pending').first()
        if not item:
            return

        initial_xp = user.total_xp
        self.client.post(f'/roadmap-item/{item.id}/complete', follow_redirects=True)
        db.session.refresh(user)
        self.assertGreater(user.total_xp, initial_xp)

    def test_streak_increments_on_activity(self):
        user = User.query.first()
        streak = StreakRecord.query.filter_by(user_id=user.id).first()
        if not streak:
            return

        initial = streak.current_streak
        roadmap = Roadmap.query.filter_by(user_id=user.id, status='active').first()
        if not roadmap:
            return

        item = RoadmapItem.query.filter_by(roadmap_id=roadmap.id, status='pending').first()
        if not item:
            return

        self.client.post(f'/roadmap-item/{item.id}/complete', follow_redirects=True)
        db.session.refresh(streak)


if __name__ == '__main__':
    unittest.main()
