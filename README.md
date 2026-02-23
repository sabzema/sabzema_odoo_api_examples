# Sabzema Odoo API Examples

A collection of Python scripts to interact with Odoo via JSON‑RPC API, designed for bulk data operations.
This project is **dockerized** for easy setup and also works natively without Docker.

## Prerequisites

- **Python 3.11** (if running without Docker)
- **Docker** (if using Docker)
- Access to an Odoo instance (URL, database name, credentials)

## Configuration

All settings are managed through environment variables.  
Copy the example environment file and adjust it to your needs:

```bash
cp env_example .env
```

## Edit the .env file:

```
ODOO_URL=https://your-odoo-instance.com
DB=your_database
USERNAME=your_username
PASSWORD=your_password
TOTAL_RECORDS=3000000
BATCH_SIZE=1000
THREADS=30
ENABLE_CSV=true
CSV_FILE=inserted_partners.csv
```

- ODOO_URL – Base URL of your Odoo server.
- DB – Odoo Database name.
- USERNAME – Odoo user login email.
- PASSWORD – Odoo user password.
- TOTAL_RECORDS – Number of records to insert (default 3 000 000).
- BATCH_SIZE – Number of records per batch (default 1000).
- THREADS – Number of concurrent threads (default 30).
- ENABLE_CSV – Enables writing inserted records to CSV (true/false, default true).
- CSV_FILE – Output CSV filename (default inserted_partners.csv)

### CSV Behavior

#### When ENABLE_CSV=true:
The script creates the CSV file if it does not exist.
Each inserted record ID is stored alongside generated data.
Thread-safe writing is used to prevent corruption.

#### When ENABLE_CSV=false:
No CSV file is created.
No disk I/O occurs.
Bulk insert runs at maximum speed (recommended for pure performance testing).

## Usage

## Running scripts

Install Python dependencies:

```
pip install -r requirements.txt
```

Run the bulk script:

```
python ./examples/bulk_insert_contacts.py
```

Run the single insert script:


```
python ./examples/single_insert_contact.py
```

## Docker Setup
Build the Docker image (only once, or after dependency changes):

```
docker build -t sabzema-python-runner .
```

### Running with Docker
If your Odoo is remote (outside Docker, e.g.):

```bash
docker run --rm -v $(pwd):/app sabzema-python-runner python ./examples/bulk_insert_contacts.py
```

If your Odoo runs in a Docker container on the same network (e.g., inside odoo_network):

```bash
docker run --network odoo_network --rm -v $(pwd):/app sabzema-python-runner python ./examples/bulk_insert_contacts.py
```

## Available Scripts

| Script | Description |
|--------|-------------|
| `bulk_insert_contacts.py` | Bulk insert contacts (`res.partner`) using multiple threads. |
| `single_insert_contact.py` | Minimal example – inserts a single contact to demonstrate basic Odoo JSON‑RPC calls. |

## Project Structure

```
.
├── Dockerfile               # Docker image definition
├── env_example              # Example environment file
├── bulk_insert_contacts.py  # Contact Bulk insert script
├── single_insert_contact.py # Add Single contact example
├── README.md                # This file
└── requirements.txt          # Python dependencies
```

## Notes

- The Docker network must exist if you use the --network flag. Check with docker network ls.
- Rebuild the Docker image if you add new dependencies to requirements.txt.
- The scripts generate Farsi (Persian) data using Faker('fa_IR') – change the locale in the code if needed.
- When running without Docker, ensure your Python environment has the required packages.
- On remote server Verify the Docker network exists: ```docker network ls```

## Example Output

After a successful run, you will see progress per batch and a final summary similar to this:

```
Batch 100: Total inserted 100000 / 100000 in 0 min 9 sec 88 ms
Total elapsed time: 0 min 40 sec 950 ms
Insertion rate: 2441.97 records per second
```

*These numbers are from an actual test run and reflect real performance on a production‑like setup.
Your results may vary depending on server load, network latency, and configuration.*


# Contributing
Contributions are welcome! If you'd like to improve the examples, fix bugs, or add new Odoo API use cases:

- Fork the repository.
- Create a feature branch (git checkout -b feature/amazing-example).
- Commit your changes (git commit -m 'Add amazing example').
- Push to the branch (git push origin feature/amazing-example).
- Open a Pull Request.

Please ensure your code follows the existing style and includes comments where necessary.

# License
This project is licensed under the MIT License.

# Contact
Created by (Sabzema)[https://sabzema.com] – feel free to reach out via GitHub Issues for questions or suggestions.

# References
- [Odoo JSON-RPC Document](https://www.odoo.com/documentation/19.0/developer/reference/external_api.html)
- JSON-RPC implementation follows the [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification).
