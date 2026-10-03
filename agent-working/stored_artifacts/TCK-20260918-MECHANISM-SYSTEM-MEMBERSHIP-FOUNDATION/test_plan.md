---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION
artifact_type: test_plan
tags: [architecture, documentation, schema]
---

# Test Plan — TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION

## New: `tests/unit/tools/test_system_registry.py` (18 tests)
Structurally mirrors `tests/tools/test_layer_registry.py` — canonical-form rejection, duplicate
rejection, append-only load/add semantics, `check_systems_registered`/`system_values` — plus one
real-repo test confirming the 7-system vocabulary was actually seeded, not just that the
mechanism works on a fixture.

## New: `tests/unit/tools/conftest.py`
Autouse fixture patching `registry._load_system_registry` to empty by default (see
`investigation.md` for why this is necessary and correct, not a workaround).

## New, in `tests/unit/tools/test_mechanism_registry.py` (11 new tests)
- Missing-system invariant: accepts a mechanism declaring a registered system; rejects one
  declaring an unregistered system (AC #3).
- Orphan-system invariant: rejects a registered system with zero declaring mechanisms, while
  confirming a real, non-orphan system in the same fixture is NOT also flagged (AC #3).
- Multi-value `systems: []` accepted cleanly (AC #2).
- A mechanism omitting `systems:` entirely does not itself trip the missing-system invariant
  (absence is `mechanisms_by_system()`'s own "unassigned" bucket's job, not a validation error).
- The real, complete registry's own `systems: []` declarations validate clean end to end.
- `mechanisms_by_system()`: groups declared membership correctly across a multi-system fixture;
  renders an unassigned mechanism by asserting its own **presence** in the `"unassigned"` list
  (AC #5 — not proven by checking the assigned rows look right); the `"unassigned"` key is always
  present even when empty; the real, complete registry has zero unassigned mechanisms (pinned —
  a future mechanism landing with empty `systems: []` fails this test, not silently rendered with
  nobody noticing).

## Regression scope run
- `tests/unit/tools/test_mechanism_registry.py` — 62/62 passed
- `tests/unit/tools/test_mechanism_priority_derivation.py` — 17/17 passed
- `tests/unit/tools/` filtered to `mechanism or system_registry` — 202/202 passed (covers every
  mechanism-registry-adjacent test file, not just the two directly touched)
- `tests/unit/tools/test_system_registry.py` — 18/18 passed
- `make mechanism-registry-validate` — `OK: ... valid, 93 mechanisms`, exit 0
