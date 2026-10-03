---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS
artifact_type: investigation
tags: [simulation-quality, corpus, calibration, world]
---

# Investigation — TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS

## Current Behavior

### Anchor mechanism (data-only, same as the LONGRUN-HOTPILLAR-ANCHORS sibling ticket)
- `tests/simulation_quality/test_grade_regression.py` — `FAST_ANCHOR_KEYS` (line 41-100, ≤500t) and
  `SLOW_ANCHOR_KEYS` (line 102-125, ≥1000t) are hand-maintained Python lists of `run_key` strings.
  `test_grade_within_anchor_band` (line 178) is `@pytest.mark.parametrize("run_key", FAST_ANCHOR_KEYS)`
  — it only runs for keys **present in the list**; `test_grade_within_anchor_band_long_run` (line 214,
  `@pytest.mark.slow`) is likewise parametrized only over `SLOW_ANCHOR_KEYS`. Both skip (not fail) if
  `run_key not in grade_anchors` (line 185/221) or if
  `data/calibration/{run_key}/quality_report.json` is missing (line 189/225). **Neither list currently
  contains any `generated_frontier_3_42` key** — confirmed by direct grep of the file (lines above) and
  by `grade_anchors.json` itself (see below).
- `test_grade_anchor_file_exists_and_valid` (line 249) asserts `MINIMUM_FAST_ANCHORS = set(FAST_ANCHOR_KEYS)`
  is a subset of `grade_anchors.json`'s keys, and that every entry in `MINIMUM_FAST_ANCHORS` has exactly
  10 pillar grades, each a member of `GRADE_ORDER = ["D","C","B","A","S"]`. Adding a `generated_frontier_3_42`
  key to `grade_anchors.json` **without** also adding it to `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS` would
  leave it present in the fixture but never exercised by either parametrized test — matching corpus
  convention (AC item 2's own wording) requires updating **all three** artifacts together: the
  `data/calibration/{run_key}/quality_report.json` file, the `grade_anchors.json` entry, and the
  matching key-list array.
- `tools/calibrate_simq.py` (`main()`, line 284) drives the actual engine run: resolves a profile
  (`_resolve_profile`, line 32 — defaults to `name` if `config/simulation_quality/profiles/{name}.yaml`
  exists, else `"default"`), loads that profile's `feature_flags:` block (line 44), compiles the named
  world via `WorldCompiler.compile()` if `data/worlds/{name}/resolved/world.resolved.yaml` exists
  (`_load_world_state`, line 108), runs `Kernel.tick_once()` for `--ticks` iterations with
  `no_frame_pacing: True`, replays `simulation_events.jsonl` through `QualityHub`, and writes
  `data/calibration/{name}_seed{seed}_{ticks}t/quality_report.json`.
- `tools/evaluate_simq.py` (`main()`, line 103) — `--dry-run` reads **every non-`_`-prefixed key in
  `grade_anchors.json`** (line 121: `anchor_keys = [k for k in all_anchors if not k.startswith("_")]`)
  and diffs its `data/calibration/{run_key}/quality_report.json` against the anchor, with no
  fast/slow filter of its own (that filtering only exists in the pytest layer via
  `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS`). This means once this ticket's entries exist in both
  `grade_anchors.json` and have a committed `quality_report.json`, `make evaluate --dry-run` (AC item
  6) will actually check them — it does not require the key-list-array step to "see" them, unlike the
  pytest parametrization.

### `generated_frontier_3_42` — current state (verified live, not assumed)
- `data/worlds/generated_frontier_3_42/world.yaml`: `ProceduralCompositionGenerator`, `seed=42`,
  `danger=3`, `settlement_style=frontier` (per `tests/integration/worldassembly/test_e2e_smoke.py:198`).
  Composes 6 modules: `frontier_village_core`, `old_mine_resource_loop`, `bandit_road_trade_pressure`,
  `goblin_camp_conflict`, `moon_cult_ruins`, `orc_clan_territory`. Already carries
  `faction_tension_overrides: {arcane_circle: 0.5, orc_clan: 0.5}` and one
  `information_source_profiles`/`pending_information_responses` pair (`town_notice_board` /
  `moon_cult_ruins_mystery`, region `moon_cave`) — added by
  `tickets/done/TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION.md`, **content-only, explicitly with no
  new anchor** (see Prior Work).
- `config/simulation_quality/profiles/generated_frontier_3_42.yaml`: `feature_flags:
  {ENABLE_BELIEF_ASSIMILATION: "ON"}` only (`ENABLE_ADVENTURE_ROUTING` and
  `ENABLE_SELF_MODEL_COGNITION` are absent → OFF by default). Confirmed to match
  `tests/simulation_quality/fixtures/expected_world_flag_state.json`'s `worlds.generated_frontier_3_42`
  entry exactly (`ENABLE_ADVENTURE_ROUTING: OFF`, `ENABLE_BELIEF_ASSIMILATION: ON`,
  `ENABLE_SELF_MODEL_COGNITION: OFF`; `content.faction_tension_overrides: true`,
  `information_content: true`, `self_model_content: false`) — the `INFRA-262` guardrail fixture
  already reflects this world's real state correctly; this ticket touches no flags/content, so no
  fixture update is needed.
- `tests/unit/worldassembly/test_corpus_diversity.py`: `generated_frontier_3_42` is present in
  `POPULATION_STABILITY_WORLDS` (line 70) and `HAZARD_KIND_COMPLETENESS_WORLDS` (line 135), and is
  **not** in `KNOWN_POPULATION_COLLAPSE_WORLDS` (line 116-125, only `dungeon_crawl`/`urban_political`)
  — meaning `test_population_stability[generated_frontier_3_42]` currently passes cleanly (not
  `xfail`), per `tickets/done/TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP.md`'s
  Implementation Notes: "`sandbox_world` and `generated_frontier_3_42` pass cleanly" at 300 ticks,
  seed 42, 60%-alive floor. This is strong (though not conclusive past 300t) live evidence the world
  runs cleanly, directly relevant to Scope item 1.
- `tests/integration/worldassembly/test_e2e_smoke.py:196`
  (`test_smoke_generated_frontier_3_42_compiles_to_authoritative_state`) confirms compile+assemble to a
  non-empty `AuthoritativeState` (44 entities per the module docstring, line 20). This is a
  compile-layer gate only (not a full kernel run), but is additional live-evidence.
- The resource-tag gap noted by an earlier ticket
  (`docs/simulation_quality/eval_matrix_results.md:1089-1101`, "orc_stronghold has a genuine gap") is
  **already closed**: `tests/unit/strategic/test_opportunities.py:232`
  (`test_resource_opportunities_orc_stronghold_tag_gap`) now asserts a hero in `orc_stronghold`
  **does** receive `gather_resource` opportunities for `iron_vein`/`wood_node` — its docstring states
  this "supersedes the former version... which documented this as a zero-opportunity gap before the
  fix," landed by `TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT` (confirmed done). No open
  content gap remains for this world as of this investigation.

### Already-existing 200t calibration data — critical finding
`data/calibration/generated_frontier_3_42_seed{42,123,456}_200t/quality_report.json` **already exist**
on disk (mtimes 2026-07-07, one day before this ticket was opened) — live-verified directly (not
assumed) by reading all three files:

| Pillar | seed42 | seed123 | seed456 | Stable? |
|---|---|---|---|---|
| COGNITION | B | B | B | yes |
| AGENCY | C | C | C | yes |
| COMBAT | A | A | A | yes |
| FACTION | S | S | S | yes |
| ECONOMY | C | C | C | yes |
| PROGRESSION | B | B | B | yes |
| SOCIAL | C | C | C | yes |
| INFORMATION | B | B | B | yes |
| WORLD | B | B | B | yes |
| NARRATIVE | A | A | A | yes |

Overall grade = `A` for all 3 seeds. This matches exactly the "documentation-only" 3-seed 200t table
in `docs/simulation_quality/eval_matrix_results.md:760-762` (FACTION=S/29 hits, INFORMATION=B/1 hit,
COGNITION=B/2 hits), produced by `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION` and explicitly
**not** committed to `grade_anchors.json`/`FAST_ANCHOR_KEYS` by that ticket's own scope decision (see
Prior Work). AGENCY=C and SOCIAL=C are archetype-correct — `ENABLE_ADVENTURE_ROUTING` and
`ENABLE_SOCIAL_COOPERATION` are both OFF for this world (per the "AGENCY — Cross-World Design Note" in
`eval_matrix_results.md:424-455`, the same ruling applies to every non-routing/non-cooperation world in
the corpus, `generated_frontier_3_42` included). ECONOMY=C is the corpus's typical baseline (no
merchant/Gini-threshold-crossing content in this world's composition).

