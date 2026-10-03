---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260805-SKILL-GATE-CONVERSION-DECISION
phase: done
date: 2026-08-05
tags: [skills, workflows]
---

# TCK-20260805-SKILL-GATE-CONVERSION-DECISION

## Title
Decide whether api-design-principles/debugging-strategies/python-performance-optimization should convert to binding gates like security

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child ticket #4 of `TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC`, merging the epic's original
"mechanism-1 fix direction" and "ticket-metadata-driven triggering re-evaluation" items per
Investigate's own finding that they are the same underlying design decision. Two independent nudge
mechanisms (a CLAUDE.md file-path auto-invoke row since 2026-07-04; a tag-based `suggested_skills`
advisory log line since 2026-07-05) exist for these 3 skills, and both produce zero real
invocations across the entire `agent-monitoring/tools.jsonl` history, despite confirmed real
applicable work (`src/api/` edits, real debugging sessions, profiling commands). Meanwhile the one
tag that WAS converted from advisory to a binding gate (`security`, via
`TCK-20260705-WORKFLOW-SECURITY-GATE`) has 2 clean real fires. This ticket investigates,
per-skill (not blanket), whether each of the 3 should convert to a binding
`implement-ticket.js` gate.

**Central open question, deliberately not decided by the epic's Plan phase**: unlike `security`
(clean APPROVED/NEEDS_CHANGES/BLOCKED verdict shape), none of these 3 has an obvious pass/fail
verdict — "did you follow API design principles" or "did you profile performance" are soft
judgments, not deterministic checks. A real design risk exists if this ticket's own Plan phase
assumes "convert all 3 to gates" is self-evidently correct just because `security`'s conversion
worked well — it must explicitly address this asymmetry.

