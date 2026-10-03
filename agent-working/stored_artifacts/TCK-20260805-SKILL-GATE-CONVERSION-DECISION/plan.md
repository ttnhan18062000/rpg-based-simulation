---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260805-SKILL-GATE-CONVERSION-DECISION
artifact_type: plan
tags: [skills, workflows]
---

# Plan — TCK-20260805-SKILL-GATE-CONVERSION-DECISION

## Decisions (per skill, per investigation.md)
1. `api-design-principles` — leave advisory, no code change.
2. `debugging-strategies` — leave advisory, no code change.
3. `python-performance-optimization` — "other fix": strengthen the existing Test-phase gate's
   reliability for performance-tagged tickets, rather than adding a new gate/phase.

## Implementation
- `.claude/workflows/implement-ticket.js` — Test-phase agent prompt (the `test-scoper` `agent()`
  call, currently only passed `files_changed`): add a conditional block, gated on
  `ticketInfo.tags && ticketInfo.tags.includes('performance')`, instructing the agent to always
  include `tests/unit/perf/` and `tests/perf/` (`-m "not slow"`) in its scoped pytest command,
  citing `docs/performance/perf_baseline_policy.md` §3 as the real regression-gate this ensures
  gets run. Mirrors `Security-Review`'s own precedent of reading `ticketInfo.tags` directly
  (`implement-ticket.js:1228-1234`) rather than a re-derived copy.
- `.claude/agents/test-scoper.md` — add the same rule to "## Scoping Rules", so the agent
  definition and the orchestrator prompt stay consistent (same discipline this session applied to
  `implement-ticket/SKILL.md` vs `implement-ticket.js`).
- No new `phase(...)` block, no new `return { status: ... }` — this is a prompt enrichment of the
  existing Test-phase gate, not a new phase; `TESTS_FAILED` remains the only blocking status this
  path can produce.

## Tests
New `tests/tools/test_perf_tag_test_scoper_wiring.py` — static raw-source-text tests against
`implement-ticket.js` and `test-scoper.md`, mirroring
`tests/tools/test_document_update_phase_wiring.py`'s established pattern (this workflow file has
no JS test runner in this repo; it is read as text, not executed). Covers: the tag check reads
`ticketInfo.tags` directly; the reminder text sits inside the Test-phase prompt (not a separate
step); it cites the real regression-gate doc; it names both `tests/unit/perf/` and `tests/perf/`;
no new blocking status is introduced (the next `return { status: ...}` after the tag check is
still `TESTS_FAILED`, the pre-existing one); `test-scoper.md` documents the identical rule in its
Scoping Rules section.

## Parity
No `src/` files touched (`.claude/workflows/*.js` and `.claude/agents/*.md` are not `src/` paths).
`expected_subsystems_for_files()` → `{}`. No parity ledger entry needed, same precedent as this
batch's earlier tickets.

## Acceptance-Criteria Map
- AC1 (per-skill decision with explicit reasoning) → investigation.md's three per-skill sections,
  each explicitly addressing the pass/fail-verdict-shape asymmetry.
- AC2 (if any gate added, mirror WORKFLOW-SECURITY-GATE's test pattern) → N/A by design — no new
  gate was added; investigation.md explains why the existing Test-phase gate, once strengthened,
  already covers the one skill (`python-performance-optimization`) with a real verdict shape.
- AC3 (coordination check with FRONTEND-DESIGN-TRIGGER-REOPEN) → satisfied — this ticket does not
  touch CLAUDE.md's Proactive Tool Use table at all, so no coordination conflict exists.
