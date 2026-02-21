#   _____ _____ _____ _____ _____ _____ _____
#  |   __|  _  | __  |__   |   __|     |  _  |
#  |__   |     | __ -|   __|   __| | | |     |
#  |_____|__|__|_____|_____|_____|_|_|_|__|__|
#

import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file (optional)
load_dotenv()

# Required configuration – must be set in environment or .env
ODOO_URL = os.getenv("ODOO_URL")
DB = os.getenv("DB")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

# Check that all required variables are present
missing = [var for var in ["ODOO_URL", "DB", "USERNAME", "PASSWORD"] if not os.getenv(var)]
if missing:
    print(f"Error: Missing required environment variables: {', '.join(missing)}")
    print("Please set them in your environment or in a .env file.")
    exit(1)

def json_rpc(session, endpoint, method, params):
    """Helper for JSON‑RPC calls with error checking."""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    resp = session.post(f"{ODOO_URL}{endpoint}", json=payload)
    resp.raise_for_status()
    result = resp.json()
    if "error" in result:
        raise Exception(f"JSON‑RPC error: {result['error']}")
    return result["result"]

# Authenticate
session = requests.Session()
try:
    json_rpc(session, "/web/session/authenticate", "call", {
        "db": DB,
        "login": USERNAME,
        "password": PASSWORD,
    })
    print("Authentication successful.")
except Exception as e:
    print(f"Authentication failed: {e}")
    exit(1)

# Create one contact
contact = {
    "name": "Test Contact",
    "email": "test@example.com",
    "phone": "+123456789",
    "company_type": "person"
}

try:
    partner_id = json_rpc(session, "/web/dataset/call_kw", "call", {
        "model": "res.partner",
        "method": "create",
        "args": [contact],
        "kwargs": {"context": {"tracking_disable": True}}
    })
    print(f"Contact created successfully! Partner ID: {partner_id}")
except Exception as e:
    print(f"Create failed: {e}")
