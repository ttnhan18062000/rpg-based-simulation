---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY
phase: done
date: 2026-07-04T12:17:33Z
tags: [simulation-quality, agency, adventure, corpus, calibration]
---

# TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY

## Title
Author 1 new real-scale unit-tier world with ENABLE_ADVENTURE_ROUTING ON by design

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §2 found that
`simq_routing_test` — the only world with AGENCY-active behavior today — is explicitly authored as
a "minimal calibration/test world," not a world representing a shipped gameplay archetype
(investigation.md §2, "A routing-capable (AGENCY-active) world that is also a 'real' gameplay
archetype" gap). Per the user's AGENCY decision, this ticket authors 1 new world at a "real"
scale/archetype (not calibration-minimal) with `ENABLE_ADVENTURE_ROUTING` ON from inception, using
the generalized `feature_flags:` profile mechanism `TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE`
introduces. **This ticket does NOT reverse `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` for any existing
world** — the 9 non-routing worlds keep AGENCY=C, permanently, per that ruling. This is a new
archetype category ("routing-capable, real-scale") added alongside "routing-inactive" and
"routing-test-only," not a reinterpretation of any existing world's archetype-correctness.

## Scope
1. Confirm `TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE` has landed (hard dependency — this
   ticket needs the generalized `feature_flags:` mechanism, not a new hardcoded scenario-name
   special case in `evaluate_simq.py`).
2. Author a new world composition at a scale comparable to the existing mid-size real archetypes
   (investigation.md §2: `urban_political` 30 entities/3 regions, `dungeon_crawl` 32/4 — not
   `simq_routing_test`-minimal, and not as large as `frontier_extended`'s 56/10). Per
   investigation.md §3, `urban_political` already has a `hero_guild` faction population (4 entities)
   framed around adventuring, so a `hero_guild`-centric archetype is not architecturally foreign —
   this new world should have an explicit adventuring/route-selection framing in its description
   (unlike `dungeon_crawl`'s "pure dungeon exploration" or `urban_political`'s "settlement-heavy...
   trade pressure," neither of which mentions adventuring/routing per investigation.md §3).
3. Set `ENABLE_ADVENTURE_ROUTING: "ON"` in this world's own
   `config/simulation_quality/profiles/<world>.yaml` `feature_flags:` block (using ticket 3's
   generalized mechanism) — this world carries the flag ON by design from its first compile, not
   toggled on after the fact.
4. Compile the world, verify 0 warnings, verify population stability (>=60% alive floor) through
   200-500 ticks (matching `simq_routing_test`'s 500-tick calibration length as a reasonable
   default for an AGENCY-focused world, since route/goal-selection dynamics may need more ticks
   than the 200-tick default to show signal).
5. Run a 3-seed calibration matrix and add grade-anchor entries. Document the resulting AGENCY grade
   (expect B/A given `simq_routing_test`'s precedent of B/A with the same flag, but do not assume —
   verify and report the actual grade).
6. Update `docs/simulation_quality/eval_matrix_results.md`'s AGENCY Cross-World Design Note
   (added by `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`) to add this new world as a second
   routing-capable archetype, explicitly distinguishing it from both the "9 non-routing worlds stay
   AGENCY=C" ruling and from `simq_routing_test`'s calibration-only purpose.
7. Run `make evaluate --dry-run` (0 regressions on pre-existing corpus, including
   `simq_routing_test`'s own anchors which ticket 3 already protected) and
   `make knowledge-index-update` if docs changed.

## Out of Scope
- Reversing `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` for `urban_political`, `dungeon_crawl`, or any of
  the other 7 existing non-routing worlds — none of them change AGENCY grade as a result of this
  ticket
- Building the generalized flag mechanism itself (that is
  `TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE`, a hard dependency of this ticket)
- Seeding FACTION/INFORMATION/self-model content into this world (keep this world isolated to the
  AGENCY mechanic per unit-tier philosophy, unless investigation finds a compelling archetype
  reason a `hero_guild`-framed world also needs e.g. faction tension — default to isolation unless
  justified)

## Acceptance Criteria
- [x] `TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE` confirmed landed before this ticket's
      implementation begins
- [x] New world exists at real-archetype scale (comparable to `urban_political`/`dungeon_crawl`,
      not `simq_routing_test`-minimal), with an explicit adventuring/route-selection archetype
      framing in its description
- [x] `ENABLE_ADVENTURE_ROUTING: "ON"` set via this world's own profile YAML `feature_flags:` block
      (not a harness-level special case)
- [x] World compiles with 0 warnings, verified population-stable (>=60% alive floor) through
      200-500 ticks
- [x] 3-seed grade-anchor entries added; actual AGENCY grade documented honestly (not assumed)
- [x] `eval_matrix_results.md`'s AGENCY Cross-World Design Note updated to reflect this new
      routing-capable archetype without altering its existing "9 non-routing worlds stay C" language
- [x] None of the 9 existing non-routing worlds' AGENCY grades change
- [x] `make evaluate --dry-run` exits 0 with 0 regressions

## Related Tickets
- TCK-20260704-SIMQ-CORPUS-TIERS-EPIC (parent epic)
- TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE — **hard dependency**; this ticket cannot start
  implementation until that mechanism exists
- TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA — the ruling this ticket explicitly does NOT reverse for any
  existing world
- TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC — defines unit-tier criteria this world should meet

## Related Docs
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §2 ("A
  routing-capable (AGENCY-active) world that is also a 'real' gameplay archetype" gap) and §3
  ("`ENABLE_ADVENTURE_ROUTING` / AGENCY broadly" — middle-ground option analysis)
- `docs/simulation_quality/eval_matrix_results.md` — existing AGENCY Cross-World Design Note

## Related Stored Artifacts
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/` — source investigation
- `stored_artifacts/TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA/` — the DA ruling this ticket must remain
  consistent with

## Related Code Areas
- `config/simulation_quality/profiles/<new-world>.yaml` — new profile file, `feature_flags:` block
- `src/domains/optimization/feature_flags.py:16` — `ENABLE_ADVENTURE_ROUTING`
- `src/domains/adventure/phase.py` — `AdventureDecisionPhase` (not modified, only exercised)
- `data/content/social/factions.yaml` — `hero_guild` faction, if reused for this world's population
- `tests/simulation_quality/fixtures/grade_anchors.json`

## Assumptions / Open Questions
- UQ-1: Exact tick count for this world's calibration matrix — default to 500 (matching
  `simq_routing_test`'s existing calibration length) unless investigation finds a stronger reason
  to use the corpus's more common 200-tick default.
- UQ-2: World name — should be self-descriptive of its routing-capable archetype (e.g.
  `hero_guild_routing`, `adventurers_crossing`) and should not collide with `simq_routing_test`'s
  existing "test world" framing, since this world is explicitly meant to read as a real archetype,
  not a calibration harness fixture.

## Implementation Notes
**Partial progress, paused mid-Implement (2026-07-07), then resumed after an unrelated hotfix.**

Before the subagent-registration bug (`TCK-20260707-SUBAGENT-FRONTMATTER`) was discovered and fixed,
a first implementation attempt got partway through this ticket via a background agent that was
deliberately stopped once the bug was found (to avoid burning further work against broken tooling).
That attempt left real, still-valid artifacts on disk:
- `config/simulation_quality/profiles/hero_guild_routing.yaml` — `feature_flags: {ENABLE_ADVENTURE_ROUTING: "ON"}`
- `data/worlds/hero_guild_routing/world.yaml` — new world composition, `hero_guild_routing`, explicit
  adventuring/route-selection framing, 5 modules (`frontier_village_core`, `hero_adventurers`,
  `mountain_pass`, `ruins_mystery_quest`, `goblin_camp_conflict`), seed 717
- `data/worlds/hero_guild_routing/world_compile_report.json` — compiled clean: 31 entities, 4 regions,
  4 resource nodes, 5 buildings, 10 quests, 5 distinct populated factions, **0 warnings**
- `data/worlds/world_index.json` — `hero_guild_routing` registered

**Process gap found and flagged, not silently carried forward:** no
`staging_artifacts/TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY/` directory exists — the paused attempt
went straight to world authoring/compilation without first producing `investigation.md`, `plan.md`,
or getting an `architecture-reviewer` APPROVED verdict, which the standard tier requires before
Implement. The compiled world above is a reasonable-looking draft (matches Scope item 2's scale
target almost exactly: 31/4 vs. the ticket's `urban_political` 30/3 / `dungeon_crawl` 32/4
comparables), but it has not been validated against a written plan or an architecture review, so it
should be treated as a strong first draft, not confirmed-correct.

**Still outstanding (Scope items 4-7, none done yet):** 200-500 tick population-stability run
(>=60% alive floor), 3-seed calibration matrix + grade-anchor entries, actual AGENCY grade
measurement (not assumed), `eval_matrix_results.md` AGENCY Cross-World Design Note update,
`make evaluate --dry-run` (0 regressions check), `make knowledge-index-update` if docs change.

**Resumption (2026-07-07, after `TCK-20260707-SUBAGENT-FRONTMATTER` landed):** ran a full retroactive
Investigate → Plan → Review pass against the existing draft using the newly-registered real
subagents. Investigation confirmed KEEP-AS-IS for the draft world (satisfies Scope 1-3 on direct
evidence). The first architecture-review pass returned NEEDS_CHANGES — `calibrate_simq.py` has zero
alive-count/floor assertions, so the plan's original population-floor step didn't actually verify the
ticket's literal AC. Plan was revised (one fix-and-retry cycle, as instructed) to add a new standalone
world-scoped test as the authoritative floor proof instead of relying on the calibration matrix. Second
architecture-review pass: **APPROVED**. Then executed `staging_artifacts/TCK-20260704-SIMQ-CORPUS-
UNIT-WORLD-AGENCY/plan.md`'s 10 steps in order:

- **Step 1** (read-only confirmation): re-confirmed by direct read — `hero_guild_routing.yaml`'s
  only content is `feature_flags: {ENABLE_ADVENTURE_ROUTING: "ON"}`; `world_compile_report.json`
  shows `entity_count: 31, region_count: 4, warnings: []`; `world_index.json` has a well-formed
  entry. No edits made.
- **Step 2** (resource-tag coverage): found a **real gap**, not a clean pass. Direct inspection of
  `ResourceOpportunityProvider.get_opportunities()` against `data/content/world/resources.yaml`
  showed `iron_vein`/`frost_shard_cluster` (placed by `mountain_pass` in region
  `mountain_pass_zone`) carry no `source_region_tags` at all, and no resource definition in the
  catalog lists `mountain_pass_zone`, `goblin_camp`, or `haunted_battlefield` — confirmed
  empirically (0 opportunities returned for a hero in any of those 3 regions, any resource kind).
  Also confirmed via direct read of `AdventureDecisionPhase.apply()` that it only ever calls
  `ResourceOpportunityProvider` (not `ServiceOpportunityProvider`), which narrows and sharpens this
  finding. Per plan.md's instruction, did **not** fix `resources.yaml` (shared catalog, out of
  scope) — added `test_resource_opportunities_mountain_pass_zone_tag_gap` to
  `tests/unit/strategic/test_opportunities.py` documenting current behavior, and filed
  `tickets/todos/TCK-20260707-HERO-GUILD-ROUTING-RESOURCE-TAG-GAP.md` as a follow-up ticket (per the
  done-checker gate's "no material gaps unstated" finding — a doc mention alone wasn't sufficient).
- **Step 3** (generic OFF-flag guard): found already done — `hero_guild_routing` was already
  present in `POPULATION_STABILITY_WORLDS` in `tests/unit/worldassembly/test_corpus_diversity.py`
  (a leftover one-line change from the earlier paused implementation attempt), matching the plan
  exactly (one-line addition, no other edits to that file). Re-verified passing.
- **Step 4** (standalone ON-flag floor test): added new file
  `tests/unit/worldassembly/test_hero_guild_routing_population_stability.py`. Applies
  `ENABLE_ADVENTURE_ROUTING=FeatureMode.ON` onto the compiled `AuthoritativeState.feature_flags` via
  `dataclasses.replace`, mirroring `calibrate_simq.py::_run_engine`'s own mechanism, then drives
  `Kernel.tick_once()` for 500 ticks at seed 42 asserting the >=60% alive floor at every 50-tick
  checkpoint. Passed cleanly — no checkpoint dropped below the floor.
- **Step 5** (3-seed calibration matrix): ran seeds 42/123/456 at 500 ticks via
  `tools/calibrate_simq.py`. **Actual measured AGENCY grade: A at all 3 seeds** (no anomalous low
  grade — no stasis-collapse trace needed). Full 10-pillar grades recorded honestly in
  `grade_anchors.json` and `FAST_ANCHOR_KEYS`. Anchor-count sanity check confirmed: 52 → 55 keys
  (exactly 3 new), `FAST_ANCHOR_KEYS` gained exactly 3 entries.
- **Step 6** (`eval_matrix_results.md` world subsection): added
  `### hero_guild_routing (unit-tier — 31 entities, 4 regions)` after `unit_selfmodel_pilot`, with
  the measured 500t/3-seed table, the three-role clarification (Step 3 = generic OFF-flag baseline;
  Step 4 = authoritative ON-flag floor proof; Step 5 = grade measurement), and the Step 2
  resource-tag gap finding + recommended follow-up. Extended the "Unit-Tier Isolation Worlds" intro
  paragraph additively to name `hero_guild_routing` as a third (larger, 500t) world.
- **Step 7** (AGENCY Cross-World Design Note): appended one new paragraph naming
  `hero_guild_routing` as a second routing-capable archetype, distinct from
  `simq_routing_test`'s calibration-only role. Existing paragraphs verified byte-identical via diff.
- **Step 8** (`corpus_tier_taxonomy.md`): added the `hero_guild_routing` Unit-tier table row;
  extended the "Three new Unit-tier worlds" intro sentence to "Four new", naming this ticket.
- **Step 9** (parity ledger): appended one clause each to `INFRA-237` and `SIMQ-CALIBRATED-001`'s
  `support_boundary` fields naming `hero_guild_routing` and its measured A grade. Confirmed via
  `git diff` that only these two `support_boundary` fields changed (8 lines added, 0 removed) and
  the YAML still parses.
- **Step 10** (final sweep): `pytest tests/unit/worldassembly/test_corpus_diversity.py
  tests/simulation_quality/test_grade_regression.py -m "not slow" -q` → 26 passed; the slow
  `hero_guild_routing` parametrization and the new standalone ON-flag test both passed explicitly;
  `tools/evaluate_simq.py --dry-run` → 40 pillars checked, **0 regressions, 0 missing**, exit 0;
  `grep -rl ENABLE_ADVENTURE_ROUTING config/simulation_quality/profiles/` → exactly
  `simq_routing_test.yaml` and `hero_guild_routing.yaml`; `make knowledge-index-update` ran clean
  (21 files re-embedded).

No deviations from the architecture-approved plan. See
`staging_artifacts/TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY/plan.md`'s "Deviations" section
(added, empty by design) for confirmation. Full Verify-gate history: `done-checker`'s first pass
returned BLOCKED (stale ticket sections/unchecked ACs, uncleaned `data/runs/`, and the resource-tag
gap needing an actual follow-up ticket instead of just a doc mention) — all three were fixed
directly (this section rewritten, `data/runs/*` cleaned, follow-up ticket filed) before re-closing.

## Test Summary
`pytest tests/unit/strategic/test_opportunities.py -q` and
`pytest tests/unit/worldassembly/test_corpus_diversity.py tests/simulation_quality/test_grade_regression.py -m "not slow" -q`
and the explicit slow `hero_guild_routing` parametrization and the new standalone
`test_hero_guild_routing_population_stability.py` all passed: **35 passed, 0 failed** total across
the four scoped commands. `tools/evaluate_simq.py --dry-run` — 40 pillars checked, **0 regressions,
0 missing**, exit 0 (the direct check for "None of the 9 existing non-routing worlds' AGENCY grades
change"). `grep -rl ENABLE_ADVENTURE_ROUTING config/simulation_quality/profiles/` returned exactly
`simq_routing_test.yaml` and `hero_guild_routing.yaml`. `make knowledge-index-update` ran clean (21
files re-embedded). No coverage gaps.

## Files Changed
- `config/simulation_quality/profiles/hero_guild_routing.yaml` (new)
- `data/worlds/hero_guild_routing/world.yaml`, `world_compile_report.json`, `resolved/*` (4 files) (new)
- `data/worlds/world_index.json` (modified — `hero_guild_routing` entry registered)
- `tests/unit/strategic/test_opportunities.py` (modified — added `test_resource_opportunities_mountain_pass_zone_tag_gap`, documenting the Step 2 gap finding)
- `tests/unit/worldassembly/test_corpus_diversity.py` (modified — `hero_guild_routing` added to `POPULATION_STABILITY_WORLDS`)
- `tests/unit/worldassembly/test_hero_guild_routing_population_stability.py` (new — standalone ON-flag population-floor test, the authoritative AC evidence)
- `tests/simulation_quality/fixtures/grade_anchors.json` (modified — 3 new seed anchors, 52 → 55 keys)
- `tests/simulation_quality/test_grade_regression.py` (modified — `FAST_ANCHOR_KEYS` +3 entries)
- `docs/simulation_quality/eval_matrix_results.md` (modified — new `hero_guild_routing` subsection + AGENCY Cross-World Design Note paragraph, additive)
- `docs/simulation_quality/corpus_tier_taxonomy.md` (modified — new Unit-tier table row, additive)
- `docs/parity_ledger/infrastructure.yaml` (modified — `INFRA-237`/`SIMQ-CALIBRATED-001` `support_boundary` additive extensions)
- `staging_artifacts/TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY/` (new — `investigation.md`, `plan.md`, `test_plan.md`, backfilled per the process-gap note below)

## Completion Summary
Authored and calibrated `hero_guild_routing`, a new real-scale unit-tier world (31 entities, 4
regions) with `ENABLE_ADVENTURE_ROUTING: "ON"` set via its own profile YAML `feature_flags:` block
from first compile, using the generalized mechanism `TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE`
introduced. Measured AGENCY grade: **A at all 3 seeds** (42/123/456, 500t) — no stasis-collapse
anomaly. Population-stability floor (>=60% alive) proven directly by a new standalone test applying
the ON-flag condition to the compiled state, since `calibrate_simq.py`'s calibration matrix has no
floor assertion of its own (an architecture-review finding that reshaped the plan's Step 4 — see
`staging_artifacts/.../plan.md`'s Deviations section, though ultimately resolved with no deviation
from the *re-reviewed and re-approved* plan). `eval_matrix_results.md`'s AGENCY Cross-World Design
Note and the corpus tier taxonomy doc were extended additively; the 9 existing non-routing worlds'
AGENCY grades are unchanged (`make evaluate --dry-run`: 0 regressions across 40 pillars).

**Process gap self-corrected:** a first implementation attempt (before this session's
`TCK-20260707-SUBAGENT-FRONTMATTER` hotfix) authored the draft world directly without producing
`staging_artifacts/` or an architecture-review verdict. This resumption ran a full retroactive
Investigate → Plan → Review pass against that existing draft before continuing — the draft was
judged KEEP-AS-IS (it independently satisfied Scope items 1-3) and the missing staging artifacts
were backfilled.

**One real, deliberately out-of-scope gap found and tracked, not left unstated:** Step 2's
resource-tag coverage check found `mountain_pass_zone`/`goblin_camp`/`haunted_battlefield` have no
`source_region_tags` coverage in the shared `data/content/world/resources.yaml` catalog (same class
of gap `TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP` fixed for `hometown`). It did not harm
this world's measured AGENCY grade, and fixing a shared catalog file is out of scope for a
single-world authoring ticket — filed as a follow-up:
`tickets/todos/TCK-20260707-HERO-GUILD-ROUTING-RESOURCE-TAG-GAP.md`.

