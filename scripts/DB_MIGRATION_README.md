# 😊 OVRA AI Database Migration Scripts

This directory contains scripts for complete database export and import operations for the OVRA AI system, including pgvector embeddings and all Django data.

## Scripts Overview

### 🔄 export_db.sh
Exports the complete PostgreSQL database with:
- **Full schema and data** (including pgvector embeddings)
- **Multiple formats**: Custom compressed dump + plain SQL
- **Django fixtures** for additional safety
- **RAG app specific data** for embeddings
- **Metadata file** with export information
- **Compressed archive** of all files

### 🔄 import_db.sh
Imports the complete database with:
- **Automatic database/user creation**
- **pgvector extension installation**
- **Multiple format support** (custom dump, SQL, compressed)
- **Django fixtures loading**
- **Migration execution**
- **Interactive and automated modes**

## Quick Start

### Export Database
```bash
# Simple export
./scripts/export_db.sh

# Files created in db_exports/:
# - ovra_ai_backup_TIMESTAMP.dump (main backup)
# - ovra_ai_backup_TIMESTAMP.sql (SQL format)
# - ovra_ai_backup_TIMESTAMP_fixtures.json (Django data)
# - ovra_ai_backup_TIMESTAMP_complete.tar.gz (all files)
```

### Import Database
```bash
# Interactive mode (recommended for first-time setup)
./scripts/import_db.sh --interactive backup_file.dump

# Quick import with defaults
./scripts/import_db.sh db_exports/ovra_ai_backup_20240101_120000.dump

# Custom database settings
./scripts/import_db.sh -d new_db -u new_user -p new_password backup_file.dump
```

## Export Script Features

### 📊 What Gets Exported
- Complete PostgreSQL database with all tables
- pgvector extension and vector embeddings
- All Django models and data
- User accounts and permissions
- RAG app documents and embeddings
- Database metadata and version info

### 📁 Export Formats
- **Custom format (.dump)**: Compressed binary format (recommended)
- **SQL format (.sql)**: Plain text SQL commands
- **Django fixtures (.json)**: Django-specific data export
- **Compressed archive (.tar.gz)**: All files in one archive

### 🔧 Configuration
The script reads database settings from Django settings.py:
- Database: `ovra_ai`
- User: `ovra_user`
- Password: `ovra_password123`
- Host: `localhost`
- Port: `5432`

## Import Script Features

### 🛠️ What Gets Imported
- Complete database structure and data
- pgvector extension (automatically installed)
- All Django models and relationships
- User accounts and permissions
- Vector embeddings and RAG data

### 🎯 Import Modes
- **Interactive mode**: Prompts for all settings
- **Automated mode**: Uses command-line arguments
- **Flexible format**: Supports .dump, .sql, .tar.gz files

### 🔧 Advanced Options
```bash
# Show all options
./scripts/import_db.sh --help

# Skip database creation (if exists)
./scripts/import_db.sh --skip-create-db backup_file.dump

# Skip user creation (if exists)
./scripts/import_db.sh --skip-create-user backup_file.dump

# Custom PostgreSQL admin credentials
./scripts/import_db.sh --admin-user postgres --admin-password admin123 backup_file.dump
```

## Usage Examples

### 🔄 Complete Migration Workflow
```bash
# 1. Export from source server
./scripts/export_db.sh

# 2. Copy export files to target server
scp db_exports/ovra_ai_backup_*_complete.tar.gz user@target-server:/path/to/ovra_ai/

# 3. Import on target server
./scripts/import_db.sh --interactive db_exports/ovra_ai_backup_*_complete.tar.gz
```

### 🔧 Development Setup
```bash
# Create development database from production export
./scripts/import_db.sh -d ovra_ai_dev -u dev_user -p dev_password production_backup.dump
```

### 🚀 Production Deployment
```bash
# Import with custom settings
./scripts/import_db.sh \
  -d ovra_ai_prod \
  -u ovra_prod_user \
  -p secure_password \
  -H production-db.example.com \
  -P 5432 \
  backup_file.dump
```

## Requirements

### 📋 System Requirements
- PostgreSQL client tools (`psql`, `pg_dump`, `pg_restore`)
- Python 3.x with Django environment
- pgvector extension (for target database)
- Sufficient disk space for exports

### 🔐 Permissions Required
- **Export**: Read access to source database
- **Import**: Superuser access to create databases and users
- **File system**: Write access to export directory

## Security Notes

### 🔒 Important Security Considerations
- Scripts contain database passwords - handle securely
- Export files contain sensitive data - encrypt in transit
- Use strong passwords for production databases
- Limit file access permissions (600 recommended)
- Store exports in secure locations

### 🛡️ Best Practices
```bash
# Set secure permissions on export files
chmod 600 db_exports/*

# Use environment variables for passwords
export DB_PASSWORD="secure_password"
export POSTGRES_ADMIN_PASSWORD="admin_password"
```

## Troubleshooting

### ❌ Common Issues

**Export fails with "permission denied"**
- Check database user permissions
- Verify PostgreSQL is running
- Ensure export directory is writable

**Import fails with "extension not found"**
- Install pgvector extension: `sudo apt-get install postgresql-15-pgvector`
- Check PostgreSQL version compatibility
- Verify extension is available: `SELECT * FROM pg_available_extensions WHERE name='vector';`

**Django migrations fail**
- Run migrations manually: `python manage.py migrate`
- Check Django settings configuration
- Verify virtual environment is activated

### 🔍 Debug Mode
Add `set -x` to script for detailed execution logs:
```bash
# Add to top of script after set -e
set -x
```

## File Structure

```
scripts/
├── export_db.sh          # Database export script
├── import_db.sh          # Database import script
└── DB_MIGRATION_README.md # This documentation

db_exports/              # Created by export script
├── ovra_ai_backup_TIMESTAMP.dump
├── ovra_ai_backup_TIMESTAMP.sql
├── ovra_ai_backup_TIMESTAMP_fixtures.json
├── ovra_ai_backup_TIMESTAMP_rag_data.json
├── ovra_ai_backup_TIMESTAMP_metadata.txt
└── ovra_ai_backup_TIMESTAMP_complete.tar.gz
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify all requirements are met
3. Test with a small database first
4. Check PostgreSQL and Django logs for errors

---

*Generated for OVRA AI - Spanish Tax Law Consultation System*
EOF < /dev/null
