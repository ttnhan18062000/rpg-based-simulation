---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION
artifact_type: investigation
tags: [simulation-quality, world, faction, information, corpus, calibration]
---

# Investigation — TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION

PHASE_TS: 2026-07-07T04:32:30Z

## Context search performed (per CLAUDE.md hard rule)

1. `mcp__knowledge-search__search_docs` (query: "bespoke archetype-matched FACTION tension
   INFORMATION source profile content expansion end-to-end worlds") — top hits: the sibling
   `TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO` (done, same mechanism, unit-tier
   counterpart), `docs/simulation_quality/corpus_tier_taxonomy.md`, `docs/simulation_quality/
   eval_matrix_results.md`, and `docs/audits/D07_content_depth.md`/`D01_rpg_feature_impact.md`
   (older faction-density audit findings, superseded by the corpus-tiers epic).
2. `graphify query "FACTION tension INFORMATION source profile content expansion worlds"` and a
   second pass with schema-specific terms — both returned unrelated nodes (`profile()` perf-harness
   matches, `agent-monitoring/README.md` "Schema" section). Graphify's extracted/inferred edges do
   not cover this ticket's surface (pure YAML content authoring, not a code dependency graph) — raw
   reads were the only productive path here, consistent with the "pure content, additive, no code
   risk" characterization this ticket itself carries.

Both tools were run before any grep/Read, per the Hard Rules; graphify's non-hit is noted honestly
rather than silently skipped.

## Path correction — the ticket's own primary evidence source no longer exists

The ticket's Request Summary, Scope, and Related Docs all cite
`staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §1–§4 as the source for
"which worlds have this content" and "the per-world faction list." **This file does not exist**
under either that path or the renamed path the sibling ticket's investigation.md claims corrected it
to (`staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/investigation.md`) — confirmed by
directory listing of both `staging_artifacts/` and `stored_artifacts/`, and by `git log --all` on
both paths returning zero commits. It was never checked into git; it existed only as an ephemeral
pre-ticket scoping artifact and has since been cleaned up. `docs/simulation_quality/
corpus_tier_taxonomy.md` (dated 2026-07-07, current) still cites this same now-missing path as its
"full evidentiary source" for §2's scale table — the taxonomy doc itself has a broken citation, not
just this ticket.

**This does not block the ticket** — Scope item 2's actual requirement ("judge which of a world's
actually-populated factions have a plausible tension relationship") is independently satisfiable by
reading each world's own compiled/resolved output directly, which is more authoritative than a
paraphrased investigation table anyway (measured, not inferred). See "Current Behavior" below for
the reconstructed per-world faction lists, cross-validated against
`tests/unit/worldassembly/test_corpus_diversity.py::EXPECTED_DISTINCT_POPULATED_FACTIONS` (exact
match on all 8 counts) and `docs/simulation_quality/eval_matrix_results.md`'s "Corpus World-Scale
Summary" table (exact match). Flag this path-loss to the planner/orchestrator as a documentation
hygiene gap worth a follow-up (the missing file is cited by name in at least 3 still-live docs).

## Current Behavior

### Mechanism: `faction_tension_overrides` / `information_source_profiles` are composition-level fields, not world.yaml schema fields

Two distinct schemas are in play and easy to conflate:

- `src/worldbuilding/schema.py::WorldSpec` (the **compiled** spec) — `factions: List[FactionSpec]`
  (`:47-55`, `initial_tension_level` bounded `[0.0, 1.0]`, default `0.0`),
  `information_source_profiles: List[InformationSourceProfileSpec]` (`:226`),
  `pending_information_responses: List[PendingInformationResponseSpec]` (`:227`). This is what
  `WorldCompiler.compile()` actually constructs `AuthoritativeState` from.
- `src/worldassembly/schema.py::WorldCompositionSpec` / `NormalizedWorldComposition` (`:37-61`,
  `:165-189`) — the **authored** composition, i.e. exactly what lives in
  `data/worlds/{world_id}/world.yaml` (`schema_version: "worldcomposition.v1"`). This is where
  `faction_tension_overrides: Dict[str, float]` (composition-scoped, keys must already be
  catalog-registered faction IDs present after module merge), `information_source_profiles`, and
  `pending_information_responses` are actually authored — **not** on `WorldSpec` directly. The
  ticket's own "Related Code Areas" line citing `src/worldbuilding/schema.py:52,226,227` names the
  compiled-spec fields these composition-level fields ultimately populate, not the authoring
  surface itself (that surface is `src/worldassembly/schema.py:40-47`).
- `src/worldassembly/resolver.py:637-646` (`WorldAssemblyResolver.assemble()`) applies
  `faction_tension_overrides` **after** catalog/module faction merge: `for f_id, tension in
  normalized_comp.faction_tension_overrides.items(): if f_id not in factions: raise ValueError(...)`
  — this is the enforcement point behind AC bullet 2 ("no non-populated-faction entries"), though
  note it actually checks against the full **post-merge factions dict** (all factions any composed
  module declares via its own `factions: [...]` list), not strictly "populated" (assigned to a
  spawned entity) — see the populated-vs-declared distinction below, which is stricter than what
  the resolver itself enforces.

### Verified: none of the 8 target worlds have this content today (re-checked live, not from the stale ticket framing)

Direct read of all 8 `data/worlds/{world}/world.yaml` files today (2026-07-07, 3 days after the
ticket's 2026-07-04 framing, after 3 completed sibling epic tickets) confirms **zero** of them
contain `faction_tension_overrides`, `information_source_profiles`, or
`pending_information_responses`. The ticket's premise still holds exactly as stated — no sibling
ticket touched these 8 worlds' own composition files. `urban_political/world.yaml:24-63` remains the
only world with this content (reference, not a target of this ticket).

### Per-world actually-populated faction lists (ground truth — reconstructed from resolved compiled output, not the missing investigation doc)

Extracted directly from each `data/worlds/{world}/resolved/world.resolved.yaml`'s
`entities[].faction` values (the same method `docs/simulation_quality/eval_matrix_results.md`'s
"Corpus World-Scale Summary" table and `test_corpus_diversity.py::
EXPECTED_DISTINCT_POPULATED_FACTIONS` both use — all three sources agree exactly):

| World | Populated factions (ground truth) | Count |
|---|---|---|
| `dungeon_crawl` | `bandit_company`, `goblin_warband`, `undead_remnants`, `wild_beast_pack` | 4 |
| `sandbox_world` | `merchant_league`, `town_council`, `wild_beast_pack` | 3 |
| `wilderness_survival` | `undead_remnants`, `wild_beast_pack` | 2 |
| `highland_traverse` | `merchant_league`, `town_council`, `wild_beast_pack` | 3 |
| `swamp_border_world` | `merchant_league`, `swamp_tribe`, `town_council`, `wild_beast_pack` | 4 |
| `frontier_living_world` | `bandit_company`, `goblin_warband`, `merchant_league`, `town_council`, `undead_remnants`, `wild_beast_pack` | 6 |
| `frontier_extended` | `bandit_company`, `forest_wardens`, `goblin_warband`, `merchant_league`, `orc_clan`, `spirit_court`, `town_council`, `undead_remnants`, `wild_beast_pack` | 9 |
| `generated_frontier_3_42` | `arcane_circle`, `bandit_company`, `goblin_warband`, `merchant_league`, `orc_clan`, `town_council`, `wild_beast_pack` | 7 |

These exactly match the ticket's own two worked examples (`dungeon_crawl`'s
`bandit_company`/`goblin_warband`/`undead_remnants`/`wild_beast_pack`; `swamp_border_world`'s
`merchant_league`/`swamp_tribe`/`town_council`/`wild_beast_pack`) — the ticket text itself was
already using this ground truth, not the missing doc's paraphrase.

**Important trap for the implementer:** a module's own declared `factions: [...]` list (e.g.
`old_mine_resource_loop.yaml:16` declares `["dwarven_mine_clan", "wild_beast_pack"]`,
`ruins_mystery_quest.yaml:18` declares `["undead_remnants", "spirit_court"]`) is a **superset** of
what actually gets assigned to a spawned entity — `dwarven_mine_clan` and `spirit_court` are
declared on modules composed into `dungeon_crawl` but **do not appear** in that world's actual
populated-faction list above (their module's only population, `old_mine_spider_cluster` /
`undead_battlefield_patrol`, resolves to a different faction via its archetype). Authoring a
`faction_tension_overrides` entry for a merely-*declared*-but-not-actually-*populated* faction would
technically pass the resolver's `if f_id not in factions: raise ValueError` check (since declared
factions are in the post-merge dict too) but would violate this ticket's own AC bullet 2's intent
("no non-populated-faction entries") — the resolved YAML's actual `entities[].faction` list (table
above), not a module's `factions:` array, is the correct check.

### Feature flag / profile YAML mechanism

`tools/calibrate_simq.py::_resolve_profile()` (`:32-41`) picks
`config/simulation_quality/profiles/{name}.yaml` if it exists (matched by `--name`/world_id), else
falls back to `"default"`. Of the 8 target worlds, **only `dungeon_crawl` currently has a profile
file** (`config/simulation_quality/profiles/dungeon_crawl.yaml` — `pillar_weights` only, no
`feature_flags:` block). The other 7 have no profile file at all today, meaning every feature flag
currently defaults OFF for them via the `"default"` fallback (`ENABLE_BELIEF_ASSIMILATION: OFF` per
`src/domains/optimization/feature_flags.py:18`). Per Scope item 4, any world where
`information_source_profiles` is seeded needs a **new** profile YAML created (for the 7 without one)
or an **edit** to the existing one (`dungeon_crawl.yaml`, to add a `feature_flags:` block it
currently lacks) — `pillar_weights` blocks are unrelated and must not be added speculatively
(confirmed by direct scorer read below: `pillar_weights` affects only composite weighting, not
whether FACTION/INFORMATION individually move off `C`).

### Compile/resolve staleness risk — checked and confirmed already resolved

`stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS/investigation.md` Finding 3/4 documented
that `frontier_extended`, `frontier_living_world`, and `wilderness_survival` had catastrophic
early-tick population collapse from stale pre-hazard-fix compiled state, and that 3 modules
(`orc_clan_territory`, `bandit_road_trade_pressure`, `old_mine_resource_loop`) lacked `hazard_kind`
entirely. **Directly re-verified today: this is fully resolved.** All 3 modules now declare
`hazard_kind: "NATURAL_TERRAIN"` (confirmed by grep on the live module YAMLs), and all 8 target
worlds' `resolved/provenance_manifest.json::created_at` timestamps are `2026-07-04T04:46-04:47`
(post-fix; `sandbox_world` is `2026-07-02`, also post-fix). Scope item 5's "recompile every touched
world and verify 0 warnings" is therefore a clean re-confirmation, not a rediscovery of a live bug —
still must be done per-world after content lands (a fresh compile could theoretically surface a new
warning class), but no inherited staleness risk exists today.

### Duplicate composition-file surface — `data/content/world_compositions/` (do not edit; precedent already establishes independent divergence)

A second copy of most compositions exists at `data/content/world_compositions/{world_id}.yaml`
(`NON_CATALOG_DIRS` in `src/content/repository.py:148` — explicitly excluded from
catalog-reference-graph validation). `docs/guides/content_authoring.md` §2 Step 4 instructs
developers to edit files in *this* directory ("Add your module_id to an existing composition's
modules list ... `data/content/world_compositions/frontier_living_world.yaml`"), which conflicts
with this ticket's own Related Code Areas naming `data/worlds/{world}/world.yaml` as the edit target.
**Resolution, confirmed by direct diff:** `data/worlds/{world}/world.yaml` is the only path
`WorldRepository("data/worlds")` (used by `cli.py`'s `resolve`/`compile`/`list` commands) actually
reads — it is the live, operative composition. The `data/content/world_compositions/` mirror is
read only by four hardcoded functions in
`tests/integration/worldassembly/test_real_content_world_compositions.py` (pinned to
`frontier_living_world`, `wilderness_survival`, `urban_political`, `dungeon_crawl` by literal path
string) that assert schema-shape properties (module count, `provided_features`, faction-context
size) — none of which assert `faction_tension_overrides`/`information_source_profiles` values. **The
two copies have already diverged for `dungeon_crawl`** (content/ mirror has 2 `module_refs` per
`test_dungeon_crawl_composition`'s own comment "goblin_camp_conflict and old_mine_resource_loop
removed... TCK-20260627-P1I-WORLD-BALANCE-FIX"; `data/worlds/dungeon_crawl/world.yaml` has 4) while
`wilderness_survival`, `highland_traverse`, `swamp_border_world`, `frontier_living_world`,
`frontier_extended` are still byte-identical to their mirrors today, and `sandbox_world` has no
mirror at all. **This establishes the precedent: only edit `data/worlds/{world}/world.yaml`; do not
touch `data/content/world_compositions/`** — doing so would be unrequested scope (the existing
regression tests there are pinned to an intentionally-frozen shape, confirmed by `dungeon_crawl`'s
own prior divergence) and risks breaking `test_dungeon_crawl_composition`'s exact
`len(spec.module_refs) == 2` assertion if the mirror were "helpfully" synced to the live 4-module
version.

## Mechanics / Engine Constraints

- `docs/mechanics/06_worldbuilding_foundation.md:40` — "Factions must have a unique ID and type
  declared in the spec." Composition-level overrides reuse an already-catalog-registered faction's
  existing `type` (via `FactionSpec.model_validate({**factions[f_id].model_dump(), ...})`,
  `resolver.py:644-646`) — no new faction type is ever introduced by this ticket's content.
- `docs/mechanics/06_worldbuilding_foundation.md:102` — "WARNING: Non-critical inconsistencies
  (e.g. ... unpopulated faction starting vaults) ... logged ... but do not halt compilation." This
  is the documented mechanism behind the "0 warnings" AC — a warning is a soft signal, not a compile
  failure; the AC requires reading `world_compile_report.json`'s `"warnings"` array is empty, not
  merely that compile exits 0.
- `src/domains/faction/diplomatic_state_machine.py:8-9,25,51,69,76` — `compute_transitions()`'s
  documented thresholds: `NEUTRAL → TENSE` at `pair_tension > 0.4` (`:76`), `TENSE → HOSTILE` at
  `pair_tension > 0.7` (`:69`), where `pair_tension = max(fa.tension_level, fb.tension_level)`
  (`:51`). This is not itself in `docs/mechanics/` (no FACTION chapter documents this threshold in
  the Mechanics Bible today — a documentation gap, not a code gap; the value is load-bearing for
  "what counts as a genuinely differentiated tension value," matching `urban_political`'s own
  `0.5` choice, which clears `>0.4` with margin without crossing `>0.7`).
- Pattern 6 (`docs/guidelines/design_patterns.md:277-301`, "Compile-Time Pillar Activation
  Pattern") — the bootstrap-gap class both `faction_tension_overrides` and
  `information_source_profiles` closed originally (`TCK-20260702-SIMQ-UPLIFT2-FACTION`/
  `-INFORMATION`). Not directly applicable here (the compiler plumbing already exists and works;
  this ticket is pure content authoring on top of it), but useful context for why "0 signal without
  content" is the expected baseline these 8 worlds show today.
- `src/simulation_quality/scorers/faction.py` (`FactionScorer`) and
  `src/simulation_quality/scorers/information.py` (`InformationScorer`) — both confirmed by direct
  read to score named event types independent of any `pillar_weights` profile entry. A genuine
  non-`C` FACTION signal requires the seeded tension to actually **cross** the `>0.4`/`>0.7`
  threshold during a live run (`diplomatic_transition`/`faction_tension_delta` events), not merely
  be present in `world.yaml` — a seeded-but-never-crossed tension is a legitimate "dormant" finding
  (`diplomacy_dormant`, negative score) to record honestly, not a bug to paper over. Same shape for
  INFORMATION: `belief_assimilated` requires `ENABLE_BELIEF_ASSIMILATION=ON` **and** a matched
  `pending_information_responses` entry; either alone produces zero signal.

## Parity Ledger Overlap

- `docs/parity_ledger/faction.yaml::FAC-012` — `faction_tension_overrides` compile-time plumbing
  (status: `verified`, priority: `P1`). `test_path` covers the mechanism's existing tests (schema,
  compiler, assembly, `test_urban_political_seeded_tension_fires_tense_transition`) — none of these
  need editing for this ticket (pure content, no logic change). Note: `faction.yaml` is not listed in
  CLAUDE.md's parity-ledger file table (`substrate/combat_movement/strategic_cognition/
  town_resource/progression/social_narrative/world_dynamics/infrastructure`) — worth flagging as a
  doc-vs-repo mismatch, not this ticket's problem to fix.
- `docs/parity_ledger/infrastructure.yaml::INFRA-245` — `InformationScorer` full contract coverage
  (status: `verified`, P1).
- `docs/parity_ledger/infrastructure.yaml::INFRA-256` — `information_source_profiles` compile-time
  plumbing (status: `verified`, P1). `divergence_note`/`support_boundary` already document that
  Branch A (`pending_information_responses`) fires exactly once per run for `urban_political` and
  that `dungeon_crawl` was spot-checked for 0 leakage — this ticket's new content is a direct
  continuation of that same evidence-gathering, not a new mechanism.
- `docs/parity_ledger/infrastructure.yaml::INFRA-257` — `pending_information_responses` compile-time
  plumbing (status: `verified`, P1), sibling entry to INFRA-256.
- **None of these are P0** — no `test_path` re-run is a hard gate for this ticket's content-only
  change, per the "P0 entries require a passing test_path" rule. All are P1 and already `verified`
  against the mechanism (not the specific per-world content), so this ticket's work does not, strictly,
  require editing any parity ledger entry — it is pure content on an already-verified mechanism, same
  precedent as the sibling `UNIT-WORLDS-FACTION-INFO` ticket, whose `plan.md` Files Changed list does
  not touch `docs/parity_ledger/` at all. Flag to the planner as a judgment call: optionally append a
  short "8 more end-to-end worlds now exercise this" note to FAC-012/INFRA-256's `v2_evidence`, but do
  not treat it as a blocking requirement.

## Prior Work

- `stored_artifacts/TCK-20260702-SIMQ-UPLIFT2-FACTION/` — established the `faction_tension_overrides`
  mechanism and `urban_political`'s exact content (`bandit_company: 0.5`, `town_council: 0.5`) — the
  reference mechanism, explicitly not to be copy-pasted (this ticket's own Scope item 2 says so, and
  the taxonomy doc's End-to-end tier definition requires archetype-matched values, not verbatim reuse).
- `stored_artifacts/TCK-20260702-SIMQ-UPLIFT2-INFORMATION/` — established
  `information_source_profiles`/`pending_information_responses` plumbing and `urban_political`'s
  `town_notice_board`/`traveling_merchant_rumors` content.
- `stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS/` — established the drift-check-and-update
  discipline this ticket's Scope item 6 explicitly reuses ("Step 4a pattern"), and the
  population-stability/hazard-kind verification method (checked above, already clean for these 8
  worlds). Also flagged (Finding, not yet fully resolved): its own `--dry-run` warning is directly
  relevant here too — see Risks below.
- `stored_artifacts/TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO/` — the unit-tier sibling of
  this exact same two mechanics (`unit_faction_tension`, `unit_information_source`), completed
  2026-07-06/07. Its `investigation.md`/`plan.md` are the closest direct precedent for command
  sequences, anchor-key conventions, and the corrected `make evaluate` (not `--dry-run`) command —
  see Anti-Drift Hazards below. Its plan.md's "Files Changed" list did not touch parity ledger files,
  confirming the judgment call above.
- `data/worlds/urban_political/world.yaml` — the only existing bespoke reference content of this
  exact shape (not a template to copy, but the field-shape example to follow).
- `docs/simulation_quality/corpus_tier_taxonomy.md` — current (2026-07-07), classifies all 8 target
  worlds today as "Regression/baseline tier" and explicitly anticipates this ticket promoting them to
  "End-to-end tier." Its own "Current tier mapping" table (lines 110-121) and narrative ("No world
  has yet been promoted into deliberate end-to-end-tier content expansion") will go stale once this
  ticket lands — not named in this ticket's own Scope list, but analogous to how the sibling
  UNIT-WORLDS ticket's plan.md treated an equivalent stale-taxonomy-doc update as an in-scope
  Finalize-step cleanup ("its own text explicitly anticipates being updated").

## Risks and Open Questions

- **UQ-1 (ticket's own, already resolved by the ticket's own default)**: "skip and document" for
  worlds with no archetype-honest INFORMATION fit is explicitly the ticket's stated default — no
  further decision needed. `wilderness_survival`'s "no settlement" framing (module composition:
  `forest_deep_ecology`, `wolf_den_near_forest`, `undead_battlefield`, `survivor_camp_shelter` — no
  settlement/notice-board-bearing module) is the concrete candidate the ticket names; this
  investigation confirms no settlement-adjacent module exists in its composition, supporting a
  documented "skip" as the honest, defensible call — but the actual judgment (what, if anything,
  plausibly serves as an information source in a pure-wilderness world — e.g. a `survivor_camp_shelter`
  NPC rumor, if that module has an addressable population) is implementation-time work, not
  pre-decidable here.
- **`make evaluate --dry-run` is very likely a no-op, mirroring the sibling ticket's own documented
  finding.** The `evaluate` Makefile target already bakes in `tools/evaluate_simq.py --dry-run`
  (`Makefile:289-290`); passing `--dry-run` again as a literal `make` argument is interpreted by GNU
  Make itself (`-n`/`--dry-run`), which prints the recipe without executing it — this ticket's own
  Scope item 8 and AC bullet 7 both write `make evaluate --dry-run` verbatim, the same defect the
  sibling ticket's investigation flagged and corrected to plain `make evaluate`. **Flag this
  explicitly to the planner — do not silently "fix" the ticket text, but do not execute the literal
  command either**, since it would silently produce a false "0 regressions" without running anything.
- **The `--dry-run` semantics of `tools/evaluate_simq.py` itself is a second, distinct trap** (this
  one real regardless of the `make` wrapper issue): `evaluate_simq.py --dry-run` diffs **existing**
  `data/calibration/*/quality_report.json` files against `grade_anchors.json` — it does **not**
  re-run the engine. Scope item 6's drift-check requires a **fresh** calibration run (via
  `tools/calibrate_simq.py` directly, or `evaluate_simq.py` **without** `--dry-run`) for every touched
  world **before** any anchor comparison means anything — comparing against pre-change calibration
  data would silently validate against content that predates this ticket's edits, defeating the
  entire point of the drift-check. This is exactly the ticket's own Scope item 6 caveat
  ("a stale anchor combined with a changed world will show as a 'regression' unless the anchor itself
  is refreshed first") — confirmed correct by direct code read.
- **`generated_frontier_3_42` has zero existing anchor entries** (`grade_anchors.json`,
  `FAST_ANCHOR_KEYS`, `SLOW_ANCHOR_KEYS` all confirmed to have no `generated_frontier_3_42_*` key,
  and `docs/simulation_quality/eval_matrix_results.md:605-608` explicitly states this and says it is
  "not part of the pillar-grade calibration corpus"). Scope item 6's "re-verify existing calibration
  anchors" literally does not apply to this world — there is nothing existing to re-verify. This
  ticket would either (a) need to newly anchor it (a meaningfully bigger, different task than
  "drift-check an existing anchor," not explicitly called out in Scope), or (b) add its
  FACTION/INFORMATION content and explicitly document "no anchor existed before or after — this
  world remains outside the calibration corpus by design" without creating new anchor entries. This
  is a genuine scope ambiguity the planner must resolve explicitly, not silently default either way.
- **Scale/effort mismatch — this is very likely more than one implementation pass's worth of careful
  per-world judgment work**, and the ticket's own UQ-2 leaves ordering (not splitting) to the
  implementer. Each of the 8 worlds requires: reading its actual archetype framing, checking its
  ground-truth populated-faction list (done above), authoring a bespoke tension pair (not a template),
  judging INFORMATION fit per-world (including at least one likely "skip" case), creating/editing a
  profile YAML, recompiling, running a 3-seed calibration, diffing against existing anchors,
  documenting drift, and updating `eval_matrix_results.md` — **per world**, immediately after that
  world's content lands (per the ticket's own UQ-2 sequencing preference). Recommend the planner
  seriously weigh splitting this into per-world (or per-2-3-world batch) implementation sub-passes
  with a checkpoint after each, rather than one monolithic pass across all 8 — the sibling unit-tier
  ticket did 2 worlds and still produced a ~450-line plan.md; this ticket is 4x the world count with
  materially harder judgment calls (archetype-matching, not template reuse) per world.
- **`dungeon_crawl`'s existing profile YAML must be edited, not replaced** — it already has a
  `pillar_weights:` block (`COMBAT: 2.0, FACTION: 0.1, SOCIAL: 0.5, INFORMATION: 0.5`); adding
  `feature_flags: {ENABLE_BELIEF_ASSIMILATION: "ON"}` must preserve the existing `pillar_weights`
  block, not overwrite the file.

## Anti-Drift Hazards

- Do not edit `data/content/world_compositions/{world}.yaml` mirrors — confirmed dead/frozen relative
  to the operative `data/worlds/{world}/world.yaml` path (see Current Behavior above); editing them
  risks breaking `test_dungeon_crawl_composition`'s pinned 2-module assertion for no benefit.
- Do not use a module's declared `factions: [...]` list as the "populated" check — use the resolved
  YAML's actual `entities[].faction` values (table above), or re-derive after any future recompile if
  module composition changes. `test_corpus_diversity.py::EXPECTED_DISTINCT_POPULATED_FACTIONS` is the
  permanent regression guard on this exact count — it must not change as a side effect of this
  ticket's tension overrides (overrides change `initial_tension_level` only, never add/remove a
  populated faction).
- Do not silently treat `generated_frontier_3_42` the same as the other 7 — it has no existing anchor
  to drift-check (see Risks above); get an explicit decision before anchoring or skipping it.
- Do not run `make evaluate --dry-run` literally, and do not run `evaluate_simq.py --dry-run` as the
  drift-check step without first re-running calibration for every touched world — both traps are
  confirmed live in the current codebase, not hypothetical.
- Do not add `pillar_weights` entries to any new/edited profile YAML unless the ticket's own AC
  requires it — confirmed by direct scorer read that `pillar_weights` does not affect whether
  FACTION/INFORMATION individually move off `C`; adding it would be unrequested scope creep (same
  guard the sibling unit-tier ticket's plan.md explicitly called out).
- Do not silently skip the "document the judgment call" AC bullet for any world, including ones where
  the answer is "used the reference `urban_political` values as a starting point but changed X for
  archetype reasons" or "skipped INFORMATION entirely" — AC bullet 1 requires this recorded per-world,
  not just for the skip cases.
- Do not forget `wolf_den_near_forest`'s `wild_beast_pack` (present in 6 of the 8 worlds) is a
  cross-cutting faction — a tension value chosen for it in one world has no bearing on any other
  world (composition-scoped overrides, confirmed by `resolver.py:637-646`'s per-composition
  application), but an implementer skimming across worlds could mistakenly assume consistency is
  required across worlds. It is not — each world's override is independent.
