---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC
artifact_type: investigation
tags: [simulation-quality, calibration, corpus, scoring, pillars, architecture]
---

# Investigation — TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC

Pre-ticket epic-scoping investigation (produced before the epic ticket ID existed, under the
working name `EPIC-SCOPE-simq-deep-coverage`; this file/folder was renamed to the real ticket ID
once the epic was created, mirroring the same rename this investigation's own §3 recommends this
epic learn from — see the `EPIC-SCOPE-INVESTIGATION-DOC-MISSING` ticket triage below). No code
changes made. Produced in response to a follow-up request after `TCK-20260704-SIMQ-CORPUS-TIERS-EPIC`
(10 tickets, corpus 10→17 worlds, tiered Unit/E2E/Stress/Regression). Two threads: (1) long-run
(≥1000t, capped at ~2000t) anchor coverage, (2) 10-pillar completeness. Also triages 6 pre-existing
standalone follow-up tickets in `tickets/todos/` for relocation into this epic's folder.

---

## 1. Long-Run Coverage Audit

### 1.1 Source of truth

- `tests/simulation_quality/fixtures/grade_anchors.json` — 61 total anchor entries.
- `tests/simulation_quality/test_grade_regression.py` — `FAST_ANCHOR_KEYS` (50 entries,
  200t/500t, run in the standard suite) vs `SLOW_ANCHOR_KEYS` (11 entries, 1000t/2000t,
  `@pytest.mark.slow`, excluded by `-m "not slow"`).
- Corpus has **17 worlds** (`data/worlds/*/` minus `world_index.json`): `crowded_frontier`,
  `dungeon_crawl`, `frontier_extended`, `frontier_living_world`, `frontier_marches`,
  `generated_frontier_3_42`, `hero_guild_routing`, `highland_traverse`,
  `resource_dense_basin`, `sandbox_world`, `simq_routing_test`, `swamp_border_world`,
  `unit_faction_tension`, `unit_information_source`, `unit_selfmodel_pilot`,
  `urban_political`, `wilderness_survival`.

### 1.2 Which worlds have ANY ≥1000t anchor today

Only **3 of 17 worlds** (18%) have any long-run anchor at all:

| World | 1000t anchors | 2000t anchors | Seeds covered |
|---|---|---|---|
| `dungeon_crawl` | seed42, seed123, seed456 | seed42, seed123, seed456 | 42/123/456 at both tiers |
| `sandbox_world` | seed42 | seed42 | seed42 only, both tiers |
| `urban_political` | seed42, seed123, seed456 | — (none) | 42/123/456 at 1000t only |

**14 of 17 worlds have zero anchors ≥1000t**: `crowded_frontier`, `frontier_extended`,
`frontier_living_world`, `frontier_marches`, `generated_frontier_3_42`, `hero_guild_routing`,
`highland_traverse`, `resource_dense_basin`, `simq_routing_test`, `swamp_border_world`,
`unit_faction_tension`, `unit_information_source`, `unit_selfmodel_pilot`,
`wilderness_survival`.

`generated_frontier_3_42` has **zero anchors of any kind** (not even 200t) in
`grade_anchors.json`, despite having its own `config/simulation_quality/profiles/
generated_frontier_3_42.yaml` — flagged as a smaller, separate gap (not part of the
long-run scope but worth a line item).

### 1.3 The critical finding: which pillars have NEVER been observed "hot" at ≥1000t

Grading across all 11 `SLOW_ANCHOR_KEYS` entries (the full ≥1000t evidence base):

