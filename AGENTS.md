# AGENTS.md

This file documents how coding agents should work in this repository.

## Purpose
- Build and maintain Discoball: Base smart-contract publishing plus IPFS-based website snapshotting.
- Keep snapshots viewable from IPFS gateways, not raw metadata blobs.

## Core Workflow
1. Understand the requested change and inspect current implementation before editing.
2. Make minimal, targeted changes.
3. Run a focused validation for the changed path.
4. Commit and push after each update.

## Project-Specific Knowledge
- Base contract address currently used in Python tools:
  - `0x3fB28659757a6edb6c53eFE1F84896F8Eaf6d5f7`
- `disco-dance.py` expects signer key in this order:
  1. `--private-key`
  2. `PRIVATE_KEY`
  3. `.secrets/deployer-base.key`
- Local IPFS defaults:
  - API: `/ip4/127.0.0.1/tcp/5001`
  - Gateway: `http://127.0.0.1:8080/ipfs/<CID>`

## Snapshot Rules (Important)
- Store snapshots as a browsable bundle:
  - `index.html`
  - localized assets
  - `snapshot.json` metadata
- Do not publish JSON-only CIDs for page rendering.
- For asset filenames, prefer `Content-Type` derived extensions (`.css`, `.js`, etc.).
  - Do not rely on dynamic URL extensions like `.php` from `load.php?...`.
- Keep offline safety behavior:
  - localize fetchable assets
  - block unresolved auto-fetch resources
  - inject CSP to prevent external-origin runtime loads

## Crawl Etiquette
- Use polite request behavior:
  - host pacing
  - retry/backoff
  - `Retry-After` support
  - cooldown after `429/503`
- Avoid repeatedly hammering rate-limited hosts.
- When a host enters cooldown, skip additional fetches and record missing resources.

## Reliability/Compatibility Notes
- Web3 account signing compatibility:
  - support both `signed_txn.rawTransaction` and `signed_txn.raw_transaction`.
- DNS verification is advisory in current flow:
  - log verification status
  - proceed with UNVERIFIED mirrors when DNS TXT is missing/mismatched.

## Validation Checklist
- Python syntax check:
  - `python3 -m py_compile disco-dance.py`
- For snapshot rendering bugs, verify gateway MIME types:
  - CSS should serve as `text/css`
  - JS should serve as `text/javascript`
- Check `snapshot.json` counters:
  - `resources_localized`, `blocked_references`, `failed_downloads`

## Git Expectations
- After each completed update:
  1. `git add` only intended files
  2. `git commit` with a specific message
  3. `git push origin <branch>`
- Never force-push unless explicitly requested.
- Do not commit secrets (`.env`, `.secrets/`, private keys).

## Communication
- Be explicit about what changed, what was validated, and any known caveats.
- If a requested action cannot be completed (e.g., push auth failure), state it clearly and provide the exact next command.
