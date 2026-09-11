---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-LIFECYCLE-SCORE-WORLD-ARCHETYPE-AWARENESS
phase: done
date: 2026-08-08
tags: [simulation-quality, world]
---

# TCK-20260808-LIFECYCLE-SCORE-WORLD-ARCHETYPE-AWARENESS

## Title
`wilderness_survival`'s 71%-identical population is not a bug — it's a deliberately-authored
monster-only "no settlement" world — but the lifecycle-score tool has no way to say so, and
flags it identically to an accidentally-homogeneous world

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The 2026-08-08 full-corpus lifecycle-score run flagged `wilderness_survival` as the corpus's most
extreme diversity outlier: **71% of its 14 entities share one identical event-type shape**
(`{biological_state_changed, capability_growth_stalled, hazard_drain_applied, movement,
progression_plateau_detected, project_started, strategic_goal_changed}`), next-worst in the
corpus is 44%.

**Investigated directly, not assumed a bug.** Read `data/worlds/wilderness_survival/world.yaml`'s
own authored `description` field: *"High danger ecology world with **no settlement** — survival
challenge for entities placed in a hostile natural environment."* Confirmed via
`world.resolved.yaml`: **zero** `town`-type regions (all 4 regions are `wilderness`), exactly
**1** building total (`healer_hut`), and its entire population (11 entities: 6 undead sentinels,
4 hungry wolves, 1 alpha wolf) is monster-role only — no CITIZEN/WORKER roles at all. With no
town, no shop, no blacksmith (recipe learning requires one — `TCK-20260808-ENTITY-IDENTITY-ROLE-
FACTION-OBSERVABILITY-GAP`'s own finding), and no civilian population, there is structurally
nothing for these entities to do beyond vitals decay, hazard drain, and movement — the 71%
clustering is very likely the **correct, expected** outcome for a world explicitly designed as a
monster-only survival gauntlet, not a defect to fix by changing the world.

**The real gap is in the tool, not the world.** `tools/entity_lifecycle_score.py` (`TCK-20260808-
ENTITY-LIFECYCLE-SCORE-METRICS`) currently has no concept of world archetype/intent — it computes
the same `dominant_shape_share`/diversity figures for every world and presents them as directly
comparable, when a monster-gauntlet world and a civilian-heavy end-to-end world are not playing
the same game. This risks two real failure modes: (1) a genuinely low-diversity *civilian* world
gets under-weighted because the reader assumes "some worlds are just like this" without checking,
or (2) a deliberately-narrow world like `wilderness_survival` gets mis-flagged as broken when it's
working as designed.

## Scope
1. **Investigate**:
   - Check whether `docs/simulation_quality/corpus_tier_taxonomy.md`'s own existing archetype/tier
     framing (`unit`/`end_to_end`/`stress`, plus any per-world "archetype" description already on
     record) already captures enough of "what kind of world is this" to reuse directly, rather
     than inventing a new taxonomy.
   - Survey the other 19 corpus worlds' own authored `description` fields for similar
     self-declared intent signals (e.g. "dungeon_crawl" per its own precedent
     `docs/simulation_quality/corpus_tier_taxonomy.md`-registered note "pure-combat, no town/
     service infrastructure" — a similar monster-only-adjacent framing already exists for at
     least one other world) — determine whether a small, explicit set of archetype categories
     (e.g. "civilian-populated" vs. "monster-only"/"combat-only") is enough, or whether this
     needs a richer signal.
   - Decide: should archetype awareness live as new corpus_registry.yaml metadata (matching the
     `density`/`scale`/`tier` precedent from `TCK-20260808-SIMQ-CORPUS-WORLD-METADATA-REGISTRY`),
     as a lifecycle-score tool-side lookup, or both?
2. **Plan**: design the exact mechanism — likely a per-world `archetype` or `expected_diversity_
   ceiling` field, surfaced in the lifecycle-score tool's own output (e.g. a
   `diversity_context: "monster-only, low diversity expected"` annotation alongside
   `dominant_shape_share`) rather than a numeric correction to the metric itself (the raw number
   should stay honest; the *interpretation* is what needs context).
3. **Implement**: the metadata + tool-output annotation, with a real test confirming
   `wilderness_survival` is correctly flagged with its own archetype context, not silently
   suppressed or hidden.

## Out of Scope
- Changing `wilderness_survival` itself (adding a settlement, civilian population, etc.) — its
  own low diversity is judged expected-by-design in this ticket's own Investigate, not a defect
  to author around, unless Investigate finds real evidence otherwise.
- Building a general-purpose world-classification ML/heuristic system — a small, explicit,
  human-curated archetype signal is the expected scope, not automated inference.
- Re-scoring or re-weighting any of the 7 per-entity lifecycle metrics themselves — this ticket
  is about interpretation context for the population-level clustering output specifically, not
  the metric formulas from the sibling tickets.

