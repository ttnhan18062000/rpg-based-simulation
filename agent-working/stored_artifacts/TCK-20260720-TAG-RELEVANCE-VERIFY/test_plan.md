---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260720-TAG-RELEVANCE-VERIFY
artifact_type: test_plan
tags: [tagging, workflows]
---

# Test Plan — TCK-20260720-TAG-RELEVANCE-VERIFY

## Regression Surface

Existing tests that must keep passing — none of this ticket's recommended changes touch
`validate_frontmatter.py`'s public contract, `tag_registry.py`'s existing functions'
signatures/return shapes, or `run_static_precheck`/`run_finalize_selfcheck`'s existing `checks`
tuples, so all of the following are pure regression (no expected behavior change):

**Unit — tag/registry tooling:**
- `tests/tools/test_tag_registry.py`
- `tests/tools/test_tag_category_registry.py`
- `tests/tools/test_validate_frontmatter.py`
- `tests/tools/test_registry_query.py` (the new drift-check helper is a new *caller* of
  `candidate_tags_from_text`, not a change to it — its existing tests must pass unmodified)
- `tests/tools/test_tag_report.py`
- `tests/tools/test_tag_corpus_sweep.py`
- `tests/tools/test_tag_skill_mapping_check.py`

**Unit — done-checker gate-check tooling:**
- `tests/tools/test_done_checker_static.py` — in particular the 6
  `test_classify_checklist_failure_*` tests (lines 670-748) and the `check_monitoring_write_recorded`
  coverage; the new `check_tag_drift` function must not be added to `run_finalize_selfcheck`'s
  `checks` tuple, so `test_run_finalize_selfcheck`-style tests asserting the fixed 4-item shape
  must keep passing unchanged.
- `tests/tools/test_classify_checklist_failure_js_mirror.py`

**Integration — workflow structure/conformance:**
- `tests/tools/test_create_tickets_tag_scope.py` — asserts specific strings are present/absent in
  `create-tickets.js`'s Structure-phase `tags:` prompt block (lines ~503-508); this ticket's
  additive relevance-self-check instruction must not remove or alter any string these tests
  already assert on.
- `tests/tools/test_workflow_meta_conformance.py`

**Architecture guard:**
- Any existing static-source-text-parsing tests for `implement-ticket.js`'s Finalize-phase region
  (none currently target `check_monitoring_write_recorded`'s call site specifically by name — the
  new `check_tag_drift` call site is a new addition to this surface, see New Tests Required).

## New Tests Required

Per AC #1 (relevance-check mechanism, folded into `ticket-scoper`/`create-tickets.js`):

- **`test_ticket_scoper_relevance_self_check_instruction_present`**
  Category: integration (source-text assertion, mirroring `test_create_tickets_tag_scope.py`'s
  established pattern for prompt-text-only changes with no runtime harness).
  Verifies: `.claude/agents/ticket-scoper.md`'s `## Output` section contains the new
  relevance-self-check field/instruction (exact wording TBD at Plan; assert on stable substrings,
  not full sentences, per this repo's own established test-fragility lesson in
  `test_create_tickets_tag_scope.py`).
  Location: `tests/tools/test_ticket_scoper_relevance_check.py` (new file) or an addition to
  `tests/tools/test_create_tickets_tag_scope.py` if Plan decides to co-locate both call sites'
  coverage.

- **`test_create_tickets_structure_relevance_self_check_instruction_present`**
  Category: integration (source-text assertion).
  Verifies: `create-tickets.js`'s Structure-phase `tags:` prompt block and `TASK_SCHEMA` both
  contain the new relevance self-check field/instruction, additive to (not replacing) the existing
  `files_found`-evidence guardrail `TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX` added — a companion
  assertion should confirm the guardrail's existing strings (`"files_found"`, `"clearly indicates
  one"`, the "Do not guess a tag from the title alone" sentence) are still present, guarding
  against the Anti-Drift Hazard of accidentally regressing that recently-landed fix.
  Location: `tests/tools/test_create_tickets_tag_scope.py` (extend — same file already covers this
  exact prompt block) or a new sibling file if Plan prefers separation.

- **`test_relevance_flag_never_blocks_scope_phase`**
  Category: architecture guard (source-text assertion on `implement-ticket.js`).
  Verifies: the relevance flag field is never referenced in any conditional that returns a
  non-`'ok'`/blocking status, and is never passed to `pushEvent(...)`'s `status`/`reason_code`
  arguments — only to `log(...)`. Mirrors the existing structural-guard-test pattern
  (`test_classify_checklist_failure_condition_key_used_not_evidence_text`) of asserting *absence*
  of a wrong wiring pattern, not just presence of the right one.
  Location: `tests/tools/test_ticket_scoper_relevance_check.py` (new) or wherever the Plan
  co-locates AC #1's coverage.

Per AC #2 (drift-check mechanism):

