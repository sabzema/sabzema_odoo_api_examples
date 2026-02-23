import time
import requests
import os
import csv
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
CSV_FILE = os.getenv("CSV_FILE", "inserted_partners.csv")
ENABLE_CSV = os.getenv("ENABLE_CSV", "false").lower() in ("1", "true", "yes")

fake = Faker("fa_IR")
lock = Lock()            # console + counters
csv_lock = Lock()        # csv writes

# ---------------------------
# PREPARE CSV (only if enabled)
# ---------------------------
if ENABLE_CSV and not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "email", "phone", "company_type"])

# ---------------------------
# JSON-RPC HELPER
# ---------------------------
def json_rpc_call(session, endpoint, method, params):
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
            raise Exception(f"JSON-RPC error: {result['error']}")
        return result["result"]
    except Exception as e:
        raise Exception(f"Request to {endpoint} failed: {e}")

# ---------------------------
# AUTHENTICATION
# ---------------------------
def authenticate():
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
# CSV WRITER (only if enabled)
# ---------------------------
def append_to_csv(ids, batch):
    if not ENABLE_CSV:
        return

    rows = []
    for rec_id, data in zip(ids, batch):
        rows.append([
            rec_id,
            data.get("name"),
            data.get("email"),
            data.get("phone"),
            data.get("company_type"),
        ])

    with csv_lock:
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

# ---------------------------
# FUNCTION TO INSERT A BATCH
# ---------------------------
def insert_batch(batch, batch_index):
    global total_inserted, batch_count
    start = time.perf_counter()

    session = authenticate()
    try:
        created_ids = json_rpc_call(session, "/web/dataset/call_kw", "call", {
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

        if isinstance(created_ids, int):
            created_ids = [created_ids]

        append_to_csv(created_ids, batch)

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
        print(
            f"\rBatch {batch_count}: Total inserted {total_inserted} / {TOTAL_RECORDS} "
            f"in {format_time(elapsed)}",
            end="",
            flush=True,
        )

# ---------------------------
# MAIN LOOP
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

    for future in futures:
        future.result()

end_time = time.perf_counter()
total_time = end_time - start_time
print(f"\nTotal elapsed time: {format_time(total_time)}")

if total_time > 0:
    rate = total_inserted / total_time
    print(f"Insertion rate: {rate:.2f} records per second")
else:
    print("Insertion rate: N/A (time too short)")
