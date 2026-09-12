---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260804-SKILL-DRIFT-DETECTION
phase: done
date: 2026-08-04
tags: [ai, workflows, skills]
---

# TCK-20260804-SKILL-DRIFT-DETECTION

## Title
Build a deterministic check that a hand-orchestration SKILL.md mentions every phase its workflow.js declares, and wire the existing unused workflow-meta-conformance runtime check into Finalize

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
This session fixed `.claude/skills/implement-ticket/SKILL.md` and
`.claude/skills/create-tickets/SKILL.md` twice each — both were already fixed once on 2026-07-08
(`TCK-20260708-SKILL-IMPLEMENT-TICKET-PHASE-DRIFT`, `TCK-20260708-SKILL-CREATE-TICKETS-WORKFLOW-TOOL-STALE`),
then drifted again into different gaps before today's `TCK-20260804-SKILL-JS-PHASE-SYNC` and
`TCK-20260804-CREATE-TICKETS-SKILL-SYNC` fixed them a second time. A third one-off patch is likely
to recur a third time without some detection mechanism — per the user's explicit standing
authorization to introduce new checks/mechanisms when justified and measurably verifiable via
agent-monitoring data.

**Two directly relevant, already-built pieces of infrastructure found during investigation, not
starting from scratch:**

1. Every `.claude/workflows/*.js` file already exports a structured `export const meta = { phases:
   [{ title, detail }, ...] }` array — confirmed accurate and current for `implement-ticket.js`
   (12 entries, includes Document-Update, matches the real `phase()` call sites exactly).
2. `tools/gate_checks/workflow_meta_conformance.py` (built by `TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK`)
   already parses this `meta.phases` array via `extract_meta_phases()` and cross-references it
   against a real run's `events.jsonl` rows — but only checks *runtime execution* (did this phase
   actually fire for this run_id), not *documentation accuracy* (does the SKILL.md prose a
   hand-orchestrating agent reads mention this phase at all). It is fully built, fully tested
   (`tests/tools/test_workflow_meta_conformance.py`, 15 tests), and **confirmed unwired into any
   workflow's Finalize phase or any skill** — built as a standalone verifier, never connected.

This ticket has two distinct, independently valuable halves:
- **(A) New**: a doc-drift check — does each hand-orchestration SKILL.md's prose mention every
  `meta.phases` title from its corresponding workflow.js? This is the actual gap that caused
  today's two recurring-drift bugs.
- **(B) Reuse**: wire the existing, already-tested `check_workflow_meta_conformance()` into
  `implement-ticket.js`'s Finalize phase (or another appropriate call site) so future *runtime*
  phase-skips are caught automatically going forward, not just doc-vs-code drift.

## Scope
- Investigate: read `tools/gate_checks/workflow_meta_conformance.py` and its test file in full;
  confirm `meta.phases` exists and is current for all 3 workflows with a hand-orchestration skill
  (`implement-ticket.js`, `create-tickets.js`, `implement-epic.js` — confirm `implement-epic.js`
  has one too, tests reference it) before designing anything on top of it.
- Design (Plan phase) a new function, e.g. `check_skill_doc_covers_meta_phases()`, likely in
  `workflow_meta_conformance.py` itself (reusing `extract_meta_phases()`, not reimplementing) or a
  sibling module: for each workflow with a corresponding `.claude/skills/<name>/SKILL.md`, assert
  every `meta.phases[i].title` string appears somewhere in the SKILL.md's text. Decide the exact
  match semantics (substring match on title, case-sensitivity, whether markdown bold/backtick
  wrapping around the title in SKILL.md should be tolerated — e.g. `**Document-Update**` vs.
  `Document-Update`).
- Decide (Plan phase) how this check gets run and by whom: a new pytest test (simplest, catches
  drift whenever the test suite runs, zero pipeline wiring needed) vs. wiring into
  `implement-ticket.js`'s own Finalize self-check (catches it live during ticket close, but only
  for whichever workflow the current ticket happens to be) vs. both. A pytest test that runs
  unconditionally on every `pytest` invocation is likely the highest-leverage, lowest-risk option
  since it needs no runtime wiring and would have caught both of today's bugs the next time anyone
  ran the test suite.
