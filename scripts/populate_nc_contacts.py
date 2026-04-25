"""
populate_nc_contacts.py

Updates Nextcloud system address book vCards for agent accounts:
FN, TITLE, ORG, NOTE, EMAIL fields.

Authenticates as the admin user via app token (OCS API).
Run after agent accounts are created and enabled.

Requires: XC_USER and XC_APP_TOKEN in .env (generate in Nextcloud Settings → Security).
"""

import os
import re
import sys

import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

BASE_URL  = os.environ["NC_URL"].rstrip("/")
XC_USER   = os.environ["NC_USER"]
XC_TOKEN  = os.environ["NC_APP_TOKEN"]

# Agent contact data — customise for your organisation
AGENTS = {
    os.getenv("AGENT_PAM"): {
        "fn":    "PAM — Products & Marketing",
        "title": "AI Agent — Products & Marketing",
        "org":   "Your Org Name",
        "note":  "Handles product catalogue, marketing campaigns, and website content.",
        "email": "products@yourdomain.com",
    },
    os.getenv("AGENT_CAS"): {
        "fn":    "CAS — Customer & Sales",
        "title": "AI Agent — Customer & Sales",
        "org":   "Your Org Name",
        "note":  "Manages customer relationships, sales pipeline, and CRM data.",
        "email": "sales@yourdomain.com",
    },
    os.getenv("AGENT_SUN"): {
        "fn":    "SUN — Supplier & Procurement",
        "title": "AI Agent — Supplier & Procurement",
        "org":   "Your Org Name",
        "note":  "Manages supplier relationships, purchase orders, and procurement.",
        "email": "procurement@yourdomain.com",
    },
    os.getenv("AGENT_FIN"): {
        "fn":    "FIN — Finance & Accounting",
        "title": "AI Agent — Finance & Accounting",
        "org":   "Your Org Name",
        "note":  "Handles invoicing, payments, financial reporting, and accounts.",
        "email": "finance@yourdomain.com",
    },
    os.getenv("AGENT_HAN"): {
        "fn":    "HAN — Human Resources",
        "title": "AI Agent — Human Resources",
        "org":   "Your Org Name",
        "note":  "Manages HR records, onboarding, and staff administration.",
        "email": "hr@yourdomain.com",
    },
    os.getenv("AGENT_EMA"): {
        "fn":    "EMA — EDM & Communications",
        "title": "AI Agent — EDM & Communications",
        "org":   "Your Org Name",
        "note":  "Manages email campaigns and external digital communications.",
        "email": "edm@yourdomain.com",
    },
    os.getenv("AGENT_DAI"): {
        "fn":    "DAI — Data & Analytics",
        "title": "AI Agent — Data & Analytics",
        "org":   "Your Org Name",
        "note":  "Handles reporting, analytics, and data pipeline management.",
        "email": "data@yourdomain.com",
    },
    os.getenv("AGENT_DAN"): {
        "fn":    "DAN — Database Admin",
        "title": "AI Agent — Database Administration",
        "org":   "Your Org Name",
        "note":  "Manages database operations and data integrity.",
        "email": "dba@yourdomain.com",
    },
}

AUTH    = HTTPBasicAuth(XC_USER, XC_TOKEN)
HEADERS = {"OCS-APIREQUEST": "true"}


def find_vcard_url(userid):
    """PROPFIND system address book to find agent's vCard URL."""
    url = f"{BASE_URL}/remote.php/dav/addressbooks/system/system/"
    resp = requests.request(
        "PROPFIND", url,
        auth=AUTH,
        headers={"Depth": "1", "Content-Type": "application/xml"},
        data="""<?xml version="1.0"?>
<d:propfind xmlns:d="DAV:">
  <d:prop><d:getetag/><d:displayname/></d:prop>
</d:propfind>""",
    )
    pattern = rf'<d:href>([^<]*{userid}[^<]*\.vcf)</d:href>'
    match = re.search(pattern, resp.text, re.IGNORECASE)
    if match:
        href = match.group(1)
        return BASE_URL + href if href.startswith("/") else href
    return None


def get_vcard(url):
    resp = requests.get(url, auth=AUTH)
    return resp.text if resp.status_code == 200 else None


def set_vcard_field(vcard, field, value):
    pattern = rf'^{field}[;:][^\r\n]*(\r?\n( [^\r\n]+)*)?'
    if re.search(pattern, vcard, re.MULTILINE | re.IGNORECASE):
        return re.sub(pattern, f"{field}:{value}", vcard, flags=re.MULTILINE | re.IGNORECASE)
    return vcard.replace("END:VCARD", f"{field}:{value}\r\nEND:VCARD")


def put_vcard(url, vcard):
    resp = requests.put(
        url, auth=AUTH,
        headers={"Content-Type": "text/vcard; charset=utf-8"},
        data=vcard.encode("utf-8"),
    )
    return resp.status_code in (200, 201, 204)


def populate_contact(userid):
    data = AGENTS[userid]
    print(f"\n=== {userid} ===")

    url = find_vcard_url(userid)
    if not url:
        print(f"  vCard URL: NOT FOUND in system address book")
        return

    print(f"  vCard URL: {url}")
    vcard = get_vcard(url)
    if not vcard:
        print(f"  GET vCard: FAIL")
        return

    for field, key in [("FN", "fn"), ("TITLE", "title"), ("ORG", "org"),
                       ("NOTE", "note"), ("EMAIL", "email")]:
        vcard = set_vcard_field(vcard, field, data[key])

    ok = put_vcard(url, vcard)
    print(f"  PUT vCard: {'OK' if ok else 'FAIL'}")


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    for userid, data in AGENTS.items():
        if not userid or not data:
            continue
        if target and userid != target:
            continue
        populate_contact(userid)
    print("\nDone.")


if __name__ == "__main__":
    main()
