---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260705-GATE-DET-PARITY-UPDATER
artifact_type: test_plan
tags: [ai, workflows, determinism]
---

# Test Plan — TCK-20260705-GATE-DET-PARITY-UPDATER

## Regression Surface

Existing tests that must keep passing (unit, all under `tests/tools/` — this is agent-workflow tooling,
no simulation `src/` or `arena-combat` surface is touched):

- `tests/tools/test_parity_ledger_scan.py` — must still pass unmodified; the new module imports
  `CANONICAL_LEDGER_FILES` from `tools/parity_ledger_scan.py` but must not alter that module's own code
  or behavior.
- `tests/tools/test_done_checker_static.py` — unrelated gate, but same `tools/gate_checks/` package;
  confirm adding a new sibling module and updating `tools/gate_checks/__init__.py` (if it exports
  anything — currently just a package marker per the done-checker ticket) does not break its imports.
- `tests/tools/test_done_checker_audit.py` — same package-level regression guard as above.

No `src/` or `tests/certification|integration|arena-combat` tests are affected — this ticket does not
change simulation code, only `.claude/workflows/implement-ticket.js`, `.claude/agents/parity-updater.md`,
and a new `tools/gate_checks/` module.

## New Tests Required

All new tests live in `tests/tools/test_parity_updater_static.py` (mirrors
`tests/tools/test_done_checker_static.py`'s location and unmarked-test convention — not part of the
`architecture` pytest marker, per SEQUENCE.md decision 1).

1. **`test_derive_mapping_reads_v2_evidence_paths`**
   - Category: unit
   - Verifies: given a fixture `docs/parity_ledger`-shaped temp directory with 2+ YAML files each
     containing an entry whose `v2_evidence` cites a `src/...py` path, the mapping-derivation function
     returns those paths mapped to the correct owning file(s).
   - Location: `tests/tools/test_parity_updater_static.py`

2. **`test_derive_mapping_handles_multi_subsystem_file` (coverage-honesty positive control)**
   - Category: unit
   - Verifies: a fixture where the *same* `src/` path appears in `v2_evidence` across two different
     fixture YAML files produces a mapping entry of `{path: {file_a, file_b}}` (a set, not a single
     value) — directly exercises the ~16%-of-paths overlap finding from `investigation.md`. This is the
     test that would fail loudly if someone "simplifies" the mapping to `file → str` instead of
     `file → set[str]`.
   - Location: `tests/tools/test_parity_updater_static.py`

3. **`test_flags_untouched_mapped_subsystem` (coverage-honesty positive control)**
   - Category: unit
   - Verifies: `files_changed=['src/engine/foo.py']` where `foo.py` is cited only in
     `combat_movement.yaml`'s fixture evidence, and `touched_ledger_files=[]` (nothing touched) → the
     cross-reference function returns a flagged/FAIL entry naming `combat_movement.yaml` for
     `src/engine/foo.py`. This is the fixture the ticket's own AC calls out explicitly ("a fixture
     `src/` change with a matching but untouched ledger subsystem must be flagged").
   - Location: `tests/tools/test_parity_updater_static.py`

4. **`test_does_not_flag_when_mapped_subsystem_touched` (negative/coverage-honesty pair to #3)**
   - Category: unit
   - Verifies: identical setup to #3, but `touched_ledger_files=['docs/parity_ledger/
     combat_movement.yaml']` → no flag for `src/engine/foo.py`. This is the ticket's own AC's "a fixture
     where the ledger was correctly touched must not be [flagged]."
   - Location: `tests/tools/test_parity_updater_static.py`

5. **`test_any_of_candidate_subsystems_touched_clears_flag` (multi-subsystem ANY-semantics guard)**
   - Category: unit
   - Verifies: a fixture `src/` path mapped to `{file_a, file_b}` (two candidate subsystems);
     `touched_ledger_files=[file_a]` only (not `file_b`) → the file is **not** flagged. Directly
     encodes the Plan decision from `investigation.md` Risk #2 (ANY-of-candidates semantics, not
     ALL-of-candidates) — this test is the guard against a future regression that silently tightens the
     semantics to "all mapped subsystems must be touched," which would make every change to a shared
     infra file (e.g. `src/engine/apply.py`) spuriously fail.
   - Location: `tests/tools/test_parity_updater_static.py`

