---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS
phase: open
date: 2026-07-04T12:17:33Z
tags: [simulation-quality, faction]
---

# TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS

## Title
Expand faction_relationships.yaml coverage toward the P2-D 50%+ target

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Folds in `docs/plans/audit_fix_plan.md` P2-D ("Faction relationships sparse"). Per
`staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §1 and §3,
`data/content/social/faction_relationships.yaml` currently has **34 relationship entries covering
20 of 120 possible undirected faction pairs (16.7%)** across 15 of 16 factions (`neutral` has
zero) — well under the original P2-D target of 50%+ coverage (60+ pairs). This is a **global
content-density gap**, not a per-world one: every world draws from the same underactivated
relationship catalog, so fixing it once benefits every world simultaneously (investigation.md §3:
"same risk class as FACTION tension seeding" — pure content, additive, no code risk).

## Scope
1. Read the current `data/content/social/faction_relationships.yaml` (34 entries, 20/120 pairs) and
   `data/content/social/factions.yaml` (16 factions) to establish the exact current coverage matrix
   — which of the 120 undirected pairs are covered, which are not, and which faction (`neutral`) has
   zero relationships today.
2. Per P2-D's own fix guidance, prioritize **conflict and economy module factions first** (highest
   encounter frequency) — cross-reference which factions actually appear as "populated" across the
   corpus (investigation.md §2's per-world faction lists) to focus new relationship entries on
   factions that actually see gameplay traffic, not purely theoretical catalog completeness.
3. Author new relationship entries to reach at least 50%+ coverage of active cross-faction pairs
   (60+ of 120 undirected pairs, per P2-D's original target) — prioritizing factions with existing
   populated presence in the corpus (per investigation.md §2) and factions appearing in conflict/
   economy modules over factions with no live gameplay presence.
4. Ensure the `neutral` faction gets at least some explicit relationship entries rather than
   remaining fully default (P2-D's finding: "Factions without explicit relationships default to
   neutral, reducing encounter variety").
5. Re-run `make evaluate --dry-run` after the catalog change — this is global content, so it may
   affect FACTION-pillar-adjacent behavior in any world with faction interactions; confirm 0
   regressions or document and resolve any drift found.
6. Update `docs/plans/audit_fix_plan.md`'s P2-D section: change status from "UNVERIFIED" to
   resolved with the new coverage percentage, mirroring the resolution-note style already used for
   other P2 items in that document (e.g. P2-B, P2-C).
7. Update the P2-D row in the Summary Table at the bottom of `audit_fix_plan.md`.

## Out of Scope
- Any per-world content changes (`faction_tension_overrides`, `information_source_profiles`) — that
  is tickets 4, 6-8 in this batch; this ticket is exclusively the global relationship catalog
- Implementing any new faction-interaction engine logic — `DiplomaticStateMachine`/
  `MilitaryConflictPhase` already exist (per `docs/plans/audit_fix_plan.md` P1-C, resolved) and are
  not touched by this ticket; this is pure catalog content
- Fixing any downstream bug this catalog expansion surfaces — file a follow-up ticket

## Acceptance Criteria
- [ ] `data/content/social/faction_relationships.yaml` coverage reaches at least 50% of the 120
      possible undirected faction pairs (60+ pairs), up from the current 20 (16.7%)
- [ ] Conflict and economy module factions are prioritized (documented reasoning in Implementation
      Notes, cross-referencing which factions have live populated presence per investigation.md §2)
- [ ] `neutral` faction has at least 1 explicit relationship entry (was 0 before this ticket)
- [ ] `make evaluate --dry-run` exits 0 with 0 regressions (or any drift found is documented and
      resolved, not silently ignored)
- [ ] `docs/plans/audit_fix_plan.md` P2-D section updated with resolution status and new coverage
      percentage, and the Summary Table's P2-D row updated to match
- [ ] `make knowledge-index-update` run (docs/plans/audit_fix_plan.md was modified)

## Related Tickets
- TCK-20260704-SIMQ-CORPUS-TIERS-EPIC (parent epic)
- TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO — its new FACTION-isolation world benefits from
  richer relationship coverage once this ticket lands
- TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION — its per-world faction tension seeding becomes
  more meaningfully differentiated once cross-faction relationships are denser
- TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS — its many-factions/small-map world benefits from richer
  relationship coverage to avoid an all-`neutral`-default outcome

## Related Docs
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §1 (mechanic
  inventory table, "Faction relationships catalog density" row) and §3 ("P2-D (faction
  relationships sparse) — fold-in candidate")
- `docs/plans/audit_fix_plan.md` — P2-D section (source finding, current UNVERIFIED status, 50%
  target) and Summary Table P2-D row

## Related Stored Artifacts
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/` — source investigation

## Related Code Areas
- `data/content/social/faction_relationships.yaml` — the file being expanded (34 entries today)
- `data/content/social/factions.yaml` — 16-faction catalog, `neutral` faction
- `src/engine/faction_decision.py` — `DiplomaticStateMachine` (consumer of this catalog, not
  modified by this ticket)

## Assumptions / Open Questions
- UQ-1: "Active cross-faction pairs" — does this mean all 120 mathematically possible pairs, or
  only pairs where both factions have populated presence somewhere in the current corpus (per
  investigation.md §2)? P2-D's original text says "50%+ coverage of active cross-faction pairs" —
  interpret "active" as populated-somewhere-in-corpus pairs first (a smaller, more meaningful
  denominator), but also report the raw 120-pair percentage for direct comparison against P2-D's
  original 16.7%-of-120 framing, so both readings are available.

## Implementation Notes
(to be filled during implementation)

## Test Summary
(to be filled during implementation)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
