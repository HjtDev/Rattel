#!/usr/bin/env bash
set -euo pipefail

# One-time, self-verifying migration for the Postgres PGDATA/volume-mount
# mismatch present in this project's compose files.
#
# Background: postgres:18 images default PGDATA to
# /var/lib/postgresql/18/docker, NOT /var/lib/postgresql/data. Unless PGDATA
# is pinned to a path inside the mounted volume, the named volume is never
# actually used by Postgres — the real data lives in the db container's
# ephemeral writable layer instead, so `docker compose down` (or any event
# that removes that specific container) silently destroys the database even
# without -v. This happened once already (dev environment, 2026-08-14).
#
# This script, in order, and aborting immediately if any step looks wrong:
#   1. Dumps the currently-running database — both pg_dump custom-format
#      (for pg_restore) and plain SQL (a redundant, human-readable fallback)
#      — and records the pre-migration public-schema table count.
#   2. Verifies the custom-format dump via `pg_restore --list` run inside
#      the (still-running, untouched) db container.
#   3. Pauses for confirmation (skip with --yes).
#   4. Patches the compose file to pin PGDATA (idempotent — skipped if a
#      PGDATA line is already present).
#   5. Stops the whole stack, removes ONLY the db container, and recreates
#      it — this is the one destructive step, and by this point the backup
#      is already on disk and verified.
#   6. Restores the dump into the fresh container and verifies the
#      public-schema table count matches step 1 exactly. Aborts loudly
#      (without bringing the rest of the stack up) on any mismatch.
#   7. Brings the rest of the stack back up.
#
# Run this from the repo root, on the host where `docker compose` actually
# runs (the production server itself, or your local machine for dev). It
# does not touch anything over SSH — for production, SSH in and run it
# there so a human is directly watching the confirmation prompt.
#
# Usage:
#   ./deploy/pgdata-migrate.sh [--compose-file FILE] [--env-file FILE] [--yes]
#
# Backups land in ./deploy/backups/ and are NEVER deleted by this script —
# clean them up yourself once you've confirmed everything is fine.

COMPOSE_FILE="docker-compose.yml"
ENV_FILE=""
ASSUME_YES=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --compose-file) COMPOSE_FILE="$2"; shift 2 ;;
    --env-file) ENV_FILE="$2"; shift 2 ;;
    --yes) ASSUME_YES=1; shift ;;
    *)
      echo "ERROR: unknown argument: $1"
      echo "Usage: $0 [--compose-file FILE] [--env-file FILE] [--yes]"
      exit 1
      ;;
  esac
done

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "ERROR: $COMPOSE_FILE not found. Run this from the repo root."
  exit 1
fi

DC=(docker compose -f "$COMPOSE_FILE")
if [[ -n "$ENV_FILE" ]]; then
  if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: $ENV_FILE not found."
    exit 1
  fi
  DC+=(--env-file "$ENV_FILE")
fi

if ! "${DC[@]}" ps >/dev/null 2>&1; then
  if command -v sudo >/dev/null 2>&1; then
    echo "==> docker compose needs elevated privileges here, using sudo"
    DC=(sudo "${DC[@]}")
  fi
fi

echo "==> Checking db service is running"
DB_STATE=$("${DC[@]}" ps --format '{{.Service}} {{.State}}' 2>/dev/null | awk '$1=="db"{print $2}')
if [[ "$DB_STATE" != "running" ]]; then
  echo "ERROR: db service is not running (state: ${DB_STATE:-missing}). Start the stack first."
  exit 1
fi

DB_USER=$("${DC[@]}" exec -T db printenv POSTGRES_USER | tr -d '\r')
DB_NAME=$("${DC[@]}" exec -T db printenv POSTGRES_DB | tr -d '\r')
if [[ -z "$DB_USER" || -z "$DB_NAME" ]]; then
  echo "ERROR: could not read POSTGRES_USER/POSTGRES_DB from the running db container."
  exit 1
fi
echo "==> Target database: $DB_NAME (user: $DB_USER)"

TS=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="deploy/backups"
mkdir -p "$BACKUP_DIR"
DUMP_FILE="$BACKUP_DIR/${DB_NAME}_${TS}.dump"
SQL_FILE="$BACKUP_DIR/${DB_NAME}_${TS}.sql"

