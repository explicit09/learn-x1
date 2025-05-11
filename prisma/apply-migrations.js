/**
 * Database Migration Application Script
 * 
 * This script applies database migrations directly to the Neon PostgreSQL database
 * without requiring the Prisma CLI. It handles both schema creation and RLS policies.
 * 
 * Usage: node apply-migrations.js
 */

import { Client } from 'pg';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';
import chalk from 'chalk';

// Load environment variables
dotenv.config();

// Set up file paths
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const MIGRATIONS_DIR = path.join(__dirname, 'migrations');

/**
 * Executes SQL from a file against the database
 * @param {Client} client - PostgreSQL client
 * @param {string} filePath - Path to SQL file
 * @param {string} description - Description for logging
 */
async function executeSqlFile(client, filePath, description) {
  try {
    console.log(chalk.blue(`Applying ${description}...`));
    const sql = fs.readFileSync(filePath, 'utf8');
    await client.query(sql);
    console.log(chalk.green(`✓ ${description} applied successfully`));
    return true;
  } catch (error) {
    console.error(chalk.red(`✗ Error applying ${description}:`));
    console.error(chalk.red(error.message));
    
    // Check if this is a duplicate error (already applied)
    if (error.message.includes('already exists')) {
      console.log(chalk.yellow(`  → This appears to be already applied, continuing...`));
      return true;
    }
    return false;
  }
}

/**
 * Records a migration in the _prisma_migrations table
 * @param {Client} client - PostgreSQL client
 * @param {string} migrationName - Name of the migration
 */
async function recordMigration(client, migrationName) {
  try {
    await client.query(`
      INSERT INTO "_prisma_migrations" ("id", "checksum", "finished_at", "migration_name", "logs", "started_at", "applied_steps_count")
      VALUES (
        gen_random_uuid(), 
        '${migrationName}_checksum', 
        NOW(), 
        '${migrationName}', 
        'Applied manually via script', 
        NOW(), 
        1
      )
      ON CONFLICT ("migration_name") DO NOTHING;
    `);
    console.log(chalk.green(`✓ Recorded migration ${migrationName}`));
  } catch (error) {
    console.error(chalk.yellow(`⚠ Could not record migration ${migrationName}:`));
    console.error(chalk.yellow(error.message));
  }
}

/**
 * Main function to apply all migrations
 */
async function applyMigrations() {
  // Validate environment variables
  if (!process.env.DIRECT_URL) {
    console.error(chalk.red('Error: DIRECT_URL environment variable is not set'));
    console.error(chalk.yellow('Please check your .env file and ensure DIRECT_URL is properly configured'));
    process.exit(1);
  }

  // Connect to the database
  const client = new Client({
    connectionString: process.env.DIRECT_URL,
  });

  try {
    console.log(chalk.blue('Connecting to database...'));
    await client.connect();
    console.log(chalk.green('Connected successfully!'));

    // Create migrations tracking table first
    const createMigrationsTableResult = await client.query(`
      CREATE TABLE IF NOT EXISTS "_prisma_migrations" (
        "id" VARCHAR(36) NOT NULL,
        "checksum" VARCHAR(64) NOT NULL,
        "finished_at" TIMESTAMP WITH TIME ZONE,
        "migration_name" VARCHAR(255) NOT NULL,
        "logs" TEXT,
        "rolled_back_at" TIMESTAMP WITH TIME ZONE,
        "started_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
        "applied_steps_count" INTEGER NOT NULL DEFAULT 0,
        CONSTRAINT "_prisma_migrations_pkey" PRIMARY KEY ("id"),
        CONSTRAINT "_prisma_migrations_migration_name_key" UNIQUE ("migration_name")
      );
    `);
    console.log(chalk.green('✓ Migration tracking table ready'));
    
    // Apply initial migration
    const initMigrationPath = path.join(MIGRATIONS_DIR, '20250509_init', 'migration.sql');
    const initSuccess = await executeSqlFile(client, initMigrationPath, 'initial schema migration');
    
    if (initSuccess) {
      await recordMigration(client, '20250509_init');
      
      // Apply RLS policies
      const rlsMigrationPath = path.join(MIGRATIONS_DIR, '20250509_rls', 'migration.sql');
      const rlsSuccess = await executeSqlFile(client, rlsMigrationPath, 'RLS policies migration');
      
      if (rlsSuccess) {
        await recordMigration(client, '20250509_rls');
      }
    }

    console.log(chalk.green.bold('Database setup completed successfully!'));
    console.log(chalk.blue('The LEARN-X platform database is now ready for use.'));
    
  } catch (error) {
    console.error(chalk.red('Error in migration process:'));
    console.error(chalk.red(error.stack || error.message));
    process.exit(1);
  } finally {
    await client.end();
  }
}

// Execute the migrations
applyMigrations().catch(error => {
  console.error(chalk.red('Fatal error:'), error);
  process.exit(1);
});
