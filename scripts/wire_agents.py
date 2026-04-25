"""
wire_agents.py

Post-creation wiring for virtual agent accounts:
- Generates WordPress Application Passwords per agent
- Re-enables Nextcloud accounts (created disabled by create_agents.py)
- Appends WP application passwords to the credentials file

Run once after create_agents.py completes successfully.
"""

import base64
import datetime
import os

import requests
from dotenv import load_dotenv

from agents import AGENTS

load_dotenv()

WP_URL          = os.environ["WP_URL"].rstrip("/")
WP_USER         = os.environ["WP_USER"]
WP_APP_PASSWORD = os.environ["WP_APP_PASSWORD"]
NC_URL          = os.environ["NC_URL"].rstrip("/")
NC_USER         = os.environ["NC_USER"]
NC_PASSWORD     = os.environ["NC_PASSWORD"]
CREDS_PATH      = os.getenv("CREDS_PATH", "agent_credentials.txt")

APP_PW_LABEL = f"agent-api-{datetime.date.today().strftime('%Y-%m')}"


def wp_auth_header() -> dict:
    token = base64.b64encode(f"{WP_USER}:{WP_APP_PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {token}", "Content-Type": "application/json"}


def nc_auth_header() -> dict:
    token = base64.b64encode(f"{NC_USER}:{NC_PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {token}", "OCS-APIREQUEST": "true", "Content-Type": "application/json"}


def get_wp_user_id(code: str) -> int | None:
    r = requests.get(
        f"{WP_URL}/wp-json/wp/v2/users",
        headers=wp_auth_header(),
        params={"search": code},
        timeout=15,
    )
    if r.status_code == 200:
        users = [u for u in r.json() if u.get("slug") == code or u.get("name", "").lower().startswith(code)]
        return users[0]["id"] if users else None
    return None


def create_wp_app_password(user_id: int, label: str) -> str | None:
    r = requests.post(
        f"{WP_URL}/wp-json/wp/v2/users/{user_id}/application-passwords",
        headers=wp_auth_header(),
        json={"name": label},
        timeout=15,
    )
    if r.status_code in (200, 201):
        return r.json().get("password")
    return None


def enable_nc_user(code: str) -> str:
    r = requests.put(
        f"{NC_URL}/ocs/v2.php/cloud/users/{code}/enable?format=json",
        headers=nc_auth_header(),
        timeout=10,
    )
    try:
        sc = r.json().get("ocs", {}).get("meta", {}).get("statuscode")
        return "OK enabled" if sc in (100, 200) else f"ERR {sc}"
    except Exception:
        return f"ERR {r.status_code}"


def append_creds(wp_app_passwords: dict) -> None:
    section = [
        "",
        f"WordPress Application Passwords — generated {datetime.date.today()} (label: {APP_PW_LABEL})",
        "-" * 60,
        f"{'Agent':<6} {'Application Password (spaces included)'}",
        "-" * 60,
    ]
    for code, pw in wp_app_passwords.items():
        section.append(f"{code:<6} {pw or 'FAILED — generate manually in WP Admin'}")

    with open(CREDS_PATH, "a", encoding="utf-8") as f:
        f.write("\n".join(section) + "\n")
    print(f"Appended WP Application Passwords to {CREDS_PATH}")


def main():
    print("\n=== Agent Wiring ===\n")

    wp_app_passwords = {}
    results = []

    for agent in AGENTS:
        code = agent["code"]
        skip = agent.get("skip_create", False)

        if skip:
            results.append((code, "skipped (admin)", "skipped (admin)"))
            continue

        print(f"  [{code}]")

        wp_role = agent.get("wp_role", "")
        if wp_role:
            uid = get_wp_user_id(code)
            if uid:
                app_pw = create_wp_app_password(uid, APP_PW_LABEL)
                wp_status = "OK" if app_pw else "ERR — no app password created"
                wp_app_passwords[code] = app_pw
            else:
                wp_status = "ERR — user not found"
                wp_app_passwords[code] = None
        else:
            wp_status = "skipped (no WP role)"
            wp_app_passwords[code] = None

        nc_status = enable_nc_user(code)
        results.append((code, wp_status, nc_status))

    print("\n" + "=" * 60)
    print(f"{'Code':<6} {'WP App Password':<22} {'Nextcloud'}")
    print("-" * 60)
    for code, wp, nc in results:
        print(f"{code:<6} {wp:<22} {nc}")
    print("=" * 60)

    agent_pws = {c: p for c, p in wp_app_passwords.items() if p}
    if agent_pws:
        print("\nAppending Application Passwords to credentials file...")
        append_creds(agent_pws)
    else:
        print("\nNo Application Passwords generated — check errors above.")

    print(f"\nDone.\nVerify: curl -u 'pam:<app_password>' {WP_URL}/wp-json/wp/v2/users/me\n")


if __name__ == "__main__":
    main()