echo "==> Recording pre-migration public-schema table count"
PRE_COUNT=$("${DC[@]}" exec -T db psql -U "$DB_USER" -d "$DB_NAME" -Atc \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';" | tr -d '\r')
echo "    public schema currently has $PRE_COUNT tables"

echo "==> Dumping database (custom format -> $DUMP_FILE)"
"${DC[@]}" exec -T db pg_dump -U "$DB_USER" -d "$DB_NAME" -F c > "$DUMP_FILE"

echo "==> Dumping database (plain SQL, redundant fallback -> $SQL_FILE)"
"${DC[@]}" exec -T db pg_dump -U "$DB_USER" -d "$DB_NAME" -F p > "$SQL_FILE"

if [[ ! -s "$DUMP_FILE" || ! -s "$SQL_FILE" ]]; then
  echo "ERROR: one or both backup files are empty. Aborting — nothing has been touched."
  exit 1
fi

echo "==> Verifying custom-format dump (pg_restore --list, inside the still-running db container)"
"${DC[@]}" cp "$DUMP_FILE" db:/tmp/pgdata_migrate_verify.dump
DUMP_TABLE_COUNT=$("${DC[@]}" exec -T db pg_restore --list /tmp/pgdata_migrate_verify.dump | grep -c ' TABLE DATA ' || true)
"${DC[@]}" exec -T db rm -f /tmp/pgdata_migrate_verify.dump
echo "    dump contains $DUMP_TABLE_COUNT table-data entries (public schema has $PRE_COUNT tables)"
if [[ "$DUMP_TABLE_COUNT" -eq 0 ]]; then
  echo "ERROR: dump appears to contain no table data. Aborting — nothing has been touched."
  exit 1
fi

echo ""
echo "Backups written and verified:"
echo "  $DUMP_FILE ($(du -h "$DUMP_FILE" | cut -f1))"
echo "  $SQL_FILE ($(du -h "$SQL_FILE" | cut -f1))"
echo ""

if [[ "$ASSUME_YES" -ne 1 ]]; then
  read -rp "Proceed to stop the stack, patch PGDATA, and recreate db? [y/N] " REPLY
  if [[ ! "$REPLY" =~ ^[Yy]$ ]]; then
    echo "Aborted — backups above are kept, nothing else was changed."
    exit 1
  fi
fi

echo "==> Patching $COMPOSE_FILE to pin PGDATA"
if grep -q 'PGDATA:' "$COMPOSE_FILE"; then
  echo "    already patched, skipping"
else
  sed -i.bak '/POSTGRES_INITDB_ARGS:/a\      PGDATA: /var/lib/postgresql/data/pgdata' "$COMPOSE_FILE"
  rm -f "${COMPOSE_FILE}.bak"
  echo "    patched"
fi

echo "==> Stopping the full stack"
"${DC[@]}" stop

echo "==> Removing the db container (its writable layer — where the old data actually lived — is discarded here; this is why we backed up first)"
"${DC[@]}" rm -f db

echo "==> Recreating db with the corrected PGDATA"
"${DC[@]}" up -d db

echo "==> Waiting for db to become healthy"
RETRY=0
until "${DC[@]}" exec -T db pg_isready -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; do
  RETRY=$((RETRY + 1))
  if [[ "$RETRY" -ge 60 ]]; then
    echo "ERROR: db did not become ready in time. Your backups are safe at:"
    echo "  $DUMP_FILE"
    echo "  $SQL_FILE"
    exit 1
  fi
  sleep 2
done

echo "==> Restoring dump into the fresh database"
"${DC[@]}" cp "$DUMP_FILE" db:/tmp/pgdata_migrate_restore.dump
"${DC[@]}" exec -T db pg_restore -U "$DB_USER" -d "$DB_NAME" --no-owner /tmp/pgdata_migrate_restore.dump
"${DC[@]}" exec -T db rm -f /tmp/pgdata_migrate_restore.dump

echo "==> Verifying post-migration table count"
POST_COUNT=$("${DC[@]}" exec -T db psql -U "$DB_USER" -d "$DB_NAME" -Atc \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';" | tr -d '\r')
echo "    public schema now has $POST_COUNT tables (was $PRE_COUNT)"
if [[ "$POST_COUNT" != "$PRE_COUNT" ]]; then
  echo "ERROR: table count mismatch after restore ($POST_COUNT vs $PRE_COUNT)."
  echo "Do NOT assume the restore is complete. Backups are safe at:"
  echo "  $DUMP_FILE"
  echo "  $SQL_FILE"
  echo "Investigate before bringing the rest of the stack up (it is currently still down)."
  exit 1
fi

echo "==> Bringing the rest of the stack back up"
"${DC[@]}" up -d --remove-orphans

echo ""
echo "Migration complete. The database now persists correctly across container"
echo "recreation — PGDATA is pinned inside the mounted volume. Backups are"
echo "kept (not deleted automatically) at:"
echo "  $DUMP_FILE"
echo "  $SQL_FILE"
