# updater.py

import os
import sys
import json
import zipfile
import tempfile
import requests

def setup_vendor():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    vendor_dir = os.path.join(current_dir, "vendor")
    if vendor_dir not in sys.path:
        sys.path.insert(0, vendor_dir)

setup_vendor()

# URL to a public raw GitHub file with version info
REMOTE_VERSION_INFO_URL = "https://raw.githubusercontent.com/WebRendHQ/Vital-Elements-Public/main/version.json"

from . import __init__
LOCAL_VERSION = ".".join(map(str, __init__.bl_info["version"]))


def check_for_updates():
    """
    1. Fetch a version.json from GitHub
    2. If remote version > local, download the zip_url
    3. Extract into the local add-on folder
    4. Prompt the user to restart Blender
    """
    try:
        resp = requests.get(REMOTE_VERSION_INFO_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[Updater] Failed to fetch version info: {e}")
        return False

    remote_version = data.get("version", "0.0")
    zip_url = data.get("zip_url", "")

    if _is_newer(remote_version, LOCAL_VERSION):
        print(f"[Updater] Found new version {remote_version} (local {LOCAL_VERSION}). Downloading...")

        # Download ZIP
        try:
            zip_resp = requests.get(zip_url, timeout=30)
            zip_resp.raise_for_status()
            zip_data = zip_resp.content
        except Exception as e:
            print(f"[Updater] Failed to download update ZIP: {e}")
            return False

        # Extract
        local_dir = os.path.dirname(os.path.abspath(__file__))
        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_path = os.path.join(tmp_dir, "update.zip")
            with open(zip_path, "wb") as f:
                f.write(zip_data)
            try:
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    zf.extractall(path=local_dir)
            except Exception as e:
                print(f"[Updater] Error extracting ZIP: {e}")
                return False

        print("[Updater] Update applied. Please restart the device to use the new version.")
        return True
    else:
        print("[Updater] No new version available.")
        return False

def _is_newer(remote_ver, local_ver):
    try:
        rv = list(map(int, remote_ver.split(".")))
        lv = list(map(int, local_ver.split(".")))
        return rv > lv
    except:
        return False