- Wire `check_workflow_meta_conformance()` (already built, already tested, confirmed unused) into
  `implement-ticket.js`'s Finalize phase, following the exact `MARKER:`-prefixed JSON CLI contract
  it already implements — non-blocking (log a warning, same class as the existing
  `check_monitoring_write_recorded`/`check_tag_drift` Finalize-tail advisories), never a new hard
  gate, since this is a new check with zero real-world track record yet.
- Add both new checks to `.claude/skills/implement-ticket/SKILL.md`'s own Finalize step
  description (dogfooding the fix this session just landed for that exact file).

## Out of Scope
- Any change to the 3 workflow `.js` files' actual `meta.phases` content — they're confirmed
  accurate for `implement-ticket.js` today; if Investigate finds staleness in the other two, that's
  a separate, smaller finding to flag, not silently fixed inside this ticket without disclosure.
- Making the new doc-drift check a hard-blocking gate on first landing — no track record yet,
  matches this session's own precedent of treating brand-new checks as advisory first.
- A general "any doc can drift from any code" framework — scoped narrowly to the specific,
  evidenced pattern (SKILL.md vs. its workflow.js's `meta.phases`), not a broader doc-staleness
  system (that already exists separately as `doc_staleness_check.py` for a different scope).
- `compact-simulation-result.js`, `generate-simulation-setup.js`, and the other workflows without a
  corresponding hand-orchestration `SKILL.md` at all — no skill exists for them to drift from,
  N/A for this ticket's mechanism.

## Acceptance Criteria
- [ ] `meta.phases` confirmed current for all 3 in-scope workflows (or staleness flagged, not silently fixed).
- [ ] New `check_skill_doc_covers_meta_phases()`-equivalent function exists, with tests, reusing `extract_meta_phases()`.
- [ ] The new check is runnable as a pytest test (catches drift on every test-suite run, no pipeline wiring dependency).
- [ ] `check_workflow_meta_conformance()` is wired into `implement-ticket.js`'s Finalize phase, non-blocking/advisory.
- [ ] `.claude/skills/implement-ticket/SKILL.md` documents both new checks in its own Finalize step description.
- [ ] Both new checks pass against the current, just-fixed state of `implement-ticket/SKILL.md` and `create-tickets/SKILL.md` (proving they don't false-positive against the two files this session just corrected).

## Related Tickets
- TCK-20260804-SKILL-JS-PHASE-SYNC, TCK-20260804-CREATE-TICKETS-SKILL-SYNC (the two recurring-drift fixes that motivated this ticket)
- TCK-20260708-SKILL-IMPLEMENT-TICKET-PHASE-DRIFT, TCK-20260708-SKILL-CREATE-TICKETS-WORKFLOW-TOOL-STALE (the first occurrence of each drift, now confirmed recurred)
- TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK (built the reusable `check_workflow_meta_conformance()` this ticket wires in)
- TCK-20260804-AGENT-DEF-GAP-FIXES (sibling ticket from the same audit, different fix class — missing agent guidance, not missing drift detection)

## Related Docs
- `docs/ai/agent_definition_gap_audit_2026-08-04.md`

## Related Stored Artifacts
None yet (standard tier, will be created).

## Related Code Areas
- `tools/gate_checks/workflow_meta_conformance.py`
- `tests/tools/test_workflow_meta_conformance.py`
- `.claude/workflows/implement-ticket.js` (Finalize phase, wiring target)
- `.claude/skills/implement-ticket/SKILL.md` (documentation target)

## Assumptions / Open Questions
Exact match semantics for the doc-drift check (substring vs. exact, markdown-wrapper tolerance) —
Plan must decide explicitly, not assume; see Scope.

## Implementation Notes
Implemented per `staging_artifacts/TCK-20260804-SKILL-DRIFT-DETECTION/plan.md` Steps 1-7, no
design deviations.

- **Step 1** (`tools/gate_checks/workflow_meta_conformance.py`): added `DEFAULT_SKILLS_DIR`
  constant, `resolve_skill_md_path()`, `_title_has_dedicated_mention()` (the collision guard —
  strips every other title that is a substring-superset of the target title from a scratch copy
  of the text before checking membership), and `check_skill_doc_covers_meta_phases()`. All added
  between `resolve_workflow_source_path()` and `collect_run_event_statuses()`, exactly as
  specified. Reuses `extract_meta_phases()` and `resolve_workflow_source_path()` directly — no
  reparsing.
- **Step 2** (`tests/tools/test_workflow_meta_conformance.py`): added `_write_skill_md()` fixture
  helper and 8 tests covering happy path, missing-title flagging, bold/plain wrapping tolerance,
  the `Review`/`Security-Review` collision guard (synthetic fixture, since no real file currently
  has that bug), real-file coverage for all 3 in-scope workflows, and the
  `extract_meta_phases()`-reuse architecture guard.
- **Step 3**: added `summarize_conformance_results()` — pure `List[dict]` -> `(status, evidence)`
  fold, no phase-specific logic, placed after `check_workflow_meta_conformance()` and before the
  `if __name__ == "__main__"` block.
- **Step 4** (`.claude/workflows/implement-ticket.js`): inserted the third Finalize-tail advisory
  block immediately after the existing `check_tag_drift` block and before the terminal `return`.
  The `Security-Review` filter is inline in the embedded `python3 -c` string at this call site
  only — never inside `workflow_meta_conformance.py`. Never reassigns `status`. The three-check
  block now spans `implement-ticket.js:1502-1581` (shifted from the plan's estimated `1502-1548`
  because the new block itself adds ~33 lines after the pre-existing two checks — this is expected
  drift from the plan's placeholder end-line, not a design deviation).
- **Step 5**: added `test_finalize_wiring_output_never_changes_terminal_status` — static half
  confirms the `PHASE_META_CHECK_JSON:` marker sits after both the `pushEvent('Finalize', ...,
  'ok', ...)` and `await writeMonitoring('DONE')` lines, and that the terminal `return {...}`
  object body never references `phaseMetaCheck.status`; behavioral half feeds
  `summarize_conformance_results()` a fixture with one FAIL entry and round-trips it through
  `json.dumps`/`json.loads`.
- **Step 6** (`.claude/skills/implement-ticket/SKILL.md`): updated Finalize step's item (b) to
  name all three advisory checks and the new line range, plus one additional sentence documenting
  `check_skill_doc_covers_meta_phases()` as the separate, pytest-only doc-drift mechanism.
- **Step 7** (`docs/ai/ticket-lifecycle.md`): added new Finalize item 9 naming all three
  advisory-only Finalize-tail checks (including the two pre-existing ones, per the plan's
  same-paragraph accuracy-fix justification).

**Minor addition beyond the plan's literal Step 1 text**: also updated
`workflow_meta_conformance.py`'s module docstring (the paragraph that previously said "This ticket
ships the verifier and its tests only — it is not wired into any workflow's Finalize phase") to
reflect that `check_workflow_meta_conformance()` is now wired in, and to describe the new
`check_skill_doc_covers_meta_phases()` function. Not explicitly listed in plan.md's Step 1 change
list; recorded as a Deviation in the plan's staging artifact per CLAUDE.md's "never silently
deviate" rule. Left the "Do NOT touch" targets (`extract_meta_phases()`,
`resolve_workflow_source_path()`, `collect_run_event_statuses()`,
`check_workflow_meta_conformance()`'s FAIL/PASS logic, the `if __name__ == "__main__"` block)
completely untouched.

## Test Summary
`pytest tests/tools/test_workflow_meta_conformance.py -v` → 24 tests total: 23 passed, 1 xfailed
(the pre-existing `test_does_not_flag_security_review_absent_when_ticket_untagged_security`,
left untouched per Scope Guards). Matches plan.md's corrected Step 5 Verify line exactly.

Full regression surface (`tests/tools/test_workflow_meta_conformance.py`,
`tests/tools/test_done_checker_static.py`, `tests/tools/test_done_checker_audit.py`,
`tests/tools/test_validate_agent_monitoring.py`,
`tests/agent_orchestration_claude_adapter/test_phase_order_conformance.py`) → 145 passed, 1
xfailed, 0 failed.

Also ran `check_skill_doc_covers_meta_phases()` directly (not via pytest) against the real, live
`implement-ticket`, `create-tickets`, and `implement-epic` workflow/SKILL.md pairs: 0 FAIL findings
for all three (12/5/3 phases respectively) — confirms no false-positive against the files this
session already fixed.

## Files Changed
- `tools/gate_checks/workflow_meta_conformance.py` — new functions (`resolve_skill_md_path`,
  `_title_has_dedicated_mention`, `check_skill_doc_covers_meta_phases`,
  `summarize_conformance_results`), new `DEFAULT_SKILLS_DIR` constant, module docstring update.
- `tests/tools/test_workflow_meta_conformance.py` — `_write_skill_md()` fixture helper + 9 new
  tests (8 from Step 2, 1 from Step 5).
- `.claude/workflows/implement-ticket.js` — new Finalize-tail advisory block
  (`check_workflow_meta_conformance` + `summarize_conformance_results`, Security-Review filtered
  at call site), lines 1550-1581.
- `.claude/skills/implement-ticket/SKILL.md` — Finalize step (item 13/(b)) updated to name all
  three advisory checks plus the new pytest-only doc-drift check.
- `docs/ai/ticket-lifecycle.md` — new Finalize section item 9 naming all three advisory-only
  Finalize-tail checks.
- `docs/ai/workflows.md` — Document-Update phase found this file's Finalize row named only 1 of
  3 advisory checks (stale the moment `check_workflow_meta_conformance` was wired in); expanded to
  name all three, plus a new footnote documenting `check_skill_doc_covers_meta_phases()` as the
  separate pytest-only doc-drift check.
- `docs/parity_ledger/infrastructure.yaml` — added `INFRA-321` (Parity phase; new entry, since
  this is real `tools/` Python code with new functions, unlike the sibling SKILL.md-prose tickets
  which needed no entry — this module previously had zero parity ledger coverage).

## Completion Summary
`implement-ticket/SKILL.md` and `create-tickets/SKILL.md` had each drifted from their JS source
twice — fixed once on 2026-07-08, then again earlier today. A third one-off patch risked recurring
a third time, so this ticket built real detection instead: `check_skill_doc_covers_meta_phases()`,
a new pytest-only check confirming every phase a workflow's `.js` declares gets a dedicated mention
in its hand-orchestration SKILL.md, collision-safe against substring-masking siblings (`Review`
vs. `Security-Review`, `Verify` vs. `Architecture-Verify`) via a strip-and-recheck guard. Separately,
wired the pre-existing but never-connected `check_workflow_meta_conformance()` (built by
`TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK`, confirmed unused for its entire life) into
`implement-ticket.js`'s Finalize tail as a third advisory-only check, catching future *runtime*
phase-skips the same way the new pytest check catches *documentation* drift. Both checks pass
cleanly against the just-fixed real files (implement-ticket 12/12, create-tickets 5/5, implement-epic
3/3), proving they don't false-positive against work already done this session. Plan needed one
review-correction round (a test-count arithmetic slip); Document-Update caught and fixed one real
staleness in `docs/ai/workflows.md`; Parity added the module's first-ever ledger entry (`INFRA-321`),
since this is real `tools/` Python code, not agent-instruction prose. Verify's first pass correctly
BLOCKED on 3 real bookkeeping gaps (stale `## Status`, missing `artifact_type` frontmatter on 2
staging files, an incomplete Files Changed list) — all fixed, second pass READY TO CLOSE, all 13
DoD conditions PASS. Full standard-tier pipeline, two Review-correction rounds, two Verify passes.