**No `1000t` (or any long-run) calibration data exists yet for this world** — confirmed by directory
listing of `data/calibration/`; only the three 200t entries are present. Scope item 3 (long-run tier)
requires a fresh engine run, not a re-use of existing data.

## Mechanics / Engine Constraints
- `docs/simulation_quality/quality_scoring_contract.md` §4.4 Normalized Score (lines 268-297, parity
  entry `INFRA-255`): `floor_tick = max(1, current_tick // 4)`; `effective_denom = max(floor_tick,
  last_event_tick)` once a pillar has scored at least one event, else `current_tick`;
  `normalized_score = raw_score / effective_denom`. At 1000t, any pillar whose events are front-loaded
  (COGNITION's single `belief_updated`/`self_model_active` fire, FACTION's `diplomatic_transition`
  burst, INFORMATION's single `belief_assimilated` fire at tick 0 — all three are exactly the mechanisms
  this world's E2E-CONTENT-EXPANSION content seeded) will see `normalized_score` shrink purely from
  denominator growth as `floor_tick` grows with `current_tick`, independent of `raw_score`. This is the
  primary mechanism to expect (and correctly attribute, not mistake for a bug) if FACTION/INFORMATION/
  COGNITION decay from S/B/B toward lower grades at 1000t — directly analogous to the already-observed
  `dungeon_crawl` FACTION S(200t)→A(500t/1000t)→B(2000t) trajectory
  (`eval_matrix_results.md:638-643`) and `urban_political`'s INFORMATION staying B across durations
  (single-fire, weight-scaled) documented in the same doc.
- §5 FACTION & MILITARY (lines 649-690): `diplomacy_dormant` (-20, zero diplomatic transitions over 200
  ticks), `faction_monopoly` (-15, single faction >80% territory by tick 500), `tension_oscillation`
  (-5, cyclic non-crossing tension) are the genuine-regression mechanisms distinct from
  `effective_denom` dilution for this world's FACTION pillar at 1000t.
- §5 COGNITION (lines 529-564): `belief_system_dormant` (-15, zero belief updates population-wide in a
  100-tick window) is the analogous genuine-decay mechanism for COGNITION, versus normalization
  dilution.
- §5 INFORMATION & BELIEF (lines 824-866, not independently re-read line-by-line here but same contract
  section family): the single `pending_information_responses` entry is a one-shot fire at tick 0 per
  the sibling ticket's precedent (`urban_political`) — expect INFORMATION to hold roughly flat (weight-
  scaled by tick count) rather than accumulate further signal at 1000t, since no mechanism in this
  world's content re-fires it.
