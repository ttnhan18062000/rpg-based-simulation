---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261030-PARITY-WRITER-KEEPS-UNEDITED-FIELD-BYTES
phase: done
date: 2026-10-30
tags: [ai, process-improvement]
---

# TCK-20261030-PARITY-WRITER-KEEPS-UNEDITED-FIELD-BYTES

## Title
`parity_ledger_writer.py` keeps the bytes of the fields an edit did not change, and agent-working owns the file.

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found by codebase-implementer during M7 batch 2, reported by codebase-planner (base 7b95b3a7f; edits to PROG-114, -115, -116, -118, -125 in `docs/parity_ledger/progression.yaml`). Changing PROG-125's `v2_evidence` through the writer also re-wrapped that entry's long folded `divergence_note`: same value, different bytes. A "this field did not change" `git diff` check then fails, and the implementer restored the bytes by hand.

Cause (read in the code, confirmed by codebase-planner's answer that PROG-125 was an edited entry): `_splice_entry` keeps other entries' bytes but re-dumps the whole edited entry with `yaml.safe_dump`. TCK-20261004-PARITY-LEDGER-WRITER-WHOLE-SHARD-REWRITE-CHURN solved this at entry level; this ticket solves it at field level, and for the same reason: churn pushes agents away from the mandated writer.

Owner decision #715 6525197149: agent-working owns `tools/parity_ledger_writer.py`; route.py reports it unowned today.

## Scope
1. `registries/session_roles.yaml`: add `tools/parity_ledger_writer.py` to the agent-working domain's `owns`, next to the other `tools/` single files, and regenerate the cards and views. If the role-card budget test moves, report the number; do not raise a budget without the owner.
2. `_splice_entry`, update path: for each top-level key of the edited entry whose parsed value is unchanged, keep that key's original lines verbatim; dump only the changed or added keys; drop removed keys. Keep the existing key order for existing keys and append new keys at the end of the entry.
3. Keep the existing safety rule: if the spliced text does not parse back to exactly the intended entries, fall back one level (whole-entry dump, then whole-shard dump). The result is always correct, even if not minimal.
4. Tests in `tests/tools/test_parity_ledger_writer.py`:
   - editing `v2_evidence` of an entry with a hand-wrapped folded `divergence_note` leaves every other line of the file byte-identical;
   - a real-shard case: a value-preserving rewrite of one field of a real `progression.yaml`-shaped entry changes only that field's lines;
   - changing the long note itself re-dumps that field only;
   - add a key, remove a key;
   - first and last entry in a shard; entry followed by blank or comment lines;
   - a shape the field splice cannot handle falls back and still parses to the intended entries.

## Out of Scope
- Formatting or re-wrapping existing ledger entries.
- `validate_entry` rules and the derived parity index.
- A YAML round-trip library (`ruamel`): a new dependency for what line splicing already does in this module.

## Acceptance Criteria
1. `python3 -m tools.sessions.route tools/parity_ledger_writer.py` names agent-working; `python3 -m tools.sessions.validate` is clean; no generated view has drift.
2. The PROG-125 repro at base 7b95b3a7f (re-point its `v2_evidence` with the original note in place) yields a `git diff` that touches only `v2_evidence` lines. Record the before and after in the Test Summary.
3. Every test in Scope 4 passes, and each one fails against the old `_splice_entry` where it asserts minimal bytes (record the mutation check).
4. `tests/tools/` passes in full (registry-edit rule). Take a lead slot, MemoryMax<=3G. `tests/tools/test_agent_working_paths_guard*.py` passes before the push.

## Related Tickets
- TCK-20261004-PARITY-LEDGER-WRITER-WHOLE-SHARD-REWRITE-CHURN (entry-level splice)

## Related Docs
- .claude/agents/parity-updater.md (the mandated writer path)

## Related Stored Artifacts
- none

## Related Code Areas
- tools/parity_ledger_writer.py (`_splice_entry`, `_dump`)
- tests/tools/test_parity_ledger_writer.py
- registries/session_roles.yaml

## Assumptions / Open Questions
- A top-level key's lines are the column-2 `key:` line (column 0 `- key:` for the first key) plus its deeper-indented or blank continuation lines. The parse-back check catches any shape where this is wrong.

## Implementation Notes
`tools/parity_ledger_writer.py`: new `_field_splice_block`; `_splice_entry` now keeps the original lines of every top-level key whose parsed value is unchanged, re-dumps only changed or added keys, drops removed keys, keeps key order and appends new keys. The existing parse-back check still guards the result; it falls back to a whole-entry dump, then a whole-shard dump. `registries/session_roles.yaml` agent-working `owns` gains `tools/parity_ledger_writer.py`; `route` now names agent-working; cards regenerated; `validate` clean.

## Test Summary
PROG-125 repro at 7b95b3a7f (re-point `v2_evidence` against that base's `progression.yaml`): before (origin/main writer) 8 changed diff lines, including a re-wrapped `divergence_note`; after, 3 changed lines, all `v2_evidence`. Mutation check: with the field splice disabled, 6 of the 9 new tests fail (the other 3 are the fallback, first/last and first-key-removed helper cases, which the old code also satisfies). `tests/tools/test_parity_ledger_writer.py`: 50 passed.

## Files Changed
tools/parity_ledger_writer.py; tests/tools/test_parity_ledger_writer.py (`TestFieldLevelSplice`); registries/session_roles.yaml; .claude/agents/session-agent-working-*.md (cards regenerated).

## Completion Summary
The parity ledger writer keeps the bytes of every unedited top-level field of an updated entry; `tools/parity_ledger_writer.py` is owned by agent-working and routes there. The PROG-125 repro changes only `v2_evidence` lines.