| Pillar | Grades observed across all 11 long-run anchors | Long-run ceiling | Peak grade seen anywhere in the SHORT-run corpus (200/500t) | Which world/seed produces that peak |
|---|---|---|---|---|
| AGENCY | C,C,C,C,C,C,C,C,C,C,C | **C — literally invariant** | A | `simq_routing_test` (all seeds, 500t), `hero_guild_routing` (all seeds, 500t) |
| COMBAT | B,B,B,B,B,B,B,B,B,B,B | **B — literally invariant** | A | `dungeon_crawl_seed42_200t`, `urban_political_seed42/456_200t/500t` |
| PROGRESSION | B,B,B,B,B,B,B,B,B,B,B | **B — literally invariant** | B (corpus-wide; never A/S anywhere) | n/a — flat everywhere, not long-run-specific |
| WORLD | B,B,B,B,B,B,B,B,B,B,B | **B — literally invariant** | B (corpus-wide; never A/S anywhere) | n/a — flat everywhere, not long-run-specific |
| FACTION | A×7, B×4 | A (decaying toward B at 2000t) | **S** | Most 200t worlds (`unit_faction_tension`, `frontier_extended`, `wilderness_survival`, `highland_traverse`, `swamp_border_world`, `frontier_marches`, `frontier_living_world`) |
| COGNITION | C×4, B×7 | B | **S** | `unit_selfmodel_pilot` (all seeds, 200t), `hero_guild_routing_seed123_500t` |
| SOCIAL | C×7, S×3 (urban_political@1000t only), C×1 | **S reached at 1000t, but never re-tested at 2000t** | S | `urban_political` @500t and @1000t (all seeds) |
| ECONOMY | C×7, B×4 | B | B (never A/S anywhere in corpus) | n/a — flat everywhere |
| INFORMATION | C×7, B×4 | B | B (never S anywhere in corpus at either short or long run) | n/a |
| NARRATIVE | A×5, B×6 | A/B | **S** | `hero_guild_routing`, `simq_routing_test` (all seeds, 500t) |

**The mechanism**: the only 3 worlds carrying any ≥1000t anchor
(`dungeon_crawl`, `sandbox_world`, `urban_political`) are the 3 general-purpose archetype
worlds that predate the unit-tier/hero-tier specialization work from
`TCK-20260704-SIMQ-CORPUS-TIERS-EPIC`. None of them is content-tuned to drive AGENCY,
COGNITION, or FACTION into their peak states — that's exactly what the *specialized*
worlds (`unit_selfmodel_pilot`, `unit_faction_tension`, `hero_guild_routing`,
`simq_routing_test`) are for, and **none of those specialized worlds has been run past
500t**. Concretely:

- **AGENCY**: we have zero evidence of what a "hot" AGENCY pillar (routing actively,
  A-grade) does over 1000-2000 ticks — does it hold, drift toward stasis (`stasis_N`,
  `population_stasis` per §5 of the pillar contract), or oscillate? This is precisely the
  drift-risk category the corpus gap is supposed to catch, and it is completely dark today.
- **FACTION**: the one piece of long-run evidence we do have (`dungeon_crawl`
  1000t→2000t) shows FACTION decaying from grade A to B as tick count grows (raw score
  same, but `effective_denom` in the normalized-score formula, §4.4 of the contract,
  grows with `last_event_tick`/`floor_tick`). If that decay dynamic generalizes, an
  S-grade FACTION world (`unit_faction_tension`) could plausibly decay to A or B by
  1000-2000t purely from the normalization mechanics, independent of any real regression —
  or it could be a genuine drift signal. We cannot currently distinguish these two
  explanations because no S-tier FACTION world has ever been run long.
- **COGNITION**: same shape — the S-grade peak (`unit_selfmodel_pilot`) is completely
  untested beyond 200t.
- **SOCIAL**: partially answered — `urban_political` shows SOCIAL holding at S through
  1000t — but `urban_political` has no 2000t anchor, so persistence beyond 1000t is
  unconfirmed, and this is the *weakest* pillar's worlds (`urban_political` only), not the
  full S-grade set.
