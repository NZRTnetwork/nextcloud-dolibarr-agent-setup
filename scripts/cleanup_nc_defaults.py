"""
cleanup_nc_defaults.py

Removes Nextcloud default files and folders from agent home directories:
Documents, Photos, Talk, Templates, Nextcloud.png, Nextcloud Manual.pdf, Nextcloud intro.mp4

Authenticates as each agent using their own password (from .env).
Run after create_agents.py and before enabling accounts.

Safe to re-run — 404 responses (item already gone) are treated as success.
"""

import os
import sys

import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.environ["NC_URL"].rstrip("/")

# Agent usernames and their passwords from environment
# Add/remove agents to match your roster
AGENTS = {
    os.getenv("AGENT_PAM"): os.getenv("AGENT_PAM_PASS"),
    os.getenv("AGENT_CAS"): os.getenv("AGENT_CAS_PASS"),
    os.getenv("AGENT_SUN"): os.getenv("AGENT_SUN_PASS"),
    os.getenv("AGENT_FIN"): os.getenv("AGENT_FIN_PASS"),
    os.getenv("AGENT_HAN"): os.getenv("AGENT_HAN_PASS"),
    os.getenv("AGENT_EMA"): os.getenv("AGENT_EMA_PASS"),
    os.getenv("AGENT_DAI"): os.getenv("AGENT_DAI_PASS"),
    os.getenv("AGENT_DAN"): os.getenv("AGENT_DAN_PASS"),
}

DEFAULT_ITEMS = [
    "Documents",
    "Photos",
    "Talk",
    "Templates",
    "Nextcloud.png",
    "Nextcloud Manual.pdf",
    "Nextcloud intro.mp4",
]


def delete_item(userid, password, item):
    url = f"{BASE_URL}/remote.php/dav/files/{userid}/{item}"
    resp = requests.delete(url, auth=HTTPBasicAuth(userid, password))
    if resp.status_code == 204:
        print(f"  deleted : {item}")
    elif resp.status_code == 404:
        print(f"  missing : {item}")
    else:
        print(f"  FAIL {resp.status_code}: {item}")


def cleanup_agent(userid, password):
    print(f"\n=== {userid} ===")
    for item in DEFAULT_ITEMS:
        delete_item(userid, password, item)


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    for userid, password in AGENTS.items():
        if not userid or not password:
            continue
        if target and userid != target:
            continue
        cleanup_agent(userid, password)
    print("\nDone.")


if __name__ == "__main__":
    main()
