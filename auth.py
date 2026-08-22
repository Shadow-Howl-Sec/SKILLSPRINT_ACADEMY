from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlsplit
from extensions import db, limiter
from models import User, Course, Coupon, Enrollment, Payment, AdminLog
from forms import RegistrationForm, LoginForm, ResetPasswordRequestForm, ResetPasswordForm
from datetime import datetime, timedelta
import json

auth = Blueprint('auth', __name__)


def _offline_mode() -> bool:
    return bool(current_app.config.get('OFFLINE_MODE', False))


def _mail_obj():
    """Return the Flask-Mail instance configured in app.py or None."""
    from flask import current_app
    return current_app.config.get('_MAIL_INSTANCE') or getattr(current_app, '_mail', None)


def send_verification_email(user):
    """Send email verification link — no-op under OFFLINE_MODE (plan §9)."""
    if _offline_mode():
        return
    from app import mail
    if mail is None:
        return
    from flask_mail import Message
    token = user.generate_verification_token()
    msg = Message('Verify Your Email - SkillSprint Academy',
                  recipients=[user.email])
    msg.body = f'''To verify your email, visit the following link:
{url_for('auth.verify_email', token=token, _external=True)}

If you did not make this request, simply ignore this email.
'''
    try:
        mail.send(msg)
    except Exception as e:
        print('Mail send error:', e)


def send_password_reset_email(user):
    """Send password reset email — no-op under OFFLINE_MODE."""
    if _offline_mode():
        return
    from app import mail
    if mail is None:
        return
    from flask_mail import Message
    token = user.generate_reset_token()
    msg = Message('Reset Your Password - SkillSprint Academy',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('auth.reset_password', token=token, _external=True)}

If you did not make this request, simply ignore this email.
'''
    try:
        mail.send(msg)
    except Exception as e:
        print('Mail send error:', e)


@auth.route('/register', methods=['GET', 'POST'])
@limiter.limit("10 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            college=form.college.data,
            year=form.year.data,
            branch=form.branch.data
        )
        user.set_password(form.password.data)

        # In OFFLINE_MODE there is no SMTP — auto-verify the email so the user
        # can log in immediately (plan §9).
        if _offline_mode():
            user.email_verified = True
        else:
            user.generate_verification_token()

        db.session.add(user)
        db.session.commit()

        if _offline_mode():
            flash('Registration successful — you can log in now (offline mode).', 'success')
        else:
            send_verification_email(user)
            flash('Registration successful! Please check your email to verify your account.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'error')
            return redirect(url_for('auth.login'))

        if not user.email_verified:
            flash('Please verify your email before logging in.', 'error')
            return redirect(url_for('auth.login'))

        if not user.is_active:
            flash('Your account has been deactivated. Please contact support.', 'error')
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)

    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@auth.route('/verify_email/<token>')
def verify_email(token):
    user = User.query.filter_by(email_verification_token=token).first()
    if user:
        user.email_verified = True
        user.email_verification_token = None
        db.session.commit()
        flash('Your email has been verified! You can now log in.', 'success')
    else:
        flash('Invalid or expired verification link.', 'error')
    return redirect(url_for('auth.login'))


@auth.route('/reset_password_request', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def reset_password_request():
    """Disabled in OFFLINE_MODE — use `python manage.py reset-password` instead (plan §9)."""
    if _offline_mode():
        flash('Offline mode: password resets are done from the admin panel or '
              'via `python manage.py reset-password <email>`.', 'info')
        return redirect(url_for('auth.login'))

    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for instructions to reset your password.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password_request.html', form=form)


@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if _offline_mode():
        abort_disabled()
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    user = User.query.filter_by(reset_password_token=token).first()
    if not user or user.reset_password_expires < datetime.utcnow():
        flash('Invalid or expired reset link.', 'error')
        return redirect(url_for('auth.login'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.reset_password_token = None
        user.reset_password_expires = None
        db.session.commit()
        flash('Your password has been reset.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form)


def abort_disabled():
    from flask import abort
    abort(404)
