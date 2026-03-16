# Manual Migration Scripts

## Current Script
- `manual_migration_20260315_event_session_columns.sql`

## Purpose
This migration aligns the database with the updated event model where:
- `events.session_id` is an opaque string
- `events.correlation_id` is an opaque string

This is required because voice sessions and mobile retries now use non-UUID identifiers such as `voice-...` and `workout-...`.

## Execute Manually
```bash
psql "$DATABASE_URL" -f apps/backend/scripts/manual_migration_20260315_event_session_columns.sql
```

## Notes
- The app does not run this automatically.
- Review the SQL before execution.
- Take a backup first if this is a shared environment.
