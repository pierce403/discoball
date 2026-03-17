#!/usr/bin/env bash
set -euo pipefail

NETWORK="${1:-base}"
MIN_DEPLOY_WEI="${MIN_DEPLOY_WEI:-5000000000000000}" # 0.005 ETH
FUNDING_TIMEOUT_SECONDS="${FUNDING_TIMEOUT_SECONDS:-1800}"
POLL_INTERVAL_SECONDS="${POLL_INTERVAL_SECONDS:-10}"
KEY_DIR=".secrets"
LOG_FILE="${LOG_FILE:-deploy.log}"
ENV_FILE="${ENV_FILE:-.env}"
ENS_RPC_URL="${ENS_RPC_URL:-https://eth.llamarpc.com}"
DEFAULT_REFUND_NAME="${DEFAULT_REFUND_NAME:-deanpierce.eth}"
FUNDING_SOURCE_LOOKUP_RETRIES="${FUNDING_SOURCE_LOOKUP_RETRIES:-12}"
FUNDING_SOURCE_LOOKUP_INTERVAL_SECONDS="${FUNDING_SOURCE_LOOKUP_INTERVAL_SECONDS:-5}"

usage() {
  cat <<'EOF'
Usage:
  script/deploy-and-verify.sh [base|base_sepolia]

Environment variables:
  BASESCAN_API_KEY       Required. BaseScan API key used by Etherscan verifier.
  PRIVATE_KEY            Optional deployer key. If missing, script auto-generates one.
  REFUND_ADDRESS         Optional override for refund destination.
                         If omitted with generated PRIVATE_KEY, refund defaults to fund source.
                         If fund source cannot be inferred, defaults to deanpierce.eth.
  LOG_FILE               Optional log path (default: deploy.log)
  ENS_RPC_URL            Optional RPC used for ENS resolution (default: https://eth.llamarpc.com)
  DEFAULT_REFUND_NAME    Optional ENS/address fallback refund target (default: deanpierce.eth)
  MIN_DEPLOY_WEI         Optional minimum balance before deployment (default: 5000000000000000)
  FUNDING_TIMEOUT_SECONDS Optional funding wait timeout (default: 1800)
  POLL_INTERVAL_SECONDS  Optional polling interval while waiting for funds (default: 10)
EOF
}

fail() {
  echo "$1" >&2
  exit 1
}

require_cmd() {
  local cmd="$1"
  command -v "${cmd}" >/dev/null 2>&1 || fail "Missing required command: ${cmd}"
}

load_env_file() {
  if [[ -f "${ENV_FILE}" ]]; then
    # shellcheck disable=SC1090
    set -a
    source "${ENV_FILE}"
    set +a
  fi
}

setup_logging() {
  touch "${LOG_FILE}"
  exec > >(tee -a "${LOG_FILE}") 2>&1
  echo
  echo "==== $(date -Iseconds) deploy-and-verify start ===="
}

infer_funding_source_from_basescan() {
  local addr="$1"
  local addr_lower="${addr,,}"
  local response=""
  local sender=""

  response="$(
    curl -fsS "${BASESCAN_API_URL}?module=account&action=txlist&address=${addr}&page=1&offset=100&sort=desc&apikey=${BASESCAN_API_KEY}"
  )" || return 1

  sender="$(
    jq -r --arg addr "${addr_lower}" '
      .result[]?
      | select((.to | ascii_downcase) == $addr)
      | select((.from | ascii_downcase) != $addr)
      | select((.value | tonumber) > 0)
      | .from
    ' <<< "${response}" | head -n 1
  )"

  [[ -n "${sender}" && "${sender}" != "null" ]] || return 1
  cast to-check-sum-address "${sender}"
}

resolve_refund_target() {
  local target="$1"
  local resolved=""

  if [[ "${target}" == *.eth ]]; then
    resolved="$(cast resolve-name "${target}" --rpc-url "${ENS_RPC_URL}" 2>/dev/null || true)"
    [[ -n "${resolved}" ]] || return 1
    cast to-check-sum-address "${resolved}"
    return 0
  fi

  cast to-check-sum-address "${target}" 2>/dev/null
}

if [[ "${NETWORK}" != "base" && "${NETWORK}" != "base_sepolia" ]]; then
  echo "Unsupported network: ${NETWORK}" >&2
  usage
  exit 1
fi

require_cmd forge
require_cmd cast
require_cmd curl

case "${NETWORK}" in
  base)
    CHAIN_ID="8453"
    EXPLORER_BASE_URL="https://basescan.org/address"
    BASESCAN_API_KEY_URL="https://basescan.org/myapikey"
    BASESCAN_API_URL="https://api.basescan.org/api"
    GAS_REQUEST_URL=""
    ;;
  base_sepolia)
    CHAIN_ID="84532"
    EXPLORER_BASE_URL="https://sepolia.basescan.org/address"
    BASESCAN_API_KEY_URL="https://sepolia.basescan.org/myapikey"
    BASESCAN_API_URL="https://api-sepolia.basescan.org/api"
    GAS_REQUEST_URL="https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet"
    ;;
