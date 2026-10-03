---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260924-M3-TERRITORY-COMBAT-FINDING-TRIAGE
artifact_type: test_plan
tags: [architecture, schema, registry, combat]
---

# Test Plan — TCK-20260924-M3-TERRITORY-COMBAT-FINDING-TRIAGE

## Regression Surface

This ticket's main deliverable is a markdown triage log
(`docs/plans/simulation_semantic_control_plane/finding_triage_log.md`) plus, conditionally, a small
number of Territory registry-row edits (existing-row evidence-text amendments per AC criteria and the
T5-item-2 open question above — not new rows, since M1 already populated all four TERR rule IDs).
There is no new code logic in this ticket's own scope. Existing coverage that must keep passing,
confirmed present by direct `ls`/read today:

**Unit — `tests/unit/tools/`:**
- `test_semantic_control_plane_schema.py` — M0's schema validators (`validate_rule_mechanism_edges`,
  `validate_rule_classifications`, `validate_mechanism_causal_edges`, `scan_rule_ids`). Must still
  pass after any Territory evidence-text edit — a text-only change to an existing row's `evidence`
  field does not change schema shape, but the file must remain valid YAML and every `rule_id`/
  `mechanism_id` must still resolve.
- `test_semantic_control_plane_drift_detector.py` — M2's drift detector. Must still report clean
  (0/0) against Territory's mapping after any evidence-text edit, since the edit only touches
  `evidence` prose, not `implemented_by` paths or `verified.verdict` values the detector actually
  diffs against. Re-run `make semantic-control-plane-drift-check` after any registry edit as a direct
  regression check, not just the pytest suite.
- `test_territory_control_view.py` — the six-axis Territory management view generator. Must still
  render correctly against the (possibly evidence-edited) TERR rows.
- `test_mechanism_registry.py`, `test_mechanism_registry_changed_code_check.py`,
  `test_mechanism_registry_completeness_check.py` — unaffected by this ticket's scope (no
  `registries/mechanisms.yaml` row is added, removed, or state-changed by this ticket), but scoped
  in as the closest sibling suite since `registries/mechanisms.yaml` is read (not written) during
  re-verification.

**No `tests/tools/` involvement** — confirmed by directory listing that `tests/tools/` holds no
`test_*.py` files relevant to this track (only `fixtures/`, `memory_probe.py`, `perf_assertions.py`),
matching the ticket's own Assumption #4 and the identical correction already recorded in
`stored_artifacts/TCK-20260924-M2-MAPPING-DRIFT-DETECTION/investigation.md`.

## New Tests Required

**Conclusion, stated explicitly per the ticket's own instruction to say so if this is the outcome:**
this ticket's scope is a doc-shaped triage log plus, at most, evidence-text edits to already-existing,
already-validated Territory rows. It introduces no new schema, no new edge type, no new classification
value, and no new code path. **No new pytest test file is required as a deliverable of this ticket.**
The existing M0 schema validator and M2 drift detector already exercise every invariant a
triage-driven evidence-text edit could violate (malformed YAML, an unresolved `rule_id`/
`mechanism_id`, a duplicate row, a stale `implemented_by`/`verified.verdict` citation) — re-running
them against the edited registry files *is* this ticket's own regression check, not a gap needing new
test code.

The one narrow exception, conditional on Plan's own decision (see investigation.md's Risks item 1):
**if** Plan decides the `ENABLE_COMBAT_ENGAGEMENT` staleness finding should be corrected in
`conflict-combat.md`'s own prose as part of this ticket (rather than deferred), that is a documentation
edit with no test surface of its own — Combat has no mechanism_registry.yaml test asserting the World
Rule doc's own prose content, and none should be added (doc-prose assertions are not this repo's
established pattern; `docs/*.md` content is not test-covered anywhere in this corpus except via the
mechanics-auditor/parity-ledger discipline, neither of which applies to a World Rule Catalog doc).

If Plan or Implement instead decides new Territory registry rows genuinely are warranted (contrary to
this investigation's own finding that M1 already covers T1/T2/T3/T4/T5-items-1/8), any such new row
is exercised for free by the existing schema validator's own generic invariant checks — still no new
test file, only a new fixture-shaped data row already covered by `test_semantic_control_plane_schema.py`'s
existing parametrized assertions (confirmed by reading that file's own structure: it tests the
validator functions generically against constructed fixtures, not against Territory-specific hardcoded
values).

## Scoped Pytest Commands

```
pytest tests/unit/tools/test_semantic_control_plane_schema.py tests/unit/tools/test_semantic_control_plane_drift_detector.py tests/unit/tools/test_territory_control_view.py -v
```

Plus the two direct tool invocations that are the real regression check for this ticket's own
registry-touching scope (already run once during Investigate, confirmed clean; re-run after any
Implement-phase registry edit):

```
python3 tools/semantic_control_plane/registry.py
make semantic-control-plane-drift-check
```

Do not run `pytest tests/` or `pytest tests/unit/` broadly — this ticket's change surface (a new
markdown file plus, conditionally, evidence-text edits to four already-existing YAML rows) does not
warrant a wider sweep than the semantic-control-plane tool family plus a direct validator/detector
run.

## Anti-Drift Test Guards

- **`test_semantic_control_plane_schema.py`'s `test_no_function_derives_classification_from_edges`**
  (cited directly in `stored_artifacts/TCK-20260924-M2-MAPPING-DRIFT-DETECTION/investigation.md`) —
  guards against a future mistake this ticket must not introduce: the triage log or any Implement-phase
  script must never mechanically derive a `rule_classifications.yaml` verdict from the edge list: every
  disposition in this ticket is a recorded human judgment call with cited re-verified evidence, exactly
  the discipline this existing test already enforces structurally.
- **The drift detector re-run itself is the guard against AC5's own failure mode** ("newly-promoted
  rows dated today must not themselves register as drift... a real M2 finding to report, not a date to
  adjust to silence it") — running `make semantic-control-plane-drift-check` after any registry edit,
  and reporting whatever it says honestly rather than tuning a date to make it read clean, is the actual
  test for this specific acceptance criterion; no pytest assertion substitutes for actually running it.
- **A manual, not automated, guard for AC4**: confirm by direct `grep` over
  `registries/{rule_mechanism_edges,rule_classifications}.yaml` after Implement that **zero** new
  `CONFLICT-*`-rule-id rows were written — Combat's mapping stays empty by this ticket's own design,
  and no existing automated test enforces that boundary (the schema validator has no concept of "which
  Rule families are allowed to have rows yet"), so this must be checked by hand at Verify, not assumed
  covered by the suite above.
