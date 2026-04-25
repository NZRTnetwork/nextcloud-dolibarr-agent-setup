"""
agents.py — Agent definitions for NZRT virtual organisation.

Edit this file to match your own agent roster before running any scripts.
"""

AGENTS = [
    {
        "code": "xc",
        "name": "XC - Admin",
        "email": "admin@yourdomain.com",
        "wp_role": "administrator",
        "nc_group": "admin",
        "nc_quota": "500 GB",
        "skip_create": True,  # admin account already exists — verify only
    },
    {
        "code": "pam",
        "name": "PAM - Products",
        "email": "products@yourdomain.com",
        "wp_role": "editor",
        "nc_group": "marketing",
        "nc_quota": "100 GB",
    },
    {
        "code": "cas",
        "name": "CAS - Sales",
        "email": "sales@yourdomain.com",
        "wp_role": "editor",
        "nc_group": "sales",
        "nc_quota": "100 GB",
    },
    {
        "code": "sun",
        "name": "SUN - Purchase",
        "email": "procurement@yourdomain.com",
        "wp_role": "editor",
        "nc_group": "procurement",
        "nc_quota": "100 GB",
    },
    {
        "code": "fin",
        "name": "FIN - Finance",
        "email": "finance@yourdomain.com",
        "wp_role": "contributor",
        "nc_group": "finance",
        "nc_quota": "200 GB",
    },
    {
        "code": "han",
        "name": "HAN - HR",
        "email": "hr@yourdomain.com",
        "wp_role": "contributor",
        "nc_group": "hr",
        "nc_quota": "150 GB",
    },
    {
        "code": "ema",
        "name": "EMA - EDM",
        "email": "edm@yourdomain.com",
        "wp_role": "editor",
        "nc_group": "edm",
        "nc_quota": "300 GB",
    },
    {
        "code": "dai",
        "name": "DAI - Data",
        "email": "data@yourdomain.com",
        "wp_role": "editor",
        "nc_group": "analytics",
        "nc_quota": "100 GB",
    },
    {
        "code": "dan",
        "name": "DAN - DBA",
        "email": "dba@yourdomain.com",
        "wp_role": "",  # no WordPress role
        "nc_group": "database",
        "nc_quota": "300 GB",
    },
]

# Dolibarr module permissions per agent (reference for set_dolibarr_permissions.py)
DOLIBARR_PERMISSIONS = {
    "xc":  "All modules (admin)",
    "pam": "Products, Stock, Manufacturing",
    "cas": "CRM, Commercial Proposals, Customer Orders, Customer Invoices",
    "sun": "Suppliers/Fournisseur, Purchase Orders, Receptions",
    "fin": "Accounting, Bank Accounts, Payments, Financial Reports",
    "han": "HR, Leave Management, Expense Reports",
    "ema": "EDM, Email Collector, Mass Emailing",
    "dai": "Data Export/Import (read only), Reports",
    "dan": "Administration only — no business modules",
}