- Engine contract: no `docs/engine/` contract directly constrains this ticket — it adds calibration
  data only, touches no `authoritative_pipeline.md` phase logic, no scorer/hub/persistence code.

## Parity Ledger Overlap
All entries below are in `docs/parity_ledger/infrastructure.yaml`, `status: verified`, `P1` (except
`INFRA-262`, `P2`) — this ticket exercises but does not modify any of them:
- `INFRA-237` (AGENCY & ACTION scorer coverage) — unaffected; `generated_frontier_3_42` has
  `ENABLE_ADVENTURE_ROUTING=OFF`, so AGENCY stays the archetype-correct C this entry already describes.
  No update needed on this axis.
- `INFRA-240` (COGNITION scorer coverage) — no evidence for `generated_frontier_3_42` cited yet;
  gains a first data point (200t, already collected) plus a first long-run data point (1000t, this
  ticket) once anchored.
- `INFRA-241` (FACTION scorer coverage) — same: gains this world's first anchored data point.
- `INFRA-250` (full SimQ test suite / anchor counts) — text says "25 run keys... (14 fast, 11 slow)",
  already stale (actual count today is ~70 non-metadata keys per the direct `grade_anchors.json` read
  in this investigation: 70 total minus 3 metadata keys = 67). This ticket's 2 new entries (minimum: 1
  fast + 1 slow) make it staler still. **Flag for parity-updater** — pre-existing staleness, not
  introduced by this ticket, but worth a corrective note in the same pass per the sibling ticket's
  precedent.
