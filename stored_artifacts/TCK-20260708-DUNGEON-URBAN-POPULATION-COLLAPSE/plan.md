---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE
artifact_type: plan
tags: [simulation-quality, world, corpus, calibration]
---

# Implementation Plan — TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE

## Summary

Both `dungeon_crawl`'s early-tick collapse and `urban_political`'s late-tick erosion trace to the
same bug *pattern* (not a shared engine cause, per investigation.md Risk 1): the resolver's
`hazard_kind` default of `"PHYSICAL"` (`src/worldassembly/resolver.py:798`) silently applies to
any region that declares `hazard_level` but never declares `hazard_kind`, and no faction is immune
to `"PHYSICAL"` — so any populated hazardous region without an explicit `hazard_kind` becomes an
unconditional lethal drain to its own occupying faction. This is a content-authoring gap, not a
mechanism defect; the mechanism itself is correct and covered by its own regression test
(`test_hazard_drain_default_hazard_kind_no_regression`) which must remain green throughout.

The fix is three narrow, independent content edits (add `hazard_kind` to
`ruins_mystery_quest.yaml`, `scalable_bandit_camp.yaml`, and `trading_company_hub.yaml`, plus one
matching `hazard_immunities` addition for `merchant_league` in `factions.yaml`), followed by
recompiling every world that composes an edited module (`dungeon_crawl`, `hero_guild_routing`,
`urban_political`), followed by direct verification (both the existing instrumented-drive method
and the actual pytest suite) before removing the two `xfail(strict=False)` markers in
`test_corpus_diversity.py`. `urban_political` additionally benefits from a stale-compile fix
(its on-disk resolved artifact predates `bandit_road_trade_pressure.yaml`'s already-landed
`hazard_kind` fix) that the recompile step picks up automatically — no separate content edit is
needed for that half.

Per the two open questions resolved in the investigation and restated in the launch instructions:
`town_council`/`merchant_league`'s `bandit_road` losses are treated as intentional conflict-pressure
flavor and are NOT touched (no hazard exemption added there), and `trading_hometown`'s
`hazard_level: 0.5` is treated as intentional ambient trade-hub risk — fixed the same way as the
other two genuine gaps (add `hazard_kind` + matching faction immunity), not zeroed out.

## Steps

### Step 1 — Add `hazard_kind` to `ruins_mystery_quest.yaml`
**Files:** `data/content/world_modules/ruins_mystery_quest.yaml`
**Change:** In the `regions` list, region `id: "haunted_battlefield"`, add a `hazard_kind:
"UNDEAD_CORRUPTION"` field immediately after the existing `hazard_level: 3.5` line (matching the
field-ordering convention already used in `old_mine_resource_loop.yaml`'s `old_mine` region:
`hazard_level` then `hazard_kind`). This matches `undead_remnants`'s existing declared
`hazard_immunities: ["UNDEAD_CORRUPTION"]` in `data/content/social/factions.yaml` (line 125) — no
faction file edit needed for this step, the immunity already exists.
**Do NOT touch:** `factions.yaml`, `spirit_court`'s faction entry (no evidence it needs an
exemption — not populating the region per `populations: ["undead_battlefield_patrol"]`), any other
region in this module, `quest_definitions`, `provides`, `observability_tags`.
**Verify:** `tests/unit/worldassembly/test_corpus_diversity.py::test_hazard_kind_completeness[dungeon_crawl]`
and `[hero_guild_routing]` (if present) still pass; new test #2 from test_plan.md (hazard_kind
matches populating faction) once written in Step 6, for this module specifically.

