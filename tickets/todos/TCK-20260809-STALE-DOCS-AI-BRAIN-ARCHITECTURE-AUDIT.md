---
status: active
layer: systems
authority: P2
audience: agent
ticket_id: TCK-20260809-STALE-DOCS-AI-BRAIN-ARCHITECTURE-AUDIT
phase: open
date: 2026-08-09
tags: [documentation, cognition]
---

# TCK-20260809-STALE-DOCS-AI-BRAIN-ARCHITECTURE-AUDIT

## Title
`docs/systems/state_machines.md` and `docs/systems/mechanics.md` (both `status: active`) describe
an `AIBrain`/`STATE_HANDLERS`/`src/ai/states/` architecture that does not exist anywhere in the
current codebase — confirmed via direct `ls`/`find`, not assumed

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Found while investigating `TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY` (same session):
`docs/systems/state_machines.md` describes a 23-state `AIBrain`/`STATE_HANDLERS` finite state
machine ("Generated from codebase analysis — `src/ai/states/`, `src/ai/brain.py`, `src/ai/goals/`,
`src/systems/`, `src/engine/`, `src/core/models/enums.py`"), with a documented `FLEE` state and
full transition table. Direct verification: `src/ai/states/` and `src/ai/brain.py` **do not
exist** in `src/` at all (confirmed via `ls`/`find`, zero results). The real, active AI
architecture is the `GoalRegistry`/`GoalScorer`/`tactical.py` (`TacticalDecisionSystem`) system —
a completely different design, with no `AIState` enum, no `STATE_HANDLERS` dict, no `AIBrain`
class anywhere in `src/`.

Its sibling `docs/systems/mechanics.md` shows the same pattern: its own "Action Economy" section
documents a `next_act_at`/`spd`-based action-delay formula (`Delay = 1.0 / max(0.1, spd/10.0)`)
that also has zero real references anywhere in `src/` (confirmed via grep for `next_act_at`) — the
real system uses `combat.readiness`/`readiness_speed` (see
`docs/engine/contracts/minimal_kernel.md` §5, real and current, cross-checked against source this
same session in `TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION`).

Both docs carry `status: active`, `layer: systems`, `authority: P1` frontmatter — nothing marks
them stale, and neither was caught by this session's own repeated use of `search_docs`, which
surfaced both as if-current, relevant results for AI/combat/flee queries. This is a real risk for
future investigations: an agent trusting these docs at face value would be reasoning about dead
code as if it were the real, active system.

## Scope
1. **Investigate** (mandatory before any doc edits):
   - Audit every file in `docs/systems/` (not just the two found so far —
     `ai_system.md`, `buildings_and_economy.md`, `combat_and_progression.md`,
     `faction_contract.md`, `strategic_cognition.md`, `world.md`,
     `world_evolution_and_resilience.md`, `world_generation.md`, `README.md`) against real `src/`
     symbols they claim to describe — confirm which are current, which are stale, and how stale
     (entirely superseded architecture vs. a few drifted details).
   - For each confirmed-stale doc, identify whether a real, current doc already covers the same
     ground elsewhere (e.g. `docs/engine/contracts/minimal_kernel.md` already documents the real
     readiness-gated action semantics that supersede `mechanics.md`'s own `next_act_at` section;
     the real `GoalRegistry`/`tactical.py` architecture may already be covered by
     `docs/engine/contracts/tactical_contract.md` and/or a strategy-layer doc not yet checked).
   - Check `docs/REGISTRY.yaml`/`docs/systems/README.md` for when these docs were last
     regenerated or hand-verified, if recorded, to help explain how the drift happened.
2. **Plan**: for each confirmed-stale doc, decide (per file, not blanket): retire/archive with a
   pointer to the real current doc, rewrite in place against real `src/` symbols, or (if a
   real current doc already fully supersedes it) delete outright — matching this repo's existing
   archive/retirement conventions (check `docs/guidelines/intentional_divergences.md` §3
   "Unsupported / Retired Behavior" and any `docs/archive/` precedent first).
3. **Implement**: only the real, confirmed-necessary doc changes — no `src/` changes are expected
   or in scope for this ticket.

## Out of Scope
- Any `src/` behavior change — this is a documentation-accuracy ticket only.
- Auditing doc trees outside `docs/systems/` (a much larger, separate effort — this ticket is
  scoped to the one directory where the staleness was actually found and confirmed).
- Building the AI/cognition features `state_machines.md`/`mechanics.md` describe but don't
  currently exist (e.g. a real `next_act_at`/`spd` action-delay system) — if Investigate finds a
  real current doc already covers the equivalent real mechanic, no new feature work is implied.

## Acceptance Criteria
- [ ] investigation.md confirms, file by file, which `docs/systems/*.md` files are stale vs. real
      (not assumed from the two files already found)
- [ ] Each confirmed-stale doc has a real, actioned outcome (retired/rewritten/deleted with a
      pointer to the real current doc) — not left silently flagged
- [ ] `docs/REGISTRY.yaml` regenerated if any doc frontmatter/status changed
- [ ] No `src/` changes (hotfix tier, doc-only)

## Related Tickets
- TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY (DONE — found this while investigating
  the real flee-decision architecture)
- TCK-20260709-REGISTRY-COUNT-STALE-DOCS (DONE — a different, unrelated stale-content finding;
  no overlap, checked to confirm before filing this ticket)

## Related Docs
- `docs/systems/state_machines.md`, `docs/systems/mechanics.md` (confirmed stale)
- `docs/engine/contracts/minimal_kernel.md`, `docs/engine/contracts/tactical_contract.md` (the
  real, current docs likely superseding at least part of the stale content)
- `docs/guidelines/intentional_divergences.md` §3 "Unsupported / Retired Behavior" (existing
  retirement convention to follow, if applicable)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/ai/goals/`, `src/engine/tactical.py`, `src/engine/cognition.py` (the real, active AI/combat
  decision architecture these docs should actually describe)

## Assumptions / Open Questions
- Whether any other `docs/systems/*.md` files beyond the two already confirmed are also stale —
  not assumed; Investigate must check each one directly.

## Implementation Notes
(To be filled during implementation.)

## Test Summary
(To be filled during implementation.)

## Files Changed
(To be filled during implementation.)

## Completion Summary
(To be filled during implementation.)
