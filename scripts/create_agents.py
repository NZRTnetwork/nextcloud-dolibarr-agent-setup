"""
create_agents.py

Creates virtual agent accounts across WordPress, Dolibarr, and Nextcloud.
Also creates cPanel email accounts via SSH if CPANEL_* env vars are set.

Run once after filling in .env from .env.example.
Imports agent definitions from agents.py — edit that file first.

Safe to re-run: existing accounts are updated, not duplicated.
"""

import base64
import datetime
import hashlib
import json
import os
import secrets
import string
import subprocess
import sys

import requests
from dotenv import load_dotenv

from agents import AGENTS, DOLIBARR_PERMISSIONS

load_dotenv()

WP_URL          = os.environ["WP_URL"].rstrip("/")
WP_USER         = os.environ["WP_USER"]
WP_APP_PASSWORD = os.environ["WP_APP_PASSWORD"]
NC_URL          = os.environ["NC_URL"].rstrip("/")
NC_USER         = os.environ["NC_USER"]
NC_PASSWORD     = os.environ["NC_PASSWORD"]

# Dolibarr via direct MySQL (adjust path to your MySQL binary)
MYSQL_BIN = os.getenv("MYSQL_BIN", "mysql")
DB_NAME   = os.getenv("DB_NAME", "dolibarr")
DB_HOST   = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT   = os.getenv("DB_PORT", "3306")
DB_USER   = os.getenv("DB_USER", "root")
DB_PASS   = os.getenv("DB_PASS", "")

# cPanel SSH (optional — set env vars to enable email account creation)
CPANEL_HOST       = os.getenv("CPANEL_SSH_HOST", "")
CPANEL_USER       = os.getenv("CPANEL_SSH_USER", "")
CPANEL_KEY        = os.getenv("CPANEL_SSH_KEY", "")
CPANEL_PASSPHRASE = os.getenv("CPANEL_SSH_PASSPHRASE", "") or None
CPANEL_DOMAIN     = os.getenv("CPANEL_DOMAIN", "")

# Path to save generated credentials
CREDS_PATH = os.getenv("CREDS_PATH", "agent_credentials.txt")


def gen_password() -> str:
    uppers   = [secrets.choice(string.ascii_uppercase) for _ in range(4)]
    lowers   = [secrets.choice(string.ascii_lowercase) for _ in range(4)]
    digits   = [secrets.choice(string.digits) for _ in range(4)]
    specials = [secrets.choice("!@#$%^&*") for _ in range(4)]
    rest     = [secrets.choice(string.ascii_letters + string.digits + "!@#$%^&*") for _ in range(16)]
    pool = uppers + lowers + digits + specials + rest
    secrets.SystemRandom().shuffle(pool)
    return "".join(pool)


def wp_auth_header() -> dict:
    token = base64.b64encode(f"{WP_USER}:{WP_APP_PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {token}", "Content-Type": "application/json"}


def nc_auth_header() -> dict:
    token = base64.b64encode(f"{NC_USER}:{NC_PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {token}", "OCS-APIREQUEST": "true", "Content-Type": "application/json"}


# ── cPanel email ─────────────────────────────────────────────────────────────

def create_cpanel_email(ssh, email_local: str, pw: str) -> str:
    cmd = (
        f"uapi --output=json Email add_pop"
        f" email={email_local} domain={CPANEL_DOMAIN} password='{pw}' quota=0"
    )
    _, stdout, stderr = ssh.exec_command(cmd)
    raw = stdout.read().decode()
    try:
        data = json.loads(raw)
        if data.get("result", {}).get("status") == 1:
            return "OK created"
        errors = data.get("result", {}).get("errors") or []
        if any("already exists" in str(e).lower() for e in errors):
            return update_cpanel_email(ssh, email_local, pw)
        return f"ERR {errors}"
    except Exception:
        err = stderr.read().decode().strip()
        return f"ERR parse: {err or raw[:80]}"