### Step 2 — Add `hazard_kind` to `scalable_bandit_camp.yaml`
**Files:** `data/content/world_modules/scalable_bandit_camp.yaml`
**Change:** In the `regions` list, region `id: "bandit_road"`, add a `hazard_kind:
"NATURAL_TERRAIN"` field immediately after the existing `hazard_level: 2.0` line (same
field-ordering convention as Step 1). This matches `bandit_company`'s existing declared
`hazard_immunities: ["NATURAL_TERRAIN"]` in `data/content/social/factions.yaml` — no faction file
edit needed.
**Do NOT touch:** `factions.yaml`, `population_recipes`, `parameters` (`danger_scale`),
`relationships`, `quest_definitions`. Note this module's `bandit_road` region id is distinct from
`bandit_road_trade_pressure.yaml`'s own `bandit_road` region used by `urban_political` (same `id`
string, different module/world — do not conflate the two when editing).
**Verify:** `test_hazard_kind_completeness[dungeon_crawl]`; new test #2 (Step 6) for this module.

### Step 3 — Add `hazard_kind` to `trading_company_hub.yaml` + matching `merchant_league` immunity
**Files:** `data/content/world_modules/trading_company_hub.yaml`,
`data/content/social/factions.yaml`
**Change:**
1. In `trading_company_hub.yaml`'s `regions` list, region `id: "hometown"`, add a `hazard_kind:
   "NATURAL_TERRAIN"` field immediately after the existing `hazard_level: 0.5` line.
2. In `factions.yaml`, the `merchant_league` entry (currently lines 54–61, no `hazard_immunities`
   key present) add a new line `hazard_immunities: ["NATURAL_TERRAIN"]` after `legacy_engine_bucket:
   "NEUTRAL"`. Confirmed by direct read: `merchant_league` currently has zero `hazard_immunities`
   entries of any kind — this is a pure addition, not an extension of an existing list, so no merge
   logic is needed. Do not touch `town_council`'s faction entry (per resolved open question #1 —
   `town_council` gets no exemption; its `bandit_road` guard losses are intentional conflict
   pressure).
**Do NOT touch:** `town_council`'s faction block in `factions.yaml`, `trading_company_hub.yaml`'s
`population_recipes`, `building_recipes`, `resource_recipes`, `parameters` (`merchant_count`),
`relationships`, `quest_definitions`. Do not zero out `hazard_level` — 0.5 is being treated as
intentional per the resolved open question, not an authoring slip.
**Verify:** `test_hazard_kind_completeness[urban_political]`; new test #2 (Step 6) for this module;
`test_hazard_drain_default_hazard_kind_no_regression` (confirms this addition did not become a
blanket immunity — `merchant_league` still has no immunity to anything except `NATURAL_TERRAIN`
specifically).

### Step 4 — Recompile the three affected worlds
**Files (generated, not hand-edited):**
`data/worlds/dungeon_crawl/resolved/world.resolved.yaml`,
`data/worlds/dungeon_crawl/resolved/provenance_manifest.json`,
`data/worlds/dungeon_crawl/world_compile_report.json`, and the equivalent generated files for
`data/worlds/hero_guild_routing/` and `data/worlds/urban_political/`.
**Change:** For each of `dungeon_crawl`, `hero_guild_routing`, `urban_political` (in any order —
independent of each other), run:
```
python3 -m src.worldbuilding.cli resolve <world_id>
python3 -m src.worldbuilding.cli compile <world_id> --seed 42 --from-resolved
```
This is the exact convention used by the precedent fix
(`stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS/plan.md` Step 2). `dungeon_crawl` and
`hero_guild_routing` pick up Step 1's and Step 2's `hazard_kind` additions (both compose
`ruins_mystery_quest`; `dungeon_crawl` also composes `scalable_bandit_camp`). `urban_political`
picks up Step 3's `trading_company_hub` edit AND, as a side effect of recompiling from current
source, the already-landed (2026-07-04, commit `33cf044d`) `hazard_kind: "NATURAL_TERRAIN"` fix in
`bandit_road_trade_pressure.yaml` that its stale compiled artifact never picked up — this is not a
new content edit, just the recompile catching up to already-fixed source.
**Do NOT touch:** Any other world's compiled artifacts. Do not hand-edit any `resolved/*.yaml` or
`*.json` file directly — always regenerate via the `cli resolve`/`cli compile` commands so
provenance stays accurate. After recompiling `urban_political`, diff the full resolved output
against the pre-recompile version to confirm `information_source_profiles`,
`pending_information_responses`, `pending_self_model_information_events`, and
`faction_tension_overrides`-derived `tension_level` (all hand-authored directly in
`urban_political/world.yaml`, independent of `hazard_kind`) survived unchanged — per investigation.md
Anti-Drift Hazards.
**Verify:** `tests/unit/worldbuilding/test_world_compiler.py -k "urban_political"` (the 4
`test_urban_political_resolved_world_seeds_*` tests); `tests/integration/worldassembly/
test_real_content_world_compositions.py::test_dungeon_crawl_composition` and
`::test_urban_political_composition`; `tests/integration/worldassembly/test_e2e_smoke.py -k
"dungeon_crawl or urban_political"`.

### Step 5 — Direct instrumented-drive re-verification (ground truth, matches investigation method)
**Files:** none changed — this is a verification-only step, may use a throwaway script in the
scratchpad directory (not committed) mirroring the investigation's `Kernel.tick_once()` harness
with per-checkpoint `alive_by_faction`/`dead_by_faction` breakdown.
**Change:** Re-run the same direct-drive method investigation.md used (seed 42, `PROD_SMALL`
profile, checkpoints at 10/20/30/40/50 for `dungeon_crawl`; 50/100/150/200/250/300 for
`urban_political`; also run `hero_guild_routing` through the same 300-tick/60%-floor check as a
regression sanity check per investigation.md Risk 4) against the freshly recompiled worlds from
Step 4. Confirm:
- `dungeon_crawl`: no faction wiped out early; `undead_remnants` and `bandit_company` survive
  tick 10/30/50 at the same rate as `goblin_warband`/`wild_beast_pack` currently do.
- `urban_political`: `bandit_company`'s `bandit_road`-stationed losses stop (recompile picked up
  the already-fixed `bandit_road_trade_pressure.yaml`); `merchant_league`'s attrition at
  `trading_hometown` stops entirely (Step 3's fix); `town_council`'s 2 `frontier_guard` losses at
  `bandit_road` are still present and expected (out of scope, per resolved open question #1) —
  confirm alive count clears 60% (>=18/30) despite those 2 still being dead.
- `hero_guild_routing`: still clears its own population-stability floor (regression check).
**Do NOT touch:** Do not treat the tick-50/checkpoint arithmetic from investigation.md as
sufficient on its own (its own arithmetic check explicitly says "verify both independently rather
than assume one implies the other") — this step must actually execute the drive, not extrapolate
from the investigation's projected numbers.
**Verify:** This step's own pass/fail *is* the verification for Acceptance Criterion 2 ("fix
applied"); it must complete successfully before Step 6.

### Step 6 — Run the full pytest regression surface + add the two new coverage tests
**Files:** `tests/unit/worldassembly/test_corpus_diversity.py` (new test additions only — do not
touch `KNOWN_POPULATION_COLLAPSE_WORLDS` or the `xfail` wrapper yet, that is Step 7)
**Change:**
1. Add `test_hazard_kind_matches_populating_faction_immunity` (or equivalent parametrized
   assertions) per test_plan.md's New Test #2 — for `dungeon_crawl` and `urban_political`'s
   resolved specs, assert every region with `hazard_level > 0` and an entity population resolves to
   a `hazard_kind` present in at least one populating faction's `hazard_immunities`. Reuse
   `_load_resolved_spec`'s existing region/faction data access pattern (already present in this
   file, see `_load_resolved_spec` at line 151) rather than adding a new fixture file.
2. Add a recompile-freshness guard for `urban_political`'s `bandit_road` region per test_plan.md's
   New Test #3, either as a standalone test in `test_world_compiler.py` (alongside the other
   `test_urban_political_resolved_world_seeds_*` tests) or folded into test #2 above if the
   implementer judges the match-check already covers a future re-staling — implementer's choice per
   test_plan.md.
3. Run the full scoped pytest commands from test_plan.md's "Scoped Pytest Commands" section,
   including the still-`xfail`-marked `test_population_stability[dungeon_crawl]` and
   `[urban_political]` (which should now report as unexpectedly-passing under
   `xfail(strict=False)`, i.e. `XPASS`, not `xfail`) and `test_population_stability[hero_guild_routing]`.
**Do NOT touch:** `ANCHORED_WORLD_BANDS`, `test_entity_count_band`,
`test_distinct_populated_factions`, `NEWLY_ANCHORED_MODULES`, `HAZARD_KIND_COMPLETENESS_WORLDS`
(already includes both worlds) — none of these need edits; running them is regression-verification
only.
**Verify:** All commands in test_plan.md's "Scoped Pytest Commands" section pass; specifically
confirm `test_population_stability[dungeon_crawl]` and `[urban_political]` both show `XPASS`
(not `xfail`) in the pytest output before proceeding to Step 7.

### Step 7 — Remove the two `xfail` markers
**Files:** `tests/unit/worldassembly/test_corpus_diversity.py`
**Change:** Remove the `"dungeon_crawl"` and `"urban_political"` entries from
`KNOWN_POPULATION_COLLAPSE_WORLDS` (lines 120–129). This dict is what drives the conditional
`pytest.mark.xfail(strict=False, ...)` wrapping in the `test_population_stability` parametrize list
(lines 227–239) — removing the two dict entries automatically removes the `xfail` wrapping for
both `pytest.param` cases (no other line needs editing; the list comprehension already branches on
dict membership). Per investigation.md Anti-Drift Hazards, do this only after Step 6 confirms
*both* worlds pass — do not remove one entry while the other is still pending.
**Do NOT touch:** `POPULATION_STABILITY_WORLDS` itself (the list of worlds under test — unchanged,
was already extended by the prior coverage-gap ticket), any other dict/list in this file.
**Verify:** Re-run `pytest tests/unit/worldassembly/test_corpus_diversity.py -v` — both
`test_population_stability[dungeon_crawl]` and `[urban_political]` now show plain `PASSED`, not
`XPASS`.

### Step 8 — Update parity ledger WORLD-029 and WORLD-060
**Files:** `docs/parity_ledger/world_dynamics.yaml`
**Change:** For both `WORLD-029` and `WORLD-060` entries, update `v2_evidence` to add
`ruins_mystery_quest`, `scalable_bandit_camp`, and `trading_company_hub` to the corpus-wide
`hazard_kind` coverage note (extending the existing 7-module list from the
TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS sweep to now cover these 3 previously-gapped modules), and
note that `urban_political`'s stale compile was refreshed. Keep `status: verified` (unchanged — the
underlying law/mechanism did not change, only content coverage). Confirm `test_path` still points
at `tests/unit/worldassembly/test_corpus_diversity.py` (already does, per investigation.md) — no
`test_path` edit needed since these are P0 entries requiring a passing test_path, which Step 7
guarantees.
**Do NOT touch:** `status` field (stays `verified`), any other entry in `world_dynamics.yaml`, any
other parity ledger file — investigation.md confirms no new entry is needed since this is content
coverage, not a mechanism behavior change.
**Verify:** Manual review only — parity ledger entries are not directly pytest-verified beyond
their `test_path` passing (confirmed by Step 7).

## Scope Guards

- Do NOT touch `src/world/environment.py::calculate_hazard_drain` — the drain mechanism is working
  exactly as documented and designed; this is a content-authoring fix only.
- Do NOT touch `src/worldassembly/resolver.py:798`'s `"PHYSICAL"` default — it is intentional and
  covered by `test_hazard_drain_default_hazard_kind_no_regression`.
- Do NOT add a blanket/wildcard `hazard_immunities` entry (e.g. any faction gaining immunity to
  `"PHYSICAL"`, or any faction gaining immunity to a hazard kind it has no narrative connection to)
  — every addition in this plan is a single specific kind (`UNDEAD_CORRUPTION` or
  `NATURAL_TERRAIN`) matched to a specific populating faction's existing thematic pattern.
- Do NOT add a `hazard_immunities` exemption for `town_council` or `merchant_league` at
  `bandit_road` (either module's `bandit_road` region) — resolved open question #1 treats their
  losses there as intentional conflict-pressure flavor, out of scope.
- Do NOT zero out `trading_company_hub.yaml`'s `hazard_level: 0.5` — resolved open question #2
  treats it as intentional ambient trade-hub risk, fixed via `hazard_kind` + immunity, not by
  removing the hazard.
- Do NOT touch `sandbox_world` or `generated_frontier_3_42` — ticket's Out of Scope, both already
  pass cleanly.
- Do NOT re-litigate `test_hazard_kind_completeness`'s presence-only coverage design — ticket's Out
  of Scope; the new Step 6 test is additive, not a replacement.
- Do NOT remove an `xfail` marker for one world while the other's fix is unverified (Step 7 depends
  on both halves of Step 6 passing together).
- Do NOT hand-edit any file under `data/worlds/*/resolved/` or `data/worlds/*/world_compile_report.json`
  directly — always regenerate via `cli resolve` / `cli compile`.
- Do NOT touch `ANCHORED_WORLD_BANDS`, `NEWLY_ANCHORED_MODULES`, `test_entity_count_band`, or
  `test_distinct_populated_factions` in `test_corpus_diversity.py`.

## Dependency Map

- Steps 1, 2, 3 are independent of each other (different files, different modules) — can be done in
  any order or in parallel.
- Step 4 depends on Steps 1–3 being complete (recompile must happen after all content edits it
  needs to pick up land) — `dungeon_crawl`'s recompile depends on Steps 1+2; `hero_guild_routing`'s
  recompile depends on Step 1 only; `urban_political`'s recompile depends on Step 3 only (and picks
  up the pre-existing `bandit_road_trade_pressure.yaml` fix automatically).
- Step 5 depends on Step 4 (needs freshly compiled artifacts on disk).
- Step 6 depends on Step 5 (do not add/run the new coverage tests or the full regression suite
  until the direct-drive method has already confirmed both worlds clear the floor — avoids
  discovering a pytest-only failure mode not caught by the direct drive).
- Step 7 depends on Step 6 confirming both worlds `XPASS` (not just one).
- Step 8 depends on Step 7 (parity ledger evidence should cite the now-passing test, not a
  still-`xfail`-marked one).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Root cause identified for `dungeon_crawl`'s early-tick collapse and `urban_political`'s late-tick erosion (documented separately) | Already satisfied by investigation.md — no plan step required; this plan implements the fix for the identified cause | N/A (investigation.md is the AC evidence) |
| Fix applied (content/config) | Steps 1, 2, 3, 4 | Step 5 (direct instrumented drive); Step 6 (`test_hazard_kind_matches_populating_faction_immunity`, `test_hazard_drain_default_hazard_kind_no_regression`) |
| `test_population_stability[dungeon_crawl]` and `[urban_political]` pass without `xfail`; markers removed | Step 7 | `pytest tests/unit/worldassembly/test_corpus_diversity.py -v` — both show `PASSED` |

## Anti-Drift Notes

- The two worlds' failures are the same bug *pattern* (resolver's `"PHYSICAL"` default), not a
  shared *engine cause* — three separate content edits and two/three separate recompiles, not one
  code change. Do not attempt to consolidate this into a single mechanism-level fix.
- `urban_political`'s dominant fix (restoring `bandit_company`'s `bandit_road` exemption) comes
  entirely from the recompile picking up already-fixed source (`bandit_road_trade_pressure.yaml`,
  fixed 2026-07-04) — Step 3's `trading_company_hub.yaml` edit is a separate, smaller contributor
  (merchant trickle-death) required by the ticket's "fix each world's genuine content/config gap"
  scope language but not strictly required to clear the 60% floor per investigation.md's own
  arithmetic (20/30 = 66.7% from the recompile alone). Do both regardless — do not skip Step 3 on
  the reasoning that the floor is "already cleared."
- After `urban_political`'s recompile, explicitly diff the resolved output for
  `information_source_profiles`, `pending_information_responses`,
  `pending_self_model_information_events`, and `faction_tension_overrides`-derived `tension_level`
  against the pre-recompile version — these are hand-authored directly in `world.yaml` and easy to
  lose if the recompile path doesn't forward composition-level overrides correctly.
- `hero_guild_routing` is currently a *passing* entry, not a failing one — Step 4/5's re-verification
  of it is a low-risk regression check (the fix only adds an exemption, never removes one), not a
  design decision point. Do not skip it on the assumption that "adding immunity can't break a
  passing test."
- `test_hazard_kind_completeness` only checks presence (truthy `hazard_kind`), not match against a
  populating faction's immunities — this is why it passed on both worlds even while they were
  actively collapsing. The new Step 6 test closes this specific gap for the two fixed worlds only;
  it does not redesign `test_hazard_kind_completeness` itself (that broader redesign is explicitly
  out of scope and noted in investigation.md Risk 5 as a candidate for a future ticket).
- `merchant_league` currently has **zero** `hazard_immunities` entries (confirmed by direct read of
  `factions.yaml` lines 54–61) — Step 3's addition is a new key, not an extension of an existing
  list. If a future investigation ever revisits this and finds `merchant_league` already has a
  `hazard_immunities` list by the time this plan is implemented, extend it (append
  `"NATURAL_TERRAIN"`) rather than overwrite, per the original launch instructions.

No Unresolved Questions — both open questions the investigation flagged (bandit_road exemption
scope, trading_hometown hazard_level intent) are resolved above with explicit reasoning per the
launch instructions. `hero_guild_routing`'s regression check is a low-risk verification step
folded into Steps 4/5/6, not a blocking design question.

## Deviations

No step was skipped, reordered, or implemented differently in scope from this plan. Two
implementation-level notes for future reference (neither changes scope or acceptance criteria):

- **Step 5's actual instrumented-drive numbers exceeded investigation.md's own arithmetic
  estimate.** The investigation projected `urban_political` would land around 20/30 (66.7%)
  alive at tick 300 if only the `bandit_road` recompile landed. The actual post-fix drive
  (both Step 3's `trading_company_hub` fix and the recompile applied together) measured 28/30
  (93.3%) alive at tick 300, with `bandit_company` and `merchant_league` both fully alive and
  only `town_council`'s 2 expected `bandit_road` guard deaths remaining. This is a stronger
  result than projected, not a discrepancy requiring investigation — the investigation itself
  flagged its own arithmetic as an estimate to be verified, not assumed, which Step 5 did.
- **Step 6's new test #2 (`test_hazard_kind_matches_populating_faction_immunity`) initially had
  a naming bug** during implementation: the first draft of test #3's freshness guard asserted
  against a region id `"hometown"`, but `trading_company_hub.yaml`'s `hometown` region resolves
  to `trading_hometown` in `urban_political`'s composed spec (disambiguated from
  `frontier_village_core.yaml`'s own `hometown`, hazard_level 0.0, unaffected). Corrected before
  landing — not a plan-level deviation, caught by the test itself failing on first run.
- The parity ledger edit (Step 8) required one wording change mid-edit: a `: ` (colon-space)
  sequence inside a plain YAML scalar broke `yaml.safe_load` (interpreted as a nested mapping
  key). Replaced with an em dash — content-only wording fix, no meaning change, caught by
  running `tools/parity_ledger_scan.py` before considering Step 8 complete.