- **NARRATIVE**: same untested-peak pattern as AGENCY/COGNITION.
- **PROGRESSION, WORLD, ECONOMY, INFORMATION**: these four are flat (grade never varies
  beyond B/C) across the *entire* 61-scenario corpus, not just the long-run subset. This is
  a different, broader finding than "no long-run evidence" — it may indicate these
  pillars have no world in the corpus that drives them into a genuinely active state at
  all (worth a light follow-up note, but is corpus-breadth work already covered by the
  just-completed tiers epic's remit, not specifically a long-run gap).

### 1.4 What this means for scope

The precise, evidence-based long-run gap to close (bounded at ≤2000t per user's explicit
cap) is: **add 1000t (and where seed-budget allows, 2000t) anchors for the worlds that are
already known to drive AGENCY, COGNITION, FACTION, and NARRATIVE into their peak grades at
short run** — i.e. `unit_selfmodel_pilot` (COGNITION=S), `unit_faction_tension`
(FACTION=S), `hero_guild_routing` and `simq_routing_test` (AGENCY=A, NARRATIVE=S,
COGNITION=S/A) — plus extending `urban_political` to 2000t to confirm SOCIAL=S
persistence. This directly answers "does drift/degenerate-loop behavior appear when a
pillar is actually exercised over a long run," which is the user's stated concern, rather
than adding more long-run data to the 3 worlds that are already flat/inert on those
pillars (which would look like coverage growth but add no new evidence).

---

## 2. Pillar Completeness Research

### 2.1 Method

Read `docs/simulation_quality/quality_scoring_contract.md` in full (1357 lines — §1 scope,
§5 all 10 pillar definitions with event types/signals/tags, §6 scenario registry, §7
extensibility protocol, §11 testing contract). Surveyed `src/simulation_quality/scorers/`
(10 files: `agency.py`, `cognition.py`, `combat.py`, `economy.py`, `faction.py`,
`information.py`, `narrative.py`, `progression.py`, `social.py`, `world_dynamics.py`).
Cross-checked candidate new-pillar dimensions against what other systems in the repo
already cover, using `Bash`/`Grep` (not raw exploration — targeted checks against named
hypotheses).

### 2.2 Candidate: determinism / replay-fidelity — REDUNDANT, already covered

`tests/certification/test_phase10_enhanced_determinism_parity.py`,
`test_world_compile_determinism.py`; `tests/integration/kernel/test_replay_fidelity.py`,
`test_determinism_suite.py`, `test_overflow_determinism.py`,
**`test_long_run_determinism.py`** (a long-run-specific determinism test already exists),
`test_worker_determinism.py`, `test_p1_replay_fidelity.py`, `test_executor_determinism.py`,
`test_phase2_determinism.py`; `tests/integration/observability/
test_phase28_observability_determinism.py`; `tests/unit/kernel/test_replay_determinism.py`.
This is an extensively covered, dedicated test domain. A SimQ pillar would duplicate it and
would also violate the module's own scope boundary (§1: "does not score correctness — that
is `hard_law_monitor`"; determinism/replay is a correctness property, not a health
gradient).

### 2.3 Candidate: performance / tick-time budget — REDUNDANT, already covered

`tests/perf/` has 14+ dedicated files (`test_perf_combat.py`, `test_perf_resource.py`,
`test_perf_strategic.py`, `test_perf_stress.py`, `test_perf_metropolis.py`, etc.) plus
per-phase budget tests (`test_phase2_self_model_budget.py` through
`test_phase9_campaign_semantic_budget.py`) tied to `docs/engine/performance_contract.md`'s
hardware classes. SimQ's *own* overhead is separately budgeted in
`tests/simulation_quality/test_performance.py` (§11.4 of the contract: <0.1ms/event
scorer overhead, <50ms report build). Adding a "performance" SimQ pillar would duplicate
`tests/perf/` and blur the module's explicit non-goal (§1: "does not score performance —
that is `perf_baseline_policy.md`").

### 2.4 Candidate: save/checkpoint integrity — REDUNDANT, already covered

