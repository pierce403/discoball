#!/usr/bin/env bash
set -euo pipefail

IPFS_PATH="${IPFS_PATH:-$HOME/.ipfs}"
IPFS_DAEMON_ARGS="${IPFS_DAEMON_ARGS:---migrate --enable-gc}"

find_ipfs_bin() {
  if command -v ipfs >/dev/null 2>&1; then
    command -v ipfs
    return 0
  fi

  local desktop_bin="/opt/IPFS Desktop/resources/app.asar.unpacked/node_modules/kubo/kubo/ipfs"
  if [[ -x "${desktop_bin}" ]]; then
    echo "${desktop_bin}"
    return 0
  fi

  return 1
}

IPFS_BIN="$(find_ipfs_bin)" || {
  echo "Could not find ipfs/kubo binary." >&2
  echo "Install Kubo or IPFS Desktop." >&2
  exit 1
}

if [[ ! -d "${IPFS_PATH}" ]]; then
  mkdir -p "${IPFS_PATH}"
fi

export IPFS_PATH

# shellcheck disable=SC2086
exec "${IPFS_BIN}" daemon ${IPFS_DAEMON_ARGS}
