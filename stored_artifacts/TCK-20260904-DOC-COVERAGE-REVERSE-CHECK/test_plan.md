---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-DOC-COVERAGE-REVERSE-CHECK
artifact_type: test_plan
tags: [testing, ai, documentation, process-improvement]
---

# Test Plan — TCK-20260904-DOC-COVERAGE-REVERSE-CHECK

## Regression Surface

Existing tests that must keep passing, unmodified:

**Unit — `tools/gate_checks/done_checker_static.py` (the module being extended):**
- `tests/tools/test_done_checker_static.py` — the full file, but especially:
  - Every existing `test_docs_coverage_*` test (lines 1399-1616) — the *forward*-direction
    contract (`_parse_docs_to_update`, `_is_none_section`, `_bullet_blocks`,
    `_RESOLVED_CONDITION_MARKER_RE`) is explicitly Out of Scope and must not regress.
  - `test_docs_coverage_signature_is_ticket_id_tier_base_dir` (line ~1620) — locks
    `check_docs_to_update_coverage`'s current parameter shape
    (`["ticket_id", "tier", "base_dir"]`); if Decision-4 (own-condition-vs-extend) changes this
    function's signature, this test's own assertion must be deliberately and visibly updated, not
    silently broken.
  - `test_run_static_precheck_includes_docs_to_update_coverage_condition` (line 1631) — confirms
    `docs_to_update_coverage` stays a named condition in `run_static_precheck`'s output regardless
    of how the reverse check is wired in.
  - Every `test_check_tag_drift_*` test (lines 1082-1126), especially
    `test_check_tag_drift_not_in_run_finalize_selfcheck_checks_tuple` — the precedent this ticket
    mirrors for mechanics must itself stay unmodified and non-blocking.
  - `test_check_monitoring_write_recorded_applies_under_hotfix_tier` (line 999) — the direct
    precedent for Decision 3 (no special-casing hotfix); must not be touched or reinterpreted.

**Integration — `.claude/workflows/implement-ticket.js` wiring (static source-text tests, no JS
runner exists in this repo):**
- `tests/tools/test_document_update_phase_wiring.py` — full file. Confirms Document-Update's
  ordering, unconditional (no hotfix guard), non-blocking failure shape, and `docs/ai/workflows.md`
  / `docs/ai/system_overview.md` table coverage. This ticket adds no new phase/agent, so none of
  these assertions should need to change — a break here signals scope creep into phase/agent
  wiring, which is out of scope.
- `tests/tools/test_doc_staleness_gate_wiring.py` — full file. Confirms the *existing*
  Implement-time hard-block gate (`doc_staleness_check.py`) stays wired exactly as-is; this ticket
  must not touch that gate at all.

**Architecture-guard:**
- Any existing test asserting `run_finalize_selfcheck`'s checks tuple composition (confirm
  `check_tag_drift` stays excluded from it) — search
  `tests/tools/test_done_checker_static.py` for `run_finalize_selfcheck` call sites.

## New Tests Required

