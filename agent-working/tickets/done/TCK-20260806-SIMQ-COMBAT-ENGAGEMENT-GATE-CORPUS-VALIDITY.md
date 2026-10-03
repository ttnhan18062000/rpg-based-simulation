---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY
phase: done
date: 2026-08-06
tags: [simulation-quality, combat, progression, feature-flags]
---

# TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY

## Title
Investigate whether `ENABLE_COMBAT_ENGAGEMENT` and quest-reward dispensing being universally
dormant across all 17 SimQ profiles invalidates the COMBAT/PROGRESSION corpus signal

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P0

## Request Summary
A 2026-08-06 raw-event investigation (3 fresh 500-tick calibration runs: `dungeon_crawl`,
`sandbox_world`, `hero_guild_routing` — 81 entities, 1,769 combined events, real
`simulation_events.jsonl`, not just `quality_report.json` rollups) found: **zero `entity_killed`,
`combat_resolved`, `level_up`, `xp_granted`, `skill_unlocked`, or `quest_reward_dispensed` events
in any of the three runs.** This directly contradicts `D20_simq_quality_status_review.md`'s Full
Pillar Health table, which currently reads COMBAT as "Healthy, archetype-correct spread" and
PROGRESSION as "Healthy, unchanged."

Root cause traced with high confidence:
- `PP-16 combat_engagement` (`CombatEngagementPhase`, `src/domains/combat_engagement/phase.py`,
  per `D19_domain_phase_inventory.md` §12) is `feature-gated` behind `ENABLE_COMBAT_ENGAGEMENT`,
  which defaults `FeatureMode.OFF` (`src/domains/optimization/feature_flags.py:17`) and is **never
  set to ON in any of the 17 files in `config/simulation_quality/profiles/`** (verified by grepping
  every profile YAML). This is the phase that "applies the damage formula, durability decay, and
  tactical modifiers" — without it, no real entity-vs-entity combat resolution happens anywhere in
  the SimQ corpus.
- Per `docs/mechanics/attribute_progression_contract.md`'s XP Gain Sources table, XP is granted
  only on a kill (`defender.identity.evolution_level * 10` monster / `* 20` hero) or a quest
  reward. With zero kills and zero quest rewards observed, `PP-28 evolution`
  (`EvolutionSystem`, which IS `active`/ungated per D19) never fires — not because it's broken, but
  because it is starved of XP input. **PP-28 itself looks correctly wired; the problem is upstream.**
- The `combat_initiated`/`combat_damage`/`near_death_survival` events that *did* appear in all
  three runs cannot be coming from `CombatEngagementPhase` (confirmed gated off) — they must come
  from a different source. Every observed hit was a flat, non-formula-scaled **25 lethal damage**
  from `"Attacker None"` (attacker untracked), immediately followed by a `near_death_survival`
  hardening save — never a kill, in every single observed instance across all 3 runs. Source of
  these events is not yet identified.
- Separately, `quest_event` fired constantly (179/64/407 times per run) reaching "started" status
  but never once reaching a reward-dispensing event — root cause not yet distinguished from the
  above (could be the same starvation chain, could be tick-length insufficiency for quest
  completion, could be a distinct bug).

This mirrors the AGENCY/`ENABLE_ADVENTURE_ROUTING` precedent (that flag is also default-OFF, but
was explicitly examined and DA-ruled as an intentional opt-in boundary, documented in
`quality_scoring_contract.md`). **No equivalent ruling exists for `ENABLE_COMBAT_ENGAGEMENT`** —
this appears to be an unexamined gap, not a deliberate decision, but that must be confirmed, not
assumed.

## Scope
1. **Trace the unidentified event source**: determine what system emits `combat_initiated` /
   `combat_damage` (flat 25 damage, `attacker_id: null`) / `near_death_survival` when
   `CombatEngagementPhase` is gated off. Candidates to check: a legacy/fallback combat path,
   hazard-drain damage misclassified by `event_extractor` as combat, or some other pre-PP-16
   mechanic. Cite exact source file/function.
2. **Determine whether `ENABLE_COMBAT_ENGAGEMENT` being off-by-default-and-never-enabled across all
   17 profiles is a deliberate ruling or an unexamined gap.** Check `git log`/ticket history for
   any prior decision on this flag (search `search_docs`/`graphify` first per Context Scan rule).
   If no ruling exists, this ticket's Investigate phase must produce a recommendation (flip ON for
   combat-relevant profiles, e.g. `dungeon_crawl`, vs. document as an intentional corpus limitation
   like AGENCY's DA ruling) — do not implement the flip without that recommendation being reasoned
   through explicitly, per the project's standing rule against forcing a fix before confirming
   bug-vs-intentional-behavior.
