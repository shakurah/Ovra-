#!/bin/bash
# 😊 OVRA AI Simple Database Export Script
# Exports complete PostgreSQL database to a single compressed file

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
EXPORT_DIR="$PROJECT_DIR/db_exports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
EXPORT_FILE="ovra_ai_complete_${TIMESTAMP}"

# Database settings
DB_NAME="ovra_ai"
DB_USER="ovra_user"
DB_PASSWORD="ovra_password123"
DB_HOST="localhost"
DB_PORT="5432"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create export directory
mkdir -p "$EXPORT_DIR"

print_status "Starting OVRA AI complete database export..."
print_status "Export file: ${EXPORT_FILE}.dump"
print_status "Location: $EXPORT_DIR"

# Check database connection
if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; then
    print_error "PostgreSQL is not running or not accessible"
    exit 1
fi

print_status "Database connection verified"

# Export everything to single compressed custom format file
print_status "Exporting complete database (this may take a few minutes)..."
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
    print_status "Export completed successfully!"
    
    # Show file info
    FILE_SIZE=$(ls -lh "$EXPORT_DIR/${EXPORT_FILE}.dump" | awk '{print $5}')
    print_status "Export file size: $FILE_SIZE"
    print_status "Export location: $EXPORT_DIR/${EXPORT_FILE}.dump"
    
    # Create info file
    cat > "$EXPORT_DIR/${EXPORT_FILE}_info.txt" << EOF
OVRA AI Complete Database Export
===============================
Export Date: $(date)
Database: $DB_NAME
File: ${EXPORT_FILE}.dump
Size: $FILE_SIZE

This file contains:
- Complete database schema
- All table data including embeddings
- pgvector extension
- All user accounts and permissions
- All Django models and relationships

To import on new server:
./scripts/import_db.sh ${EXPORT_FILE}.dump
EOF
    
    print_status "Export info saved to: ${EXPORT_FILE}_info.txt"
    print_status "Ready for migration to new server!"
else
    print_error "Export failed!"
    exit 1
fi