esac

setup_logging

load_env_file

if [[ -z "${BASESCAN_API_KEY:-}" ]]; then
  echo "Missing BASESCAN_API_KEY environment variable." >&2
  echo "Create one here: ${BASESCAN_API_KEY_URL}" >&2
  echo "Checked env file: ${ENV_FILE}" >&2
  usage
  exit 1
fi

USING_GENERATED_KEY=0
WAITED_FOR_FUNDING=0
DEPLOYER_PRIVATE_KEY="${PRIVATE_KEY:-}"
KEY_FILE="${KEY_DIR}/deployer-${NETWORK}.key"

if [[ -z "${DEPLOYER_PRIVATE_KEY}" ]]; then
  USING_GENERATED_KEY=1
  mkdir -p "${KEY_DIR}"
  chmod 700 "${KEY_DIR}"

  if [[ -f "${KEY_FILE}" ]]; then
    DEPLOYER_PRIVATE_KEY="$(tr -d '[:space:]' < "${KEY_FILE}")"
    echo "Using generated deployer key from ${KEY_FILE}"
  else
    WALLET_OUTPUT="$(cast wallet new)"
    DEPLOYER_PRIVATE_KEY="$(printf '%s\n' "${WALLET_OUTPUT}" | awk '/Private key:/ {print $3}')"
    [[ -n "${DEPLOYER_PRIVATE_KEY}" ]] || fail "Failed to generate deployer private key."
    printf '%s\n' "${DEPLOYER_PRIVATE_KEY}" > "${KEY_FILE}"
    chmod 600 "${KEY_FILE}"
    echo "Generated deployer key and wrote it to ${KEY_FILE}"
  fi
fi

DEPLOYER_ADDRESS="$(cast wallet address --private-key "${DEPLOYER_PRIVATE_KEY}")"
echo "Deployer address: ${DEPLOYER_ADDRESS}"

REFUND_ADDRESS_INPUT="${REFUND_ADDRESS:-}"

if [[ -n "${REFUND_ADDRESS_INPUT}" ]]; then
  REFUND_ADDRESS="$(resolve_refund_target "${REFUND_ADDRESS_INPUT}")" || fail "Invalid REFUND_ADDRESS: ${REFUND_ADDRESS_INPUT}"
else
  REFUND_ADDRESS=""
fi

echo "Deploying DiscoBallRegistry to ${NETWORK} (chain ${CHAIN_ID})..."
echo "Verification target: BaseScan (Etherscan-compatible API)"
MIN_DEPLOY_ETH="$(cast --to-unit "${MIN_DEPLOY_WEI}" ether)"
BALANCE_WEI="$(cast balance "${DEPLOYER_ADDRESS}" --rpc-url "${NETWORK}")"
BALANCE_ETH="$(cast --to-unit "${BALANCE_WEI}" ether)"
echo "Current deployer balance: ${BALANCE_ETH} ETH"

if (( BALANCE_WEI < MIN_DEPLOY_WEI )); then
  WAITED_FOR_FUNDING=1
  echo
  echo "Funding required before deployment."
  echo "Send at least ${MIN_DEPLOY_ETH} ETH to: ${DEPLOYER_ADDRESS}"
  if [[ -n "${GAS_REQUEST_URL}" ]]; then
    echo "Request Base Sepolia gas here: ${GAS_REQUEST_URL}"
  fi
  if [[ -n "${REFUND_ADDRESS}" ]]; then
    echo "Leftover funds will be returned to: ${REFUND_ADDRESS}"
  else
    echo "Leftover funds will be returned to the source funding address."
    echo "If source cannot be inferred, fallback is: ${DEFAULT_REFUND_NAME}"
  fi
  echo

  DEADLINE=$(( $(date +%s) + FUNDING_TIMEOUT_SECONDS ))
  while (( $(date +%s) < DEADLINE )); do
    BALANCE_WEI="$(cast balance "${DEPLOYER_ADDRESS}" --rpc-url "${NETWORK}")"
    if (( BALANCE_WEI >= MIN_DEPLOY_WEI )); then
      BALANCE_ETH="$(cast --to-unit "${BALANCE_WEI}" ether)"
      echo "Funding received: ${BALANCE_ETH} ETH"
      break
    fi
    REMAINING=$(( DEADLINE - $(date +%s) ))
    BALANCE_ETH="$(cast --to-unit "${BALANCE_WEI}" ether)"
    echo "Waiting for funds... current balance ${BALANCE_ETH} ETH, timeout in ${REMAINING}s"
    sleep "${POLL_INTERVAL_SECONDS}"
  done

  BALANCE_WEI="$(cast balance "${DEPLOYER_ADDRESS}" --rpc-url "${NETWORK}")"
  if (( BALANCE_WEI < MIN_DEPLOY_WEI )); then
    fail "Funding timeout reached before minimum deploy balance was met."
  fi