3. **Separately investigate the quest-reward-dispensing gap**: is it downstream of the same
   starvation chain, a distinct tick-length issue (quests may need more than 500 ticks to
   complete), or a separate bug in the quest completion → reward path?
4. Produce a concrete finding and recommendation; do not silently "fix" anything in this ticket
   without the recommendation being explicit and reasoned (this ticket may conclude with a
   follow-up implementation ticket rather than doing the flip itself, per the ECONOMY-ADVENTURE-
   ROUTE-SCORER-BIAS ticket's precedent of investigation-then-decide).
5. Correct `D20_simq_quality_status_review.md`'s Full Pillar Health table entries for COMBAT and
   PROGRESSION if this investigation confirms their "Healthy" verdicts were based on a corpus-wide
   disabled mechanic, not genuine archetype-correct balance.

## Out of Scope
- Actually flipping `ENABLE_COMBAT_ENGAGEMENT` to ON, re-running the full 79-scenario corpus, or
  recalibrating `grade_anchors.json` — that is follow-up implementation work once this
  investigation's recommendation is in hand, likely a separate ticket.
- `TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE`'s scoring-rule design work — that ticket is
  **blocked** on this one's findings (no point designing a capability-trend rule against data that
  may not exist under current corpus configuration).
- `TCK-20260806-SIMQ-FACTION-LIFECYCLE-TRAJECTORY` — unaffected; FACTION showed real activity
  (`diplomatic_transition` fired in every run) in the same raw-event pull, no dependency.

## Acceptance Criteria
- [ ] `investigation.md` identifies the exact source of the observed `combat_initiated`/
      `combat_damage`/`near_death_survival` events despite `CombatEngagementPhase` being gated off
- [ ] `investigation.md` states explicitly whether `ENABLE_COMBAT_ENGAGEMENT`'s off-by-default,
      never-enabled-anywhere status is a prior deliberate ruling (cite it) or an unexamined gap
- [ ] A concrete recommendation is produced (flip flag for specific profiles vs. document as
      intentional limitation), with reasoning, not just a raw finding
- [ ] The quest-reward-dispensing gap is traced to a specific cause (shared root cause, tick-length
      issue, or distinct bug), not left as "also zero, unexplained"
- [ ] `D20_simq_quality_status_review.md`'s COMBAT/PROGRESSION Full Pillar Health entries are
      corrected if their "Healthy" verdicts are found to rest on this gap
- [ ] `TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE` is updated to reflect whether it remains
      blocked, can proceed, or needs re-scoping based on this ticket's findings

## Related Tickets
- TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE (**blocked by this ticket** — its
  capability-trend scoring design needs to know whether real growth data exists in the corpus)
- TCK-20260806-SIMQ-LIFECYCLE-PILLAR-BOUNDARY-DOC (prior session doc — its PROGRESSION/COMBAT
  boundary ruling still holds; this ticket investigates whether the *data* behind those pillars is
  trustworthy, a distinct question)

## Related Docs
- `docs/audits/D19_domain_phase_inventory.md` §12 (PP-16 `combat_engagement`, feature-gated),
  §"PP-29" (`progression_conversion`, feature-gated, distinct from PP-28 `evolution` which is
  active)
- `docs/mechanics/attribute_progression_contract.md` (XP Gain Sources, Lifecycle sections)
- `src/domains/optimization/feature_flags.py` (all flag defaults)
- `docs/audits/D20_simq_quality_status_review.md` (Full Pillar Health table — COMBAT/PROGRESSION
  rows to potentially correct)
- `docs/simulation_quality/quality_scoring_contract.md` §5 COMBAT/PROGRESSION, AGENCY's
  `ENABLE_ADVENTURE_ROUTING` DA-ruling precedent (search for how that decision was documented)

## Related Stored Artifacts
None yet — will be created at
`staging_artifacts/TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY/` during
implementation.

## Related Code Areas
- `src/domains/combat_engagement/phase.py` (`CombatEngagementPhase`, gated)
- `src/engine/evolution.py` (`EvolutionSystem`, PP-28, active/ungated — confirmed not the bug)
- `src/domains/progression/phase.py` (`ProgressionConversionPhase`, PP-29, gated separately)
- `src/domains/optimization/feature_flags.py`
- `config/simulation_quality/profiles/*.yaml` (all 17)
- quest system / reward dispatch path (exact file TBD by Investigate)

