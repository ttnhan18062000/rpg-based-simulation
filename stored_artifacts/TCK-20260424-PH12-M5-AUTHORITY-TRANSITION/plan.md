---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260424-PH12-M5-AUTHORITY-TRANSITION
artifact_type: plan
tags: [ph12, m5, authority, transition]
---

# Phase 12 Milestone 5 Execution Plan: Authority Transition

## 1. Ledger Ratification
- Update `docs/engine/legacy_replacement_ledger.md`.
- Mark CLI, REST API, and Replay as `[x] Supported` and `[x] Ratified`.

## 2. Retirement Manifest
- Create `docs/engine/phase13_retirement_manifest.md`.
- Categorize legacy files:
    - Core Logic (`src/core/`)
    - Legacy API (`src/api/`)
    - Legacy Workers (`src/workers/`)
    - Legacy Tests (`tests/`)

## 3. Global Scan
- Run `grep -r "from src\." . --exclude-dir=src --exclude-dir=src --exclude-dir=tests --exclude-dir=tests`.
- Verify no active system code is bypassing the delegation layer.

## 4. Documentation Cleanup
- Ensure `README.md` and `docs/engine/` index files point to V2 as the authoritative entrypoint.
