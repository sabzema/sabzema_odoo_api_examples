#   _____ _____ _____ _____ _____ _____ _____
#  |   __|  _  | __  |__   |   __|     |  _  |
#  |__   |     | __ -|   __|   __| | | |     |
#  |_____|__|__|_____|_____|_____|_|_|_|__|__|
#

import time
import requests
import os
from faker import Faker
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ---------------------------
# CONFIGURATION from environment (with defaults)
# ---------------------------
ODOO_URL = os.getenv("ODOO_URL")
DB = os.getenv("DB")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

TOTAL_RECORDS = int(os.getenv("TOTAL_RECORDS", "100000"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1000"))
THREADS = int(os.getenv("THREADS", "30"))

fake = Faker("fa_IR")
lock = Lock()                            # for updating shared counters safely

# ---------------------------
# JSON‑RPC HELPER (for new endpoints)
# ---------------------------
def json_rpc_call(session, endpoint, method, params):
    """Perform a JSON‑RPC request to the given endpoint and return the result."""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1,
    }
    try:
        resp = session.post(f"{ODOO_URL}{endpoint}", json=payload)
        resp.raise_for_status()
        result = resp.json()
        if "error" in result:
            raise Exception(f"JSON‑RPC error: {result['error']}")
        return result["result"]
    except Exception as e:
        raise Exception(f"Request to {endpoint} failed: {e}")

# ---------------------------
# AUTHENTICATION (returns an authenticated session)
# ---------------------------
def authenticate():
    """Authenticate and return a requests.Session with the session cookie."""
    session = requests.Session()
    json_rpc_call(session, "/web/session/authenticate", "call", {
        "db": DB,
        "login": USERNAME,
        "password": PASSWORD,
    })
    return session

# ---------------------------
# TIME FORMATTING FUNCTION
# ---------------------------
def format_time(seconds):
    minutes = int(seconds // 60)
    sec = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{minutes} min {sec} sec {millis} ms"

# ---------------------------
# CONTACT GENERATOR
# ---------------------------
def generate_contact(i=None):
    """Generate Farsi contact info"""
    return {
        "name": fake.name(),
        "email": fake.email(),
        "phone": fake.phone_number(),
        "company_type": "person",
    }

# ---------------------------
# GLOBAL COUNTERS
# ---------------------------
total_inserted = 0
batch_count = 0

# ---------------------------
# FUNCTION TO INSERT A BATCH (executed in a thread)
# ---------------------------
def insert_batch(batch, batch_index):
    global total_inserted, batch_count
    start = time.perf_counter()

    # Each thread authenticates once (creates its own session with cookie)
    session = authenticate()
    try:
        json_rpc_call(session, "/web/dataset/call_kw", "call", {
            "model": "res.partner",
            "method": "create",
            "args": [batch],
            "kwargs": {
                "context": {
                    "tracking_disable": True,
                    "mail_create_nolog": True,
                    "mail_create_nosubscribe": True,
                    "no_reset_password": True,
                }
            }
        })
    except Exception as e:
        with lock:
            print(f"\nBatch {batch_index} failed: {e}", flush=True)
        raise
    finally:
        session.close()

    end = time.perf_counter()
    elapsed = end - start

    with lock:
        batch_count += 1
        total_inserted += len(batch)
        print(f"\rBatch {batch_count}: Total inserted {total_inserted} / {TOTAL_RECORDS} "
              f"in {format_time(elapsed)}", end="", flush=True)

# ---------------------------
# MAIN LOOP WITH THREAD POOL
# ---------------------------
start_time = time.perf_counter()

with ThreadPoolExecutor(max_workers=THREADS) as executor:
    futures = []
    current_batch = []

    for i in range(1, TOTAL_RECORDS + 1):
        current_batch.append(generate_contact(i))
        if len(current_batch) >= BATCH_SIZE:
            batch_to_submit = current_batch
            current_batch = []
            futures.append(executor.submit(insert_batch, batch_to_submit, batch_count))

    if current_batch:
        futures.append(executor.submit(insert_batch, current_batch, batch_count))

    # Wait for all threads and re-raise any exception
    for future in futures:
        future.result()

end_time = time.perf_counter()
total_time = end_time - start_time
print(f"\nTotal elapsed time: {format_time(total_time)}")

# Calculate and print insertion rate
if total_time > 0:
    rate = total_inserted / total_time
    print(f"Insertion rate: {rate:.2f} records per second")
else:
    print("Insertion rate: N/A (time too short)")