def update_cpanel_email(ssh, email_local: str, pw: str) -> str:
    cmd = (
        f"uapi --output=json Email passwd_pop"
        f" email={email_local} domain={CPANEL_DOMAIN} password='{pw}'"
    )
    _, stdout, stderr = ssh.exec_command(cmd)
    raw = stdout.read().decode()
    try:
        data = json.loads(raw)
        if data.get("result", {}).get("status") == 1:
            return "OK updated"
        return f"ERR {data.get('result',{}).get('errors','')}"
    except Exception:
        return f"ERR parse: {stderr.read().decode().strip() or raw[:60]}"


# ── WordPress ─────────────────────────────────────────────────────────────────

def _wp_user_id(code: str) -> int | None:
    r = requests.get(
        f"{WP_URL}/wp-json/wp/v2/users",
        headers=wp_auth_header(),
        params={"search": code},
        timeout=15,
    )
    if r.status_code == 200:
        users = [u for u in r.json() if u.get("slug") == code or u.get("username") == code]
        return users[0]["id"] if users else None
    return None


def create_or_update_wp_user(code: str, name: str, email: str, pw: str, role: str) -> str:
    uid = _wp_user_id(code)
    if uid:
        r = requests.post(
            f"{WP_URL}/wp-json/wp/v2/users/{uid}",
            headers=wp_auth_header(),
            json={"password": pw},
            timeout=15,
        )
        return "OK updated" if r.status_code in (200, 201) else f"ERR update {r.status_code}"
    roles = [role] if role else []
    r = requests.post(
        f"{WP_URL}/wp-json/wp/v2/users",
        headers=wp_auth_header(),
        json={"username": code, "name": name, "email": email, "password": pw, "roles": roles},
        timeout=15,
    )
    if r.status_code in (200, 201):
        return f"OK created ({role or 'no role'})"
    return f"ERR {r.status_code}: {r.json().get('message', r.text)[:60]}"


def verify_wp_user(code: str) -> str:
    return "OK verified" if _wp_user_id(code) else "ERR not found"


# ── Dolibarr (direct MySQL) ──────────────────────────────────────────────────

