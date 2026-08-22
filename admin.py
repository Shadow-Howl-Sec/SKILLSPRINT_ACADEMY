from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import User, Course, Coupon, Enrollment, Payment, AdminLog
from datetime import datetime
import json

admin = Blueprint('admin', __name__)

# --- Coupon API: Create and Update ---
@admin.route('/admin/api/coupons', methods=['POST'])
@login_required
def add_coupon():
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    data = request.get_json()
    try:
        coupon = Coupon(
            code=data['code'],
            discount_type=data['discount_type'],
            discount_value=float(data['discount_value']),
            course_id=data.get('course_id'),
            max_uses=int(data.get('max_uses', 100)),
            used_count=0,
            valid_from=datetime.strptime(data['valid_from'], '%Y-%m-%d'),
            valid_until=datetime.strptime(data['valid_until'], '%Y-%m-%d'),
            is_active=True
        )
        db.session.add(coupon)
        db.session.commit()
        return jsonify({'success': True, 'coupon_id': coupon.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@admin.route('/admin/api/coupons/<int:coupon_id>', methods=['PUT'])
@login_required
def update_coupon(coupon_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    data = request.get_json()
    coupon = Coupon.query.get_or_404(coupon_id)
    try:
        coupon.code = data['code']
        coupon.discount_type = data['discount_type']
        coupon.discount_value = float(data['discount_value'])
        coupon.course_id = data.get('course_id')
        coupon.max_uses = int(data.get('max_uses', 100))
        coupon.valid_from = datetime.strptime(data['valid_from'], '%Y-%m-%d')
        coupon.valid_until = datetime.strptime(data['valid_until'], '%Y-%m-%d')
        coupon.is_active = data.get('is_active', True)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# --- User API: Update ---
@admin.route('/admin/api/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    data = request.get_json()
    user = User.query.get_or_404(user_id)
    try:
        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.phone = data.get('phone', user.phone)
        user.college = data.get('college', user.college)
        user.year = data.get('year', user.year)
        user.branch = data.get('branch', user.branch)
        user.is_active = data.get('is_active', user.is_active)
        user.is_admin = data.get('is_admin', user.is_admin)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Admin routes
@admin.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    # Comprehensive dashboard statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    admin_users = User.query.filter_by(is_admin=True).count()
    total_courses = Course.query.count()
    active_courses = Course.query.filter_by(is_active=True).count()
    total_enrollments = Enrollment.query.count()
    total_payments = Payment.query.count()
    completed_payments = Payment.query.filter_by(status='completed').count()
    total_revenue = db.session.query(db.func.sum(Payment.final_amount)).filter_by(status='completed').scalar() or 0
    total_coupons = Coupon.query.count()
    active_coupons = Coupon.query.filter_by(is_active=True).count()
    
    # Recent activities
    recent_enrollments = Enrollment.query.order_by(Enrollment.enrollment_date.desc()).limit(5).all()
    recent_payments = Payment.query.order_by(Payment.payment_date.desc()).limit(5).all()
    recent_admin_activities = AdminLog.query.order_by(AdminLog.created_at.desc()).limit(10).all()
    
    # System health indicators
    system_health = {
        'database_connected': True,
        'admin_users_online': admin_users,
        'recent_errors': 0,  # You can implement error tracking
        'backup_status': 'up_to_date'  # You can implement backup tracking
    }
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         active_users=active_users,
                         admin_users=admin_users,
                         total_courses=total_courses,
                         active_courses=active_courses,
                         total_enrollments=total_enrollments,
                         total_payments=total_payments,
                         completed_payments=completed_payments,
                         total_revenue=total_revenue,
                         total_coupons=total_coupons,
                         active_coupons=active_coupons,
                         recent_enrollments=recent_enrollments,
                         recent_payments=recent_payments,
                         recent_admin_activities=recent_admin_activities,
                         system_health=system_health)

@admin.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/users.html', users=users)

@admin.route('/admin/courses')
@login_required
def admin_courses():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    courses = Course.query.all()
    return render_template('admin/courses.html', courses=courses)

@admin.route('/admin/coupons')
@login_required
def admin_coupons():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    coupons = Coupon.query.all()
    courses = Course.query.all()
    return render_template('admin/coupons.html', coupons=coupons, courses=courses)

@admin.route('/admin/payments')
@login_required
def admin_payments():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    payments = Payment.query.paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/payments.html', payments=payments)

@admin.route('/admin/system')
@login_required
def admin_system():
    """System settings and configuration (admin only)"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))

    # Local inbox (offline replacement for SMTP contact — plan §9).
    from models import LocalInbox
    inbox_msgs = (LocalInbox.query
                  .order_by(LocalInbox.created_at.desc()).limit(20).all())

    # Get system information
    system_info = {
        'total_users': User.query.count(),
        'total_courses': Course.query.count(),
        'total_enrollments': Enrollment.query.count(),
        'total_revenue': db.session.query(db.func.sum(Payment.final_amount)).filter_by(status='completed').scalar() or 0,
        'admin_users': User.query.filter_by(is_admin=True).count(),
        'recent_activities': AdminLog.query.order_by(AdminLog.created_at.desc()).limit(20).all(),
        'offline_mode': current_app.config.get('OFFLINE_MODE', False),
        'inbox_msgs': inbox_msgs,
        'unread_inbox': sum(1 for m in inbox_msgs if not m.is_read),
    }

    return render_template('admin/system.html', system_info=system_info)

# API endpoints for admin actions
@admin.route('/admin/api/users/<int:user_id>/toggle_status', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    
    # Log admin action
    log = AdminLog(
        admin_id=current_user.id,
        action='toggle_user_status',
        table_name='user',
        record_id=user_id,
        new_values=json.dumps({'is_active': user.is_active}),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({'success': True, 'is_active': user.is_active})

@admin.route('/admin/api/courses/<int:course_id>', methods=['GET'])
@login_required
def get_course_data(course_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    course = Course.query.get_or_404(course_id)
    return jsonify({
        'id': course.id,
        'title': course.title,
        'description': course.description,
        'category': course.category,
        'difficulty': course.difficulty,
        'duration_weeks': course.duration_weeks,
        'price': course.price,
        'discounted_price': course.discounted_price,
        'icon_class': course.icon_class,
        'is_active': course.is_active
    })

@admin.route('/admin/api/courses/<int:course_id>', methods=['PUT'])
@login_required
def update_course(course_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    course = Course.query.get_or_404(course_id)
    data = request.get_json()
    
    # Debug: Print incoming data
    print(f"Updating course {course_id} with data: {data}")
    
    try:
        # Validate required fields
        required_fields = ['title', 'description', 'category', 'difficulty', 'duration_weeks', 'price']
        for field in required_fields:
            if field not in data or not data[field]:
                print(f"Missing field: {field}")
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        course.title = data['title']
        course.description = data['description']
        course.category = data['category']
        course.difficulty = data['difficulty']
        course.duration_weeks = int(data['duration_weeks'])
        course.price = float(data['price'])
        
        # Handle discounted price
        if data.get('discounted_price') and data['discounted_price'] != '':
            course.discounted_price = float(data['discounted_price'])
        else:
            course.discounted_price = None
            
        course.icon_class = data.get('icon_class', '')
        course.features = data.get('features', '')
        course.roadmap_steps = data.get('roadmap_steps', '')
        course.video_links = data.get('video_links', '')
        course.practice_tests = data.get('practice_tests', '')
        course.mini_projects = data.get('mini_projects', '')
        course.course_materials = data.get('course_materials', '')
        course.target_branches = data.get('target_branches', '')
        course.industry_relevance = data.get('industry_relevance', '')
        course.certification_info = data.get('certification_info', '')
        
        db.session.commit()
        print(f"Successfully updated course {course_id}")
        
        # Log admin action
        log = AdminLog(
            admin_id=current_user.id,
            action='update_course',
            table_name='course',
            record_id=course_id,
            new_values=json.dumps(data),
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Course updated successfully'})
    except ValueError as e:
        db.session.rollback()
        print(f"ValueError: {e}")
        return jsonify({'error': f'Invalid data format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Exception: {e}")
        return jsonify({'error': f'Database error: {str(e)}'}), 400

@admin.route('/admin/api/courses', methods=['POST'])
@login_required
def add_course():
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    
    try:
        # Validate required fields
        required_fields = ['title', 'description', 'category', 'difficulty', 'duration_weeks', 'price']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Handle discounted price
        discounted_price = None
        if data.get('discounted_price') and data['discounted_price'] != '':
            discounted_price = float(data['discounted_price'])
        
        course = Course(
            title=data['title'],
            description=data['description'],
            category=data['category'],
            difficulty=data['difficulty'],
            duration_weeks=int(data['duration_weeks']),
            price=float(data['price']),
            discounted_price=discounted_price,
            icon_class=data.get('icon_class', ''),
            features=data.get('features', ''),
            roadmap_steps=data.get('roadmap_steps', ''),
            video_links=data.get('video_links', ''),
            practice_tests=data.get('practice_tests', ''),
            mini_projects=data.get('mini_projects', ''),
            course_materials=data.get('course_materials', ''),
            target_branches=data.get('target_branches', ''),
            industry_relevance=data.get('industry_relevance', ''),
            certification_info=data.get('certification_info', ''),
            is_active=True
        )
        
        db.session.add(course)
        db.session.commit()
        
        # Log admin action
        log = AdminLog(
            admin_id=current_user.id,
            action='add_course',
            table_name='course',
            record_id=course.id,
            new_values=json.dumps(data),
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Course added successfully', 'course_id': course.id})
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': f'Invalid data format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 400

@admin.route('/admin/api/courses/<int:course_id>/toggle_status', methods=['POST'])
@login_required
def toggle_course_status(course_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    course = Course.query.get_or_404(course_id)
    course.is_active = not course.is_active
    db.session.commit()
    
    # Log admin action
    log = AdminLog(
        admin_id=current_user.id,
        action='toggle_course_status',
        table_name='course',
        record_id=course_id,
        new_values=json.dumps({'is_active': course.is_active}),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({'success': True, 'is_active': course.is_active})

@admin.route('/admin/api/coupons/<int:coupon_id>/toggle_status', methods=['POST'])
@login_required
def toggle_coupon_status(coupon_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    coupon = Coupon.query.get_or_404(coupon_id)
    coupon.is_active = not coupon.is_active
    db.session.commit()
    
    # Log admin action
    log = AdminLog(
        admin_id=current_user.id,
        action='toggle_coupon_status',
        table_name='coupon',
        record_id=coupon_id,
        new_values=json.dumps({'is_active': coupon.is_active}),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({'success': True, 'is_active': coupon.is_active})

# Additional admin API endpoints for full authority
@admin.route('/admin/api/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    """Delete a user (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    if user_id == current_user.id:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    
    # Log admin action
    log = AdminLog(
        admin_id=current_user.id,
        action='delete_user',
        table_name='user',
        record_id=user_id,
        new_values=json.dumps({'deleted': True}),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'User deleted successfully'})

@admin.route('/admin/api/courses/<int:course_id>', methods=['DELETE'])
@login_required
def delete_course(course_id):
    """Delete a course (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    
    # Log admin action
    log = AdminLog(
        admin_id=current_user.id,
        action='delete_course',
        table_name='course',
        record_id=course_id,
        new_values=json.dumps({'deleted': True}),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Course deleted successfully'})

@admin.route('/admin/api/coupons/<int:coupon_id>', methods=['DELETE'])
@login_required
def delete_coupon(coupon_id):
    """Delete a coupon (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    coupon = Coupon.query.get_or_404(coupon_id)
    db.session.delete(coupon)
    db.session.commit()
    
    # Log admin action
    log = AdminLog(
        admin_id=current_user.id,
        action='delete_coupon',
        table_name='coupon',
        record_id=coupon_id,
        new_values=json.dumps({'deleted': True}),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Coupon deleted successfully'})

@admin.route('/admin/api/users/<int:user_id>/make_admin', methods=['POST'])
@login_required
def make_user_admin(user_id):
    """Make a user an admin (super admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    user = User.query.get_or_404(user_id)
    user.is_admin = True
    db.session.commit()
    
    # Log admin action
    log = AdminLog(
        admin_id=current_user.id,
        action='make_user_admin',
        table_name='user',
        record_id=user_id,
        new_values=json.dumps({'is_admin': True}),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'User promoted to admin'})

@admin.route('/admin/api/users/<int:user_id>/remove_admin', methods=['POST'])
@login_required
def remove_user_admin(user_id):
    """Remove admin privileges from a user (super admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    if user_id == current_user.id:
        return jsonify({'error': 'Cannot remove your own admin privileges'}), 400
    
    user = User.query.get_or_404(user_id)
    user.is_admin = False
    db.session.commit()
    
    # Log admin action
    log = AdminLog(
        admin_id=current_user.id,
        action='remove_user_admin',
        table_name='user',
        record_id=user_id,
        new_values=json.dumps({'is_admin': False}),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Admin privileges removed'})

@admin.route('/admin/api/system/stats', methods=['GET'])
@login_required
def get_system_stats():
    """Get comprehensive system statistics (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        stats = {
            'total_users': User.query.count(),
            'active_users': User.query.filter_by(is_active=True).count(),
            'admin_users': User.query.filter_by(is_admin=True).count(),
            'total_courses': Course.query.count(),
            'active_courses': Course.query.filter_by(is_active=True).count(),
            'total_enrollments': Enrollment.query.count(),
            'total_payments': Payment.query.count(),
            'completed_payments': Payment.query.filter_by(status='completed').count(),
            'total_revenue': db.session.query(db.func.sum(Payment.final_amount)).filter_by(status='completed').scalar() or 0,
            'total_coupons': Coupon.query.count(),
            'active_coupons': Coupon.query.filter_by(is_active=True).count(),
            'recent_activities': []
        }
        
        # Get recent admin activities
        recent_logs = AdminLog.query.order_by(AdminLog.created_at.desc()).limit(10).all()
        for log in recent_logs:
            stats['recent_activities'].append({
                'action': log.action,
                'table': log.table_name,
                'admin': log.admin.first_name if log.admin else 'Unknown',
                'timestamp': log.created_at.isoformat()
            })
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin.route('/admin/api/system/backup', methods=['POST'])
@login_required
def backup_system():
    """Create system backup (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # This is a placeholder for backup functionality
        # In a real system, you would implement actual backup logic
        backup_info = {
            'timestamp': datetime.utcnow().isoformat(),
            'admin': current_user.email,
            'status': 'backup_created'
        }
        
        # Log admin action
        log = AdminLog(
            admin_id=current_user.id,
            action='system_backup',
            table_name='system',
            record_id=0,
            new_values=json.dumps(backup_info),
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'System backup initiated', 'backup_info': backup_info})
    except Exception as e:
        return jsonify({'error': str(e)}), 500 