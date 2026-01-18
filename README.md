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

## Database Setup

This project uses PostgreSQL in a Docker container for local development.

### Quick Start

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
   - Initialize the database with your SQL schemas from `postgres/sql/create_tables/`
   - Persist data in a Docker volume

4. **Verify the database is running**
   ```bash
   docker compose ps
   ```

   You should see the `mtg-similarcards-db` container running and healthy.

### Database Configuration

Database credentials are stored in the `.env` file (not tracked in git). Default values:

- **User:** `mtguser`
- **Password:** `mtgpassword`
- **Database:** `mtg_similarcards`
- **Port:** `5432`
- **Connection String:** `postgresql://mtguser:mtgpassword@localhost:5432/mtg_similarcards`

To customize these values, edit the `.env` file.

### Database Connection in Python

The `db.py` module provides convenient connection helpers:

```python
from db import get_cursor

# Simple query
with get_cursor() as cur:
    cur.execute("SELECT * FROM sets")
    results = cur.fetchall()
    for row in results:
        print(row)
```

Or use the connection directly:

```python
from db import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("INSERT INTO sets (code, name, type) VALUES (%s, %s, %s)",
                    ('ONE', 'Phyrexia: All Will Be One', 'expansion'))
```

### Useful Docker Commands

```bash
# Start the database
docker compose up -d

# Stop the database
docker compose down

# View logs
docker compose logs -f postgres

# Access the database CLI
docker compose exec postgres psql -U mtguser -d mtg_similarcards

# Reset the database (CAUTION: deletes all data)
docker compose down -v
docker compose up -d

# Check container health
docker compose ps
```

### Database Schema

The database schema is defined in `postgres/sql/create_tables/`:

- **sets** - MTG set information
  - `code` (PRIMARY KEY) - Set code (e.g., 'ONE')
  - `name` - Full set name
  - `type` - Set type (e.g., 'expansion', 'core')
  - `release_date` - Date the set was released
  - `online_only` - Boolean flag for online-only sets

### Accessing the Database Externally

You can connect to the database using any PostgreSQL client:

- **Host:** `localhost`
- **Port:** `5432`
- **Database:** `mtg_similarcards`
- **User:** `mtguser`
- **Password:** `mtgpassword`

Popular tools:
- [pgAdmin](https://www.pgadmin.org/)
- [DBeaver](https://dbeaver.io/)
- [TablePlus](https://tableplus.com/)
- [psql](https://www.postgresql.org/docs/current/app-psql.html) (CLI)

## Development

### Running the Application

```bash
uv run python main.py
```

### Adding New SQL Tables

1. Create a new `.sql` file in `postgres/sql/create_tables/`
2. The file will be automatically executed when the database container starts
3. If the container is already running, you need to reset it:
   ```bash
   docker compose down -v
   docker compose up -d
   ```

### Testing Database Connection

```python
from db import test_connection

if test_connection():
    print("Database connection successful!")
else:
    print("Database connection failed!")
```

## Troubleshooting

### Port Already in Use

If port 5432 is already in use, you can change it in `.env`:

```env
POSTGRES_PORT=5433
```

Then update the `DATABASE_URL` accordingly.

### Container Won't Start

Check the logs:
```bash
docker compose logs postgres
```

### Cannot Connect from Python

1. Ensure the container is running: `docker compose ps`
2. Check the health status is "healthy"
3. Verify your `.env` file has the correct credentials
4. Try connecting with psql to verify the database is accessible:
   ```bash
   psql postgresql://mtguser:mtgpassword@localhost:5432/mtg_similarcards
   ```

### Reset Everything

To completely reset the database and start fresh:

```bash
docker compose down -v  # Remove containers and volumes
docker compose up -d    # Recreate everything
```
