#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="ipfs-kubo.service"
SYSTEMD_USER_DIR="${HOME}/.config/systemd/user"
SERVICE_PATH="${SYSTEMD_USER_DIR}/${SERVICE_NAME}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KUBO_LAUNCHER="${SCRIPT_DIR}/ipfs-kubo-daemon.sh"
IPFS_PATH_DEFAULT="${IPFS_PATH:-$HOME/.ipfs}"
IPFS_API_URL="${IPFS_API_URL:-http://127.0.0.1:5001}"

if ! command -v systemctl >/dev/null 2>&1; then
  echo "systemctl is required to install the user service." >&2
  exit 1
fi

if [[ ! -x "${KUBO_LAUNCHER}" ]]; then
  echo "Missing executable launcher: ${KUBO_LAUNCHER}" >&2
  echo "Run: chmod +x ${KUBO_LAUNCHER}" >&2
  exit 1
fi

mkdir -p "${SYSTEMD_USER_DIR}"

cat > "${SERVICE_PATH}" <<EOF
[Unit]
Description=IPFS Kubo Daemon
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
Environment=IPFS_PATH=${IPFS_PATH_DEFAULT}
ExecStart=${KUBO_LAUNCHER}
Restart=always
RestartSec=2

[Install]
WantedBy=default.target
EOF

echo "Wrote service file: ${SERVICE_PATH}"

systemctl --user daemon-reload
systemctl --user enable --now "${SERVICE_NAME}"

echo "Service status:"
systemctl --user --no-pager --full status "${SERVICE_NAME}" | sed -n '1,40p'

echo "Waiting for IPFS API at ${IPFS_API_URL}..."
for _ in $(seq 1 20); do
  if curl -sS -m 2 -X POST "${IPFS_API_URL}/api/v0/version" >/dev/null 2>&1; then
    echo "IPFS API is ready."
    exit 0
  fi
  sleep 1
done

echo "IPFS service started but API did not become ready in time." >&2
exit 1
