---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC
phase: open
date: 2026-07-04T12:17:33Z
tags: [simulation-quality, world, corpus, documentation, taxonomy]
---

# TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC

## Title
Document the Unit/End-to-End/Stress/Regression SimQ corpus tier taxonomy

## Status
OPEN

## Tier
hotfix

## Type
documentation

## Priority
P1

## Request Summary
`staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` and the parent epic
(`TCK-20260704-SIMQ-CORPUS-TIERS-EPIC`) introduce a test-pyramid-style tier vocabulary for the SimQ
world corpus (Unit / End-to-End / Stress / Regression) that does not exist anywhere in the docs
today. Every other child ticket in this batch (`TCK-20260704-SIMQ-CORPUS-*`) references this
taxonomy by name — new worlds are described as "unit-tier" or "stress-tier" without a canonical
definition of what that means, which worlds belong to which tier today, or how a future world
addition should be classified. This ticket creates that canonical reference.

**Tier justification (hotfix, not standard):** this is a single new doc with no code changes, no
schema changes, and no calibration re-run required — it only classifies and describes worlds/
mechanics that already exist per the investigation's own tables. It mirrors the doc-only hotfix
precedent set by `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` (same shape: document an already-decided
architectural stance, no staging artifacts required). Self-evident intent: transcribe the tier
definitions and the investigation's existing world-inventory table into a durable, discoverable
doc location.

## Scope
1. Create a new doc — `docs/simulation_quality/corpus_tier_taxonomy.md` — defining:
   - **Unit tier**: new, small, synthetic-content-OK worlds, each isolating exactly ONE gated
     mechanic with everything else at baseline. Template/synthetic content acceptable; narrative
     coherence is not a goal.
   - **End-to-end tier**: existing archetype worlds get richer, bespoke, archetype-matched content
     (not templated).
   - **Stress tier**: new worlds specifically filling identified scale-diversity gaps.
   - **Regression/baseline tier**: already-calibration-anchored worlds, left alone as a stable
     control group — explicitly a "do not touch" policy, not an oversight.
2. Map every world currently under `data/worlds/` to its tier as of 2026-07-04 (all 10 are
   Regression/baseline today, since none of the new unit/stress worlds exist yet — state this
   explicitly so the doc doesn't read as if tiers are already populated).
3. Define criteria for classifying a future world addition into one of the four tiers (e.g.
   "isolates exactly one Pattern-6 field with everything else at baseline" → unit tier; "fills a
   named scale-diversity gap from an investigation" → stress tier; "extends an existing archetype
   world's content richness" → end-to-end tier).
4. Cross-reference `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` as
   the evidentiary source for the current per-world content/scale tables (§1, §2), rather than
   duplicating the full tables verbatim.
5. Add an entry to `docs/REGISTRY.yaml` if a REGISTRY entry pattern applies to
   `docs/simulation_quality/` docs (check existing entries for `eval_matrix_results.md` /
   `event_type_coverage.md` for the pattern to follow).
6. Run `make knowledge-index-update` (required — this ticket creates a new file under `docs/`).

## Out of Scope
- Authoring any actual unit/stress-tier world content (that is tickets 4-6, 8 in this batch)
- Changing any existing world's tier classification behavior (this ticket only documents; it does
  not gate or enforce tier membership in code)
- Re-running `make evaluate` calibration (no world content or code changes in this ticket)

## Acceptance Criteria
- [ ] `docs/simulation_quality/corpus_tier_taxonomy.md` exists with all four tier definitions
- [ ] All 10 current worlds under `data/worlds/` are explicitly mapped to Regression/baseline tier
      in the new doc, with a note that no unit/end-to-end-richened/stress worlds exist yet as of
      this ticket's authoring date
- [ ] Future-classification criteria section exists and is concrete enough that a later ticket could
      cite it (not vague)
- [ ] New doc cites `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md`
      directly rather than re-deriving its tables
- [ ] `docs/REGISTRY.yaml` updated if applicable (per existing `docs/simulation_quality/*` entries)
- [ ] `make knowledge-index-update` run successfully after the doc is added
- [ ] `python3 tools/validate_frontmatter.py docs/simulation_quality/corpus_tier_taxonomy.md
      --content-type doc` passes

## Related Tickets
- TCK-20260704-SIMQ-CORPUS-TIERS-EPIC (parent epic)
- TCK-20260704-SIMQ-CORPUS-SCALE-METRIC — references this taxonomy for scale-axis criteria
- TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO — first unit-tier worlds; must conform to this
  doc's unit-tier definition
- TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT — unit-tier world; must conform
- TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY — unit-tier world; must conform
- TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION — end-to-end tier; must conform
- TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS — stress tier; must conform
- TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA — doc-only hotfix precedent this ticket's tier choice mirrors

## Related Docs
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` — full per-world
  content/scale evidence (§1 mechanic inventory table, §2 scale diversity table and gap analysis)
- `docs/simulation_quality/eval_matrix_results.md` — existing calibration grade tables
- `docs/simulation_quality/quality_scoring_contract.md` — SimQ pillar contract
- `docs/plans/audit_fix_plan.md`

## Related Stored Artifacts
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/` — this ticket's evidentiary source

## Related Code Areas
- `data/worlds/` — the 10 worlds being tier-mapped (no code changes, reference only)
- `docs/REGISTRY.yaml`

## Assumptions / Open Questions
- UQ-1: Should the taxonomy doc live under `docs/simulation_quality/` (SimQ-specific) or
  `docs/guidelines/` (general authoring guidance)? Scoped to `docs/simulation_quality/` since the
  tiering is specifically about SimQ calibration corpus organization, not general world-authoring
  guidance (that's `docs/guides/content_authoring.md`) — confirm this placement is correct during
  implementation, and relocate if investigation reveals a stronger existing convention.

## Implementation Notes
(to be filled during implementation)

## Test Summary
(to be filled during implementation)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
