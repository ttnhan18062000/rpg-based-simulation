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
DONE

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
- [x] investigation.md confirms, file by file, which `docs/systems/*.md` files are stale vs. real
      (not assumed from the two files already found) — 8 of 10 confirmed stale, 2 confirmed
      current, via direct symbol-level cross-checks against `src/`, not a frontmatter heuristic
- [x] Each confirmed-stale doc has a real, actioned outcome (retired/rewritten/deleted with a
      pointer to the real current doc) — not left silently flagged. All 8 archived to
      `docs/archive/systems/` with a pointer note; 5 real cross-references elsewhere in the repo
      updated; disclosed (not silently absorbed) where no single current replacement doc exists
- [x] `docs/REGISTRY.yaml` regenerated if any doc frontmatter/status changed
- [x] No `src/` changes (hotfix tier, doc-only)

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
- `stored_artifacts/TCK-20260809-STALE-DOCS-AI-BRAIN-ARCHITECTURE-AUDIT/`

## Related Code Areas
- `src/ai/goals/`, `src/engine/tactical.py`, `src/engine/cognition.py` (the real, active AI/combat
  decision architecture these docs should actually describe)

## Assumptions / Open Questions
- Whether any other `docs/systems/*.md` files beyond the two already confirmed are also stale —
  not assumed; Investigate checked each one directly. Resolved: 6 more were found stale
  (`ai_system.md`, `buildings_and_economy.md`, `combat_and_progression.md`,
  `world_evolution_and_resilience.md`, `world_generation.md`, `world.md`); 2 confirmed current
  (`faction_contract.md`, `strategic_cognition.md`).
- Whether `status: active` + no `last_verified` frontmatter reliably predicts staleness — tested
  and rejected as a shortcut: it correlated with staleness in 7/8 cases but `strategic_cognition.md`
  broke the pattern (confirmed current via direct symbol check despite matching the "risky"
  frontmatter shape). Direct per-file symbol verification remained mandatory throughout.

## Implementation Notes
Created `docs/archive/systems/` (new subfolder, matching the existing per-source-directory
convention already used by `docs/archive/combat/`, `docs/archive/core/`, `docs/archive/world/`).
`git mv`'d all 8 confirmed-stale files there, rewrote each one's frontmatter to this repo's real
archive convention (`status: archive`, `authority: P2`, `audience: historical`, `layer: systems`,
`original_date: unknown` — no generation date was ever recorded), and prepended a pointer note
citing the real current replacement doc(s) or disclosing the gap where none exists.

Rewrote `docs/systems/README.md` to link only the 2 confirmed-current files plus a note on the
retired set.

A dedicated cross-reference sweep (grep across all of `docs/`, `.claude/`, `.agents/` for live
links to the 8 archived paths — not just re-checking symbol names) found 5 real live references
needing updates beyond the directory's own README: `docs/simulation/town_contract.md` and
`docs/world/generator_contract.md` (both `status: authoritative`, `last_verified`-dated — found
only via this sweep, not the initial symbol-only investigation pass, which had wrongly concluded
no current replacement existed for `buildings_and_economy.md`/`world_generation.md`; corrected
before finalizing), `docs/guides/diagram_index.md` (removed a stale mermaid-diagram table row),
and both the `.claude/` and `.agents/` copies of `systems-economy/SKILL.md` (re-pointed to
`town_contract.md`). Historical `stored_artifacts/*/investigation.md`/`plan.md` references from
already-closed, unrelated tickets were deliberately left untouched — frozen historical record,
not live guidance, matching this repo's own convention.

`docs/REGISTRY.yaml` regenerated (active doc count 243→235, exactly the 8 archived files —
`docs/archive/` is a load-bearing skip-directory in `tools/generate_registry.py` by existing
design, confirmed via direct source read). `make knowledge-index-update` run (4 files re-embedded,
8 deleted — confirms the knowledge-search index also excludes `docs/archive/`).

## Test Summary
See `stored_artifacts/TCK-20260809-STALE-DOCS-AI-BRAIN-ARCHITECTURE-AUDIT/test_plan.md` for full
detail. Key result: a direct `search_docs` query for the exact terms that originally surfaced
`state_machines.md` as an apparently-current result now returns zero hits from the archived
content — the specific risk this ticket was filed to close is confirmed closed.

## Files Changed
- `docs/systems/state_machines.md`, `mechanics.md`, `ai_system.md`, `buildings_and_economy.md`,
  `combat_and_progression.md`, `world_evolution_and_resilience.md`, `world_generation.md`,
  `world.md` → moved to `docs/archive/systems/` (frontmatter rewritten, pointer note prepended)
- `docs/systems/README.md` (rewritten — 2 current links + retirement note)
- `docs/simulation/town_contract.md`, `docs/world/generator_contract.md` (cross-reference fixed)
- `docs/guides/diagram_index.md` (stale table row removed)
- `.claude/skills/systems-economy/SKILL.md`, `.agents/skills/systems-economy/SKILL.md`
  (cross-reference fixed)
- `docs/REGISTRY.yaml` (regenerated)

## Completion Summary
Audited all 10 files in `docs/systems/` (not assumed from the 2 originally flagged) via direct
symbol-level cross-checks against `src/`. Found 8 comprehensively stale — describing a
`src/actions/`-and-`src/ai/states.py`-centric architecture that predates the current codebase
structure, likely a single "generated from codebase analysis" snapshot never regenerated since —
and 2 confirmed still current. Archived the 8 stale files to `docs/archive/systems/` following
this repo's own real archival convention, each with a pointer note to its real current replacement
(or a disclosed gap where none exists). A dedicated link-integrity sweep found and fixed 5 real
live cross-references elsewhere in the repo that would otherwise have kept pointing at now-archived
content, including 2 cases where the initial investigation had wrongly concluded no replacement
existed — corrected once found rather than shipped. `docs/REGISTRY.yaml` regenerated;
`search_docs` confirmed to no longer surface the archived content. No `src/` changes.