def _mysql(sql: str) -> tuple[int, str, str]:
    args = [MYSQL_BIN, f"-h{DB_HOST}", f"-P{DB_PORT}", f"-u{DB_USER}", DB_NAME, "-e", sql]
    if DB_PASS:
        args.insert(4, f"-p{DB_PASS}")
    r = subprocess.run(args, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def create_or_update_dolibarr_user(code: str, name: str, email: str, pw: str) -> str:
    pw_md5 = hashlib.md5(pw.encode()).hexdigest()
    rc, out, _ = _mysql(f"SELECT COUNT(*) FROM llx_user WHERE login='{code}';")
    count = int(out.strip().split()[-1]) if rc == 0 and out.strip() else 0
    if count > 0:
        rc2, _, err = _mysql(
            f"UPDATE llx_user SET pass_crypted='{pw_md5}', tms=NOW() WHERE login='{code}';"
        )
        return "OK updated" if rc2 == 0 else f"ERR update {err.strip()[:60]}"
    sql = (
        f"INSERT INTO llx_user "
        f"(entity, login, lastname, email, pass_crypted, statut, admin, datec, tms) VALUES "
        f"(1, '{code}', '{name}', '{email}', '{pw_md5}', 1, 0, NOW(), NOW());"
    )
    rc, _, err = _mysql(sql)
    return "OK created" if rc == 0 else f"ERR {err.strip()[:60]}"


# ── Nextcloud ─────────────────────────────────────────────────────────────────

def nc_post(path: str, data: dict) -> dict:
    r = requests.post(f"{NC_URL}{path}?format=json", headers=nc_auth_header(), json=data, timeout=15)
    return r.json().get("ocs", {})


def nc_put(path: str, data: dict | None = None) -> dict:
    r = requests.put(f"{NC_URL}{path}?format=json", headers=nc_auth_header(), json=data, timeout=10)
    try:
        return r.json().get("ocs", {})
    except Exception:
        return {}


def ensure_nc_groups() -> None:
    r = requests.get(f"{NC_URL}/ocs/v1.php/cloud/groups?format=json", headers=nc_auth_header(), timeout=10)
    existing = r.json().get("ocs", {}).get("data", {}).get("groups", [])
    needed = {a["nc_group"] for a in AGENTS if not a.get("skip_create")}
    for group in sorted(needed):
        if group not in existing:
            nc_post("/ocs/v1.php/cloud/groups", {"groupid": group})
            print(f"    [NC] created group: {group}")


def create_or_update_nc_user(code: str, name: str, email: str, pw: str, group: str, quota: str) -> str:
    data = nc_post("/ocs/v2.php/cloud/users",
                   {"userid": code, "password": pw, "displayName": name,
                    "email": email, "groups": [group], "quota": quota})
    status_code = data.get("meta", {}).get("statuscode")
    if status_code in (100, 200):
        nc_put(f"/ocs/v2.php/cloud/users/{code}/disable")
        return "OK created (disabled — run wire_agents.py to enable)"
    if status_code == 102:
        res = nc_put(f"/ocs/v2.php/cloud/users/{code}", {"key": "password", "value": pw})
        sc2 = res.get("meta", {}).get("statuscode")
        return "OK updated" if sc2 in (100, 200) else f"ERR update {sc2}"
    msg = data.get("meta", {}).get("message", str(data)[:60])
    return f"ERR {status_code}: {msg}"


# ── Credentials save ──────────────────────────────────────────────────────────

def save_creds(passwords: dict) -> None:
    lines = [
        f"Agent Credentials — generated {datetime.date.today()}",
        "=" * 60,
        f"{'Agent':<6} {'Password':<32} {'Email'}",
        "-" * 60,
    ]
    for agent in AGENTS:
        code = agent["code"]
        lines.append(f"{code:<6} {passwords.get(code, ''):<32} {agent['email']}")
    lines += ["", "Systems: cPanel email / WordPress / Dolibarr / Nextcloud"]
    content = "\n".join(lines) + "\n"
    with open(CREDS_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Credentials saved to {CREDS_PATH}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("\n=== Virtual Agent Account Creation ===\n")

    print("Creating Nextcloud groups...")
    ensure_nc_groups()
    print("Nextcloud groups ready.\n")

    ssh = None
    if CPANEL_HOST and CPANEL_USER and CPANEL_KEY:
        try:
            import paramiko
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=CPANEL_HOST, username=CPANEL_USER, key_filename=CPANEL_KEY,
                        passphrase=CPANEL_PASSPHRASE, port=2200, timeout=15)
            print("SSH connected OK\n")
        except Exception as e:
            print(f"SSH failed: {e}\nEmail accounts will be skipped.")
            ssh = None
    else:
        print("CPANEL_* env vars not set — skipping email account creation.\n")

    passwords = {}
    results = []

    for agent in AGENTS:
        code     = agent["code"]
        name     = agent["name"]
        email    = agent["email"]
        wp_role  = agent["wp_role"]
        nc_group = agent["nc_group"]
        nc_quota = agent["nc_quota"]
        skip     = agent.get("skip_create", False)
        pw       = gen_password()
        passwords[code] = pw
        email_local = email.split("@")[0]

        print(f"  [{code}] {name}")

        em  = create_cpanel_email(ssh, email_local, pw) if ssh else "skipped"
        wp  = verify_wp_user(code) if skip else create_or_update_wp_user(code, name, email, pw, wp_role)
        dol = "skipped (admin)" if skip else create_or_update_dolibarr_user(code, name, email, pw)
        nc  = "skipped (admin)" if skip else create_or_update_nc_user(code, name, email, pw, nc_group, nc_quota)

        results.append((code, em, wp, dol, nc))

    if ssh:
        ssh.close()

    print("\n" + "=" * 78)
    print(f"{'Code':<6} {'Email':<12} {'WordPress':<18} {'Dolibarr':<16} {'Nextcloud'}")
    print("-" * 78)
    for code, em, wp, dol, nc in results:
        print(f"{code:<6} {em:<12} {wp:<18} {dol:<16} {nc}")
    print("=" * 78)

    save_creds(passwords)
    print("\nNext steps:")
    print("  1. Run wire_agents.py to enable NC accounts and generate WP application passwords")
    print("  2. Run create_nc_shares.py to set up folder access")
    print("  3. Run set_dolibarr_permissions.py to assign module permissions")
    print("  4. Run populate_nc_profiles.py to set profile fields")
    print("  5. Run cleanup_nc_defaults.py to remove default NC home folders\n")


if __name__ == "__main__":
    main()
