-- Migration: {{description}}
-- Revision: {{revision}}                 -- e.g. 91a2b3c4d5e6
-- Down Revision: {{down_revision}}       -- e.g. previous revision id or None
-- Created: {{date}}                      -- ISO8601
-- Author: {{author}}
-- Dialect: {{dialect}}                   -- e.g. sqlite, postgresql

-- Notes:
--  - This template is intended as a SQL-first migration snippet you can embed
--    into an Alembic revision (or run directly against the DB for quick tests).
--  - Keep schema and heavy data migrations separate where possible.
--  - For SQLite, some ALTER operations are limited; use the recommended
--    create-temp-table / copy / drop / rename pattern when modifying columns.

-- =====================
-- UP (apply migration)
-- =====================
BEGIN;

-- Safety: check DB dialect if you need dialect-specific statements
-- Example (Postgres only):
-- DO $$ BEGIN
--   -- place plpgsql checks or helper statements here
-- END $$;

-- Example: create a new table (idempotent)
-- CREATE TABLE IF NOT EXISTS tasks (
--   id INTEGER PRIMARY KEY,
--   title TEXT NOT NULL,
--   description TEXT,
--   completed BOOLEAN NOT NULL DEFAULT FALSE,
--   priority TEXT NOT NULL DEFAULT 'MEDIUM',
--   created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
-- );

-- Example: add a column (Postgres)
-- ALTER TABLE tasks ADD COLUMN IF NOT EXISTS priority TEXT DEFAULT 'MEDIUM';

-- Example: add a column for SQLite (works across SQLite versions)
-- ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT 'MEDIUM';
-- Note: removing columns in SQLite requires table recreation (see DOWN section).

-- Example: backfill data after schema change (do this in a separate transaction
-- if the update touches many rows or requires special locking):
-- UPDATE tasks SET priority = 'MEDIUM' WHERE priority IS NULL;

COMMIT;


-- =====================
-- DOWN (revert migration)
-- =====================
BEGIN;

-- Reverse: drop the column (Postgres)
-- ALTER TABLE tasks DROP COLUMN IF EXISTS priority;

-- Reverse: drop the table (idempotent)
-- DROP TABLE IF EXISTS tasks;

-- SQLite reverse pattern for removing a column (manual):
-- 1) CREATE new table without the column
-- 2) COPY data from old to new
-- 3) DROP old table
-- 4) ALTER TABLE new_table RENAME TO old_table
-- Example:
-- CREATE TABLE tasks_new (
--   id INTEGER PRIMARY KEY,
--   title TEXT NOT NULL,
--   description TEXT,
--   completed BOOLEAN NOT NULL DEFAULT FALSE,
--   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );
-- INSERT INTO tasks_new (id, title, description, completed, created_at)
--   SELECT id, title, description, completed, created_at FROM tasks;
-- DROP TABLE tasks;
-- ALTER TABLE tasks_new RENAME TO tasks;

COMMIT;

-- =====================
-- Implementation tips
-- =====================
-- - When using Alembic, prefer generating a Python revision with `--autogenerate`
--   and paste verified SQL into `op.execute("""<SQL>""")` blocks where needed.
-- - Keep destructive steps documented and include backups for production.
-- - For complex data migrations, add tests that run the migration against a
--   temporary DB and validate the transformation.
