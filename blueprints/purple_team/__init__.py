"""Purple Team blueprint (Gap 2).

Provides:
  /purple-team/log          — timeline of completed exercises (attack → detect → document)
  /purple-team/log/new      — manual log entry for ad-hoc practice
  /purple-team/coverage     — ATT&CK matrix coverage grid
  /purple-team/export       — Markdown export for portfolio
"""
from flask import Blueprint

purple_team_bp = Blueprint("purple_team", __name__, url_prefix="/purple-team")

from blueprints.purple_team import routes  # noqa: F401,E402