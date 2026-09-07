---
status: active
layer: mechanics
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER
date: 2026-09-07
---

# Plan: TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER

## Summary
Author `docs/mechanics/07_social_political_dynamics.md` by promoting
`docs/simulation/social_systems_contract.md`'s structure, independently re-verifying every formula
against real code, and correcting the 5 sections Investigate found materially fabricated
(Appraisal's trust formula, Reputation, Contracts, Guilds, Party). Relocate the reputation-discount
fragment out of `03_economic_laws.md`. Cross-link (not rewrite) the 3 existing partial contracts.
Correct `social_systems_contract.md` itself in place rather than leave a known-inaccurate P1/active
doc contradicting the new chapter.

## Ordered Steps
1. Write `docs/mechanics/07_social_political_dynamics.md` — 10 numbered sections (Appraisal &
   Contracts, Relationships, Social Memory, Reputation, Contract Lifecycle, Shop Discount, Guilds,
   Party & Group Coordination, Party Composition, Mutation Rules), a Related Contracts cross-link
   section, and a Compliance Status footer, matching Chapter 06's exact frontmatter/heading/
   "Implementing Code" conventions.
2. Correct `docs/simulation/social_systems_contract.md`'s 5 diverged sections in place, each with an
   inline "Corrected 2026-09-07" note and a pointer to the new chapter's fuller treatment; add a
   top-of-file provenance note summarizing all 5.
3. Relocate `03_economic_laws.md` §4.1's formula body into Chapter 07 §6; replace the original
   subsection with a short pointer, not a duplicate.
4. Update `docs/mechanics/README.md` (TOC entry + Compliance Status summary line) and
   `06_worldbuilding_foundation.md` (master per-chapter Compliance Status table row) for chapter 07.
5. Update the two roadmap-tracking docs (`rpg_social_narrative_mechanics_hardening_plan.md`,
   `rpg_design_roadmap.md`'s Hardening backlog item 1) to reflect the hardening backlog is now fully
   shipped.
6. Regenerate `docs/REGISTRY.yaml`; run `make knowledge-index-update` (docs/ changed).
7. Verify: `tools/validate_frontmatter.py` on every touched/created doc; re-run
   `tests/tools/test_generate_registry.py` (registry-drift check) and any other doc-structure tests.

## Files To Change
- `docs/mechanics/07_social_political_dynamics.md` (new)
- `docs/mechanics/README.md`
- `docs/mechanics/06_worldbuilding_foundation.md`
- `docs/mechanics/03_economic_laws.md`
- `docs/simulation/social_systems_contract.md`
- `docs/plans/rpg_design_roadmap/rpg_social_narrative_mechanics_hardening_plan.md`
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`
- `docs/REGISTRY.yaml` (regenerated)

## Scope Guards
- Do not build any new mechanism, mutate any `src/` file, or edit `docs/parity_ledger/*.yaml` — this
  is a docs-only ticket; no behavior change, no parity entries affected.
- Do not rewrite the 3 existing partial contracts (`social_memory_contract.md`, `chronicle_contract.md`,
  `faction_contract.md`) — cross-link only.
- Do not re-litigate or re-decide the `SOC-FAC-*`/`SOC-CHRON-*` spot-check — already done 2026-09-05,
  cite it, don't redo it.
- Do not transcribe any formula from `social_systems_contract.md` without independently re-verifying
  it against the cited source file/line first.

## Dependency Map
Step 1 (write the new chapter) depends on Investigate's own per-formula verification being complete
first (already done). Steps 2-5 are independent of each other and can be done in any order once
step 1's corrected formulas are known. Step 6-7 depend on all doc edits (1-5) being complete.

## Acceptance Criteria Map
- AC1 (chapter exists, Certified Level 1, every formula cited against real code) → step 1, verified
  during Investigate.
- AC2 (liveness question resolved with a direct code check) → pre-resolved before this pass, cited
  in Chapter 07 §4 and the corrected Reputation section of `social_systems_contract.md`.
- AC3 (`03_economic_laws.md` fragment cross-linked, not duplicated) → step 3.
- AC4 (`SOC-FAC-*`/`SOC-CHRON-*` spot-check recorded) → already done 2026-09-05, unchanged by this
  ticket, cited in the new chapter's Related Contracts section.

## Risks
None outstanding.