## Acceptance Criteria
- [ ] investigation.md surveys existing archetype/tier signals across the corpus and confirms
      whether reuse or a new field is the right shape
- [ ] plan.md specifies the exact metadata field(s) and where the tool surfaces them
- [ ] Implemented: `wilderness_survival`'s own diversity figures ship with real archetype context
      in the tool's output, verified by a real test, not just a doc note
- [ ] `docs/simulation_quality/entity_lifecycle_score.md` / `docs/guides/entity_lifecycle_score.md`
      updated to explain the new context field
- [ ] Scoped pytest passes

## Related Tickets
- TCK-20260808-ENTITY-LIFECYCLE-SCORE-METRICS, TCK-20260808-ENTITY-LIFECYCLE-SCORE-CALIBRATION
  (the tool this ticket extends — both DONE)
- TCK-20260808-SIMQ-CORPUS-WORLD-METADATA-REGISTRY, TCK-20260808-CORPUS-DENSITY-METRICS-AND-GUIDE
  (precedent for per-world metadata fields in `corpus_registry.yaml` — both DONE)

## Related Docs
- `docs/simulation_quality/corpus_tier_taxonomy.md` (existing per-world tier/archetype framing to
  check for reuse first)
- `docs/simulation_quality/entity_lifecycle_score.md` / `docs/guides/entity_lifecycle_score.md`
  (the sibling tool's own docs, to be updated)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/entity_lifecycle_score.py` (`cluster_paths()`, tool output shape)
- `tools/generate_corpus_registry.py` (if archetype metadata lands in `corpus_registry.yaml`)
- `data/worlds/wilderness_survival/world.yaml` (the concrete example this ticket is grounded in)

## Assumptions / Open Questions
- Whether a small, explicit set of archetype categories is sufficient, or whether real per-world
  variation needs a richer signal — not assumed; Investigate should survey the real corpus before
  committing to a taxonomy shape.

## Implementation Notes
Subagent spawning unavailable this session (200/200 cap) — self-performed throughout, disclosed as
in the sibling tickets.

Real, comprehensive corpus survey found a field-level pitfall before settling on the right
signal: `entity.identity.role` (the `EntityRole` IntEnum, which does have a real `MONSTER=2`
value) is unreliable — real data shows every monster-kind entity across the corpus is tagged
`role=CITIZEN`, not `role=MONSTER` (a real, disclosed, out-of-scope finding for whoever next
touches entity role tagging). `entity.kind` (a content-driven string) is the real signal, matching
the resolved YAML's own `entities[].role` field (a confusing name collision, not the same as
`EntityRole`) 1:1.

The real survey found 3 monster-only worlds, not just `wilderness_survival` as originally framed:
`wilderness_survival`, `dungeon_crawl`, `quest_dense_frontier` — all zero civilian-service
(worker/guard/merchant/blacksmith) population; every other 17 worlds have all 4. This is a
genuinely bimodal split across the real corpus, no world sits in between, supporting a small
2-value archetype enum rather than a richer taxonomy.

Reused `corpus_registry.yaml`'s existing `_worlds` metadata precedent (`density`/`scale`/`tier`)
rather than inventing a new taxonomy document, per Investigate's own finding that
`corpus_tier_taxonomy.md`'s tier dimension answers a different question (testing purpose, not
population archetype).

## Test Summary
`pytest tests/tools/test_corpus_registry.py tests/tools/test_entity_lifecycle_score.py -q` —
34/34 passed (5 new: 2 registry archetype tests, 3 diversity_context annotation tests), including
the pre-existing `test_corpus_registry_committed_file_matches_fresh_generation` regression guard
(confirms the regenerated registry with the new field matches a fresh run byte-for-byte).

## Files Changed
- `tools/generate_corpus_registry.py` — new `compute_archetype()`, wired into
  `build_worlds_section()`
- `config/simulation_quality/corpus_registry.yaml` — regenerated with the new `archetype` field
  (20 worlds)
- `tools/entity_lifecycle_score.py` — `cluster_paths()`/`score_run()`/`main()` thread an optional
  `world_name`, surfacing a `diversity_context` annotation when the world's archetype is
  `monster_only_gauntlet`
- `tests/tools/test_corpus_registry.py`, `tests/tools/test_entity_lifecycle_score.py` — new tests
- `docs/simulation_quality/entity_lifecycle_score.md`, `docs/guides/entity_lifecycle_score.md`,
  `docs/simulation_quality/corpus_tier_taxonomy.md` — updated

## Completion Summary
Extended the archetype-awareness gap beyond its original single-world framing: a real corpus-wide
survey found 3 monster-only worlds, not 1, and a real field-level pitfall (`EntityRole` enum
unreliable, `entity.kind` string is the real signal) along the way. Implemented as a small,
computed, reused-precedent registry field plus an optional, fail-open tool annotation — the raw
diversity numbers stay honest, only their interpretation gets context. All 5 of the ticket's own
Acceptance Criteria items satisfied.
