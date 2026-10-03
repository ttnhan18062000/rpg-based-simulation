---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP
phase: done
date: 2026-07-07
tags: [simulation-quality, world, corpus, calibration]
---

# TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP

## Title
`test_population_stability`/`test_hazard_kind_completeness` don't parametrize `dungeon_crawl`, `sandbox_world`, or `generated_frontier_3_42`

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found during `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION`'s Verify phase (done-checker gate).
`tests/unit/worldassembly/test_corpus_diversity.py`'s `POPULATION_STABILITY_WORLDS` list is built from
`ANCHORED_WORLD_BANDS.keys()` (`frontier_extended`, `frontier_living_world`, `wilderness_survival`,
`highland_traverse`, `swamp_border_world` — the 5 worlds `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`
anchored) plus the unit-tier isolation worlds added by later tickets
(`unit_faction_tension`/`unit_information_source`/`unit_selfmodel_pilot`/`hero_guild_routing`). It
never included `dungeon_crawl`, `sandbox_world`, `generated_frontier_3_42` (or `urban_political`,
though that one may have separate coverage — verify during investigation), so the >=60%-alive-floor
population-collapse regression guard and the hazard-kind-completeness guard do not run against them
at all. This predates `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION` (which added FACTION/
INFORMATION content to `dungeon_crawl` and `sandbox_world`, and content-only to
`generated_frontier_3_42`) — that ticket did not introduce the gap, it surfaced it.

