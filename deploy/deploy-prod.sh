#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   1) cp deploy/deploy.prod.env.example deploy/deploy.prod.env
#   2) fill deploy/deploy.prod.env
#   3) ./deploy/deploy-prod.sh

DEPLOY_ENV_FILE="${DEPLOY_ENV_FILE:-deploy/deploy.prod.env}"
if [[ ! -f "${DEPLOY_ENV_FILE}" ]]; then
  echo "ERROR: ${DEPLOY_ENV_FILE} not found. Create it from deploy/deploy.prod.env.example"
  exit 1
fi

# shellcheck disable=SC1090
source "${DEPLOY_ENV_FILE}"

SERVER_HOST="${SERVER_HOST:-}"
SERVER_USER="${SERVER_USER:-}"
SERVER_PATH="${SERVER_PATH:-/opt/Rattel}"
SSH_PORT="${SSH_PORT:-22}"
SSH_KEY_PATH="${SSH_KEY_PATH:-}"

if [[ -z "${SERVER_HOST}" || -z "${SERVER_USER}" ]]; then
  echo "ERROR: SERVER_HOST and SERVER_USER are required in ${DEPLOY_ENV_FILE}"
  exit 1
fi
if [[ -n "${SSH_KEY_PATH}" && ! -f "${SSH_KEY_PATH}" ]]; then
  echo "ERROR: SSH key not found at ${SSH_KEY_PATH}"
  exit 1
fi

if [[ ! -f "docker-compose.prod.yml" ]]; then
  echo "ERROR: run this script from repo root."
  exit 1
fi

SSH_CMD=(ssh -p "${SSH_PORT}")
RSYNC_SSH="ssh -p ${SSH_PORT}"
if [[ -n "${SSH_KEY_PATH}" ]]; then
  SSH_CMD+=(-i "${SSH_KEY_PATH}")
  RSYNC_SSH="ssh -i ${SSH_KEY_PATH} -p ${SSH_PORT}"
fi

echo "==> Syncing project to ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}"
rsync -az --delete \
  --exclude='.git' \
  --exclude='.idea' \
  --exclude='.vscode' \
  --exclude='**/__pycache__' \
  --exclude='**/*.pyc' \
  --exclude='**/.venv' \
  --exclude='**/node_modules' \
  --exclude='**/.next' \
  --exclude='media' \
  --exclude='RattelBackend/media' \
  --exclude='.env' \
  --exclude='*.log' \
  -e "${RSYNC_SSH}" \
  ./ "${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/"

echo "==> Running remote deployment steps"
"${SSH_CMD[@]}" "${SERVER_USER}@${SERVER_HOST}" "SERVER_PATH='${SERVER_PATH}' bash -s" <<'REMOTE'
set -euo pipefail

cd "${SERVER_PATH}"

if [[ ! -f .env.prod ]]; then
  echo "ERROR: ${SERVER_PATH}/.env.prod not found"
  exit 1
fi
if [[ ! -f RattelBackend/.env.prod ]]; then
  echo "ERROR: ${SERVER_PATH}/RattelBackend/.env.prod not found"
  exit 1
fi
if [[ ! -f rattel-frontend/.env.prod ]]; then
  echo "ERROR: ${SERVER_PATH}/rattel-frontend/.env.prod not found"
  exit 1
fi

mkdir -p RattelBackend/staticfiles RattelBackend/media

# Start core infra first
sudo docker compose --env-file .env.prod -f docker-compose.prod.yml up -d db redis

# Wait for db/redis to be healthy before Django management commands
until [ "$(sudo docker inspect -f '{{.State.Health.Status}}' rattel_db 2>/dev/null)" = "healthy" ]; do
  echo "Waiting for rattel_db to become healthy..."
  sleep 2
done
until [ "$(sudo docker inspect -f '{{.State.Health.Status}}' rattel_redis 2>/dev/null)" = "healthy" ]; do
  echo "Waiting for rattel_redis to become healthy..."
  sleep 2
done

# Run Django finalization before backend health checks rely on migrated tables
sudo docker compose --env-file .env.prod -f docker-compose.prod.yml run --rm backend python manage.py migrate --noinput
sudo docker compose --env-file .env.prod -f docker-compose.prod.yml run --rm backend python manage.py collectstatic --noinput

# Start/update app services
sudo docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build backend celery celery-beat flower frontend

# Show status
sudo docker compose --env-file .env.prod -f docker-compose.prod.yml ps
REMOTE

echo "==> Deploy finished"
