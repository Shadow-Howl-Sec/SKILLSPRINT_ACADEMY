import base64
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

def apply_update(download_url, signature_url=None):
    """Download, verify, and stage a release from inside the application."""
    if not _is_trusted_release_url(download_url):
        logger.warning("Rejected update URL outside the trusted release hosts")
        return False

    try:
        from paths import get_app_root
    except ImportError as e:
        logger.error(f"Failed to import paths module: {e}")
        return False

    app_dir = get_app_root()
    signature_url = signature_url or (download_url + ".sig")
    if not _is_trusted_release_url(signature_url):
        logger.warning("Rejected update signature URL outside the trusted release hosts")
        return False
    temp_dir = tempfile.mkdtemp(prefix="skillsprint-update-")
    package_path = os.path.join(temp_dir, "release.zip")
    signature_path = os.path.join(temp_dir, "release.sig")
    extract_dir = os.path.join(temp_dir, "release")
    try:
        _download(download_url, package_path)
        _download(signature_url, signature_path)
        _verify_package(package_path, signature_path)
        _safe_extract(package_path, extract_dir)
        staged_dir = os.path.join(tempfile.gettempdir(), "skillsprint-staged-update")
        if os.path.exists(staged_dir):
            shutil.rmtree(staged_dir)
        shutil.copytree(extract_dir, staged_dir)
        _schedule_install(staged_dir, app_dir)
    except Exception as e:
        logger.error(f"Failed to apply update: {e}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return False
    return True


def _is_trusted_release_url(value):
    parsed = urlparse(value or "")
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    if parsed.hostname == "github.com":
        return "/Shadow-Howl-Sec/SKILLSPRINT_ACADEMY/releases/" in parsed.path
    return parsed.hostname == "objects.githubusercontent.com"


def _download(url, destination):
    response = requests.get(url, stream=True, timeout=120)
    response.raise_for_status()
    with open(destination, "wb") as output:
        for chunk in response.iter_content(1024 * 1024):
            if chunk:
                output.write(chunk)


def _verify_package(package_path, signature_path):
    public_key = os.environ.get("UPDATER_PUBLIC_KEY", "")
    if not public_key:
        if os.environ.get("UPDATER_ALLOW_UNSIGNED", "false").lower() == "true":
            return True
        raise ValueError("UPDATER_PUBLIC_KEY is not configured")
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    with open(signature_path, "rb") as signature_file, open(package_path, "rb") as package_file:
        Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key)).verify(
            signature_file.read(), package_file.read()
        )
    return True


def _safe_extract(package_path, destination):
    os.makedirs(destination, exist_ok=True)
    destination_abs = os.path.abspath(destination)
    with zipfile.ZipFile(package_path) as archive:
        for member in archive.infolist():
            target = os.path.abspath(os.path.join(destination, member.filename))
            if os.path.commonpath((destination_abs, target)) != destination_abs:
                raise ValueError("update contains an unsafe path")
        archive.extractall(destination)


def _schedule_install(staged_dir, app_dir):
    executable = os.path.join(app_dir, "SkillSprintAcademy.exe")
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        _install_now(staged_dir, app_dir)
        return
    script = os.path.join(tempfile.gettempdir(), "skillsprint-install-update.cmd")
    with open(script, "w", encoding="ascii") as command_file:
        command_file.write(
            f'@echo off\r\ntimeout /t 2 /nobreak >nul\r\n'
            f'xcopy /E /I /Y "{staged_dir}\\*" "{app_dir}\\" >nul\r\n'
            f'start "" "{executable}"\r\ndel "%~f0"\r\n'
        )
    subprocess.Popen(["cmd.exe", "/c", script], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    os._exit(0)


def _install_now(staged_dir, app_dir):
    backup = app_dir + ".previous"
    if os.path.exists(backup):
        shutil.rmtree(backup, ignore_errors=True)
    os.rename(app_dir, backup)
    try:
        shutil.copytree(staged_dir, app_dir)
    except Exception:
        shutil.rmtree(app_dir, ignore_errors=True)
        os.rename(backup, app_dir)
        raise
    shutil.rmtree(backup, ignore_errors=True)