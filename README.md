# Nextcloud + Dolibarr Agent Setup Scripts

Python scripts for provisioning a multi-agent organisation on Nextcloud and Dolibarr ERP. Automates account creation, folder shares, profile data, and Nextcloud address book entries across multiple user accounts.

Built to provision the 9 AI agent accounts for [NZRT Network](https://nzrtnetwork.com)'s virtual organisation. Pairs with [claude-code-multi-agent-setup](https://github.com/NZRTnetwork/claude-code-multi-agent-setup).

---

## Scripts

| Script | What it does |
|--------|-------------|
| `agents.py` | Agent roster and Dolibarr permission reference — **edit this first** |
| `create_agents.py` | Create accounts across WordPress, Dolibarr, Nextcloud, and cPanel email |
| `wire_agents.py` | Enable Nextcloud accounts + generate WordPress Application Passwords |
| `create_nc_shares.py` | Create scoped /Shared/ folder access per agent via Nextcloud OCS API |
| `populate_nc_profiles.py` | Set display name, headline, bio, email, org, role on each NC profile |
| `populate_nc_contacts.py` | Update agent vCards in the Nextcloud system address book |
| `cleanup_nc_defaults.py` | Remove default NC home folders (Documents, Photos, Talk, etc.) from agent accounts |

---

## Run Order

For a fresh setup, run in this order:

```bash
# 0. Edit agents.py with your agent roster first

# 1. Create accounts on all systems
python scripts/create_agents.py

# 2. Enable NC accounts + generate WP Application Passwords
python scripts/wire_agents.py

# 3. Set up /Shared/ folder access
python scripts/create_nc_shares.py

# 4. Set NC profile fields
python scripts/populate_nc_profiles.py

# 5. Update NC address book vCards
python scripts/populate_nc_contacts.py

# 6. Remove default NC home folders
python scripts/cleanup_nc_defaults.py
```

Each script is idempotent — safe to re-run if something fails partway through.

---

## Setup

```bash
git clone https://github.com/NZRTnetwork/nextcloud-dolibarr-agent-setup
cd nextcloud-dolibarr-agent-setup
pip install -r requirements.txt
cp .env.example .env
# Edit .env and scripts/agents.py before running anything
```

---

## Configuration

### .env

Copy `.env.example` to `.env` and fill in your values. Key variables:

```env
# Nextcloud
NC_URL=https://your-nextcloud.com/nextcloud
NC_USER=admin
NC_PASSWORD=your-admin-password
NC_APP_TOKEN=your-app-token          # NC Settings → Security → App passwords

# WordPress
WP_URL=https://yoursite.com
WP_USER=admin
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx  # WP Admin → Users → Application Passwords

# Dolibarr (direct MySQL — used by create_agents.py)
MYSQL_BIN=mysql
DB_NAME=dolibarr
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASS=
```

**Never commit `.env` to git.** It's in `.gitignore`.

### agents.py

Edit `scripts/agents.py` to match your agent roster before running any scripts. Each agent entry sets:
- `code` — username across all systems
- `name` — display name
- `email` — email address
- `wp_role` — WordPress role (editor, contributor, or blank)
- `nc_group` — Nextcloud group
- `nc_quota` — Nextcloud storage quota

---

## Permission Model

Each agent gets access only to Nextcloud folders relevant to their role:

| Agent | Nextcloud Folder | Access |
|-------|-----------------|--------|
| pam (marketing) | /Shared/Marketing | R+W |
| cas (sales) | /Shared/Sales | R+W |
| sun (procurement) | /Shared/Procurement | R+W |
| fin (finance) | /Shared/Finance | R+W |
| han (HR) | /Shared/HR | R+W |
| ema (documents) | /Shared/Dolibarr_EDM, /Shared/Archive | R+W |
| dai (analytics) | All /Shared/ folders | R only |
| dan (DBA) | /Shared/Database | R+W |
| All agents | /Shared/Templates | R only |

Edit the `SHARES` list in `create_nc_shares.py` to match your own structure.

---

## Shared Folder Structure

Create these folders in Nextcloud before running `create_nc_shares.py`:

```
/Shared/
├── Marketing/
├── Sales/
├── Procurement/
├── Finance/
├── HR/
├── Analytics/
├── Database/
├── Dolibarr_EDM/
├── Archive/
├── Templates/
└── CREDS/          ← admin only, never shared with agents
```

---

## Requirements

- Python 3.8+
- Nextcloud instance with admin access
- Dolibarr instance with MySQL access
- WordPress instance with Application Passwords enabled (WordPress 5.6+)

Optional: cPanel SSH access for email account creation (set `CPANEL_*` env vars).

---

## License

MIT

---

*Built by NZRT Network · [nzrtnetwork.com](https://nzrtnetwork.com)*
