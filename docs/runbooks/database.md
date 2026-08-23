# Database Runbook

## Overview

This project uses PostgreSQL 16 with the `pgvector` extension, running in a Docker container. The database is configured via `docker-compose.yml` and uses persistent volumes to store data.

**Key Components:**
- **Container:** `mtg-similarcards-db`
- **Image:** `pgvector/pgvector:pg16`
- **Data Volume:** `postgres_data` (persists database data)
- **Init Scripts:** `./src/database/sql/create_tables/` mounted to `/docker-entrypoint-initdb.d`

## Database Configuration

Default environment variables (can be overridden in `.env`):
- `POSTGRES_USER`: mtguser
- `POSTGRES_PASSWORD`: mtgpassword
- `POSTGRES_DB`: mtgcards_db
- `POSTGRES_PORT`: 5432

## Initial Database Setup

When you first run `docker-compose up`, PostgreSQL automatically:

1. Creates an empty database using the volume `postgres_data`
2. Executes all SQL scripts in `/docker-entrypoint-initdb.d` (alphabetically)
3. These scripts only run **once** during initial database creation

Currently initialized tables:
- `sets` - MTG set information
- `cards` - MTG card data
- `card_images` - Cached card artwork (FK to `cards.id`)

## Important: docker-entrypoint-initdb.d Behavior

⚠️ **Critical Understanding:**

The `/docker-entrypoint-initdb.d` directory has special behavior:
- Scripts **ONLY execute when the database is first initialized**
- This happens when the volume is **empty** (first run)
- Once the volume contains data, these scripts are **completely ignored**

### What This Means

**If you add a new SQL file to `src/database/sql/create_tables/`:**
- Running `docker-compose up` will **NOT** execute the new script
- Your existing tables and data remain **completely untouched**
- The new SQL file will sit there unused until the database is recreated

**Your data is safe!** Adding new table files will NOT overwrite your existing database.

### Script Order Matters — Use a Numeric Prefix

Scripts execute in **lexicographic order**, not dependency order. Any file that
declares a `REFERENCES other_table(...)` foreign key must sort *after* the file
creating that table. Hence the numeric prefixes:

```
00_extensions.sql     CREATE EXTENSION vector
01_sets.sql
02_cards.sql
03_card_images.sql    REFERENCES cards(id)  -> must come after 02_
```

Note that `IF NOT EXISTS` does **not** protect you here — it guards against the
table existing, but a `REFERENCES` clause still has to resolve its target
immediately.

**When adding a table, give it the next free prefix, placed after anything it
references.** Without a prefix, `card_images.sql` would sort *before*
`cards.sql` (`_` = 0x5F sorts before `s` = 0x73) and init would fail.

### ⚠️ A Failed Init Poisons the Volume Permanently

Init scripts run under `ON_ERROR_STOP=1`, and PGDATA is initialized **before**
they run. So if any script errors:

1. Init aborts — every remaining script is skipped
2. But the data directory is already initialized, so the volume looks valid
3. Every later start logs `Skipping initialization` and **never retries**
4. Postgres starts, reports **healthy**, and accepts connections normally

The result is a database that passes the healthcheck and answers `SELECT 1`
while containing no tables. Applications only discover this at their first real
query — e.g. `relation "sets" does not exist` from the sets ETL.

**Rebuilding the image does not fix this.** `postgres_data` is a named volume
with a lifecycle independent of images and containers; it survives
`docker-compose build` and plain `docker-compose down`. Recovery requires
dropping the volume:

```bash
make db-reset          # runs: docker-compose down -v
docker-compose up -d postgres
docker-compose logs postgres   # verify: no "ERROR:", no "Skipping initialization"
```

To confirm init actually succeeded rather than trusting the healthcheck:

```bash
docker exec mtg-similarcards-db psql -U mtguser -d mtgcards_db -c '\dt'
```

## Adding New Tables to Existing Database

Since `docker-entrypoint-initdb.d` scripts don't run on existing databases, use one of these methods:

### Option 1: Manual Execution (Recommended)

Execute the SQL file manually in the running container:

```bash
# Method A: Execute SQL file directly
docker exec -i mtg-similarcards-db psql -U mtguser -d mtgcards_db < src/database/sql/create_tables/your_new_table.sql

# Method B: Interactive psql session
docker exec -it mtg-similarcards-db psql -U mtguser -d mtgcards_db
# Then paste your SQL or use \i to import files
```

**Pros:**
- Quick and simple
- No data loss
- Full control over execution

