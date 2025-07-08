const fs = require('fs');
const path = require('path');
const pool = require('../config/database');

class MigrationRunner {
  constructor() {
    this.migrationsPath = path.join(__dirname, '../../migrations');
  }

  async createMigrationsTable() {
    await pool.query(`
      CREATE TABLE IF NOT EXISTS migrations (
        id SERIAL PRIMARY KEY,
        filename VARCHAR(255) NOT NULL UNIQUE,
        executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);
  }

  async getExecutedMigrations() {
    const result = await pool.query('SELECT filename FROM migrations ORDER BY id');
    return result.rows.map(row => row.filename);
  }

  async runMigration(filename) {
    const filePath = path.join(this.migrationsPath, filename);
    const sql = fs.readFileSync(filePath, 'utf8');
    
    await pool.query('BEGIN');
    try {
      await pool.query(sql);
      await pool.query('INSERT INTO migrations (filename) VALUES ($1)', [filename]);
      await pool.query('COMMIT');
      console.log(`Migration ${filename} executed successfully`);
    } catch (error) {
      await pool.query('ROLLBACK');
      throw error;
    }
  }

  async run() {
    await this.createMigrationsTable();
    
    const executedMigrations = await this.getExecutedMigrations();
    const migrationFiles = fs.readdirSync(this.migrationsPath)
      .filter(file => file.endsWith('.sql'))
      .sort();

    for (const file of migrationFiles) {
      if (!executedMigrations.includes(file)) {
        await this.runMigration(file);
      }
    }
    
    console.log('All migrations completed');
  }
}

if (require.main === module) {
  const runner = new MigrationRunner();
  runner.run().catch(console.error).finally(() => process.exit());
}

module.exports = MigrationRunner;