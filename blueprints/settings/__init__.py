from flask import Blueprint

settings_bp = Blueprint("settings", __name__)

from blueprints.settings import routes  # noqa: F401