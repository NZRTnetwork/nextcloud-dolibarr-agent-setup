"""
populate_nc_profiles.py

Sets Nextcloud user profile fields for agent accounts:
displayname, headline, biography, email, organisation, role.

Authenticates as each agent using their own password —
Nextcloud profile fields can only be set by the user themselves.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("NC_BASE_URL")

# Agent profile data — customise for your organisation
# Format: username: {field: value}
AGENT_PROFILES = {
    os.getenv("AGENT_PAM"): {
        "password": os.getenv("AGENT_PAM_PASS"),
        "displayname": "Pam — Marketing",
        "headline": "Products & Marketing Agent",
        "biography": "AI agent responsible for product management and marketing across WordPress, Dolibarr, and Nextcloud.",
        "email": "pam@yourdomain.com",
        "organisation": "Your Org Name",
        "role": "Products & Marketing",
    },
    os.getenv("AGENT_CAS"): {
        "password": os.getenv("AGENT_CAS_PASS"),
        "displayname": "Cas — Sales",
        "headline": "Customer & Sales Agent",
        "biography": "AI agent responsible for CRM, proposals, orders, and invoices.",
        "email": "cas@yourdomain.com",
        "organisation": "Your Org Name",
        "role": "Customer & Sales",
    },
    os.getenv("AGENT_FIN"): {
        "password": os.getenv("AGENT_FIN_PASS"),
        "displayname": "Fin — Finance",
        "headline": "Finance & Accounting Agent",
        "biography": "AI agent responsible for accounting, bank reconciliation, and payments.",
        "email": "fin@yourdomain.com",
        "organisation": "Your Org Name",
        "role": "Finance & Accounting",
    },
    os.getenv("AGENT_DAN"): {
        "password": os.getenv("AGENT_DAN_PASS"),
        "displayname": "Dan — DBA",
        "headline": "Database Administrator Agent",
        "biography": "AI agent responsible for database management, backups, and system configuration.",
        "email": "dan@yourdomain.com",
        "organisation": "Your Org Name",
        "role": "DBA",
    },
    # Add remaining agents following the same pattern
}

# OCS profile fields to set
PROFILE_FIELDS = ["displayname", "headline", "biography", "email", "organisation", "role"]


def set_profile_field(username, password, field, value):
    url = f"{BASE_URL}/ocs/v2.php/cloud/users/{username}"
    resp = requests.put(
        url,
        auth=(username, password),
        headers={"OCS-APIRequest": "true", "Accept": "application/json"},
        data={"key": field, "value": value},
    )
    if resp.status_code not in (200, 204):
        print(f"    Warning: {field} — HTTP {resp.status_code}")
    return resp.status_code


def main():
    for username, profile in AGENT_PROFILES.items():
        if not username:
            continue
        print(f"\n{username}:")
        password = profile.get("password")
        if not password:
            print(f"  No password set — skipping")
            continue
        for field in PROFILE_FIELDS:
            value = profile.get(field, "")
            if value:
                status = set_profile_field(username, password, field, value)
                print(f"  {field}: {status}")

    print("\nDone.")


if __name__ == "__main__":
    main()