fi

if [[ -z "${REFUND_ADDRESS}" ]]; then
  if [[ "${USING_GENERATED_KEY}" -eq 1 ]]; then
    LOOKUP_RETRIES="${FUNDING_SOURCE_LOOKUP_RETRIES}"
    if [[ "${WAITED_FOR_FUNDING}" -eq 0 ]]; then
      LOOKUP_RETRIES=1
      echo "No fresh funding wait in this run; doing a single funding-source lookup before fallback."
    fi

    if command -v jq >/dev/null 2>&1; then
      echo "Resolving refund address from funding source..."
      for ((attempt=1; attempt<=LOOKUP_RETRIES; attempt++)); do
        if REFUND_ADDRESS="$(infer_funding_source_from_basescan "${DEPLOYER_ADDRESS}")"; then
          break
        fi
        if (( attempt < LOOKUP_RETRIES )); then
          echo "Funding source not indexed yet (attempt ${attempt}/${LOOKUP_RETRIES}); retrying..."
          sleep "${FUNDING_SOURCE_LOOKUP_INTERVAL_SECONDS}"
        fi
      done
    else
      echo "jq not found; skipping funding source inference."
    fi

    if [[ -z "${REFUND_ADDRESS}" ]]; then
      REFUND_ADDRESS="$(resolve_refund_target "${DEFAULT_REFUND_NAME}")" || fail "Could not resolve fallback refund target: ${DEFAULT_REFUND_NAME}"
      echo "Using fallback refund target ${DEFAULT_REFUND_NAME}: ${REFUND_ADDRESS}"
    fi
  else
    REFUND_ADDRESS="${DEPLOYER_ADDRESS}"
  fi
fi

echo "Refund address: ${REFUND_ADDRESS}"

PRIVATE_KEY="${DEPLOYER_PRIVATE_KEY}" BASESCAN_API_KEY="${BASESCAN_API_KEY}" forge script script/Deploy.s.sol:DeployScript \
  --rpc-url "${NETWORK}" \
  --broadcast \
  --verify \
  --verifier etherscan \
  -vvvv

RUN_FILE="$(ls -1t "broadcast/Deploy.s.sol/${CHAIN_ID}"/run-*.json 2>/dev/null | head -n 1 || true)"

if [[ -z "${RUN_FILE}" ]]; then
  echo "Deployment finished, but no broadcast run file was found for chain ${CHAIN_ID}." >&2
  RUN_FILE=""
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "Install 'jq' to print deployed address automatically." >&2
else
  if [[ -n "${RUN_FILE}" ]]; then
    CONTRACT_ADDRESS="$(
      jq -r '.transactions[] | select(.transactionType=="CREATE" and .contractName=="DiscoBallRegistry") | .contractAddress' "${RUN_FILE}" | head -n 1
    )"

    if [[ -n "${CONTRACT_ADDRESS}" && "${CONTRACT_ADDRESS}" != "null" ]]; then
      echo "Deployed DiscoBallRegistry: ${CONTRACT_ADDRESS}"
      echo "Explorer: ${EXPLORER_BASE_URL}/${CONTRACT_ADDRESS}"
    else
      echo "Deployment finished. Could not extract contract address from ${RUN_FILE}" >&2
    fi
  fi
fi

if [[ "${REFUND_ADDRESS,,}" == "${DEPLOYER_ADDRESS,,}" ]]; then
  echo "Refund address matches deployer; skipping refund transfer."
  exit 0
fi

BALANCE_WEI="$(cast balance "${DEPLOYER_ADDRESS}" --rpc-url "${NETWORK}")"
if (( BALANCE_WEI == 0 )); then
  echo "No remaining balance to refund."
  exit 0
fi

GAS_PRICE_WEI="$(cast gas-price --rpc-url "${NETWORK}")"
GAS_BUFFER_WEI=$(( GAS_PRICE_WEI * 25000 ))

if (( BALANCE_WEI <= GAS_BUFFER_WEI )); then
  echo "Remaining balance is too low to safely refund after gas buffer."
  exit 0
fi

REFUND_WEI=$(( BALANCE_WEI - GAS_BUFFER_WEI ))
REFUND_ETH="$(cast --to-unit "${REFUND_WEI}" ether)"

echo "Returning ${REFUND_ETH} ETH to ${REFUND_ADDRESS}..."
cast send "${REFUND_ADDRESS}" \
  --value "${REFUND_WEI}" \
  --rpc-url "${NETWORK}" \
  --private-key "${DEPLOYER_PRIVATE_KEY}" >/dev/null

echo "Refund transaction submitted."
FINAL_BALANCE_WEI="$(cast balance "${DEPLOYER_ADDRESS}" --rpc-url "${NETWORK}")"
FINAL_BALANCE_ETH="$(cast --to-unit "${FINAL_BALANCE_WEI}" ether)"
echo "Final deployer balance: ${FINAL_BALANCE_ETH} ETH"
