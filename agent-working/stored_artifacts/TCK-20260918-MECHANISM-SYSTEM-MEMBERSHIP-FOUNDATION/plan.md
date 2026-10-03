---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION
artifact_type: plan
tags: [architecture, documentation, schema]
---

# Plan — TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION

## Steps

1. Build `registries/system_registry.jsonl` + `tools/mechanism_registry/system_registry.py`,
   structurally copying `registries/layer_registry.jsonl`/`tools/layer_registry.py`'s own
   append-only, CLI-managed pattern (§1 of the ticket's own Scope). Register the 7-system
   vocabulary the value investigation (child 1) seeded: `combat`, `progression`, `cognition`,
   `social`, `faction`, `economy`, `world`.
2. Add `systems: []` to every one of the 93 mechanisms in `registries/mechanisms.yaml`, using the
   value investigation's own full membership assignment verbatim (not re-derived) — declared on
   each mechanism, not held as a registry-side list (§2 of the ticket's own Scope, and its own
   stated rationale: a separate list is a second place holding mechanism ids that can dangle on
   rename).
3. Add two new invariants to `registry.py::validate()` — missing system (every `systems: []`
   value resolves to a registered system) and orphan system (every registered system has ≥1
   mechanism declaring it) — matching this file's own existing invariant-numbering convention
   (now 10, up from a docstring that already understated 8 as "seven," fixed in passing).
4. Add `mechanisms_by_system()`, a read-only query function (mirroring
   `all_mechanisms_combined_view()`'s own shape) that groups mechanism ids by system, with a real
   `"unassigned"` key always present — even with zero members — so a caller never needs a
   `.get(..., [])` guess and an omission bug is structurally impossible to hide.
5. Discovered mid-implementation, not anticipated: the new orphan-system invariant reads a
   REAL, always-loaded external registry file, unlike `layers`/`unaudited_depends_on_edges`
   (both self-contained fields inside the `data` dict `validate()` already receives) — this broke
   18 pre-existing tests that pass minimal synthetic fixtures never declaring `systems: []` at
   all, since none of the 7 real registered systems has a member in a 2-3-mechanism fixture. Fixed
   with an autouse `tests/unit/tools/conftest.py` fixture that patches the registry lookup to
   empty by default; the 2 tests that validate the REAL, complete registry restore the real
   lookup explicitly via `monkeypatch`.
6. Write tests proving both new invariants fail on deliberately invalid fixtures (AC #3) — a
   `systems: []` value not resolving to any registered system, and a registered system with zero
   declaring mechanisms — never proven merely by a clean pass on valid data.
7. Write a test proving `mechanisms_by_system()`'s `"unassigned"` bucket renders an unassigned
   mechanism by asserting its own *presence* in the output (AC #5), not by checking the assigned
   rows look right, since an omission bug is invisible to the latter.
8. Write `tests/unit/tools/test_system_registry.py`, structurally mirroring
   `tests/tools/test_layer_registry.py` — the CLI/registry-file mechanics are a direct copy of an
   already-tested pattern, so the test coverage should be too.
9. Update `docs/plans/mechanism_tier_model_initiative.md`'s status block (not a new doc — the
   ticket's own Implementation Notes are explicit that a second plan doc would be the exact
   duplication this whole effort exists to prevent) to record the foundation landing, the value
   investigation's own "proceed with a required change" verdict, and the baseline-comparison
   requirement it places on any future rollup.
