# app/paths.py
import os
import sys

APP_NAME = "SkillSprintAcademy"

def get_data_root():
    """Stable location for the DB/logs — never touched by updates."""
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    else:
        base = os.path.expanduser("~/.local/share")  # Linux/Kali dev use
    path = os.path.join(base, APP_NAME, "data")
    os.makedirs(path, exist_ok=True)
    return path

def get_app_root():
    """Where the current app's code/exe lives — this folder gets replaced on update."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__ + "/.."))

def get_updater_path():
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    else:
        base = os.path.expanduser("~/.local/share")
    return os.path.join(base, APP_NAME, "updater.exe")