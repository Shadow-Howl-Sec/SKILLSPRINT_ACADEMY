from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, FloatField, IntegerField, DateField, DateTimeField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional
from models import User, Course, Coupon
from datetime import datetime

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    college = StringField('College/University', validators=[DataRequired(), Length(max=100)])
    year = SelectField('Year of Study', choices=[
        ('1st Year', '1st Year'),
        ('2nd Year', '2nd Year'),
        ('3rd Year', '3rd Year'),
        ('4th Year', '4th Year'),
        ('Graduate', 'Graduate'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    branch = StringField('Branch/Stream', validators=[DataRequired(), Length(max=50)])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class CourseForm(FlaskForm):
    title = StringField('Course Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('development', 'Development'),
        ('data', 'Data Science'),
        ('security', 'Cybersecurity'),
        ('ai', 'AI & ML')
    ], validators=[DataRequired()])
    difficulty = SelectField('Difficulty', choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced')
    ], validators=[DataRequired()])
    duration_weeks = IntegerField('Duration (Weeks)', validators=[DataRequired()])
    price = FloatField('Price (₹)', validators=[DataRequired()])
    discounted_price = FloatField('Discounted Price (₹)', validators=[Optional()])
    icon_class = StringField('Icon Class (Bootstrap)', validators=[Optional()])
    features = TextAreaField('Features (JSON)', validators=[Optional()])
    roadmap_steps = TextAreaField('Roadmap Steps (JSON)', validators=[Optional()])
    is_active = BooleanField('Active')
    submit = SubmitField('Save Course')

class CouponForm(FlaskForm):
    code = StringField('Coupon Code', validators=[DataRequired(), Length(max=20)])
    discount_type = SelectField('Discount Type', choices=[
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount')
    ], validators=[DataRequired()])
    discount_value = FloatField('Discount Value', validators=[DataRequired()])
    course_id = SelectField('Course (Optional)', coerce=int, validators=[Optional()])
    max_uses = IntegerField('Maximum Uses', validators=[DataRequired()])
    valid_from = DateTimeField('Valid From', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    valid_until = DateTimeField('Valid Until', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Coupon')

    def validate_code(self, code):
        coupon = Coupon.query.filter_by(code=code.data).first()
        if coupon:
            raise ValidationError('Coupon code already exists.')

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    college = StringField('College/University', validators=[DataRequired(), Length(max=100)])
    year = SelectField('Year of Study', choices=[
        ('1st Year', '1st Year'),
        ('2nd Year', '2nd Year'),
        ('3rd Year', '3rd Year'),
        ('4th Year', '4th Year'),
        ('Graduate', 'Graduate'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    branch = StringField('Branch/Stream', validators=[DataRequired(), Length(max=50)])
    is_admin = BooleanField('Admin Access')
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save User')

class PaymentForm(FlaskForm):
    user_id = SelectField('User', coerce=int, validators=[DataRequired()])
    course_id = SelectField('Course', coerce=int, validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    discount_amount = FloatField('Discount Amount', validators=[Optional()])
    final_amount = FloatField('Final Amount', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    ], validators=[DataRequired()])
    submit = SubmitField('Save Payment') 