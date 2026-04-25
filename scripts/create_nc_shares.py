"""
create_nc_shares.py

Creates Nextcloud folder shares for agent accounts via OCS API.
Each agent gets scoped R or R+W access to their designated /Shared/ folders.

Run after creating the /Shared/ folder structure and agent accounts in Nextcloud.
Safe to re-run — checks for existing shares before creating.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("NC_BASE_URL")
ADMIN_USER = os.getenv("NC_ADMIN_USER")
ADMIN_TOKEN = os.getenv("NC_ADMIN_TOKEN")

# Nextcloud OCS permission constants
READ_ONLY = 1
READ_WRITE = 15  # read + update + create + delete

# Share matrix: (folder_path, agent_username, permission)
# Adjust to match your agent usernames and folder structure
SHARES = [
    ("/Shared/Marketing",    os.getenv("AGENT_PAM"), READ_WRITE),
    ("/Shared/Marketing",    os.getenv("AGENT_DAI"), READ_ONLY),
    ("/Shared/Sales",        os.getenv("AGENT_CAS"), READ_WRITE),
    ("/Shared/Sales",        os.getenv("AGENT_DAI"), READ_ONLY),
    ("/Shared/Procurement",  os.getenv("AGENT_SUN"), READ_WRITE),
    ("/Shared/Procurement",  os.getenv("AGENT_DAI"), READ_ONLY),
    ("/Shared/Finance",      os.getenv("AGENT_FIN"), READ_WRITE),
    ("/Shared/Finance",      os.getenv("AGENT_DAI"), READ_ONLY),
    ("/Shared/HR",           os.getenv("AGENT_HAN"), READ_WRITE),
    ("/Shared/Analytics",    os.getenv("AGENT_DAI"), READ_WRITE),
    ("/Shared/Database",     os.getenv("AGENT_DAN"), READ_WRITE),
    ("/Shared/Dolibarr_EDM", os.getenv("AGENT_EMA"), READ_WRITE),
    ("/Shared/Dolibarr_EDM", os.getenv("AGENT_DAI"), READ_ONLY),
    ("/Shared/Archive",      os.getenv("AGENT_EMA"), READ_WRITE),
    ("/Shared/Archive",      os.getenv("AGENT_DAI"), READ_ONLY),
    # Templates — all agents read-only
    ("/Shared/Templates",    os.getenv("AGENT_PAM"), READ_ONLY),
    ("/Shared/Templates",    os.getenv("AGENT_CAS"), READ_ONLY),
    ("/Shared/Templates",    os.getenv("AGENT_SUN"), READ_ONLY),
    ("/Shared/Templates",    os.getenv("AGENT_FIN"), READ_ONLY),
    ("/Shared/Templates",    os.getenv("AGENT_HAN"), READ_ONLY),
    ("/Shared/Templates",    os.getenv("AGENT_EMA"), READ_WRITE),  # ema manages templates
    ("/Shared/Templates",    os.getenv("AGENT_DAI"), READ_ONLY),
    ("/Shared/Templates",    os.getenv("AGENT_DAN"), READ_ONLY),
    # CREDS — not shared with any agent
]


def get_existing_shares():
    """Return set of (path, shareWith) tuples for existing shares."""
    url = f"{BASE_URL}/ocs/v2.php/apps/files_sharing/api/v1/shares"
    resp = requests.get(
        url,
        auth=(ADMIN_USER, ADMIN_TOKEN),
        headers={"OCS-APIRequest": "true", "Accept": "application/json"},
    )
    resp.raise_for_status()
    data = resp.json()
    existing = set()
    for share in data.get("ocs", {}).get("data", []):
        existing.add((share.get("path"), share.get("share_with")))
    return existing


def create_share(folder_path, share_with, permissions):
    url = f"{BASE_URL}/ocs/v2.php/apps/files_sharing/api/v1/shares"
    payload = {
        "path": folder_path,
        "shareType": 0,  # 0 = user share
        "shareWith": share_with,
        "permissions": permissions,
    }
    resp = requests.post(
        url,
        auth=(ADMIN_USER, ADMIN_TOKEN),
        headers={"OCS-APIRequest": "true", "Accept": "application/json"},
        data=payload,
    )
    resp.raise_for_status()
    result = resp.json()
    status = result.get("ocs", {}).get("meta", {}).get("statuscode")
    if status == 100:
        share_id = result["ocs"]["data"]["id"]
        perm_label = "R+W" if permissions == READ_WRITE else "R"
        print(f"  Created: {folder_path} → {share_with} ({perm_label}) [ID {share_id}]")
    else:
        print(f"  Warning: {folder_path} → {share_with} — status {status}")


def main():
    print(f"Connecting to {BASE_URL} as {ADMIN_USER}")
    existing = get_existing_shares()
    print(f"Found {len(existing)} existing shares\n")

    created = 0
    skipped = 0

    for folder_path, agent, permissions in SHARES:
        if not agent:
            print(f"  Skipping {folder_path} — agent env var not set")
            continue
        if (folder_path, agent) in existing:
            print(f"  Exists:  {folder_path} → {agent}")
            skipped += 1
            continue
        create_share(folder_path, agent, permissions)
        created += 1

    print(f"\nDone. Created: {created}, Skipped (already exist): {skipped}")


if __name__ == "__main__":
    main()
