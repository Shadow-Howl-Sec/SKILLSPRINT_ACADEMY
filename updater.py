# updater.py — built separately as updater.exe, ships once, rarely rebuilt
import sys, os, time, shutil, zipfile, tempfile, subprocess

def wait_for_process_exit(pid, timeout=20):
    import ctypes
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    start = time.time()
    while time.time() - start < timeout:
        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return True  # process no longer exists
        ctypes.windll.kernel32.CloseHandle(handle)
        time.sleep(0.5)
    return False

def main():
    download_url = sys.argv[1]
    app_dir      = sys.argv[2]   # ...\SkillSprintAcademy\app
    exe_name     = sys.argv[3]   # SkillSprintAcademy.exe
    caller_pid   = int(sys.argv[4])

    wait_for_process_exit(caller_pid)
    time.sleep(1)  # small extra safety margin for file handles to release

    tmp_zip = os.path.join(tempfile.gettempdir(), "ssa_update.zip")
    extract_dir = os.path.join(tempfile.gettempdir(), "ssa_update_extracted")

    r = __import__("requests").get(download_url, stream=True, timeout=30)
    with open(tmp_zip, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)

    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    with zipfile.ZipFile(tmp_zip) as z:
        z.extractall(extract_dir)

    if os.path.exists(app_dir):
        shutil.rmtree(app_dir)          # safe: app_dir has NO user data in it
    shutil.copytree(extract_dir, app_dir)

    os.remove(tmp_zip)
    shutil.rmtree(extract_dir)

    subprocess.Popen([os.path.join(app_dir, exe_name)])  # relaunch new version

if __name__ == "__main__":
    main()