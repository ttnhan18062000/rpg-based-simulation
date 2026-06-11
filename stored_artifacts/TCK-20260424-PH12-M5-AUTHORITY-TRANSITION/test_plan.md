---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260424-PH12-M5-AUTHORITY-TRANSITION
artifact_type: test_plan
tags: [ph12, m5, authority, transition]
---

# Phase 12 M5 Test Plan: Authority Validation

## 1. Governance Audit
- Verify `legacy_replacement_ledger.md` marks all Phase 12 items as `RATIFIED`.
- Verify `docs/engine/phase12_exit_package.md` exists and is complete.

## 2. Defaulting Check
- Ensure `os.getenv("USE_V2_ENGINE", "1")` defaults to "1" in the kernel.
