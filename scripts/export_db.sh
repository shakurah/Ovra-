#!/bin/bash
# 😊 OVRA AI Database Export Script
# Exports complete PostgreSQL database with pgvector embeddings and Django data

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_DIR/backend"
EXPORT_DIR="$PROJECT_DIR/db_exports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
EXPORT_FILE="ovra_ai_backup_${TIMESTAMP}"

# Database settings from Django settings
DB_NAME="ovra_ai"
DB_USER="ovra_user"
DB_PASSWORD="ovra_password123"
DB_HOST="localhost"
DB_PORT="5432"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Create export directory
mkdir -p "$EXPORT_DIR"

print_status "Starting OVRA AI database export..."
print_status "Export directory: $EXPORT_DIR"
print_status "Database: $DB_NAME"
print_status "Timestamp: $TIMESTAMP"

# Check if PostgreSQL is running
if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; then
    print_error "PostgreSQL is not running or not accessible"
    exit 1
fi

# Check if database exists
if ! PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\q" 2>/dev/null; then
    print_error "Database '$DB_NAME' does not exist or cannot be accessed"
    exit 1
fi

print_status "Database connection verified"

# Export database schema and data including pgvector extension
print_status "Exporting database schema and data..."
PGPASSWORD="$DB_PASSWORD" pg_dump \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --username="$DB_USER" \
    --dbname="$DB_NAME" \
    --verbose \
    --clean \
    --no-owner \
    --no-privileges \
    --format=custom \
    --compress=9 \
    --file="$EXPORT_DIR/${EXPORT_FILE}.dump"

if [ $? -eq 0 ]; then
    print_status "Database dump completed successfully"
else
    print_error "Database dump failed"
    exit 1
fi

# Also create a plain SQL dump for compatibility
print_status "Creating plain SQL dump..."
PGPASSWORD="$DB_PASSWORD" pg_dump \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --username="$DB_USER" \
    --dbname="$DB_NAME" \
    --verbose \
    --clean \
    --no-owner \
    --no-privileges \
    --format=plain \
    --file="$EXPORT_DIR/${EXPORT_FILE}.sql"

if [ $? -eq 0 ]; then
    print_status "SQL dump completed successfully"
else
    print_error "SQL dump failed"
    exit 1
fi

# Export Django fixtures for additional safety
print_status "Exporting Django fixtures..."
cd "$BACKEND_DIR"

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    print_status "Virtual environment activated"
fi

# Export all Django data as JSON fixtures
python manage.py dumpdata \
    --natural-foreign \
    --natural-primary \
    --indent=2 \
    --output="$EXPORT_DIR/${EXPORT_FILE}_fixtures.json"

if [ $? -eq 0 ]; then
    print_status "Django fixtures exported successfully"
else
    print_warning "Django fixtures export failed (this is optional)"
fi

# Export specific models that might have embeddings
print_status "Exporting RAG app data..."
python manage.py dumpdata rag_app \
    --natural-foreign \
    --natural-primary \
    --indent=2 \
    --output="$EXPORT_DIR/${EXPORT_FILE}_rag_data.json" 2>/dev/null || true

# Create a metadata file with export information
print_status "Creating metadata file..."
cat > "$EXPORT_DIR/${EXPORT_FILE}_metadata.txt" << EOF
OVRA AI Database Export Metadata
================================
Export Date: $(date)
Database Name: $DB_NAME
Database User: $DB_USER
Database Host: $DB_HOST
Database Port: $DB_PORT
Export Files:
- ${EXPORT_FILE}.dump (Custom format with compression)
- ${EXPORT_FILE}.sql (Plain SQL format)
- ${EXPORT_FILE}_fixtures.json (Django fixtures)
- ${EXPORT_FILE}_rag_data.json (RAG app specific data)

PostgreSQL Version: $(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT version();" 2>/dev/null | head -1)

Extensions in database:
$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT extname FROM pg_extension;" 2>/dev/null)

Database Size: $(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" 2>/dev/null)
EOF

# Compress all export files
print_status "Compressing export files..."
cd "$EXPORT_DIR"
tar -czf "${EXPORT_FILE}_complete.tar.gz" "${EXPORT_FILE}"* 2>/dev/null || {
    print_warning "Failed to create compressed archive, but individual files are available"
}

# Calculate file sizes
print_status "Export Summary:"
echo "=================="
ls -lh "$EXPORT_DIR/${EXPORT_FILE}"* 2>/dev/null || true

print_status "Database export completed successfully!"
print_status "Export location: $EXPORT_DIR"
print_status "Main files:"
print_status "  - ${EXPORT_FILE}.dump (PostgreSQL custom format)"
print_status "  - ${EXPORT_FILE}.sql (Plain SQL format)"
print_status "  - ${EXPORT_FILE}_fixtures.json (Django data)"
print_status "  - ${EXPORT_FILE}_complete.tar.gz (All files compressed)"

print_warning "Remember to:"
print_warning "1. Test the export by importing to a test database"
print_warning "2. Store the export securely"
print_warning "3. The export includes all embeddings and vector data"
print_warning "4. Database password is included in this script - handle securely"

echo
print_status "Export completed at $(date)"