`src/engine/scenario_checkpoint.py` (`ScenarioCheckpointer.save`/`.restore`) and
`src/engine/checkpoint.py` have dedicated tests:
`tests/integration/kernel/test_checkpoint_reproducibility.py` and
`tests/unit/engine/test_scenario_checkpointer.py`. Not a SimQ gap.

### 2.5 Candidate: content/catalog health — REDUNDANT, already covered

`src/content/validator.py` implements `CAT-REL-001` through `CAT-REL-011` catalog
relationship/reference validation rules, run independently of SimQ. Not a SimQ gap.

### 2.6 Candidate found with real (if narrow) merit: building/infrastructure sabotage

Cross-referenced the engine's 31-phase authoritative pipeline
(`docs/engine/authoritative_pipeline.md` §"The 31 Phases of Refinement") against every
pillar's "Pipeline:" anchor list and "Event types scored" list in the contract §5. All 31
phases map cleanly to an existing pillar's scored event types **except**:

- Phase 15, `building_sabotage` → `src/engine/sabotage.py::BuildingSabotageSystem.resolve()`.
  "Law: Entities can damage town infrastructure (LEG-RPG-001/006). Sabotaged buildings lose
  functionality, impacting regional services."

This is a **live, non-dead** mechanic: it fires on `SABOTAGE`/`ENTITY_ACT` task intents,
mutates `building_updates` (hp_delta, functional_set), and is exercised by real corpus
content — `urban_political`'s resolved world spec and the `trading_company_hub.yaml` world
module reference sabotage-relevant buildings (`grep -rl sabotage data/worlds/
data/content/` returns `urban_political/resolved/world.resolved.yaml`,
`urban_political/resolved/provenance_manifest.json`, and
`data/content/world_modules/trading_company_hub.yaml`). No pillar's event list — WORLD's
(`political_change`, `world_evolving`, `persistent_structure`) or otherwise — includes a
building-damage/sabotage tag, and `docs/simulation_quality/event_type_coverage.md` has no
reference to sabotage at all.

**Important qualifier**: `BuildingSabotageSystem.resolve()` does not emit any
`ObservabilityEventEnvelope`/`SimulationEvent` today — it only writes `BuildingUpdate`
records (`hp_delta`, `functional_set`) directly to durable state. There is currently no
event for a scorer to hook into. Closing this gap therefore requires **two** pieces of
work, not one: (a) emit a new event type (e.g. `building_sabotaged`) from this phase, and
(b) add a scoring rule consuming it.

