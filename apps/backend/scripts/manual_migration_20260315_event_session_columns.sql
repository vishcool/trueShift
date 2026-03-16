-- TrueShift manual migration
-- Purpose:
-- 1. Change events.session_id and events.correlation_id from UUID to VARCHAR(128)
-- 2. Preserve existing values as text
-- 3. Ensure indexes exist for the new lookup paths
--
-- Review before running in production.
-- Suggested usage:
--   psql "$DATABASE_URL" -f apps/backend/scripts/manual_migration_20260315_event_session_columns.sql

BEGIN;

ALTER TABLE events
    ALTER COLUMN session_id TYPE VARCHAR(128)
    USING CASE
        WHEN session_id IS NULL THEN NULL
        ELSE session_id::text
    END;

ALTER TABLE events
    ALTER COLUMN correlation_id TYPE VARCHAR(128)
    USING CASE
        WHEN correlation_id IS NULL THEN NULL
        ELSE correlation_id::text
    END;

CREATE INDEX IF NOT EXISTS ix_events_session_id ON events (session_id);
CREATE INDEX IF NOT EXISTS ix_events_correlation_id ON events (correlation_id);

COMMIT;
