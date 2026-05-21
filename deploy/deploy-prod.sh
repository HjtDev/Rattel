#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./deploy/deploy-prod.sh [--follow]
#
# Deploys Django/Next.js project to production server via SSH
# Handles rsync, Docker Compose rebuild, health checks, and log streaming

FOLLOW=0
for arg in "$@"; do
  case "$arg" in
    --follow) FOLLOW=1 ;;
    *)
      echo "ERROR: unknown argument: $arg"
      echo "Usage: $0 [--follow]"
      exit 1
      ;;
  esac
done

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
  echo "ERROR: run this script from repo root"
  exit 1
fi

SSH_CMD=(ssh -p "${SSH_PORT}")
RSYNC_SSH="ssh -p ${SSH_PORT}"
if [[ -n "${SSH_KEY_PATH}" ]]; then
  SSH_CMD+=(-i "${SSH_KEY_PATH}")
  RSYNC_SSH="ssh -i ${SSH_KEY_PATH} -p ${SSH_PORT}"
fi

echo "==> Syncing project to ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}"
RSYNC_FLAGS=(-az --delete)
if [[ "${FOLLOW}" -eq 1 ]]; then
  RSYNC_FLAGS+=(-v --progress)
fi

rsync "${RSYNC_FLAGS[@]}" \
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

echo "==> Running remote deployment"

# Use -t for interactive TTY when following logs
SSH_FLAGS=()
if [[ "${FOLLOW}" -eq 1 ]]; then
  SSH_FLAGS+=(-t)
fi

"${SSH_CMD[@]}" "${SSH_FLAGS[@]}" "${SERVER_USER}@${SERVER_HOST}" "SERVER_PATH='${SERVER_PATH}' FOLLOW='${FOLLOW}' bash -s" <<'REMOTE_SCRIPT'
set -euo pipefail

cd "${SERVER_PATH}"

echo "==> Checking required .env files"
for env_file in .env.prod RattelBackend/.env.prod rattel-frontend/.env.prod; do
  if [[ ! -f "$env_file" ]]; then
    echo "ERROR: ${SERVER_PATH}/$env_file not found"
    exit 1
  fi
done

# Determine sudo requirement
if [[ "$(id -u)" -eq 0 ]]; then
  SUDO=""
  echo "==> Running as root"
else
  if command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
    echo "==> Running with sudo"
  else
    echo "ERROR: current user is not root and sudo is not available"
    exit 1
  fi
fi

echo "==> Creating required directories"
mkdir -p RattelBackend/staticfiles RattelBackend/media

echo "==> Pulling base images from registry"
$SUDO docker compose -f docker-compose.prod.yml pull || true

echo "==> Building custom images"
$SUDO docker compose -f docker-compose.prod.yml build --pull

echo "==> Starting services"
$SUDO docker compose -f docker-compose.prod.yml up -d --remove-orphans

echo "==