- **`test_check_tag_drift_flags_mismatch`**
  Category: unit.
  Verifies: given a ticket file whose `Files Changed`/`Related Code Areas` text contains a
  registered `subsystem-topic` tag word (e.g. `dashboard`) but whose frontmatter `tags:` does not
  include it, `check_tag_drift()` returns a flagged status with evidence naming the candidate tag.
  Location: `tests/tools/test_done_checker_static.py` (co-located with the other Part B
  `check_*` function tests, same file's existing convention).

- **`test_check_tag_drift_clean_when_tags_cover_candidates`**
  Category: unit.
  Verifies: when the declared `tags:` already include every candidate tag
  `candidate_tags_from_text()` would derive, `check_tag_drift()` returns a clean/non-flagged
  status.
  Location: `tests/tools/test_done_checker_static.py`.

- **`test_check_tag_drift_no_candidates_is_clean`**
  Category: unit (edge case).
  Verifies: when `Files Changed`/`Related Code Areas` text yields zero candidate
  `subsystem-topic` matches, the function returns clean, not flagged — no candidates is not
  evidence of drift.
  Location: `tests/tools/test_done_checker_static.py`.

- **`test_check_tag_drift_not_in_run_finalize_selfcheck_checks_tuple`**
  Category: architecture guard.
  Verifies: `run_finalize_selfcheck()`'s returned checklist still has exactly 4 entries with the
  same 4 `condition` names (`migration_complete`, `ticket_finalized`,
  `working_log_exactly_one_row`, `registry_entry_regenerated`) after this ticket lands —
  `check_tag_drift` must never appear in it. Direct regression guard for AC #3 and this
  investigation's placement recommendation.
  Location: `tests/tools/test_done_checker_static.py`.

- **`test_finalize_tag_drift_check_never_changes_status_from_done`**
  Category: architecture guard (source-text assertion on `implement-ticket.js`, mirroring the
  existing `check_monitoring_write_recorded` wiring's own untested-but-structurally-obvious
  placement — this test makes that placement explicit and checked).
  Verifies: the `bash()` block invoking `check_tag_drift` is positioned after
  `writeMonitoring('DONE')`'s call and the blocking `finalizeFailures`/`FINALIZE_INCOMPLETE`
  return, and no code path conditions the final `return`'s `status` field on `check_tag_drift`'s
  result.
  Location: new file, e.g. `tests/tools/test_finalize_tag_drift_wiring.py`, following
  `test_classify_checklist_failure_js_mirror.py`'s established convention (raw-source-text
  parsing, no JS runtime available in this repo).

Per AC #4 (documentation):

- No dedicated automated test — `docs/guides/ticket_tagging.md` is `layer: guidelines`,
  `audience: developer` prose; this repo's established convention (confirmed by every sibling
  tagging ticket's own Test Summary) is a manual before/after re-read at Verify time, not an
  automated doc-content test, unless Plan decides otherwise.

Per AC #5 (`docs/ai/agents.md` update, conditional):

- If Plan decides the relevance check is documented as an addition to `ticket-scoper`'s existing
  agent-summary entry (per this investigation's recommendation, not a new agent row), no dedicated
  test is needed beyond the doc-staleness gate (`tools/gate_checks/doc_staleness_check.py`), which
  already runs post-Implement against `files_changed`.

## Scoped Pytest Commands

Primary (all files this ticket's recommended changes touch or must not regress):

```
python3 -m pytest tests/tools/test_done_checker_static.py tests/tools/test_validate_frontmatter.py \
  tests/tools/test_registry_query.py tests/tools/test_tag_registry.py \
  tests/tools/test_tag_category_registry.py tests/tools/test_create_tickets_tag_scope.py \
  tests/tools/test_classify_checklist_failure_js_mirror.py -q
```

Secondary (broader tag-tooling regression sweep, matching
`TCK-20260720-TAG-TOUCHPOINT-CLEANUP`'s own precedent command):

```
python3 -m pytest tests/tools/ -q
```

Never: `pytest tests/` (repo-wide) — this ticket's scope is entirely `tools/`/`.claude/`
tooling; there is no `src/` or simulation-behavior surface to regress.

## Anti-Drift Test Guards

- `test_check_tag_drift_not_in_run_finalize_selfcheck_checks_tuple` (above) is the direct guard
  against AC #3's "neither mechanism blocks" requirement being silently violated by a future edit
  that folds the drift check into the blocking tuple for "consistency."
- `test_relevance_flag_never_blocks_scope_phase` (above) is the equivalent guard on the Scope-phase
  side, modeled on the same absence-assertion pattern
  `test_classify_checklist_failure_condition_key_used_not_evidence_text` already established in
  this codebase for a structurally similar "must never silently become the blocking signal"
  concern.
- The companion assertion inside `test_create_tickets_structure_relevance_self_check_instruction_present`
  (that the `files_found`-evidence guardrail's existing strings are still present) directly guards
  against `TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX`'s very recently landed fix being silently
  regressed by this ticket's own prompt-text edit to the same block.
- Re-running `tests/tools/test_registry_query.py` unmodified after adding the drift-check's new
  caller of `candidate_tags_from_text()` is itself an anti-drift guard: any accidental change to
  that function's signature or matching behavior (rather than purely adding a new caller) would
  surface here first, before it could silently affect prior-work search
  (`create-tickets.js`'s Investigate phase, `investigator.md`'s "Finding Prior Work" step) which
  also depends on it.
- `test_run_finalize_selfcheck`-shape assertions (existing, in `test_done_checker_static.py`) —
  confirm they assert the *count* of returned checklist items, not just that specific conditions
  are present, so an accidental 5th item addition would fail loudly rather than being masked by a
  superset-only assertion. If the existing tests only check for presence of the 4 named
  conditions (not absence of a 5th), the new
  `test_check_tag_drift_not_in_run_finalize_selfcheck_checks_tuple` test above closes that gap
  explicitly.
