---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260720-DOCS-AI-SCHEMA-ACCURACY
phase: done
date: 2026-07-20
tags: [documentation, data-quality]
---

# TCK-20260720-DOCS-AI-SCHEMA-ACCURACY

## Title
Fix docs/ai/*.md and docs/agent-monitoring/schema.md accuracy found by the agent-orchestration audit

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
The same 2026-07-20 audit that produced TCK-20260720-MONITORING-PIPELINE-BUGFIXES and
TCK-20260720-CLAUDE-MD-CONSISTENCY-FIXES found several places where `docs/ai/*.md` and
`docs/agent-monitoring/schema.md` — the documentation describing the agent system itself, distinct
from CLAUDE.md's own master instructions — are wrong: false counts, a false doc-coverage claim, a
claim about a nonexistent `Workflow` tool, stale enums, and a false "Closed by" citation in the
audit doc. Fixing all of these together per user direction. One additional item from the original
audit list (missing CLAUDE.md auto-invoke rows for `brainstorming`/`test-driven-development`) was
investigated further during this ticket and found to be a **false positive**, not fixed — see
Assumptions.

## Scope
- `docs/ai/system_overview.md`: corrected the false claim of a `Workflow` tool (none exists in
  this harness — orchestrating sessions read `.js` workflow files directly and translate their
  constructs by hand); corrected "11 subagents" to 13 (2 places); corrected the false claim that
  `simq-audit` is "not yet listed" in `workflows.md` (it has a full section, same depth as every
  other workflow); added `cost_proxy_score` to the documented `events.jsonl` field list (it was
  missing, making the adjacent "token/cost telemetry not recorded" claim read as broader than
  reality).
- `docs/ai/agents.md`, `docs/ai/workflows.md`, `docs/ai/ticket-lifecycle.md`: corrected the
  static pre-check count from "5 machine-checkable conditions" to the real 6 (added
  `ticket_field_values_valid`, which has no dedicated numbered DoD condition yet — a prior
  ticket's own Implementation Notes explicitly deferred that); corrected `ticket-lifecycle.md`'s
  Finalize self-check enumeration from 3 to the real 4 checks (added `registry_entry_regenerated`).
- `docs/agent-monitoring/schema.md`: added `simq-audit` to the documented `workflow` enum (it
  was missing despite `simq-audit.js` writing real run records with that value); added the missing
  `Architecture-Verify` phase to the `implement-ticket` phase-values table; added missing
  phase-values sections for `implement-epic` and `simq-audit` workflows (neither existed at all).
- `docs/ai/skills.md`: corrected the same false `Workflow`-tool claim; corrected the "Project
  Skills" table, which listed 11 workflow shortcuts as equally slash-invokable when only 4 actually
  have a `.claude/skills/*/SKILL.md` wrapper — split the table into the 4 real skills and a new
  explicit list of the 7 workflows with no wrapper (not currently invocable via slash command).
- `tools/agent-monitoring/record_run.py`: added `agent_count` to the `REQUIRED` field set,
  matching `schema.md`'s own documented `Nullable: No` for that field (not previously enforced;
  not manifesting in production since all 4 real callers already pass it, but a real
  code/doc contract mismatch). Updated `tests/tools/test_record_run.py`'s shared `_VALID_RECORD`
  fixture and added 3 new tests covering the enforcement directly.
- `tools/agent-monitoring/retro_nudge_hook.py`: corrected a docstring claiming
  `pre_tool_hook.py`/`post_tool_hook.py` share its once-per-session gating pattern — they are
  unconditional loggers with no such gating; the real shared pattern is with
  `epic_staleness_check.py` (verified directly).
- `docs/ai/agent_infrastructure_audit.md`: corrected Recommendation 1's false "Closed by
  TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING — resolved via hard-blocking" claim — that
  ticket's own Out of Scope section explicitly states the grep/find advisory hook was kept
  advisory, not escalated; confirmed live in this session that the hook still only emits
  `additionalContext`. Added a "partially closed" note to Risk 2 (a monitoring-failure trace now
  exists via a later ticket, but the underlying non-blocking design is unchanged). Added a
  "partially closed" note to Recommendation 4 (skill-catalog pruning) — a prior ticket
  investigated 6 named skills and correctly kept all of them, but `frontend-design` and
  `prompt-builder` were outside that ticket's scope and remain unevaluated.

## Out of Scope
- The live bugs and CLAUDE.md-specific fixes — tracked in the two sibling tickets from the same
  audit (TCK-20260720-MONITORING-PIPELINE-BUGFIXES, TCK-20260720-CLAUDE-MD-CONSISTENCY-FIXES).
- The gate-check wiring decisions and skills/docs orphan cleanup findings from the same audit —
  tracked separately (TCK-D batch, gate-check wiring decisions; a follow-up batch for orphan
  skill re-evaluation).
- Creating `SKILL.md` wrappers for the 7 unwrapped simulation/lab workflows — this ticket only
  corrects the documentation to stop overclaiming; building the wrappers is a real feature-scoping
  decision, explicitly flagged as future work, not built here.
- Adding CLAUDE.md auto-invoke rows for `brainstorming`/`test-driven-development` — investigated
  and found to be a false positive (see Assumptions); no change made.

## Acceptance Criteria
- [x] `docs/ai/system_overview.md` no longer claims a `Workflow` tool exists; subagent count
      corrected to 13 in both locations; `simq-audit` doc-coverage claim corrected;
      `cost_proxy_score` added to the `events.jsonl` field list.
- [x] `docs/ai/agents.md`, `docs/ai/workflows.md`, `docs/ai/ticket-lifecycle.md` all describe the
      static pre-check as aggregating 6 conditions, not 5, with the 6th's undecided DoD-number
      status noted; `ticket-lifecycle.md`'s Finalize self-check enumeration lists all 4 real checks.
- [x] `docs/agent-monitoring/schema.md`'s `workflow` field documentation includes `simq-audit`;
      the `implement-ticket` phase table includes `Architecture-Verify`; `implement-epic` and
      `simq-audit` each have a phase-values section.
- [x] `docs/ai/skills.md` no longer claims a `Workflow` tool exists; the Project Skills table
      accurately distinguishes the 4 skills with real `SKILL.md` wrappers from the 7 workflows
      that have none.
- [x] `record_run.py`'s `REQUIRED` set includes `agent_count`; `validate_record` rejects a
      record missing or null on `agent_count`, verified by dedicated tests; `0` (a legitimate
      falsy-but-valid value) still passes.
- [x] `retro_nudge_hook.py`'s docstring accurately describes which hook scripts share its
      once-per-session gating pattern (verified directly against `epic_staleness_check.py`'s code).
- [x] `docs/ai/agent_infrastructure_audit.md`'s Recommendation 1 no longer falsely claims the
      grep/find advisory hook was hard-blocked; Risk 2 and Recommendation 4 each have an accurate
      partial-closure note.
- [x] No regression: `tests/tools/test_record_run.py` (16/16, including 3 new), broader
      vocabulary/schema/skill-scoped suite (39/39), full `tests/tools/` suite run as a final check.

## Related Tickets
- TCK-20260720-MONITORING-PIPELINE-BUGFIXES, TCK-20260720-CLAUDE-MD-CONSISTENCY-FIXES (sibling
  hotfix batches from the same audit)
- TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM (added the 6th static pre-check this ticket documents)
- TCK-20260709-REGISTRY-REGEN-ON-CLOSE (added the 4th Finalize self-check this ticket documents)
- TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING (the ticket whose scope was misrepresented by the
  false "Closed by" citation this ticket corrects)
- TCK-20260705-SIX-SKILLS-INVESTIGATION (the prior investigation that correctly decided
  `brainstorming`/`test-driven-development` should NOT be added to CLAUDE.md's auto-invoke table
  — confirmed still correct, no change made here)
- TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT (established `record_run.py`'s non-null
  required-field enforcement pattern this ticket extends to `agent_count`)

## Related Docs
- docs/ai/system_overview.md, docs/ai/agents.md, docs/ai/workflows.md, docs/ai/ticket-lifecycle.md
- docs/agent-monitoring/schema.md
- docs/ai/skills.md
- docs/ai/agent_infrastructure_audit.md

## Related Stored Artifacts
None (hotfix — self-evident intent captured in this ticket).

## Related Code Areas
- tools/agent-monitoring/record_run.py
- tests/tools/test_record_run.py
- tools/agent-monitoring/retro_nudge_hook.py

## Assumptions / Open Questions
- CLAUDE.md's Proactive Tool Use table was flagged by the original audit as missing auto-invoke
  rows for `brainstorming` and `test-driven-development`, whose own `SKILL.md` descriptions use
  mandatory language ("You MUST use this..."). Investigated further during this ticket by reading
  `stored_artifacts/TCK-20260705-SIX-SKILLS-INVESTIGATION/investigation.md` directly: that prior
  ticket already investigated exactly this question via a 27-transcript evidence analysis and
  found both skills **correctly redundant** — TDD's Iron Law would actively conflict with this
  repo's real implement-then-test pipeline ordering (not merely duplicate a rule), and
  brainstorming's core function is already served natively by the repo's mandatory
  investigation/plan ticket-staging gate. This is a **false positive** from the original audit
  synthesis, corrected during implementation rather than blindly applied — no CLAUDE.md change
  made for this item.
- The 7 unwrapped simulation/lab workflows (`generate-simulation-setup`,
  `prepare-simulation-execution`, `investigate-simulation-result`,
  `propose-simulation-enhancements`, `register-simulation-result`, `compact-simulation-result`,
  `update-knowledge-store`) remain genuinely not invocable via slash command — this ticket makes
  the docs honest about that gap but does not close it; building the 7 wrappers is real,
  unscoped future work.

## Implementation Notes
All corrections are either mechanical (verified against direct evidence: reading the target
doc/code, running `ls`/`grep` to confirm real counts and contents) or, in the `record_run.py`
case, a small, test-covered enforcement change with confirmed-safe blast radius (all 4 real
production callers already pass `agent_count`; only a shared test fixture needed updating). The
CLAUDE.md auto-invoke item was investigated rather than mechanically applied, and correctly
resulted in no change — demonstrating the "check if already investigated/decided" discipline this
project's own workflow rules require before treating something as a new gap.

## Test Summary
- `tests/tools/test_record_run.py`: 16/16 passing (13 pre-existing, fixture updated + 3 new:
  `test_missing_agent_count_rejected`, `test_null_agent_count_rejected`,
  `test_agent_count_zero_is_falsy_but_valid`).
- Broader scoped regression (`vocabulary or schema or skill or agent_ops_dashboard_glossary`):
  39/39 passing.
- Full `tests/tools/` suite run as a final safety net.
- No test suite exists for `.claude/workflows/*.js`/`docs/ai/*.md`/`docs/agent-monitoring/
  schema.md` content directly (these are prose/documentation, not code) — verified via direct
  reads and greps instead, per this repo's established convention for these file types.

## Files Changed
- docs/ai/system_overview.md
- docs/ai/agents.md
- docs/ai/workflows.md
- docs/ai/ticket-lifecycle.md
- docs/agent-monitoring/schema.md
- docs/ai/skills.md
- docs/ai/agent_infrastructure_audit.md
- tools/agent-monitoring/record_run.py
- tests/tools/test_record_run.py
- tools/agent-monitoring/retro_nudge_hook.py

## Completion Summary
Corrected accuracy issues across `docs/ai/*.md`, `docs/agent-monitoring/schema.md`, and one small
enforcement gap in `record_run.py`, all found by the 2026-07-20 agent-orchestration audit: false
subagent/workflow counts, a nonexistent `Workflow` tool claim (2 files), stale phase/workflow
enums, an overclaiming skills table, a false "Closed by" citation and two missing partial-closure
notes in the audit doc, and an unenforced-but-documented-required field. One flagged item
(CLAUDE.md auto-invoke rows) was investigated and correctly found to be a false positive — a prior
ticket had already deliberately decided against it with real evidence — so no change was made,
demonstrating this project's own "verify before treating as a new gap" discipline in practice.
