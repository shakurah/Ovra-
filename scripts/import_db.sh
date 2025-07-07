#!/bin/bash
# 😊 OVRA AI Database Import Script
# Imports complete PostgreSQL database with pgvector embeddings and Django data

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_DIR/backend"
EXPORT_DIR="$PROJECT_DIR/db_exports"

# Default database settings (can be overridden)
DB_NAME="${DB_NAME:-ovra_ai}"
DB_USER="${DB_USER:-ovra_user}"
DB_PASSWORD="${DB_PASSWORD:-ovra_password123}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
POSTGRES_ADMIN_USER="${POSTGRES_ADMIN_USER:-postgres}"
POSTGRES_ADMIN_PASSWORD="${POSTGRES_ADMIN_PASSWORD:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_input() {
    echo -e "${BLUE}[INPUT]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to prompt for input
prompt_input() {
    local prompt="$1"
    local default="$2"
    local response
    
    if [ -n "$default" ]; then
        print_input "$prompt [$default]: "
    else
        print_input "$prompt: "
    fi
    
    read -r response
    echo "${response:-$default}"
}

# Function to prompt for password
prompt_password() {
    local prompt="$1"
    local response
    
    print_input "$prompt: "
    read -s -r response
    echo
    echo "$response"
}

# Usage function
usage() {
    echo "Usage: $0 [OPTIONS] BACKUP_FILE"
    echo
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -d, --database NAME     Database name (default: ovra_ai)"
    echo "  -u, --user NAME         Database user (default: ovra_user)"
    echo "  -p, --password PASS     Database password (default: ovra_password123)"
    echo "  -H, --host HOST         Database host (default: localhost)"
    echo "  -P, --port PORT         Database port (default: 5432)"
    echo "  --admin-user USER       PostgreSQL admin user (default: postgres)"
    echo "  --admin-password PASS   PostgreSQL admin password"
    echo "  --interactive           Interactive mode for entering credentials"
    echo "  --skip-create-db        Skip database creation (assumes it exists)"
    echo "  --skip-create-user      Skip user creation (assumes it exists)"
    echo
    echo "Examples:"
    echo "  $0 db_exports/ovra_ai_backup_20240101_120000.dump"
    echo "  $0 --interactive db_exports/ovra_ai_backup_20240101_120000.dump"
    echo "  $0 -d mydb -u myuser db_exports/ovra_ai_backup_20240101_120000.sql"
}

# Parse command line arguments
INTERACTIVE=false
SKIP_CREATE_DB=false
SKIP_CREATE_USER=false
BACKUP_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -d|--database)
            DB_NAME="$2"
            shift 2
            ;;
        -u|--user)
            DB_USER="$2"
            shift 2
            ;;
        -p|--password)
            DB_PASSWORD="$2"
            shift 2
            ;;
        -H|--host)
            DB_HOST="$2"
            shift 2
            ;;
        -P|--port)
            DB_PORT="$2"
            shift 2
            ;;
        --admin-user)
            POSTGRES_ADMIN_USER="$2"
            shift 2
            ;;
        --admin-password)
            POSTGRES_ADMIN_PASSWORD="$2"
            shift 2
            ;;
        --interactive)
            INTERACTIVE=true
            shift
            ;;
        --skip-create-db)
            SKIP_CREATE_DB=true
            shift
            ;;
        --skip-create-user)
            SKIP_CREATE_USER=true
            shift
            ;;
        -*)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
        *)
            BACKUP_FILE="$1"
            shift
            ;;
    esac
done

