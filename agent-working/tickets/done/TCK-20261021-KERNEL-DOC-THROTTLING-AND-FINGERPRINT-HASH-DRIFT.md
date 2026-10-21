---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261021-KERNEL-DOC-THROTTLING-AND-FINGERPRINT-HASH-DRIFT
phase: done
date: 2026-10-21
tags: []
---

# TCK-20261021-KERNEL-DOC-THROTTLING-AND-FINGERPRINT-HASH-DRIFT

## Title
Engine contract drift: kernel.md still says Emergency Throttling drops work (DEV-014 made it report-only) and calls the isolation fingerprint SHA-256 where known_limitations §2.3 says MD5

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P3

## Request Summary
Lead-planner-u24's read-only pass on origin/main (2026-10-21) found two drifts. They have not been verified here yet.
1. docs/engine/kernel.md, "Emergency Throttling", says the remaining work is dropped. That contradicts DEV-014, under which throttling is report-only.
2. kernel.md calls the isolation fingerprint SHA-256. docs/engine/known_limitations.md §2.3 says MD5 over selected domains.
For each, the code decides which doc is wrong. This is a parity fix, after v1.

## Scope
- Read the throttling path and the fingerprint function in src/engine.
- Correct whichever docs are wrong, and update the parity ledger entry (infrastructure.yaml or substrate.yaml).
- If the code differs from both docs, stop and ask the owner.

## Out of Scope
- Anything before v1. The simulation-behaviour freeze holds until the v1 record lands.

## Acceptance Criteria
- Both statements match the code, with the code path cited.
- The parity ledger entry is updated.

## Related Tickets
- TCK-20261019-RECORD-BASELINE-V1 (do after it)

## Related Docs
- docs/engine/

## Related Stored Artifacts
- none

## Related Code Areas
- docs/engine/kernel.md, docs/engine/known_limitations.md §2.3, the DEV-014 divergence entry, src/engine (throttling and fingerprint code)

## Assumptions / Open Questions
- Lead-planner-u24 reported this; it has not been re-verified here yet.

## Implementation Notes
Verified: Kernel._phase_resolution and the end-of-tick check only call Kernel._report_budget_overrun (record + watchdog alert; nothing dropped, mode not forced; DEV-014). StateFingerprinter.get_fingerprint hashes with hashlib.md5 (src/replay/fingerprint.py:119) over selected domains, consumed by Kernel._guard_stability. Code agrees with known_limitations 2.3 and DEV-014; kernel.md was the stale doc. Fixed 'Emergency Throttling' (now 'Budget Overrun (report-only)') and the Tier-2 fingerprint line. The ledger already carried the correct MD5 and report-only statements (INFRA-223, deterministic_execution.md), so no ledger edit was needed. No code, no runs.

## Test Summary
Docs only. Doc/parity validators and registry check run; no simulation, no pytest.

## Files Changed
docs/engine/kernel.md

## Completion Summary
Docs corrected to match the code; code unchanged. See Implementation Notes.