## Scope
1. Confirm which of the corpus's 10+ compiled worlds currently have `test_population_stability`/
   `test_hazard_kind_completeness` coverage vs. not (re-derive from `POPULATION_STABILITY_WORLDS`
   and any other coverage list in `test_corpus_diversity.py`, don't assume the 3 named above are the
   only gaps — verify `urban_political`'s status too).
2. Add `dungeon_crawl`, `sandbox_world`, and `generated_frontier_3_42` (and `urban_political`, if
   confirmed missing) to `POPULATION_STABILITY_WORLDS`.
3. Run each newly-added world through `test_population_stability` and `test_hazard_kind_completeness`
   to confirm they actually pass — if any fails, that is a genuine pre-existing defect this ticket
   must then decide whether to fix (content/hazard-tag gap) or escalate, not silently paper over.

## Out of Scope
- Adding any of these worlds to `ANCHORED_WORLD_BANDS` (a separate, larger concern — entity-count-band
  anchoring, not just population-stability/hazard-kind coverage)
- Any FACTION/INFORMATION/AGENCY content changes — this is a test-coverage-only ticket

## Acceptance Criteria
- [x] Full audit of which corpus worlds have `test_population_stability`/`test_hazard_kind_completeness`
      coverage, documented in this ticket's investigation
- [x] `dungeon_crawl`, `sandbox_world`, `generated_frontier_3_42` added to `POPULATION_STABILITY_WORLDS`
      (plus `urban_political` if confirmed missing)
- [x] All newly-covered worlds pass both tests, or any genuine failure is documented and escalated
      (not silently fixed as an undocumented side effect)

## Related Tickets
- TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION — the ticket whose done-checker gate surfaced this
  pre-existing gap
- TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS — originally added `test_population_stability` and the 5-world
  `ANCHORED_WORLD_BANDS` list this ticket's `POPULATION_STABILITY_WORLDS` builds on
- TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC — parent epic; relocated into
  `tickets/todos/simq-deep-coverage/`. Sequenced FIRST (with the other 3 resource/coverage-gap
  tickets) per that folder's `SEQUENCE.md` — `dungeon_crawl`, `sandbox_world`, and
  `generated_frontier_3_42` are exactly the worlds carrying (or, for `generated_frontier_3_42`,
  about to newly carry) this epic's long-run anchors, so closing their population-stability
  coverage gap first is directly relevant groundwork

## Related Docs
- None beyond the code itself (`tests/unit/worldassembly/test_corpus_diversity.py`'s own module
  docstring documents `test_population_stability`'s purpose)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION/` — where this gap was found

## Related Code Areas
- `tests/unit/worldassembly/test_corpus_diversity.py` — `POPULATION_STABILITY_WORLDS`,
  `test_population_stability`, `test_hazard_kind_completeness`

## Assumptions / Open Questions
- Assumes adding these worlds to the list is purely additive and low-risk (matching the precedent of
  every prior ticket that added a world to this same list) — but a genuine population-collapse or
  hazard-kind failure surfacing for one of them is a real possibility this ticket must handle
  honestly, not assume away.

## Implementation Notes
**Audit (Scope item 1).** `tests/unit/worldassembly/test_corpus_diversity.py` has two
world-coverage lists: `POPULATION_STABILITY_WORLDS` (12 worlds: the 8 `ANCHORED_WORLD_BANDS` keys
plus 4 unit-tier isolation worlds) and, previously, `test_hazard_kind_completeness`'s inline
`list(ANCHORED_WORLD_BANDS.keys())` (8 worlds — same set as the entity-count-band test). The
corpus (`data/worlds/*`) has 16 compiled worlds. Cross-referencing against the corpus found 5
worlds with zero `test_population_stability` coverage: `dungeon_crawl`, `sandbox_world`,
`generated_frontier_3_42`, `urban_political` (all four named/implied in the ticket), plus
`simq_routing_test`. `simq_routing_test` was deliberately left out: per
`tickets/done/TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY.md` it is explicitly a calibration-only
world (its own `evaluate_simq.py`/`grade_anchors.json` regression path), the same reason it was
never folded into `ANCHORED_WORLD_BANDS` or `POPULATION_STABILITY_WORLDS` by any prior ticket — out
of this ticket's named scope, left untouched. `urban_political` was confirmed missing from both
lists, as the ticket flagged as needing verification.

**Fix (Scope item 2).** Added `dungeon_crawl`, `sandbox_world`, `generated_frontier_3_42`,
`urban_political` to `POPULATION_STABILITY_WORLDS`. For `test_hazard_kind_completeness`, the ticket
title/acceptance-criteria ("both tests", "pass both tests") required parallel coverage, but folding
these 4 worlds into `ANCHORED_WORLD_BANDS` itself was explicitly out of scope (would also pull them
into `test_entity_count_band`'s entity-count-band anchoring). Introduced a new
`HAZARD_KIND_COMPLETENESS_WORLDS` list (`ANCHORED_WORLD_BANDS` keys + the same 4 worlds) and
repointed `test_hazard_kind_completeness`'s parametrize at it instead of
`list(ANCHORED_WORLD_BANDS.keys())`. This is additive to `ANCHORED_WORLD_BANDS` in list form only —
`ANCHORED_WORLD_BANDS` itself, and `test_entity_count_band`'s parametrize, are untouched.

**Verification (Scope item 3).** Ran both tests against all 4 newly-added worlds:
- `test_hazard_kind_completeness`: all 4 pass cleanly (12/12 total, up from 8/8).
- `test_population_stability` (300 ticks, seed 42, 60%-alive floor): `sandbox_world` and
  `generated_frontier_3_42` pass cleanly. `dungeon_crawl` and `urban_political` **genuinely fail** —
  `dungeon_crawl` collapses to 43.8% alive by tick 50 (early-tick pattern matching Finding 3);
  `urban_political` erodes to 56.7% alive by tick 300 (late-tick, narrow 1-entity miss). Per the
  ticket's own instruction ("must then decide whether to fix ... or escalate, not silently paper
  over") and the explicit test-coverage-only scope boundary (no content/config changes allowed),
  these are escalated rather than fixed here: filed
  `tickets/todos/TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE.md` (standard tier) as the
  root-cause/fix ticket, and marked both parametrize cases
  `@pytest.mark.xfail(strict=False, reason=...)` (matching the codebase's existing xfail convention
  in `tests/integration/scenarios/test_content_foundation.py`) via a new
  `KNOWN_POPULATION_COLLAPSE_WORLDS` dict, so the coverage is real, documented, and traceable rather
  than silently excluded or left red. Full suite: 48 passed, 2 xfailed, 0 unexpected failures.

## Test Summary
`.venv/bin/python3 -m pytest tests/unit/worldassembly/test_corpus_diversity.py -v` — 48 passed,
2 xfailed (`test_population_stability[dungeon_crawl]`, `test_population_stability[urban_political]`,
both documented pre-existing defects, escalated to TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE).
50/50 collected, 0 unexpected failures, 0 skipped.

## Files Changed
- `tests/unit/worldassembly/test_corpus_diversity.py`
- `tickets/todos/TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE.md` (new — escalation ticket)

## Completion Summary
Closed the coverage gap: `POPULATION_STABILITY_WORLDS` now covers all corpus worlds except the
intentionally-separate `simq_routing_test` calibration world; `test_hazard_kind_completeness` gained
a parallel `HAZARD_KIND_COMPLETENESS_WORLDS` list covering the same 4 newly-added worlds without
touching `ANCHORED_WORLD_BANDS`. Two genuine pre-existing population-collapse defects
(`dungeon_crawl`, `urban_political`) were found and escalated (not fixed, per scope) to a new
standard-tier ticket with `xfail` markers keeping them visible and traceable.
