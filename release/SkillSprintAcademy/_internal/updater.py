# updater.py — built separately as updater.exe, ships once, rarely rebuilt
# Verifies Ed25519 signature of update zip before applying
import sys, os, time, shutil, zipfile, tempfile, subprocess, base64

# Ed25519 public key for verifying update signatures (embedded at build time)
# This should be replaced with the actual public key when building
UPDATE_PUBLIC_KEY_B64 = os.environ.get("UPDATER_PUBLIC_KEY", "")
# Fallback: allow unsigned updates if no key configured (dev mode only)
ALLOW_UNSIGNED = os.environ.get("UPDATER_ALLOW_UNSIGNED", "false").lower() == "true"

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

def verify_signature(zip_path, sig_path):
    """Verify Ed25519 signature of zip file using embedded public key.
    
    Returns True if valid, False otherwise.
    """
    if not UPDATE_PUBLIC_KEY_B64:
        if ALLOW_UNSIGNED:
            print("[WARN] No public key configured — allowing unsigned update (dev mode)")
            return True
        print("[ERROR] No public key configured for signature verification")
        return False
    
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from cryptography.exceptions import InvalidSignature
        
        public_key = Ed25519PublicKey.from_public_bytes(base64.b64decode(UPDATE_PUBLIC_KEY_B64))
        
        with open(sig_path, "rb") as f:
            signature = f.read()
        
        with open(zip_path, "rb") as f:
            data = f.read()
        
        public_key.verify(signature, data)
        print("[OK] Ed25519 signature verified")
        return True
    except ImportError:
        print("[ERROR] cryptography library not available for signature verification")
        return False
    except Exception as e:
        print(f"[ERROR] Signature verification failed: {e}")
        return False

def main():
    if len(sys.argv) < 6:
        print("Usage: updater.py <download_url> <app_dir> <exe_name> <caller_pid> <sig_url>")
        sys.exit(1)
    
    download_url = sys.argv[1]
    app_dir      = sys.argv[2]   # ...\SkillSprintAcademy\app
    exe_name     = sys.argv[3]   # SkillSprintAcademy.exe
    caller_pid   = int(sys.argv[4])
    sig_url      = sys.argv[5]   # URL to .sig file

    wait_for_process_exit(caller_pid)
    time.sleep(1)  # small extra safety margin for file handles to release

    tmp_zip = os.path.join(tempfile.gettempdir(), "ssa_update.zip")
    tmp_sig = os.path.join(tempfile.gettempdir(), "ssa_update.sig")
    extract_dir = os.path.join(tempfile.gettempdir(), "ssa_update_extracted")

    # Download zip
    print(f"[INFO] Downloading update from {download_url}")
    r = __import__("requests").get(download_url, stream=True, timeout=60)
    r.raise_for_status()
    with open(tmp_zip, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
    print(f"[OK] Downloaded {os.path.getsize(tmp_zip)} bytes")

    # Download signature
    print(f"[INFO] Downloading signature from {sig_url}")
    r = __import__("requests").get(sig_url, timeout=30)
    r.raise_for_status()
    with open(tmp_sig, "wb") as f:
        f.write(r.content)
    print(f"[OK] Downloaded signature ({len(r.content)} bytes)")

    # Verify signature BEFORE extracting
    if not verify_signature(tmp_zip, tmp_sig):
        print("[ERROR] Signature verification failed — aborting update")
        os.remove(tmp_zip)
        os.remove(tmp_sig)
        sys.exit(1)

    # Extract verified zip
    print("[INFO] Extracting verified update...")
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    with zipfile.ZipFile(tmp_zip) as z:
        z.extractall(extract_dir)

    # Atomic replace
    print("[INFO] Installing update...")
    if os.path.exists(app_dir):
        shutil.rmtree(app_dir)          # safe: app_dir has NO user data in it
    shutil.copytree(extract_dir, app_dir)

    # Cleanup
    os.remove(tmp_zip)
    os.remove(tmp_sig)
    shutil.rmtree(extract_dir)

    print("[OK] Update installed, relaunching...")
    subprocess.Popen([os.path.join(app_dir, exe_name)])  # relaunch new version

if __name__ == "__main__":
    main()