- `INFRA-252` (`evaluate_simq.py` standing harness) — confirmed by direct code read
  (`tools/evaluate_simq.py:121`) that `--dry-run` iterates **all** `grade_anchors.json` keys with no
  fast/slow filter (the entry's text says "full mode re-runs... for all fast anchor scenarios," which
  is the same pre-existing doc/code mismatch the sibling ticket already flagged — not introduced here).
  This ticket's AC item 6 (`make evaluate --dry-run` confirms 0 regressions) depends on this actual
  behavior: once this ticket's `quality_report.json` files and `grade_anchors.json` entries exist, the
  dry-run diff will include them regardless of `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS` membership.
- `INFRA-262` (per-world calibration-profile feature-flag guardrail,
  `tests/integration/test_world_profile_feature_flag_guardrail.py`) — its fixture
  (`expected_world_flag_state.json`) already correctly describes `generated_frontier_3_42`'s flag/
  content state (verified above). This ticket adds no flags/content — **no fixture update needed**.

No `P0` parity entries were found overlapping this ticket's scope — all touched entries are `P1`/`P2`,
`status: verified`. This ticket adds calibration evidence for a previously-uncalibrated world; it does
not require any entry's `status` to flip (unless a live 1000t run surfaces a genuine bug, in which case
that is documented and escalated per this ticket's own Scope item 1 framing, not silently fixed here).

## Prior Work
- `stored_artifacts/TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS/` — sibling ticket, same
  `calibrate_simq.py`/`grade_anchors.json`/`SLOW_ANCHOR_KEYS` mechanism, different worlds (no overlap).
  Its `plan.md`'s Step 3-10 pattern (add-anchor → add-key → document → parity-update → verify) is the
  direct template for this ticket's own Plan phase.