6. **`test_unmapped_file_is_not_a_failure`**
   - Category: unit
   - Verifies: `files_changed` includes a `src/` path that appears in no fixture YAML's `v2_evidence` at
     all → result for that path is `NA`/no-mapping-found, not `FAIL` and not silently dropped from the
     output — encodes Risk #3's explicit-default decision (visible "no mapping" signal, not indistinguishable
     from "checked, no issue").
   - Location: `tests/tools/test_parity_updater_static.py`

7. **`test_excludes_faction_yaml`**
   - Category: unit
   - Verifies: a fixture directory containing a `faction.yaml` alongside the 8 canonical files, with a
     `src/` path cited only in `faction.yaml`'s evidence → that path is not mapped to any candidate
     subsystem (mapping-derivation only scans `CANONICAL_LEDGER_FILES`, imported from
     `tools/parity_ledger_scan.py`, not every file under the ledger directory).
   - Location: `tests/tools/test_parity_updater_static.py`

8. **`test_non_src_paths_ignored`**
   - Category: unit
   - Verifies: `files_changed` containing non-`src/` paths (e.g. `tests/...`, `docs/...`) are excluded
     from the cross-reference entirely (mirrors the existing `parityNoSrcChange` filter's own `src/`
     prefix convention in `implement-ticket.js`, so the new check's semantics are consistent with the
     skip-eligibility check it coexists with).
   - Location: `tests/tools/test_parity_updater_static.py`

9. **`test_reuses_canonical_ledger_files_constant` (architecture-consistency guard)**
   - Category: unit / architecture guard (in intent, though the file itself stays unmarked per
     SEQUENCE.md decision 1 — this just asserts the *import*, not a new pytest marker)
   - Verifies: `parity_updater_static.py` imports `CANONICAL_LEDGER_FILES` from
     `tools.parity_ledger_scan` rather than redefining its own copy of the 8-file tuple — a direct
     `is`-identity or equality assertion against the imported constant. Prevents the two modules'
     canonical-file lists silently drifting apart.
   - Location: `tests/tools/test_parity_updater_static.py`

## Scoped Pytest Commands

```
pytest tests/tools/test_parity_updater_static.py -v
pytest tests/tools/ -v
```

Never `pytest tests/`. The second command re-runs the full `tests/tools/` regression surface (including
`test_parity_ledger_scan.py` and the done-checker suite) to confirm no cross-module import breakage from
adding the new sibling file.

## Anti-Drift Test Guards

- Test #5 (`test_any_of_candidate_subsystems_touched_clears_flag`) is the single most important
  anti-drift guard in this plan: it is the only test that would catch a future change silently
  tightening multi-subsystem semantics from ANY to ALL, which would turn this gate from "useful backstop"
  into "spurious-FAIL machine" for every ticket touching a widely-cited shared file
  (`src/engine/apply.py`, `src/core/state.py`, etc. — see `investigation.md`'s quantified overlap list).
- Test #6 (`test_unmapped_file_is_not_a_failure`) guards against the check silently expanding its own
  scope to demand ledger entries for files that have never had one — which is explicitly Out of Scope
  (re-deciding what needs an entry at all is not this ticket's job).
- Test #7 (`test_excludes_faction_yaml`) guards against silent scope creep making `faction.yaml` a 9th
  canonical subsystem, which the sibling `WORKFLOW-PARITY-SKIP` ticket deliberately excluded.
- Test #9 (`test_reuses_canonical_ledger_files_constant`) guards against the two `tools/` modules'
  canonical-file lists drifting apart if someone edits one without the other — the actual risk called out
  in `investigation.md`'s Anti-Drift Hazards.
- No test is planned for the `implement-ticket.js` prompt-wiring change itself (Step-0/self-check prompt
  text, `PARITY_SCHEMA` addition) beyond manual/structural review, consistent with the repo having no JS
  test harness (confirmed: no `.test.js` files anywhere, `package.json` lists only front-end/graph
  dependencies) and the done-checker ticket before it verifying its own equivalent JS change the same
  way.
