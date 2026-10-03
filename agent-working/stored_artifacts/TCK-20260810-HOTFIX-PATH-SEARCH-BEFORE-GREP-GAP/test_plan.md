---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP
artifact_type: test_plan
tags: [ai, agent-monitoring, process-improvement]
---

# Test Plan — TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP

## Regression Surface

This is a docs/skill-instruction-text fix — no `src/` behavior changes, so the regression surface
is entirely the existing static/raw-text tests that assert on `.claude/skills/implement-ticket/SKILL.md`
and its sibling `.claude/workflows/implement-ticket.js`, plus the workflow-meta-conformance guard.
All must keep passing unmodified in shape (only new assertions may be added, none removed):

**Unit / static-text tests:**
- `tests/tools/test_current_run_sidecar_orchestrator.py` — asserts on `SKILL.md`/`implement-ticket.js`
  sidecar-write adjacency; must not regress since this ticket does not touch sidecar logic.
- `tests/tools/test_workflow_meta_conformance.py` — `check_skill_doc_covers_meta_phases()` asserts
  every `meta.phases` title from `implement-ticket.js` appears in `SKILL.md`'s prose; adding a new
  sentence to the existing "Investigate" step (line 58) must not remove or rename that step's
  heading text, or this test regresses.
- `tests/tools/test_concern_investigator_agent_definition.py` — unrelated agent
  (`concern-investigator`), but shares the "assert context-scan ordering appears in a `.md` file's
  raw text" pattern this ticket's new test will reuse; confirm it still passes untouched (proves no
  accidental cross-file edit).
- `tests/tools/test_generate_retro.py` — covers `compute_tool_safety_metrics()` (the
  search-before-grep compliance detector `INFRA-315` tracks); this ticket does not change detector
  logic, so these must pass unmodified — a regression here would indicate scope creep into the
  detector itself, which is explicitly out of scope.

**Integration:** none applicable — no `src/` runtime path is touched, so no arena-combat or
integration suite is in the regression surface for this ticket.

## New Tests Required

Per Acceptance Criteria item 2 ("An explicit search-before-grep callout exists at that entry
point"):

- **Test name:** `test_skill_investigate_step_has_search_before_grep_callout`
  **Category:** unit (static raw-text assertion, matching
  `tests/tools/test_current_run_sidecar_orchestrator.py`'s established pattern — no JS/Markdown
  test runner exists for `.claude/workflows/*.js` or `.claude/skills/*.md`, so these are read via
  `Path.read_text()` and asserted against with substring/regex checks, not executed)
  **What it verifies:** `.claude/skills/implement-ticket/SKILL.md`'s numbered pipeline step 2
  ("Investigate", currently line 58) contains an explicit instruction that a fresh
  `search_docs`/`graphify` call must happen before any grep/Read, even when Step 0's upfront
  context search already ran — i.e. the fix must be phase-scoped, not just re-pointing at Step 0.
  Asserts the phrase appears within the Investigate step's own text block (bounded by the step 2
  and step 3 markers), not merely anywhere in the file, so the test can't be satisfied by leaving
  the fix only in Step 0.
  **Where it should live:** `tests/tools/test_current_run_sidecar_orchestrator.py` (extend the
  existing file — same target file, same raw-text-parsing approach, avoids a near-duplicate new
  test module) or a new `tests/tools/test_skill_investigate_search_before_grep.py` if the
  implementer judges the existing file's scope (sidecar-specific) shouldn't absorb an unrelated
  concern — either placement is acceptable; prefer extending the existing file only if it does not
  make that file's own docstring/scope claim inaccurate.

- **Test name:** `test_skill_investigate_callout_survives_step0_removal_check` (defense-in-depth,
  optional but recommended given the Anti-Drift Hazard about Step 0 substitution)
  **Category:** unit (static raw-text assertion)
  **What it verifies:** the new Investigate-step callout text is self-contained (does not merely
  say "see Step 0 above" or similar cross-reference-only phrasing) — i.e. a reader executing step 2
  in isolation (as a hand-orchestrating session naturally does, phase by phase) gets the full
  instruction without needing to re-read Step 0. This directly targets the failure mode this ticket
  diagnosed: Step 0 already existed and evidently didn't prevent the 3 flagged violations.
  **Where it should live:** same file as above.

- **Test name:** `test_docs_to_update_lists_agent_monitoring_guide` (traceability guard, not a
  functional test)
  **Category:** unit / architecture guard
  **What it verifies:** if `check_docs_to_update_coverage`-style static parsing is reused, confirms
  `docs/guides/agent_monitoring.md` was actually touched (per this investigation's "Docs Requiring
  Update" section) once Implement lands — this mirrors `done-checker`'s own
  `docs_to_update_coverage` condition rather than duplicating it as a hand-written test; if
  `done_checker_static.py::check_docs_to_update_coverage` already covers this at Verify time (it
  does, per `docs/ai/ticket-lifecycle.md`'s Verify section), a dedicated new test here is optional
  — list it only if the implementer wants an earlier, pre-Verify signal.
  **Where it should live:** N/A if relying on the existing Verify-phase static check (preferred,
  avoids duplicate coverage).

No new tests are needed for `compute_tool_safety_metrics()` itself — this ticket does not change
detector logic (explicitly out of scope, matching the identical exclusion in the predecessor
`SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP` ticket).

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_workflow_meta_conformance.py tests/tools/test_generate_retro.py -v
```

If the new test is placed in a new file instead of extending the sidecar-orchestrator test:

```
.venv/bin/python3 -m pytest tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_workflow_meta_conformance.py tests/tools/test_generate_retro.py tests/tools/test_skill_investigate_search_before_grep.py -v
```

Never: `pytest tests/` — scope stays inside `tests/tools/` (agent-orchestration/monitoring tooling
domain), matching both predecessor tickets' own scoped runs.

## Anti-Drift Test Guards

- **Guard against "fixed Step 0 only, not the Investigate step":** the new
  `test_skill_investigate_step_has_search_before_grep_callout` test must bound its text-search to
  the Investigate step's own block (between the "2. **Investigate**" marker and the "3. **Plan**"
  marker), not the whole file — otherwise a fix that only touches Step 0 (already present, already
  proven insufficient by this ticket's own evidence) would false-pass the test.
- **Guard against accidentally touching `investigator.md`:** re-run
  `tests/tools/test_concern_investigator_agent_definition.py` unmodified as a tripwire — it asserts
  on a different agent file's content and should show zero diff-sensitivity to this ticket's edits;
  any failure here signals scope bleed into agent-definition files this ticket must not touch.
- **Guard against detector-logic scope creep:** `tests/tools/test_generate_retro.py`'s
  `compute_tool_safety_metrics()` coverage must pass with zero code changes to
  `tools/agent-monitoring/generate_retro.py` — if this ticket's diff touches that file at all, that
  is a signal the fix drifted from "entry-point instruction" into "detector logic," which
  `INFRA-315`'s parity entry and this ticket's own Out of Scope both forbid.
- **Guard against hotfix-tier pipeline redesign:** confirm no diff touches the hotfix-tier branch
  of `.claude/workflows/implement-ticket.js` (around line 721-722, the `pushEvent('Investigate',
  'investigator', 'skipped', ...)` hotfix short-circuit) — this ticket's own investigation
  confirmed hotfix tier is not the mechanism involved, and "Redesigning hotfix-tier's pipeline
  stages" is explicit Out of Scope.
