# SkillSprint Academy

SkillSprint Academy is a Flask-based learning platform for course management, user registration, payments, and admin dashboards.

## Project structure

- `app.py` - application entrypoint and main route handlers
- `auth.py` - authentication, registration, password reset, and email workflows
- `admin.py` - admin dashboards and API endpoints
- `models.py` - SQLAlchemy ORM models
- `config.py` - environment-based Flask configuration
- `extensions.py` - Flask extension setup
- `forms.py` - form definitions for registration and login
- `requirements.txt` - Python dependencies
- `static/` - CSS, JavaScript, images
- `templates/` - HTML templates for public pages, auth, admin, and student views

## Setup

1. Create a Python virtual environment:

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with any environment variables you need, for example:

   ```text
   SECRET_KEY=your-secret-key
   DATABASE_URL=sqlite:///skillsprint.db
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USERNAME=your-email@example.com
   MAIL_PASSWORD=your-email-password
   MAIL_DEFAULT_SENDER=your-email@example.com
   RAZORPAY_KEY_ID=rzp_test_xxxxxxxx
   RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxx
   GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
   GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret
   ADMIN_EMAIL=admin@skillsprint.com
   ADMIN_PASSWORD=your_admin_password
   ```

4. Run the application:

   ```powershell
   python app.py
   ```

   The project will initialize the database tables automatically on first startup.

## Notes

- Local development files such as `__pycache__`, generated database files, and temporary instance files are not part of the cleaned project.
- Use the `requirements.txt` file to recreate a fresh virtual environment later.
- The `app.py` entrypoint automatically creates the database schema when started.

## Cleanup performed

- Removed `refactor.py`
- Removed generated `__pycache__` and local database artifacts
- Removed the local `instance/` folder contents and notebook database file

## License

This repository does not include an explicit license file. Add one if you intend to share or publish the project.
