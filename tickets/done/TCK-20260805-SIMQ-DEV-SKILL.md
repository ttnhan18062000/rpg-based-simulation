---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260805-SIMQ-DEV-SKILL
phase: open
date: 2026-08-05
tags: [skills, simulation-quality]
---

# TCK-20260805-SIMQ-DEV-SKILL

## Title
Author a skill for developing/debugging simulation_quality scorers (complementing simq-audit's audit-only coverage)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Domain-coverage sweep child ticket, from `TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC`.
`src/simulation_quality/` already has a real, actively-used skill (`simq-audit`, 5 real
invocations, backed by `.claude/workflows/simq-audit.js` and `tools/simq_audit_gaps.py`), but
reading `simq-audit/SKILL.md` directly confirms it is entirely the audit/governance workflow
(Recalibrate → Classify Drift → Update Anchors → Sync Docs → Parity Check → Verify → Report — "is
this a regression against grade anchors"). It does not cover adding a new scorer, understanding
`pillar_accumulator.py`/`quality_hub.py` internals, or debugging why a specific pillar score came
out wrong. This ticket closes that development-side gap without touching or duplicating
`simq-audit`'s existing audit-side coverage.

## Scope
- Author a new skill (or a documented extension/companion to `simq-audit` — Plan decides the
  right shape) covering: `pillar_accumulator.py`/`pillars.py`/`quality_hub.py`/`score_record.py`
  internals, how to add a new scorer under `src/simulation_quality/scorers/`, and how to debug a
  specific pillar producing an unexpected score.
- Source from `docs/simulation_quality/quality_scoring_contract.md` and any other real contract
  docs for this subsystem, not authored from scratch.
- Explicitly do not duplicate or modify `simq-audit`'s existing audit/governance content — this is
  additive, a different phase of the same subsystem's lifecycle.

## Out of Scope
- Any change to `simq-audit/SKILL.md`, `simq-audit.js`, or `tools/simq_audit_gaps.py` — already
  correct for their own scope.
- The `src/observability/` gap — related but distinct, covered by its own sibling ticket.

## Acceptance Criteria
- [x] New standalone skill (`.claude/skills/simq-dev/SKILL.md`) authored, sourced from
      `docs/simulation_quality/quality_scoring_contract.md` §4/§7, covering data model, adding a
      pillar, adding a rule, conflict detection, and debugging — not audit/governance.
- [x] Does not duplicate `simq-audit`'s content — source-text guard test confirms zero overlap in
      audit-specific vocabulary (`Recalibrate`, `grade anchors`); `simq-audit/SKILL.md` untouched.
- [x] `docs/ai/skills.md` updated to list the new skill.

## Related Tickets
- TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC (parent epic)
- TCK-20260805-OBSERVABILITY-SKILL (sibling domain-gap ticket)
- TCK-20260628-SIMQ-EPIC (built the subsystem this skill covers)

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md`
- `.claude/skills/simq-audit/SKILL.md` (read-only reference — the existing audit-side coverage this ticket must not duplicate)

## Related Stored Artifacts
None yet (standard tier, will be created).

## Related Code Areas
- `src/simulation_quality/` (pillar_accumulator.py, pillars.py, quality_hub.py, score_record.py, scorers/)
- `.claude/skills/` (new skill target)

## Assumptions / Open Questions
Exact shape (standalone new skill vs. companion extension to simq-audit) — Plan phase decides.

## Implementation Notes
Authored `.claude/skills/simq-dev/SKILL.md`, `source: project`, sourced from
`quality_scoring_contract.md`: the 3 core data-model classes (§4.1-4.3: `ScoreRecord`,
`ScoringContext`, `PillarAccumulator`), the real 9-step "adding a new pillar" protocol (§7.1,
including the hard "no numeric literals in scorer code" rule), the "adding a scoring rule" steps
(§7.2), and the conflict-detection rules (§7.3) — including the real, disclosed, still-unresolved
divergence (`EconomyScorer.paid_info_transaction` returns a live-scored contribution where the
design says "documentary only," per `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION`'s own
Implementation Notes) stated plainly rather than hidden, since it's a real place to check when
debugging an unexpectedly-high ECONOMY score. Confirmed `simq-audit/SKILL.md` is entirely
audit/governance (Recalibrate → drift → anchors) with zero dev-side overlap — this skill is purely
additive, cross-referencing but not duplicating it.

Applied `OBSERVABILITY-SKILL`'s finding directly: registered `simq-dev` in
`agent-orchestration/skills.yaml` before regenerating the `.agents/` Codex mirror (mirror
generation requires explicit contract registration, confirmed not needed to be rediscovered this
time).

**Real gate catch during Verify**: first `run_static_precheck` pass failed `frontmatter_valid` —
used `layer: simulation-quality` in all 3 staging artifacts' frontmatter, but the registered layer
value is `layer: simulation` (no `simulation-quality` layer exists in the registry). Fixed all 3
files, re-ran, clean pass.

Done entirely directly (no subagents — hard 200-agent spawn cap, per explicit user decision to
continue solo).

## Test Summary
New `tests/tools/test_simq_dev_skill_content.py` — 9 tests, all passing: valid frontmatter with
`source: project`; all 3 core data-model classes present; all 3 pillar-protocol markers present;
the `EconomyScorer`/`paid_info_transaction` divergence disclosed; a real no-duplication guard
(confirms `simq-audit`'s own `Recalibrate`/`grade anchors` vocabulary is genuinely absent from the
new skill, and genuinely present in `simq-audit` itself as a sanity check); cross-references
`simq-audit` by name; 2 cited test paths verified to actually exist on disk;
`docs/ai/skills.md` lists it; `.agents/` mirror body matches. Regression check:
`pytest tests/agent_orchestration_codex_adapter/` — 27 passed. `doc_staleness_check.py` → PASS.
`clean_data_runs_early()` → PASS. `expected_subsystems_for_files()` → `{}` — no parity entry
needed. `run_static_precheck('standard', ...)` — all 7 conditions PASS (after the frontmatter
layer fix above).

## Files Changed
- `.claude/skills/simq-dev/SKILL.md` (new) — the skill.
- `.agents/skills/simq-dev/SKILL.md` (new) — Codex mirror.
- `agent-orchestration/skills.yaml` — registered the new skill in the contract.
- `docs/ai/skills.md` — added to the Project-Level Skill Files table.
- `tests/tools/test_simq_dev_skill_content.py` (new) — 9 tests.

## Parity
No `src/` files touched. `expected_subsystems_for_files()` → `{}`. No parity ledger entry needed.

## Completion Summary
Closed the confirmed dev-side gap in `src/simulation_quality/` skill coverage without touching or
duplicating `simq-audit`'s existing, correct audit-workflow scope — verified by a genuine
source-text no-overlap guard, not just an assertion in prose. Content grounded in real contract
§4/§7 sections, including a disclosed real divergence between documented and actual scorer
behavior (a genuinely useful debugging lead, not something to paper over). Caught and fixed a real
frontmatter layer-name error at Verify rather than before. No known material gap.
