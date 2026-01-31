.PHONY: help run-main run-insert db-up db-down db-logs db-shell db-reset test-connection install install-dev clean

# Default target - show help
help:
	@echo "Available targets:"
	@echo ""
	@echo "  Database Operations:"
	@echo "    db-up            - Start PostgreSQL database container"
	@echo "    db-down          - Stop PostgreSQL database container"
	@echo "    db-logs          - View database container logs"
	@echo "    db-shell         - Connect to PostgreSQL shell"
	@echo "    db-reset         - Stop database and remove volume (fresh start)"
	@echo "    test-connection  - Test database connection"
	@echo ""
	@echo "  Data Operations:"
	@echo "    run-insert       - Run example insert script (sets PYTHONPATH)"
	@echo ""
	@echo "  Application:"
	@echo "    run-main         - Run main application (sets PYTHONPATH)"
	@echo ""
	@echo "  Python Environment:"
	@echo "    install          - Install project in editable mode"
	@echo "    install-dev      - Install with development dependencies"
	@echo "    clean            - Remove Python cache files"
	@echo ""

# Database management
db-up:
	@echo "Starting PostgreSQL database..."
	docker-compose up -d postgres
	@echo "Waiting for database to be ready..."
	@sleep 5
	docker-compose exec postgres pg_isready -U mtguser -d mtgcards_db

db-down:
	@echo "Stopping PostgreSQL database..."
	docker-compose down

db-logs:
	docker-compose logs -f postgres

db-shell:
	@echo "Connecting to PostgreSQL shell..."
	docker-compose exec postgres psql -U mtguser -d mtgcards_db

db-reset:
	@echo "Warning: This will delete all database data!"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	docker-compose down -v
	@echo "Database reset complete. Run 'make db-up' to start fresh."

test-connection:
	@echo "Testing database connection..."
	PYTHONPATH=$(shell pwd) uv run python -c "from src.database.db import test_connection; exit(0 if test_connection() else 1)"

# Application
run-main:
	@echo "Running main application..."
	PYTHONPATH=$(shell pwd) uv run python src/app/main.py

# Data operations
run-insert:
	@echo "Running example insert script..."
	PYTHONPATH=$(shell pwd) uv run python src/database/sql/upsert/example_upsert.py

# Python environment
	
install:
	@echo "Installing project in editable mode..."
	pip install -e .

install-dev:
	@echo "Installing project with development dependencies..."
	pip install -e ".[dev]"

clean:
	@echo "Cleaning Python cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
