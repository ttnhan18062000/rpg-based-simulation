---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-HOTFIX-INFRA-324-STALE-LINE-CITATION
phase: open
date: 2026-09-02
tags: []
---

# TCK-20260902-HOTFIX-INFRA-324-STALE-LINE-CITATION

## Title
Fix stale line-number citation in parity ledger entry INFRA-324 (lifecycle.py:43)

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
`docs/parity_ledger/infrastructure.yaml`'s `INFRA-324` entry (narrative `text`, around line 8239)
cites `src/systems/lifecycle_systems/lifecycle.py:43` as the location of KILL/old-age
death-classification logic. That line number was already stale before
TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE touched the file (at that ticket's starting HEAD,
line 43 was a blank line inside the module docstring, not the death-classification logic the
sentence describes) — this ticket's own 2-line import insertion just moved the wrong target
further, from a blank line to the docstring's closing `"""`. Not caused by that ticket; found and
disclosed during its Parity phase, left unfixed as out-of-scope for that ticket's own diff.

## Scope
- Re-locate the actual current line(s) implementing KILL/old-age death classification in
  `src/systems/lifecycle_systems/lifecycle.py`.
- Update INFRA-324's cited line number via `tools/parity_ledger_writer.py` (never hand-edit the
  YAML directly, per project convention).
- Spot-check `docs/parity_ledger/infrastructure.yaml` and any other shard for further stale
  line-number citations into `lifecycle.py`, since this file has now been touched by multiple
  tickets this session (life-stage transitions, occupation-change trigger, coming-of-age) without a
  full line-citation audit across shards.

## Out of Scope
- Any behavior change to `lifecycle.py` itself.
- Auditing every parity-ledger line citation repo-wide (only `lifecycle.py`-citing entries).

## Acceptance Criteria
- [ ] INFRA-324's cited line number(s) for `lifecycle.py` are re-verified against current file
      content and corrected via `tools/parity_ledger_writer.py`.
- [ ] Any other stale `lifecycle.py` line citation found during the spot-check is also corrected.
- [ ] `docs/parity_ledger/infrastructure.yaml` still validates (schema + index rebuild).

## Related Tickets
- TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE (found and disclosed this gap during its own Parity phase; did not fix it as out-of-scope)

## Related Docs
- docs/parity_ledger/infrastructure.yaml (INFRA-324)
- docs/parity_ledger/schema.json

## Related Stored Artifacts
- stored_artifacts/TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE/ (Parity phase findings)

## Related Code Areas
- src/systems/lifecycle_systems/lifecycle.py

## Assumptions / Open Questions
- Whether the same drift pattern exists for other `lifecycle.py`-citing entries in other shards
  is unconfirmed — the disclosing ticket only grepped `docs/parity_ledger/*.yaml` for `lifecycle.py`
  references and found this as the sole numeric line citation at the time.

## Implementation Notes
(fill in during implementation)

## Test Summary
(fill in during implementation)

## Files Changed
(fill in during implementation)

## Completion Summary
(fill in during implementation)
