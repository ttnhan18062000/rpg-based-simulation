---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-HOTFIX-INFRA-324-STALE-LINE-CITATION
phase: done
date: 2026-09-02
tags: []
---

# TCK-20260902-HOTFIX-INFRA-324-STALE-LINE-CITATION

## Title
Fix stale line-number citation in parity ledger entry INFRA-324 (lifecycle.py:43)

## Status
DONE

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
- [x] INFRA-324's cited line number(s) for `lifecycle.py` are re-verified against current file
      content and corrected via `tools/parity_ledger_writer.py`.
- [x] Any other stale `lifecycle.py` line citation found during the spot-check is also corrected.
- [x] `docs/parity_ledger/infrastructure.yaml` still validates (schema + index rebuild).

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
`def resolve_lifecycle(...)` in `src/systems/lifecycle_systems/lifecycle.py` is now at line 40
(confirmed via direct grep of `^    def `), not line 43 — it had drifted downward across several
imports added by earlier M3 tickets (`from src.ai.life_stage import LifeStageService`,
`from src.ai.coming_of_age import choose_archetype, is_excluded_no_birth_record`, etc.), none of
which updated this citation since none of them were the ticket that originally introduced it.
Updated `INFRA-324`'s `text` field in `docs/parity_ledger/infrastructure.yaml` via
`tools/parity_ledger_writer.py`'s `write_entry()` (loaded the full entry, replaced only the
`lifecycle.py:43` substring with `lifecycle.py:40`, re-validated, wrote back) — never hand-edited.
Grepped every `docs/parity_ledger/*.yaml` shard for `lifecycle_systems/lifecycle.py:` afterward:
this was the only numeric line citation into that file anywhere in the ledger, confirming no other
entry needed the same fix.

## Test Summary
`python3 tools/parity_index.py build` — rebuilt cleanly, 2132 entries, 9 shards, `status: ok`.
`/home/u24desktop/Working/venv/bin/python3 -m pytest tests/tools/ -k parity -q` — 161 passed, 0
failed (schema/index/writer tests all still pass against the corrected entry).

## Files Changed
- `docs/parity_ledger/infrastructure.yaml` (INFRA-324's `text` field, one line-citation correction)
- `tickets/inprogress/TCK-20260902-HOTFIX-INFRA-324-STALE-LINE-CITATION.md` (this file)

## Completion Summary
Fixed a pre-existing stale line citation in parity ledger entry INFRA-324, disclosed but not fixed
during TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE's own Parity phase. The citation pointed at
`src/systems/lifecycle_systems/lifecycle.py:43` for the location of
`LifecycleSystem.resolve_lifecycle()`'s KILL/old-age death-classification logic; that function now
starts at line 40 after several M3-batch tickets added imports above it. Corrected via the
sanctioned `tools/parity_ledger_writer.py` write path (never hand-edited YAML), confirmed via
direct read of the current file rather than trusted from memory, and confirmed via a full-shard
grep that no other entry cites a `lifecycle.py` line number needing the same fix.
