import os
import subprocess
import sys
import logging

logger = logging.getLogger(__name__)

def apply_update(download_url):
    """
    Apply an update by launching the external updater process.
    This function exits the current process immediately after spawning the updater.
    """
    try:
        # Import paths lazily to avoid circular imports
        from paths import get_updater_path, get_app_root
    except ImportError as e:
        logger.error(f"Failed to import paths module: {e}")
        return False

    updater = get_updater_path()
    app_dir = get_app_root()
    my_pid = os.getpid()

    # Verify updater exists
    if not os.path.exists(updater):
        logger.error(f"Updater not found at: {updater}")
        return False

    logger.info(f"Launching updater: {updater} for {download_url}")
    
    try:
        # Launch updater as detached process
        if sys.platform == "win32":
            creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            subprocess.Popen(
                [updater, download_url, app_dir, "SkillSprintAcademy.exe", str(my_pid)],
                creationflags=creationflags,
                close_fds=True
            )
        else:
            subprocess.Popen(
                [updater, download_url, app_dir, "SkillSprintAcademy.exe", str(my_pid)],
                start_new_session=True,
                close_fds=True
            )
    except Exception as e:
        logger.error(f"Failed to launch updater: {e}")
        return False

    # Exit the current process - updater takes over
    logger.info("Exiting application for update")
    os._exit(0)