**Recommendation: NOT a new pillar.** Per the extensibility protocol (§7.1 vs §7.2 of the
contract), a single new signal for a mechanic this narrow (one phase, one world touching it
today) is a **new scoring rule under the existing WORLD pillar** ("Is the world itself
alive... regions transforming... or is the world a static backdrop entities move through
without consequence?" — infrastructure damage is squarely a "world consequence" question),
not grounds for an 11th top-level pillar. `FACTION` is a plausible secondary owner given
`urban_political`'s faction-conflict framing, but WORLD is the cleaner primary per the
conflict-detection rule in §7.3 (no existing pillar currently claims building-state
events).

### 2.7 Overall conclusion

**No new top-level pillar is justified.** The four "obvious" candidate dimensions
(determinism, performance, checkpoint integrity, catalog health) are each already owned by
dedicated, mature systems outside SimQ, and the contract explicitly scopes SimQ away from
all four (§1 "What this module is NOT" table). The one genuine, evidence-backed gap found
(`building_sabotage`) is real but narrow, blocked on an event-emission prerequisite, and
fits cleanly as a new rule inside the existing WORLD pillar rather than a new pillar. This
should be scoped as a small standalone ticket (event emission + WORLD scoring rule + unit
test), not part of the epic's core long-run-coverage work, and is optional/lower priority
relative to the long-run gap.

---

## 3. Existing Follow-Up Ticket Triage

All 6 tickets read in full from `tickets/todos/` (they are loose files directly under
`tickets/todos/`, not inside a subfolder — there is no `tickets/todos/simq/` directory;
the completed `TCK-20260704-SIMQ-CORPUS-TIERS-EPIC`'s child-ticket folder already moved to
`tickets/done/simq-corpus-tiers/`). Each was live-reverified against current repo state
(not just re-read):

| Ticket | Still valid? | Evidence re-checked | Recommendation |
|---|---|---|---|
| `TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER` | **Yes** | All 12 named files still lack a leading `---` YAML block (`head -c 20` on each, verified live) | **Relocate as-is.** Independent doc-hygiene chore, not corpus/pillar work, but a legitimate open gap with no scope overlap with this epic. Fine to fold in as a housekeeping child ticket if the epic wants a single umbrella, or leave standalone — either is defensible; slight preference for standalone since it's unrelated in subject matter (docs registry, not SimQ corpus/pillars). |
| `TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT` | **Yes** | Root cause (`ResourceOpportunityProvider.get_opportunities()` gating on catalog-wide `source_region_tags`, `src/world/providers/resources.py:69`) is architectural and unresolved; ticket explicitly scopes a corpus-wide audit not yet done | **Relocate as-is.** Directly relevant to corpus content health, same subsystem the deep-coverage epic is auditing; natural companion to long-run-anchor work since routing/resource stasis is exactly the AGENCY drift risk this epic is chasing. |
| `TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP` | **Yes** | Live-checked `config/simulation_quality/profiles/urban_political.yaml` — still has no `feature_flags: ENABLE_ADVENTURE_ROUTING` entry (only `ENABLE_SOCIAL_COOPERATION`/`ENABLE_BELIEF_ASSIMILATION`); gap remains dormant exactly as described | **Relocate as-is.** Same subsystem as above; also directly relevant if this epic's `urban_political` 2000t extension work (§1.4) ever considers enabling adventure routing there — worth resolving in the same pass to avoid the dormant risk activating unexpectedly under new long-run anchors. |
| `TCK-20260707-HERO-GUILD-ROUTING-RESOURCE-TAG-GAP` | **Yes** | Live-checked `data/content/world/resources.yaml`: `iron_vein` (line 13) and `frost_shard_cluster` (line 107) both still have no `metadata.source_region_tags` field at all, confirming the ticket's exact claim | **Relocate as-is.** `hero_guild_routing` is one of the worlds this epic's own §1.4 recommends extending to long-run anchors (it's the AGENCY-hot world) — closing its resource-tag gap first, before adding 1000t+ anchors, avoids anchoring a long-run grade against content with a known latent stasis risk. |
| `TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP` | **Yes** | Live-checked `tests/unit/worldassembly/test_corpus_diversity.py`: `POPULATION_STABILITY_WORLDS = list(ANCHORED_WORLD_BANDS.keys()) + [4 unit-tier worlds]`; `ANCHORED_WORLD_BANDS` still excludes `dungeon_crawl`, `sandbox_world`, `generated_frontier_3_42`, and `urban_political` | **Relocate as-is.** These are exactly the 3 worlds carrying all existing long-run anchors (§1.2) plus one of the untested-`generated_frontier_3_42` gap worlds — closing this coverage gap is directly relevant groundwork before/alongside adding new long-run anchors to those same worlds. |
| `TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING` | **Yes** | Confirmed `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/` and `stored_artifacts/EPIC-SCOPE-full-feature-world-coverage/` do not exist anywhere; only `tickets/done/simq-corpus-tiers/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC.md` exists (the epic ticket itself, not its cited investigation doc) | **Relocate as-is**, but note it is a documentation/traceability-only ticket with zero code/content overlap with the rest of this epic — it can run fully independently and in parallel with everything else. Also worth noting as a **process lesson for this new epic**: write this epic's own `investigation.md`/`plan.md` into a folder matching the real epic ticket ID and make sure it survives into `stored_artifacts/` at epic close, so this same citation-rot pattern doesn't recur. **[Applied: this file was written under the working name `EPIC-SCOPE-simq-deep-coverage/` before the epic ticket ID existed, then renamed to `staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/` once it did — the lesson was followed, not just noted.]** |

**Summary recommendation**: all 6 tickets are still valid (none resolved, none stale,
none superseded) and all 6 are reasonable to relocate into the new epic's folder. Four of
the six (`RESOURCE-REGION-COVERAGE-AUDIT`, `URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP`,
`HERO-GUILD-ROUTING-RESOURCE-TAG-GAP`, `CORPUS-POPULATION-STABILITY-COVERAGE-GAP`) have
direct, evidence-backed sequencing relationships to this epic's long-run-anchor work
(§1.4) and should probably be sequenced *before* the long-run anchors that touch the same
worlds (`hero_guild_routing`, `urban_political`, `dungeon_crawl`/`sandbox_world`). The
other two (`DOCS-REGISTRY-MISSING-FRONTMATTER`, `EPIC-SCOPE-INVESTIGATION-DOC-MISSING`) are
subject-matter-independent housekeeping that can run in parallel without blocking anything,
whether folded into this epic's folder or left standalone — this is a naming/organization
call for the epic ticket, not a correctness question.

---

## 4. Long-Run Test Infrastructure Mechanism

Confirmed by reading `test_grade_regression.py`, `tools/evaluate_simq.py`, the Makefile,
and `pyproject.toml`'s marker registration:

1. **Pytest marker**: `slow` is a registered marker (`pyproject.toml` line 68:
   `"slow: marks tests as slow..."`). `SLOW_ANCHOR_KEYS` entries in
   `test_grade_regression.py` are wrapped in `@pytest.mark.slow` +
   `@pytest.mark.parametrize("run_key", SLOW_ANCHOR_KEYS)` on
   `test_grade_within_anchor_band_long_run`. The fast suite runs with `-m "not slow"`
   (see `make test-quick`, `make simq-full-audit`); `make simq-full-audit-slow` runs
   `pytest tests/simulation_quality/test_grade_regression.py -q` with **no** `-m` filter,
   which picks up both fast and slow parametrized cases.

2. **Data-only extension point — no test-infrastructure code changes required** to add a
   new 1000t/2000t anchor:
   - Add the run's grade dict to `tests/simulation_quality/fixtures/grade_anchors.json`
     (key format `{world}_seed{N}_{ticks}t`).
   - Add the same key string to `SLOW_ANCHOR_KEYS` in `test_grade_regression.py`.
   - Generate and commit the calibration artifact at
     `data/calibration/{run_key}/quality_report.json` via
     `python3 tools/calibrate_simq.py --name <world> --seed <N> --ticks <T>`.
   This is the exact, already-proven pattern used to add the existing 11 slow anchors
   (`dungeon_crawl`/`sandbox_world`/`urban_political` at 1000t/2000t) — confirmed by
   the inline comments in `SLOW_ANCHOR_KEYS` documenting which tickets added which keys.

3. **`evaluate_simq.py` (non-`--dry-run`, i.e. `make evaluate-full`) iterates every key
   present in `grade_anchors.json` with no tick-count filter** — the Makefile's own
   comment ("Re-run engine for all fast (≤500t) scenarios") is **stale/inaccurate**: the
   code (`tools/evaluate_simq.py` `main()`, scenarios = `anchor_keys` when `--scenario` is
   not passed) has no fast/slow split logic at all; it would attempt to re-run the engine
   for existing 1000t/2000t keys too if invoked without `--dry-run`. This is a minor,
   pre-existing documentation/behavior mismatch, not something this epic needs to fix, but
   worth a one-line note if a ticket touches that file — new anchors do **not** need any
   change here to be picked up; they're automatically included by virtue of being in
   `grade_anchors.json`.

4. **Per-world feature-flag activation for long-run "hot" worlds**: `evaluate_simq.py`
   sourced its flags generically from each world's `config/simulation_quality/
   profiles/<name>.yaml` `feature_flags:` block (post
   `TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE`, no more hardcoded `ROUTING_KEYS`
   special-casing). Confirmed the profile directory currently has files for
   `hero_guild_routing`, `unit_information_source`, `unit_selfmodel_pilot`,
   `simq_routing_test`, `urban_political`, `dungeon_crawl`, `sandbox_world`,
   `frontier_extended`, `frontier_living_world`, `frontier_marches`,
   `generated_frontier_3_42`, `highland_traverse`, `swamp_border_world`, and `default` —
   but **`unit_faction_tension`, `crowded_frontier`, `resource_dense_basin`, and
   `wilderness_survival` have no profile file** (they run under whatever `default.yaml`
   sets). Before anchoring `unit_faction_tension` at long-run, verify whether it needs a
   profile at all — its FACTION=S grade at 200t already fires without one (base world
   content is sufficient), so this is likely a non-issue, but should be confirmed live
   rather than assumed when the corresponding ticket is scoped.

5. **`make evaluate-full` vs the slow tier**: neither `make evaluate-full` nor
   `make simq-full-audit-full` is documented or wired to distinguish slow scenarios by
   design (per finding 3) — but in practice today they only ever re-run what's in
   `grade_anchors.json`, so adding new 1000t/2000t keys does technically make them
   slower for anyone running `make evaluate-full` without `--scenario`. This has been true
   since the existing 11 slow anchors were added, so it's an accepted, pre-existing
   pattern, not a new risk this epic introduces — noted only for completeness.

---

## 5. Open Questions Requiring a Human Decision

1. **Exact anchor matrix to author.** §1.4 gives a directional recommendation (extend
   `unit_selfmodel_pilot`, `unit_faction_tension`, `hero_guild_routing`,
   `simq_routing_test` to 1000t; extend `urban_political` to 2000t) but not an exact
   seed × tick-count grid. Given the ≤2000t cap, should every world get both 1000t *and*
   2000t, or should tick budget be spent on more worlds at 1000t only vs. fewer worlds at
   both tiers? This is a real trade-off (calibration run cost vs. coverage breadth) that
   needs a decision before ticket-writing.
2. **Sequencing vs. the 4 relocated resource/coverage tickets.** §3 recommends fixing
   `HERO-GUILD-ROUTING-RESOURCE-TAG-GAP` and `URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP`
   *before* anchoring those same worlds at long run, since both gaps carry a latent
   AGENCY-stasis risk that a long-run run could inadvertently surface as a "regression."
   Confirm this ordering is acceptable (it adds sequencing constraints to the epic's
   `SEQUENCE.md` rather than allowing fully parallel child tickets).
3. **`building_sabotage` follow-up: in this epic or deferred?** §2.6 is a real, narrow,
   evidence-backed gap but requires an event-emission change (not just a scoring rule) —
   confirm whether it belongs in this epic (as a small, lower-priority child ticket) or
   should be filed separately/deferred, since it's unrelated to the long-run-coverage
   thread.
4. **`generated_frontier_3_42`'s total absence from `grade_anchors.json`.** Found
   incidentally in §1.2 — this world has a calibration profile but zero anchors of any
   kind. Confirm whether this is intentional (world used only for corpus-diversity/
   population-stability tests, not grade calibration) or an oversight worth a line item
   in this epic or the population-stability ticket already in scope.
5. **`unit_faction_tension`/`crowded_frontier`/`resource_dense_basin`/
   `wilderness_survival` missing calibration profiles** (§4 point 4) — confirm whether
   `unit_faction_tension` needs one before being extended to long-run anchors, or whether
   `default.yaml` is sufficient (its FACTION=S already fires at 200t without one, which is
   suggestive but not proof for a 1000t+ run).
