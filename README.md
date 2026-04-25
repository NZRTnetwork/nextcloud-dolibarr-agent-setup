# Nextcloud + Dolibarr Agent Setup Scripts

Python scripts for provisioning a multi-agent organisation on Nextcloud and Dolibarr ERP. Automates the tedious parts of setting up multiple user accounts with scoped permissions, shared folders, and profile data.

Built to provision 9 AI agent accounts for NZRT Network's virtual organisation.

## What These Scripts Do

| Script | What it does |
|--------|-------------|
| `create_nc_shares.py` | Creates scoped folder shares in Nextcloud via OCS API — each agent gets R or R+W access to their folders only |
| `populate_nc_profiles.py` | Sets display name, headline, bio, email, org, and role on each agent's Nextcloud profile |
| `cleanup_nc_defaults.py` | Removes Nextcloud's default folders (Documents, Photos, Talk, Templates, etc.) from agent accounts |
| `create_shared_readmes.py` | Uploads README.md files to each /Shared/ subfolder describing its purpose, manager, and retention policy |
| `set_dolibarr_permissions.py` | Sets module-level permissions for each agent in Dolibarr via MySQL — 58 permission records across 7 agents |

## The Permission Model

Each agent gets access only to the Nextcloud folders relevant to their role:

| Agent | Nextcloud Folder | Access |
|-------|-----------------|--------|
| pam (marketing) | /Shared/Marketing | R+W |
| cas (sales) | /Shared/Sales | R+W |
| sun (procurement) | /Shared/Procurement | R+W |
| fin (finance) | /Shared/Finance | R+W |
| han (HR) | /Shared/HR | R+W |
| ema (documents) | /Shared/Dolibarr_EDM, /Shared/Archive | R+W |
| dai (analytics) | All /Shared/ folders | R (read only) |
| dan (DBA) | /Shared/Database | R+W |
| All agents | /Shared/Templates | R |

## Prerequisites

- Python 3.8+
- Nextcloud instance with admin access
- Dolibarr instance with MySQL access (for permissions script)
- Agent user accounts already created in Nextcloud and Dolibarr

## Setup

```bash
git clone https://github.com/nzrtnetwork/nextcloud-dolibarr-agent-setup
cd nextcloud-dolibarr-agent-setup
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
```

## Configuration

Copy `.env.example` to `.env` and fill in your values:

```env
# Nextcloud
NC_BASE_URL=https://your-nextcloud.com/nextcloud
NC_ADMIN_USER=admin
NC_ADMIN_TOKEN=your-app-token-here

# Dolibarr
DOL_DB_HOST=localhost
DOL_DB_NAME=dolibarr
DOL_DB_USER=dolibarr_user
DOL_DB_PASS=your-db-password

# Agent accounts (Nextcloud usernames)
AGENT_PAM=pam
AGENT_CAS=cas
AGENT_SUN=sun
AGENT_FIN=fin
AGENT_HAN=han
AGENT_EMA=ema
AGENT_DAI=dai
AGENT_DAN=dan
```

**Never commit `.env` to git.** It's in `.gitignore`.

## Running the Scripts

Run in this order for a fresh setup:

```bash
# 1. Clean default NC folders from agent accounts
python scripts/cleanup_nc_defaults.py

# 2. Set agent profile data
python scripts/populate_nc_profiles.py

# 3. Create /Shared/ folder shares
python scripts/create_nc_shares.py

# 4. Upload READMEs to each shared folder
python scripts/create_shared_readmes.py

# 5. Set Dolibarr module permissions
python scripts/set_dolibarr_permissions.py
```

Each script is idempotent — safe to re-run if something fails partway through.

## Nextcloud App Token

Use a Nextcloud App Password (not your main password) for `NC_ADMIN_TOKEN`:
1. Log in to Nextcloud as admin
2. Go to Settings → Security → Devices & sessions
3. Create new app password, label it `api-setup`
4. Paste into `.env`

## Dolibarr Permissions

`set_dolibarr_permissions.py` sets permissions directly in MySQL. It uses the `llx_user_rights` table. Adjust the `PERMISSIONS` dict in the script for your Dolibarr module IDs — these vary by Dolibarr version and installed modules.

Run `SELECT * FROM llx_rights_def WHERE module_position > 0 ORDER BY module_position, id;` to get your module permission IDs.

## Shared Folder Structure

Scripts assume this structure exists in Nextcloud under `/Shared/`:

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
│   ├── Finance/
│   ├── Sales/
│   ├── HR/
│   └── General/
└── CREDS/          ← admin only, never shared
```

Create these folders in Nextcloud before running `create_nc_shares.py`.

## Real-World Usage

These scripts provision the agent infrastructure for [NZRT Network](https://nzrtnetwork.com)'s 9-agent virtual organisation. The agent roles and folder structure align with the [claude-code-multi-agent-setup](https://github.com/nzrtnetwork/claude-code-multi-agent-setup) pattern.

## License

MIT

---

*Built by NZRT Network · [nzrtnetwork.com](https://nzrtnetwork.com)*
