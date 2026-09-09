import os
import json
import requests
import logging

# Update these for your actual repository
GITHUB_REPO = os.environ.get("UPDATE_GITHUB_REPO", "Shadow-Howl-Sec/SKILLSPRINT_ACADEMY")
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases"

logger = logging.getLogger(__name__)

# Default local version if no VERSION file
DEFAULT_VERSION = "1.0.0"
VERSION_FILE = "VERSION"


def get_local_version(base_path):
    """Read local version from VERSION file."""
    version_file = os.path.join(base_path, VERSION_FILE)
    try:
        with open(version_file) as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.warning(f"VERSION file not found at {version_file}, using default {DEFAULT_VERSION}")
        return DEFAULT_VERSION
    except Exception as e:
        logger.error(f"Error reading VERSION file: {e}")
        return DEFAULT_VERSION


def _version_tuple(v):
    """Turn '1.2.10' into (1, 2, 10) for correct numeric comparison."""
    try:
        return tuple(int(part) for part in v.split("."))
    except (ValueError, AttributeError):
        return (0, 0, 0)


def check_for_update(base_path, timeout=5):
    """
    Returns a dict describing update status. Never raises — if offline
    or GitHub is unreachable, returns update_available=None so the UI
    can just silently skip the banner instead of erroring.
    """
    local_version = get_local_version(base_path)
    
    # In offline mode, don't attempt network requests
    if os.environ.get("OFFLINE_MODE", "true").lower() in ("true", "1", "yes", "on"):
        logger.debug("Offline mode enabled, skipping update check")
        return {"update_available": None, "current_version": local_version}

    try:
        headers = {"Accept": "application/vnd.github.v3+json"}
        resp = requests.get(GITHUB_API_URL, timeout=timeout, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        
        latest_tag = data.get("tag_name", "").lstrip("v")
        if not latest_tag:
            logger.warning("No tag_name in GitHub release response")
            return {"update_available": False, "current_version": local_version}

        download_url = data.get("html_url")  # fallback: link to the release page
        for asset in data.get("assets", []):
            if asset["name"].endswith(".zip"):
                download_url = asset["browser_download_url"]
                break

        if _version_tuple(latest_tag) > _version_tuple(local_version):
            logger.info(f"Update available: {local_version} -> {latest_tag}")
            return {
                "update_available": True,
                "current_version": local_version,
                "latest_version": latest_tag,
                "download_url": download_url,
                "release_notes": data.get("body", ""),
                "release_url": data.get("html_url", GITHUB_RELEASES_URL),
                "published_at": data.get("published_at"),
            }
        
        logger.debug(f"No update available (current: {local_version}, latest: {latest_tag})")
        return {"update_available": False, "current_version": local_version}

    except requests.Timeout:
        logger.warning("Update check timed out")
        return {"update_available": None, "current_version": local_version, "error": "timeout"}
    except requests.ConnectionError:
        logger.warning("Update check failed - connection error (offline?)")
        return {"update_available": None, "current_version": local_version, "error": "connection"}
    except requests.RequestException as e:
        logger.warning(f"Update check request failed: {e}")
        return {"update_available": None, "current_version": local_version, "error": str(e)}
    except (KeyError, ValueError) as e:
        logger.error(f"Update check parsing error: {e}")
        return {"update_available": None, "current_version": local_version, "error": "parse_error"}
    except Exception as e:
        logger.error(f"Unexpected update check error: {e}")
        return {"update_available": None, "current_version": local_version, "error": "unknown"}