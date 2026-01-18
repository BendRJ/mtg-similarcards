# MTG Similar Cards

A Python application for finding similar Magic: The Gathering cards.

## Prerequisites

- Python 3.13+
- Docker and Docker Compose
- [uv](https://github.com/astral-sh/uv) (Python package manager)

## Dependencies

This project uses:
- **psycopg 3** - Modern PostgreSQL adapter for Python
- **python-dotenv** - Environment variable management

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mtg-similarcards
   ```

2. **Install Python dependencies**
   ```bash
   uv sync
   ```

3. **Start the database**
   ```bash
   docker compose up -d
   ```

   This will:
   - Pull the PostgreSQL 16 Alpine image
   - Create a container named `mtg-similarcards-db`
   - Initialize the database with SQL schemas from `database/sql/create_tables/`
   - Persist data in a Docker volume

4. **Verify the database is running**
   ```bash
   docker compose ps
   ```

   You should see the `mtg-similarcards-db` container running and healthy.

## Database

### Configuration

Database credentials are stored in the `.env` file (not tracked in git). Default values:

- **User:** `mtguser`
- **Password:** `mtgpassword`
- **Database:** `mtgcards_db`
- **Port:** `5432`

### Connection in Python

The `database/db.py` module provides convenient connection helpers:

```python
from database.db import get_cursor

# Simple query
with get_cursor() as cur:
    cur.execute("SELECT * FROM sets")
    results = cur.fetchall()
    for row in results:
        print(row)
```

Or use the connection directly:

```python
from database.db import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("INSERT INTO sets (code, name, type) VALUES (%s, %s, %s)",
                    ('ONE', 'Phyrexia: All Will Be One', 'expansion'))
```

### Test Connection

```python
from database.db import test_connection

if test_connection():
    print("Database connection successful!")
else:
    print("Database connection failed!")
```

### Detailed Documentation

For comprehensive database information including:
- Docker commands and operations
- Adding new tables to existing databases
- Troubleshooting and common issues
- Backup and restore procedures
- Schema management
- Security best practices

**See: [docs/runbooks/database.md](docs/runbooks/database.md)**

## Development

### Running the Application

```bash
uv run python main.py
```

### Project Structure

```
mtg-similarcards/
├── database/
│   ├── db.py                    # Database connection helpers
│   ├── schemas/                 # JSON schema definitions
│   └── sql/
│       ├── create_tables/       # Table creation SQL scripts
│       └── insert/              # Sample insert scripts
├── docs/
│   └── runbooks/
│       └── database.md          # Comprehensive database guide
├── docker-compose.yml           # Database container configuration
├── main.py                      # Application entry point
└── README.md                    # This file