## Assumptions / Open Questions
- Whether the unidentified flat-25-damage event source is itself a bug worth fixing independently
  of the `ENABLE_COMBAT_ENGAGEMENT` question, or an intentional simplified fallback, is unknown —
  Investigate must not assume either way.
- Whether quest-reward dispensing shares the combat-engagement root cause or is a distinct issue is
  explicitly left open per the Uncertainty Rule.

## Implementation Notes
Investigation escalated twice past its own starting premise, disclosed transparently rather than
forced to fit the original scope. Started from "is `ENABLE_COMBAT_ENGAGEMENT` an unexamined gap" —
found it is a deliberate, documented ruling (DEV-002) and was never the relevant lever anyway (it
gates posture assessment, not damage resolution). Traced the real combat/damage event source to
`event_extractor.py`'s post-tick HP-diff detection, and — via a second pass reading
`src/core/updates.py`/`src/engine/world_dynamics.py`/`src/engine/combat.py` directly — confirmed an
exact bug: the combat-damage branch never checks `CombatUpdate.outcome_kind`, so hazard drain
(honestly tagged `outcome_kind="HAZARD"` by `world_dynamics.py`) gets double-classified as combat.
That finding generalized further: `kernel.py:909` confirmed the entire observability pipeline (not
just combat) is built on this one post-tick diffing call, with a real delivery queue
(`BoundedObservabilityQueue`) sitting unused as a push target downstream of it.

Produced 3 follow-up tickets rather than expanding this one's scope: the confirmed bug fix
(hotfix), the generalized push-vs-diff architecture question (standard, investigation-first,
seeded with a concrete shaper-registry design candidate mirroring `QualityHub.SCORER_REGISTRY`),
and the still-open quest-completion-pacing question (standard, investigation-first). Updated
`TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE`'s blocking dependency to point at the two
combat-relevant follow-ups. Corrected `D20_simq_quality_status_review.md`'s COMBAT Full Pillar
Health entry (no longer an unqualified "Healthy") and added Finding 10 documenting the full chain.
No `src/`/`tests/` files touched by this ticket itself — confirmed via `git status` at both Review
and Architecture-Verify.

## Test Summary
No production code changed by this ticket (doc + ticket-filing only), so no `pytest` run.
Verification: `python3 tools/validate_frontmatter.py` passed on all 6 touched/created files (4 doc
files, 3 staging artifacts, corrected once after an initial `frontmatter_valid` gate FAIL on the
staging artifacts' schema — fixed by matching the schema from a prior session ticket's real staging
artifacts, not by loosening the check). `run_static_precheck('...', 'standard', None)` returned all
PASS on the second run. `make knowledge-index-update` ran successfully after the doc edits.

## Files Changed
- `docs/audits/D20_simq_quality_status_review.md` — corrected COMBAT Full Pillar Health entry,
  added Finding 10
- `staging_artifacts/TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY/` — investigation.md
  (+ 2 addenda), plan.md, test_plan.md
- `tickets/todos/simq-pillar-lifecycle-depth/TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX.md` (new)
- `tickets/todos/simq-pillar-lifecycle-depth/TCK-20260806-SIMQ-OBSERVABILITY-PUSH-BASED-ARCHITECTURE.md` (new)
- `tickets/todos/simq-pillar-lifecycle-depth/TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE.md` (new)
- `tickets/todos/simq-pillar-lifecycle-depth/TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE.md` — blocking dependency updated
- `tickets/todos/simq-pillar-lifecycle-depth/SEQUENCE.md` — rewritten for the full 6-ticket state

## Completion Summary
Investigated the reported zero-combat-kill/zero-XP finding from the parent raw-event pull. The
original hypothesis (`ENABLE_COMBAT_ENGAGEMENT` as an unexamined policy gap) was wrong — that flag
is a deliberate, already-documented ruling and doesn't even gate damage resolution. The real cause
is a confirmed, precise bug in `event_extractor.py` (missing `outcome_kind` check, causing hazard
drain to be double-classified as combat), now filed as its own hotfix with a known fix. That
finding generalized into a materially larger question — the entire observability pipeline is
post-tick diffing, not trigger-point emission — filed as its own standard-tier investigation,
seeded with a concrete candidate design (apply-layer emission via a small shaper registry,
mirroring an existing proven pattern in this codebase). Quest-completion pacing remains open,
tracked separately. `TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE` now correctly blocks on
the two real follow-ups instead of the resolved original question.