## Scope
- Investigate (per skill): does a real, checkable verdict shape exist for this skill's domain, or
  would a gate need to rely on soft LLM judgment (weaker than `security`'s pattern)?
- Investigate: is the tag-registry mapping (`triggers_skill` field, `SKILL-MAPPING-DEDUP`
  mechanism) the right lever, or does the CLAUDE.md file-path table need a different fix
  entirely (e.g. folding into the phase-translation-table pattern this session established for
  hand-orchestration skills)?
- Decide, with explicit reasoning, per skill: convert to gate, some other fix, or leave as-is —
  not a blanket decision.
- If any gate is added: mirror `WORKFLOW-SECURITY-GATE`'s own AC3 pattern (a zero-added-latency
  negative test — a ticket without the triggering tag produces zero new events), plus a hotfix-tier
  trigger case (Step 1's sibling ticket found tier-independence isn't perfectly followed in
  practice for the existing gate — don't repeat that gap for any new one).

## Out of Scope
- Rebuilding `tools/tag_registry.py::get_skill_mapping()` or the `skill-mapping` CLI subcommand —
  already exists (`SKILL-MAPPING-DEDUP`). Any mapping expansion adds a `triggers_skill` field via
  `add_tag()`, never hand-edits files.
- Re-litigating `WORKFLOW-TAG-TUNING-INVESTIGATION`'s finding that mechanism 2 (tag suggestion) is
  advisory-by-design and correctly wired — that finding stands; this ticket only decides whether
  specific already-mapped tags should gain a gate.

## Acceptance Criteria
- [x] Per-skill decision (convert / other fix / leave as-is) for `api-design-principles`,
      `debugging-strategies`, `python-performance-optimization`, each with explicit reasoning
      addressing the pass/fail-verdict-shape asymmetry — see `investigation.md`.
- [x] If any gate added: mirrors `WORKFLOW-SECURITY-GATE`'s test pattern including the
      zero-latency-negative and hotfix-trigger cases. **N/A by design** — no new gate/phase was
      added; the one skill with a real verdict shape (`python-performance-optimization`) was
      routed through the existing Test-phase gate instead (see Completion Summary).
- [x] Coordination check with any other child ticket touching CLAUDE.md's "Proactive Tool Use"
      table — satisfied, this ticket never touches that table.

## Related Tickets
- TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC (parent epic)
- TCK-20260805-SKILLS-DOC-STALENESS-FIX (DONE — must land first, this ticket edits the same docs/ai/skills.md section)
- TCK-20260704-SKILL-TRIGGER-COVERAGE (wired the original CLAUDE.md rows this ticket re-examines)
- TCK-20260705-TAG-SKILL-SUGGEST, TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION (built/root-caused mechanism 2)
- TCK-20260705-WORKFLOW-SECURITY-GATE (the proven pattern to mirror or explicitly diverge from)
- TCK-20260720-SKILL-MAPPING-DEDUP (the live mapping mechanism to extend if needed)

## Related Docs
- `docs/ai/skills.md`
- CLAUDE.md ("Proactive Tool Use" table)

## Related Stored Artifacts
None yet (standard tier, will be created).

## Related Code Areas
- `.claude/workflows/implement-ticket.js`
- `tools/tag_registry.py`
- `.claude/agents/ticket-scoper.md`

## Assumptions / Open Questions
The core gate-conversion question is genuinely open — this ticket's own Investigate/Plan phases
resolve it with evidence, not assumed here.

## Implementation Notes
Per-skill decision, grounded in real investigation (see `investigation.md`):
- `api-design-principles` — **leave advisory, no gate.** The one hard-checkable rule in this
  domain (presenters-only API boundary) is already enforced independently by
  `tests/architecture/test_api_read_model_guard.py`, unconditional on this skill firing. No code
  change.
- `debugging-strategies` — **leave advisory, no gate.** No deterministic verdict shape exists for
  "did you debug well." No code change.
- `python-performance-optimization` — **"other fix," not a gate.** A real verdict shape exists
  (`PerfRegressionGate`), but adding a new phase would duplicate the existing Test-phase gate.
  Instead: `.claude/workflows/implement-ticket.js`'s Test-phase prompt now reads
  `ticketInfo.tags.includes('performance')` directly (mirrors `Security-Review`'s own precedent)
  and, when true, instructs `test-scoper` to always include `tests/unit/perf/`/`tests/perf/`
  regardless of which `src/` paths changed — closing a real gap where a performance-motivated
  change outside `src/perf/` itself (e.g. `src/engine/`, `src/world/`) could silently skip the
  real regression-gate check. Mirrored the identical rule into `.claude/agents/test-scoper.md`'s
  Scoping Rules section so the JS and the agent definition stay consistent.

Done entirely directly (no subagents — hard 200-agent spawn cap, per explicit user decision to
continue solo).

## Test Summary
New `tests/tools/test_perf_tag_test_scoper_wiring.py` — 7 static raw-source-text tests against
`implement-ticket.js` and `test-scoper.md` (same established pattern as
`test_document_update_phase_wiring.py`; the JS is never executed, only read as text). Covers: the
tag check reads `ticketInfo.tags` directly; the reminder sits inside the Test-phase prompt (not a
separate step); it cites the real `docs/performance/perf_baseline_policy.md` §3 doc; both
`tests/unit/perf/` and `tests/perf/` are named; no new blocking status was introduced (confirmed
the next `return { status: ... }` after the tag check is still the pre-existing `TESTS_FAILED`);
`test-scoper.md` documents the identical rule in its Scoping Rules section. Regression check:
`pytest tests/tools/test_document_update_phase_wiring.py tests/tools/test_doc_staleness_gate_wiring.py
tests/tools/test_shadow_packet_call_site.py tests/tools/test_step0_ts_orchestrator.py
tests/tools/test_workflow_meta_conformance.py` — 90 passed, confirming surrounding phase wiring
untouched. `doc_staleness_check.py` → PASS (real doc update:
`docs/guidelines/tag_taxonomy.md`'s Process/Skill-signal section now records this decision, since
it's the doc that named `performance` as future gate-routing material in the first place).
`clean_data_runs_early()` → PASS. `expected_subsystems_for_files()` → `{}` — no parity entry
needed. `run_static_precheck('standard', ...)` — all 7 conditions PASS.

## Files Changed
- `.claude/workflows/implement-ticket.js` — Test-phase prompt now reads the `performance` tag and
  conditionally reminds `test-scoper` to include `tests/unit/perf/`/`tests/perf/`.
- `.claude/agents/test-scoper.md` — mirrored the identical rule in Scoping Rules.
- `tests/tools/test_perf_tag_test_scoper_wiring.py` (new) — 7 tests.
- `docs/guidelines/tag_taxonomy.md` — Process/Skill-signal section records the per-skill decision
  and what was actually built for `performance`.

## Parity
No `src/` files touched. `expected_subsystems_for_files()` → `{}`. No parity ledger entry needed.

## Completion Summary
Investigated all 3 candidate skills individually rather than assuming `security`'s successful gate
conversion generalizes. `api-design-principles` and `debugging-strategies` have no deterministic
verdict shape a gate could check — left advisory, no code change, matching this ticket's own
explicit warning against blanket-converting based on one success. `python-performance-optimization`
does have a real verdict shape (`PerfRegressionGate`), but investigation found it was already
reachable through the existing Test-phase gate — the real gap was `test-scoper`'s file-path-only
mapping missing performance-motivated changes outside `src/perf/`. Fixed that gap directly
(tag-driven prompt enrichment + matching agent-definition rule) rather than adding a duplicate new
phase. `docs/guidelines/tag_taxonomy.md` updated to record the decision, since it's the doc that
originally named `performance` as future tag-driven-gate-routing material. No known material gap.
