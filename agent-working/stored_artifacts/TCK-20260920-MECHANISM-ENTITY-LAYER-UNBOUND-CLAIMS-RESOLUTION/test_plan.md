---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-ENTITY-LAYER-UNBOUND-CLAIMS-RESOLUTION
phase: done
date: 2026-09-20
tags: [architecture, schema, simulation-quality]
---

# Test Plan — TCK-20260920-MECHANISM-ENTITY-LAYER-UNBOUND-CLAIMS-RESOLUTION

## New tests

`tests/unit/tools/test_mechanism_registry.py` (9 new): `parse_implemented_by_entry` splits
path-only/symbol-level/method-level correctly; `validate()` accepts a real top-level symbol-level
binding and a real method-level binding; `validate()` rejects a nonexistent symbol, a method bound
to the wrong class, a nonexistent method, and a method bound to a nonexistent class;
`symbol_defined_in_file` direct unit test proving the class-body boundary (same method name on two
different classes in one file resolves independently).

## Updated pinned tests (each with a full investigation comment, not just a number change)

- `test_mechanism_state_caller_check.py::test_real_registry_findings_pinned` — expanded finding
  set from 1 to 6, each with independent direct re-verification recorded in the comment (not
  trusted from the tool's own report).
- `test_mechanism_registry_completeness_check.py::test_real_registry_enumeration_and_binding_counts_pinned`
  — `bound` 25->29, `unbound` 36->32, with per-target attribution.

## Manual verification (per this program's own established discipline)

- Every one of the 24 mechanisms' proposed bindings independently checked for a real, non-test
  caller via direct grep before being written to the registry (not trusted from investigation
  agents' own reports).
- `BetrayalRecord(` and `breakthroughs_add=`/`active_breakthroughs=` repo-wide grep, independently
  re-run to confirm both state-correction claims (zero real constructors/producers).
- `motivation_doctrine`'s deleted-code behavior cross-checked against
  `docs/guidelines/intentional_divergences.md` #2.53 directly, not assumed from the edge's own
  prior note.
- `registry.py::validate()` re-run after every substantive edit (never batched blind).
- All 5 blocking mechanism-registry checks (`validate`, `atlas-check`, `capabilities-check`,
  `wiring-map-classdef-check`, `registry-html-check`) re-run clean after the full batch.

## Results

`tests/unit/tools/` full suite: 260 passed (241 pre-existing baseline + 9 new + updates to 2
pinned tests, net delta reflecting the new tests only since pinned tests were modified, not
added). `registry.py::validate()`: clean, 93 mechanisms. All 5 blocking checks: clean.