- `tickets/done/TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION.md` — authored
  `generated_frontier_3_42`'s `faction_tension_overrides`/`information_source_profiles`/
  `pending_information_responses` content and its `ENABLE_BELIEF_ASSIMILATION: "ON"` profile flag, ran
  the 3-seed 200t calibration this investigation reused as live evidence, and **explicitly declined**
  to anchor it: `eval_matrix_results.md:752-758` states "This world has zero existing `grade_anchors.
  json` entries and deliberately receives none from this ticket... newly anchoring a world is a
  materially bigger task than re-verifying one, out of this ticket's scope... a future ticket to
  newly-anchor it is a separate, larger scope decision." This ticket is that separate, larger-scope
  follow-up.
- `tickets/done/TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP.md` — added
  `generated_frontier_3_42` to `POPULATION_STABILITY_WORLDS`/`HAZARD_KIND_COMPLETENESS_WORLDS` and
  live-verified it passes both (300t, seed 42) — directly supports Scope item 1's "confirm live"
  requirement, though it does not substitute for a full calibration-harness run (different tick count,
  different tool).
- `tickets/done/TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT.md` — closed the
  `orc_stronghold` resource-tag gap that affects this world's `orc_clan_territory` module (shared with
  `frontier_extended`/`frontier_living_world`/`resource_dense_basin`/`frontier_marches`/
  `crowded_frontier`); confirmed no open gap remains via direct test read (see Current Behavior).
- `tickets/todos/simq-deep-coverage/SEQUENCE.md` item 8 — confirms this ticket has "no hard dependency
  on tickets 1-4 or 7 — `generated_frontier_3_42` is a different world with no shared prerequisite,"
  consistent with the ticket's own framing. All 4 of the epic's prerequisite-block tickets (1-4) are
  independently confirmed `done` regardless.
- `docs/simulation_quality/corpus_tier_taxonomy.md:131` — currently documents
  `generated_frontier_3_42` as "FACTION + INFORMATION content authored but deliberately left outside
  the anchored calibration corpus (no `grade_anchors.json` entries)." **This line will become stale
  once this ticket lands** and is not listed in the ticket's own Related Docs — flagged as a doc this
  ticket should also update (see Risks).
- `tickets/done/TCK-20260702-SIMQ-ANCHORS`, `TCK-20260702-SIMQ-EVAL-MATRIX`,
  `TCK-20260702-SIMQ-EVAL-HARNESS` — established the calibrate → commit-fixture → add-to-key-list
  mechanism this ticket reuses verbatim.

## Risks and Open Questions
1. **Non-blocking — `corpus_tier_taxonomy.md:131` will go stale.** Not listed in this ticket's Related
   Docs, but its "deliberately left outside the anchored calibration corpus" framing becomes factually
   wrong once this ticket adds anchors. Recommend updating it in the same session per the repo's parity/
   doc-consistency rule, even though the ticket's own Related Docs section only names
   `eval_matrix_results.md`.
2. **Non-blocking — same citation-rot pattern already flagged once.** This ticket's own Request Summary
   cites `staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md` §1.2 as its primary
   evidentiary source. That path **does not exist** — confirmed directly
   (`staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/` is absent; only
   `tickets/todos/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC.md` and
   `tickets/todos/simq-deep-coverage/SEQUENCE.md` exist). This is the exact gap
   `TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING` (done) already found and is tracking for the
   sibling ticket too. Every specific factual claim attributed to that citation ("zero anchors of any
   kind... despite having its own calibration profile") is independently re-verified true in this
   investigation regardless of the missing citation — non-blocking, but should be logged the same way
   the sibling ticket logged it.
3. **Open, Plan-phase decision — exact seed/tick grid for the long-run tier.** The ticket's Scope item
   3 requires "at least one long-run anchor (1000t)," capped at 2000t. The existing 200t data covers 3
   seeds; whether the long-run tier should also run 3 seeds (matching the fast-tier convention already
   established for this world) or just seed 42 (matching several other worlds' 1000t-tier convention,
   e.g. `sandbox_world_seed42_1000t`, `unit_selfmodel_pilot_seed42_1000t`) is not dictated by the
   ticket text and is left to the Plan phase, consistent with `SEQUENCE.md`'s note that "exact seed
   count per world/tier... is left to that ticket's own Plan phase to decide with cost/coverage
   reasoning."
4. **Low-risk — `effective_denom` dilution could push FACTION/INFORMATION/COGNITION down 1-2 letters at
   1000t**, per the Mechanics/Engine Constraints section above. This is expected, architecturally
   intentional behavior (not a bug) if it occurs, and should be attributed explicitly in the
   `eval_matrix_results.md` write-up rather than assumed away — matching the `dungeon_crawl` FACTION
   precedent. Do not force the 1000t anchor to match the 200t grades if the live data disagrees.
5. **Not a risk, but worth stating plainly:** unlike the LONGRUN-HOTPILLAR-ANCHORS sibling ticket, this
   ticket has **no upstream population-erosion confound** to account for —
   `generated_frontier_3_42` is confirmed *not* in `KNOWN_POPULATION_COLLAPSE_WORLDS`. A population
   check at whatever tick count the long-run calibration run reaches is still good practice (cheap,
   traceable) but is not gating a known defect the way `urban_political`'s was for the sibling ticket.

## Anti-Drift Hazards
- **Do not touch `src/simulation_quality/scorers/*.py`, `src/domains/adventure/*`, or
  `data/content/world/resources.yaml`.** This is a data-only ticket (calibration artifact + fixture
  entries + key-list additions); any temptation to "improve" a grade found during data collection
  (e.g., seeding more `information_source_profiles`, adjusting `faction_tension_overrides`) is content
  work explicitly excluded by this ticket's own Out of Scope ("Any content/catalog changes to
  `generated_frontier_3_42` itself").
- **Do not add `generated_frontier_3_42` to `ANCHORED_WORLD_BANDS` or
  `POPULATION_STABILITY_WORLDS`/`HAZARD_KIND_COMPLETENESS_WORLDS`.** The latter two already contain it
  (done by a prior ticket); `ANCHORED_WORLD_BANDS` (entity-count-band anchoring) is a distinct concern
  this ticket's Related Code Areas do not name and should not be touched.
- **Do not reuse the existing 200t `quality_report.json` files uncritically without at least spot-
  verifying determinism.** They are one day old and match the doc exactly, but the ticket explicitly
  says "confirm live (do not assume)" for Scope item 1 — a fresh re-run (or an explicit, documented
  decision to trust the existing artifacts with the reasoning stated) should be a deliberate Plan-phase
  choice, not a silent skip.
- **Do not conflate this ticket with `TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP`'s scope**
  (test-coverage-only, already done) or `TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT`'s
  scope (resource-tag audit, already done) — both are complete prerequisites/context, not remaining
  work for this ticket.
- **`test_grade_anchor_file_exists_and_valid` requires exactly 10 pillar grades per entry** — the new
  `grade_anchors.json` entries must include all 10 pillars (including the archetype-correct C's for
  AGENCY/SOCIAL/ECONOMY), not just the "interesting" non-C pillars, or this structural test fails.