# Interactive mode
if [ "$INTERACTIVE" = true ]; then
    print_status "Interactive mode enabled"
    DB_NAME=$(prompt_input "Database name" "$DB_NAME")
    DB_USER=$(prompt_input "Database user" "$DB_USER")
    DB_PASSWORD=$(prompt_password "Database password")
    DB_HOST=$(prompt_input "Database host" "$DB_HOST")
    DB_PORT=$(prompt_input "Database port" "$DB_PORT")
    POSTGRES_ADMIN_USER=$(prompt_input "PostgreSQL admin user" "$POSTGRES_ADMIN_USER")
    POSTGRES_ADMIN_PASSWORD=$(prompt_password "PostgreSQL admin password")
    
    if [ -z "$BACKUP_FILE" ]; then
        echo
        print_status "Available backup files:"
        ls -la "$EXPORT_DIR"/*.dump "$EXPORT_DIR"/*.sql 2>/dev/null || print_warning "No backup files found in $EXPORT_DIR"
        echo
        BACKUP_FILE=$(prompt_input "Backup file path" "")
    fi
fi

# Validate backup file
if [ -z "$BACKUP_FILE" ]; then
    print_error "No backup file specified"
    usage
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    print_error "Backup file does not exist: $BACKUP_FILE"
    exit 1
fi

# Check required tools
print_status "Checking required tools..."
for tool in psql pg_restore createdb createuser; do
    if ! command_exists "$tool"; then
        print_error "Required tool '$tool' is not installed"
        exit 1
    fi
done

print_status "Starting OVRA AI database import..."
print_status "Backup file: $BACKUP_FILE"
print_status "Database: $DB_NAME"
print_status "User: $DB_USER"
print_status "Host: $DB_HOST"
print_status "Port: $DB_PORT"

# Check if PostgreSQL is running
if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" > /dev/null 2>&1; then
    print_error "PostgreSQL is not running or not accessible at $DB_HOST:$DB_PORT"
    exit 1
fi

print_status "PostgreSQL connection verified"

# Set admin password for PostgreSQL operations
if [ -z "$POSTGRES_ADMIN_PASSWORD" ]; then
    print_warning "No admin password provided, attempting without password"
    PGPASSWORD_ADMIN=""
else
    PGPASSWORD_ADMIN="$POSTGRES_ADMIN_PASSWORD"
fi

# Create database user if not exists
if [ "$SKIP_CREATE_USER" = false ]; then
    print_status "Creating database user '$DB_USER'..."
    
    # Check if user exists
    if PGPASSWORD="$PGPASSWORD_ADMIN" psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_ADMIN_USER" -d postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1; then
        print_warning "User '$DB_USER' already exists"
    else
        PGPASSWORD="$PGPASSWORD_ADMIN" psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_ADMIN_USER" -d postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
        if [ $? -eq 0 ]; then
            print_status "User '$DB_USER' created successfully"
        else
            print_error "Failed to create user '$DB_USER'"
            exit 1
        fi
    fi
    
    # Grant necessary privileges
    PGPASSWORD="$PGPASSWORD_ADMIN" psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_ADMIN_USER" -d postgres -c "ALTER USER $DB_USER CREATEDB;"
    PGPASSWORD="$PGPASSWORD_ADMIN" psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_ADMIN_USER" -d postgres -c "ALTER USER $DB_USER SUPERUSER;"
fi

# Create database if not exists
if [ "$SKIP_CREATE_DB" = false ]; then
    print_status "Creating database '$DB_NAME'..."
    
    # Check if database exists
    if PGPASSWORD="$PGPASSWORD_ADMIN" psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_ADMIN_USER" -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
        print_warning "Database '$DB_NAME' already exists"
        print_input "Drop and recreate database? (y/N): "
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            print_status "Dropping existing database..."
            PGPASSWORD="$PGPASSWORD_ADMIN" psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_ADMIN_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
        else
            print_warning "Using existing database"
        fi
    fi
    
    # Create database if it doesn't exist
    if ! PGPASSWORD="$PGPASSWORD_ADMIN" psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_ADMIN_USER" -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
        PGPASSWORD="$PGPASSWORD_ADMIN" psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_ADMIN_USER" -d postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
        if [ $? -eq 0 ]; then
            print_status "Database '$DB_NAME' created successfully"
        else
            print_error "Failed to create database '$DB_NAME'"
            exit 1
        fi
    fi
fi

# Install pgvector extension
print_status "Installing pgvector extension..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS vector;"
if [ $? -eq 0 ]; then
    print_status "pgvector extension installed successfully"
else
    print_warning "Failed to install pgvector extension (it may already be installed or not available)"
fi

# Install other common extensions
print_status "Installing additional extensions..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;" 2>/dev/null || true
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS btree_gin;" 2>/dev/null || true
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS unaccent;" 2>/dev/null || true

# Determine backup file format
BACKUP_FORMAT=""
if [[ "$BACKUP_FILE" == *.dump ]]; then
    BACKUP_FORMAT="custom"
elif [[ "$BACKUP_FILE" == *.sql ]]; then
    BACKUP_FORMAT="sql"
elif [[ "$BACKUP_FILE" == *.tar.gz ]]; then
    print_status "Extracting compressed backup..."
    TEMP_DIR=$(mktemp -d)
    tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"
    
    # Find the main dump file
    DUMP_FILE=$(find "$TEMP_DIR" -name "*.dump" | head -1)
    if [ -n "$DUMP_FILE" ]; then
        BACKUP_FILE="$DUMP_FILE"
        BACKUP_FORMAT="custom"
    else
        SQL_FILE=$(find "$TEMP_DIR" -name "*.sql" | head -1)
        if [ -n "$SQL_FILE" ]; then
            BACKUP_FILE="$SQL_FILE"
            BACKUP_FORMAT="sql"
        else
            print_error "No valid backup file found in compressed archive"
            exit 1
        fi
    fi
fi

# Import database
print_status "Importing database from $BACKUP_FILE..."
print_status "Format: $BACKUP_FORMAT"

if [ "$BACKUP_FORMAT" = "custom" ]; then
    # Use pg_restore for custom format
    PGPASSWORD="$DB_PASSWORD" pg_restore \
        --host="$DB_HOST" \
        --port="$DB_PORT" \
        --username="$DB_USER" \
        --dbname="$DB_NAME" \
        --verbose \
        --clean \
        --no-owner \
        --no-privileges \
        "$BACKUP_FILE"
elif [ "$BACKUP_FORMAT" = "sql" ]; then
    # Use psql for SQL format
    PGPASSWORD="$DB_PASSWORD" psql \
        --host="$DB_HOST" \
        --port="$DB_PORT" \
        --username="$DB_USER" \
        --dbname="$DB_NAME" \
        --file="$BACKUP_FILE"
else
    print_error "Unknown backup format"
    exit 1
fi

if [ $? -eq 0 ]; then
    print_status "Database import completed successfully"
else
    print_error "Database import failed"
    exit 1
fi

# Import Django fixtures if available
FIXTURES_FILE="${BACKUP_FILE%.*}_fixtures.json"
if [ -f "$FIXTURES_FILE" ]; then
    print_status "Found Django fixtures file: $FIXTURES_FILE"
    print_status "Importing Django fixtures..."
    
    cd "$BACKEND_DIR"
    
    # Activate virtual environment if it exists
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        print_status "Virtual environment activated"
    fi
    
    # Load fixtures
    python manage.py loaddata "$FIXTURES_FILE"
    
    if [ $? -eq 0 ]; then
        print_status "Django fixtures imported successfully"
    else
        print_warning "Django fixtures import failed (this is optional)"
    fi
else
    print_warning "No Django fixtures file found, skipping fixtures import"
fi

# Run Django migrations to ensure database is up to date
print_status "Running Django migrations..."
cd "$BACKEND_DIR"

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

python manage.py migrate --fake-initial 2>/dev/null || python manage.py migrate

if [ $? -eq 0 ]; then
    print_status "Django migrations completed successfully"
else
    print_warning "Django migrations failed (this may be expected)"
fi

# Verify import
print_status "Verifying database import..."
TABLE_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d '[:space:]')
EXTENSION_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM pg_extension;" 2>/dev/null | tr -d '[:space:]')

print_status "Import verification:"
print_status "  - Tables in database: $TABLE_COUNT"
print_status "  - Extensions installed: $EXTENSION_COUNT"

# Check for pgvector extension specifically
if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT 1 FROM pg_extension WHERE extname='vector';" 2>/dev/null | grep -q 1; then
    print_status "  - pgvector extension: ✓ Installed"
else
    print_warning "  - pgvector extension: ✗ Not found"
fi

# Clean up temporary files
if [ -n "$TEMP_DIR" ] && [ -d "$TEMP_DIR" ]; then
    rm -rf "$TEMP_DIR"
    print_status "Cleaned up temporary files"
fi

print_status "Database import completed successfully!"
print_status "Database: $DB_NAME"
print_status "User: $DB_USER"
print_status "Host: $DB_HOST"
print_status "Port: $DB_PORT"

print_warning "Remember to:"
print_warning "1. Update your Django settings.py with the correct database credentials"
print_warning "2. Test the application to ensure everything works correctly"
print_warning "3. Run any additional setup scripts if required"
print_warning "4. Update environment variables if needed"

echo
print_status "Import completed at $(date)"