**Cons:**
- Manual process
- No automatic version tracking
- Easy to forget which changes were applied

### Option 2: Database Migration Tool (Best for Production)

Use a migration tool like Alembic, Flyway, or custom Python scripts:

```bash
# Example with Alembic
pip install alembic psycopg2-binary

# Initialize migrations
alembic init migrations

# Create migration
alembic revision -m "add new table"

# Apply migration
alembic upgrade head
```

**Pros:**
- Version controlled schema changes
- Rollback capability
- Automatic tracking of applied migrations
- Team-friendly (everyone applies same migrations)

**Cons:**
- Initial setup required
- Learning curve
- More complex than manual execution

### Option 3: Recreate Database (Nuclear Option)

⚠️ **WARNING: This deletes ALL existing data!**

```bash
# Stop and remove containers AND volumes
docker-compose down -v

# Start fresh - all SQL files in create_tables/ will execute
docker-compose up -d
```

**When to use:**
- Development only
- Starting fresh with new schema
- You have backups or don't need existing data

**NEVER use in production or with important data!**

## Common Database Operations

### Connect to Database

```bash
# Interactive psql session
docker exec -it mtg-similarcards-db psql -U mtguser -d mtgcards_db

# Execute single query
docker exec -it mtg-similarcards-db psql -U mtguser -d mtgcards_db -c "SELECT * FROM sets LIMIT 5;"

# Connect from host (if port 5432 is exposed)
psql -h localhost -U mtguser -d mtgcards_db
```

### View Tables

```sql
-- List all tables
\dt

-- Describe table structure
\d table_name

-- Show table with indexes and constraints
\d+ table_name
```

### Backup Database

```bash
# Backup entire database
docker exec mtg-similarcards-db pg_dump -U mtguser mtgcards_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup specific table
docker exec mtg-similarcards-db pg_dump -U mtguser -t sets mtgcards_db > sets_backup.sql
```

### Restore Database

```bash
# Restore from backup
docker exec -i mtg-similarcards-db psql -U mtguser -d mtgcards_db < backup.sql
```

### View Database Logs

```bash
# View container logs
docker logs mtg-similarcards-db

# Follow logs in real-time
docker logs -f mtg-similarcards-db
```

## Troubleshooting

### Database Won't Start

Check container status:
```bash
docker-compose ps
docker logs mtg-similarcards-db
```

Common issues:
- Port 5432 already in use
- Invalid credentials in `.env`
- Volume permission issues

### New SQL File Not Executing

**This is expected behavior!** See "docker-entrypoint-initdb.d Behavior" above.

Solutions:
- Use Option 1, 2, or 3 from "Adding New Tables to Existing Database"

### Connection Refused

Verify:
1. Container is running: `docker-compose ps`
2. Health check passes: `docker inspect mtg-similarcards-db`
3. Port mapping is correct in `docker-compose.yml`

### Data Disappeared

If you ran `docker-compose down -v`, the volume was deleted.

**Prevention:**
- Never use `-v` flag unless you want to delete data
- Regular backups (see Backup section)
- Use `docker-compose down` (without `-v`) to preserve data

## Database Schema Changes Workflow

Recommended workflow for schema changes:

1. **Create SQL file** in appropriate directory
2. **Test locally** using Option 1 (manual execution)
3. **Document change** in migration notes or commit message
4. **For production:** Use Option 2 (migration tool) for tracked changes
5. **Backup** before applying changes to production

## Health Checks

The container includes a health check that runs every 10 seconds:

```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' mtg-similarcards-db

# View health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' mtg-similarcards-db
```

## Security Notes

- **Don't commit** `.env` files with real credentials
- Use strong passwords in production
- Limit database port exposure (don't expose to internet)
- Regular backups are essential
- Consider read-only users for reporting queries

## Quick Reference

```bash
# Start database
docker-compose up -d

# Stop database (preserves data)
docker-compose down

# Reset database (DELETES DATA!)
docker-compose down -v && docker-compose up -d

# Connect to database
docker exec -it mtg-similarcards-db psql -U mtguser -d mtgcards_db

# Add new table manually
docker exec -i mtg-similarcards-db psql -U mtguser -d mtgcards_db < path/to/new_table.sql

# Backup
docker exec mtg-similarcards-db pg_dump -U mtguser mtgcards_db > backup.sql

# Restore
docker exec -i mtg-similarcards-db psql -U mtguser -d mtgcards_db < backup.sql