1. **`test_reverse_docs_coverage_fails_when_touched_doc_not_in_files_changed_or_related_docs`**
   Category: unit.
   Verifies: a `git status --porcelain`-visible `docs/` path (mocked/monkeypatched, mirroring
   existing `test_docs_coverage_*` tests' `monkeypatch` pattern for `_git_touched_paths`) that
   appears in neither the ticket's `## Files Changed` nor `## Related Docs` section text produces
   `FAIL`, with evidence naming the specific missing path.
   Location: `tests/tools/test_done_checker_static.py`.

2. **`test_reverse_docs_coverage_passes_when_touched_doc_appears_in_files_changed`**
   Category: unit.
   Verifies: the same touched-doc scenario, but the path appears verbatim in `## Files Changed` —
   `PASS`.
   Location: `tests/tools/test_done_checker_static.py`.

3. **`test_reverse_docs_coverage_passes_when_touched_doc_appears_in_related_docs_only`**
   Category: unit.
   Verifies: the path appears only in `## Related Docs`, not `## Files Changed` — still `PASS`
   (per ticket Scope: "does not appear... in the ticket's resolved Files Changed **or** Related
   Docs section text" — either section satisfies it).
   Location: `tests/tools/test_done_checker_static.py`.

4. **`test_reverse_docs_coverage_directory_collapse_tolerance`**
   Category: unit.
   Verifies: a wholly-new untracked `docs/` subdirectory git collapses to a trailing-slash entry
   (e.g. `?? docs/newsubsystem/`) is still recognized as covering
   `docs/newsubsystem/foo.md` if that literal path string appears in the section text — reuses
   `_path_touched`'s existing directory-collapse tolerance (line 416-426), confirming the reverse
   check calls the same helper rather than reimplementing path matching.
   Location: `tests/tools/test_done_checker_static.py`.

5. **`test_reverse_docs_coverage_ITEM_INSTANCE_HISTORY_style_non_docs_path_is_out_of_scope`**
   (or equivalently named per Plan's Decision 2 resolution)
   Category: unit / architecture guard.
   Verifies explicitly, using a fixture shaped after the real
   `TCK-20260831-ITEM-INSTANCE-HISTORY` incident (a touched `src/core/state.py`, not a `docs/`
   path, absent from Files Changed): if Decision 2 resolves `docs/`-only, this test asserts the
   check correctly does **not** flag the missing `src/` path (proving the scope boundary is
   intentional, not an accidental miss) — this test exists specifically to prevent silent scope
   creep in either direction on a decision this investigation flagged as consequential.
   Location: `tests/tools/test_done_checker_static.py`.

6. **Historical-incident regression fixture — pick at least one of the three named incidents**
   (`test_reverse_docs_coverage_reproduces_RACE_RELATIONS_MATRIX_incident` and/or
   `..._READINESS_SPEED_FORMULA_incident`, per AC #3).
   Category: unit (fixture-based regression).
   Verifies: reconstructing the pre-hand-patch state (a fixture ticket body whose `## Files
   Changed`/`## Related Docs` omits `docs/mechanics/02_combat_laws.md` or
   `docs/simulation_quality/corpus_tier_taxonomy.md`, with `git status` mocked to show that path
   touched) makes the new check `FAIL` — proving it would have caught the real incident before the
   hand-patch, not just a synthetic case.
   Location: `tests/tools/test_done_checker_static.py`.

7. **`test_reverse_docs_coverage_hotfix_tier_behavior`**
   Category: unit (decision-pinning).
   Verifies whichever way Decision 3 resolves, explicitly and by name (mirroring
   `test_check_monitoring_write_recorded_applies_under_hotfix_tier`'s own "documents and locks in"
   comment style): either (a) the reverse check runs identically under `tier == "hotfix"` — no
   `NA` branch, `git status`/ticket-body-only inputs suffice — or (b) it explicitly returns `NA`
   for hotfix with evidence stating why, matching the forward check's existing shape. Whichever
   branch Plan/Implement choose, this test must assert that behavior positively, not merely absence
   of a crash.
   Location: `tests/tools/test_done_checker_static.py`.

8. **`test_run_static_precheck_wires_reverse_check_blocking`**
   Category: integration (aggregation wiring).
   Verifies: `run_static_precheck`'s output includes the reverse check's result (whether folded
   into the existing `docs_to_update_coverage` entry's evidence or as its own new named condition —
   per Decision 4), and that a `FAIL` here is not silently absorbed into a `PASS` elsewhere.
   Location: `tests/tools/test_done_checker_static.py`.

9. **`test_verify_prompt_mentions_reverse_check_or_updated_condition_language`**
   Category: architecture guard (static source-text, mirrors
   `test_verify_prompt_cites_condition_6_alongside_static_conditions`'s existing pattern at line
   1649).
   Verifies: the Verify-phase agent prompt in `implement-ticket.js` still accurately describes what
   `docs_to_update_coverage`'s static-script output means, post-extension — catches prompt-text
   drift if the check's meaning changes without the prompt being updated.
   Location: `tests/tools/test_done_checker_static.py` (co-located with the sibling test it
   mirrors) or a new file if the sibling test's own file boundary makes more sense once seen.

10. **`test_doc_updater_prompt_includes_self_check_instruction`**
    Category: unit (static prompt-text assertion, mirrors
    `test_document_update_phase_appears_in_workflows_md_table`'s file-read-and-assert pattern).
    Verifies: `.claude/agents/doc-updater.md`'s prompt text contains an explicit self-check
    instruction (cross-reference actual touched paths against Files Changed/Related Docs, flag
    same-turn) — per this ticket's AC #4's own caveat, "agent-interpreted, matching this file's
    existing test-surface limitation," this test can only assert the *instruction's presence*, not
    that an agent actually follows it at runtime.
    Location: a new or existing test file under `tests/tools/` asserting against
    `.claude/agents/doc-updater.md`'s raw text (no agent-prompt test runner exists in this repo).

## Scoped Pytest Commands

```
pytest tests/tools/test_done_checker_static.py -v
pytest tests/tools/test_document_update_phase_wiring.py tests/tools/test_doc_staleness_gate_wiring.py -v
```

Both scoped to the `tools/gate_checks/done_checker_static.py` module and the two workflow-wiring
test files this ticket's Related Code Areas name — never the full `tests/tools/` directory (145+
files, many with unrelated network/MCP dependencies, per this project's "scope to the domain under
modification" testing rule and the precedent already set in
`TCK-20260831-ITEM-INSTANCE-HISTORY`'s own Test Summary).

If a new test file is created for AC #4 (item 10 above), add it explicitly to this command line
rather than leaving it to be discovered only by a directory-wide run.

## Anti-Drift Test Guards

- **Every existing `test_docs_coverage_*` test (forward direction) must still pass byte-for-byte
  unmodified** — a red flag if any of them needed editing to accommodate the reverse check; the
  ticket's Out of Scope explicitly forbids touching the forward contract.
- **`test_check_tag_drift_not_in_run_finalize_selfcheck_checks_tuple` must still pass** — proves
  the reverse check's own blocking wiring did not accidentally also promote `check_tag_drift` (or
  vice versa) into a blocking role it was deliberately kept out of.
- **A test asserting the reverse check's status vocabulary is `PASS`/`FAIL` (and, if `NA` is used
  for hotfix, `NA`) — never `CLEAN`/`FLAGGED`** — guards against silently copying
  `check_tag_drift`'s non-blocking vocabulary along with its mechanics (see investigation.md's
  Anti-Drift Hazards).
- **A test confirming `docs/parity_ledger/*.yaml` paths are never routed through `doc-updater`'s
  own self-check instruction** (AC #4) — `doc-updater.md`'s Per-Family Rules already exclude
  `parity_ledger/`; the new self-check instruction must not implicitly relitigate that boundary.
- **`test_document_update_runs_unconditionally_no_hotfix_guard`
  (`test_document_update_phase_wiring.py`) must still pass** — confirms this ticket's AC #4 prompt
  edit did not accidentally introduce a hotfix-conditional guard into the Document-Update phase
  itself (a different phase-level concern from the new Verify-time check's own tier handling).
