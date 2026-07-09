---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE
artifact_type: investigation
tags: [simulation-quality, world, corpus, calibration]
---

# Investigation — TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE

## Current Behavior

### Method: direct instrumented drive (same method as Finding 3)

Rather than trust static config reading alone, both worlds were driven directly via
`Kernel.tick_once()` (matching `test_population_stability`'s own harness exactly — seed 42,
`PROD_SMALL` profile) with a per-checkpoint `alive_by_faction` / `dead_by_faction` breakdown
added. This is ground truth, not inference.

**dungeon_crawl** (32 starting entities, checkpoints 10/20/30/40/50):

```
tick 10: alive=15/32  alive={goblin_warband:9, wild_beast_pack:5, undead_remnants:1}
                       dead={undead_remnants:5, bandit_company:12}
tick 30: alive=14/32  alive={goblin_warband:9, wild_beast_pack:5}
                       dead={undead_remnants:6, bandit_company:12}
tick 50: alive=14/32  (unchanged — matches the ticket's reported 43.8%)
```

100% of `bandit_company` (12/12) is dead by tick 10. 100% of `undead_remnants` (6/6) is dead by
tick 30. `goblin_warband` (9/9) and `wild_beast_pack` (5/5) — the only two factions with a
correctly-matched hazard exemption (see below) — survive at full strength through tick 50 with
**zero** losses. This is not partial attrition or combat losses; it is two entire factions being
wiped out almost immediately while two others take no losses at all.

**urban_political** (30 starting entities, checkpoints 50/100/150/200/250/300):

```
tick 50:  alive=18/30  alive={town_council:12, merchant_league:2, bandit_company:1, hero_guild:3}
                        dead={bandit_company:3, merchant_league:7, town_council:2}
tick 100–250: identical to tick 50 (18/30, floor exactly 18.0 — passes by zero margin)
tick 300: alive=17/30  dead={merchant_league:8, bandit_company:3, town_council:2}
```

This directly **contradicts the ticket's framing of "gradual erosion across the full 300-tick
window."** The real shape is: the same early-tick attrition mechanism as `dungeon_crawl` fires by
tick 50 (12 of 13 eventual deaths happen in the first 50 ticks), the population then sits exactly
on the 60% floor (18/30) for 200 ticks, and a single additional `merchant_league` entity dies
somewhere between tick 250–300, tipping it one entity under. It is a two-phase pattern (fast
early die-off + one slow straggler), not a smooth gradual decline — the "erosion" only *looks*
gradual because the test samples every 50 ticks and the bulk of death is invisible before the
first checkpoint.

### Root cause: `RegionState.hazard_kind` resolver default (`"PHYSICAL"`) matching no faction's `hazard_immunities`

`src/worldassembly/resolver.py:798`:
```python
regions_spec_list.append(RegionSpec(
    ...
    hazard_kind=getattr(reg, "hazard_kind", "PHYSICAL"),
    ...
))
```
When a world module's region declares `hazard_level` but not `hazard_kind`, the resolver silently
defaults `hazard_kind` to the literal string `"PHYSICAL"`. `src/world/environment.py::
EnvironmentService.calculate_hazard_drain` (lines 16–41) checks
`region.hazard_kind in get_hazard_immunities(entity's faction)` — if no match, the entity takes
the full `hazard_level * (1.0 + calamity_intensity) * 10` drain, **unconditionally, every tick**.
No faction in `data/content/social/factions.yaml` declares `hazard_immunities: ["PHYSICAL"]` — it
is a value nothing is ever immune to. This exact default and its consequence is intentionally
documented and regression-guarded: `docs/mechanics/05_world_evolution.md` lines 89–93 ("content
must explicitly author both a region's `hazard_kind` and a faction's matching
`hazard_immunities`... for the exemption to take effect") and
`tests/unit/world/test_regional_consequences.py::test_hazard_drain_default_hazard_kind_no_regression`
(asserts the default is `"PHYSICAL"` and that nothing lists it in `hazard_immunities` — "the new
field must not grant accidental universal immunity"). **The drain mechanism itself is working
exactly as designed and is not the bug.** The bug is a content gap: which world modules never
declared `hazard_kind` for a hazardous region their own populating faction occupies.

### dungeon_crawl: two never-declared modules (genuine, un-fixed content gap)

`dungeon_crawl/world.yaml` composes `ruins_mystery_quest`, `goblin_camp_conflict`,
`old_mine_resource_loop`, `scalable_bandit_camp`.

| Module (region) | hazard_level | hazard_kind in source | Populating faction | Faction's `hazard_immunities` | Match? |
|---|---|---|---|---|---|
| `goblin_camp_conflict.yaml` (`goblin_camp`) | 3.0 | `NATURAL_TERRAIN` (declared) | `goblin_warband` | `["NATURAL_TERRAIN"]` | **yes** |
| `old_mine_resource_loop.yaml` (`old_mine`) | 2.0 | `NATURAL_TERRAIN` (declared) | `wild_beast_pack` | `["NATURAL_TERRAIN"]` | **yes** |
| `ruins_mystery_quest.yaml` (`haunted_battlefield`) | 3.5 | **not declared → defaults `PHYSICAL`** | `undead_remnants` | `["UNDEAD_CORRUPTION"]` | **no** |
| `scalable_bandit_camp.yaml` (`bandit_road`) | 2.0 | **not declared → defaults `PHYSICAL`** | `bandit_company` | `["NATURAL_TERRAIN"]` | **no** |

`git log` confirms `ruins_mystery_quest.yaml` and `scalable_bandit_camp.yaml` have **never**, at
any point in their history, declared `hazard_kind` (`grep -c hazard_kind` = 0 in the current file
and every prior revision). These two modules were simply never included in the 7-module sweep
`TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS` performed (`docs/mechanics/05_world_evolution.md` lines
100–106 names the 7: `orc_clan_territory`, `bandit_road_trade_pressure`,
`old_mine_resource_loop`, `forest_warden_grove`, `undead_battlefield`, `nomadic_herd`,
`sunken_swamp_border` — `ruins_mystery_quest` and `scalable_bandit_camp` are absent from that
list). The 18 entities populating these two regions (6 `undead_sentinel` + 12 `bandit_company`
scouts, `pop_0`) are the exact 18 entities that die (32 − 14 = 18), and they die almost instantly
because `dungeon_crawl` has **no zero-hazard region at all** ("No settlement — pure dungeon
exploration," per its own `world.yaml` description) — there is nowhere for an exposed entity to
retreat to.

### urban_political: one stale compile + one never-declared module

`urban_political/world.yaml` composes `frontier_village_core`, `trading_company_hub`,
`bandit_road_trade_pressure`, `hero_adventurers`.

**bandit_road (hazard_level 2.0) — stale compiled artifact, not a content gap.**
`bandit_road_trade_pressure.yaml` *does* declare `hazard_kind: "NATURAL_TERRAIN"` in its current
source (matching `bandit_company`'s `["NATURAL_TERRAIN"]`). `git log -p` shows this line was added
in commit `33cf044d` on **2026-07-04 13:31:25+07:00**
("TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS: ... fix corpus-wide hazard_kind content gap"). But
`data/worlds/urban_political/resolved/provenance_manifest.json::created_at` is
**2026-07-03T17:45:11Z — a full day *before* that commit landed.** `urban_political` was never
recompiled since, so its on-disk `resolved/world.resolved.yaml` still shows `bandit_road`
`hazard_kind: PHYSICAL` (confirmed by direct grep of the resolved YAML), reproducing the exact
"stale compiled instance" bug class Finding 3 (`stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-
WORLD-CORPUS/investigation.md`) already diagnosed for 8 other worlds — `urban_political` was
simply not on that remediation's recompile list because, at the time that ticket ran, it appeared
to already be current. This one is the dominant contributor: `bandit_company` (4 `bandit_scout`
entities stationed at `bandit_road`) shows 3/4 dead by tick 50 and stays there — recompiling alone
(picking up the already-fixed source) removes this loss.

**trading_hometown (hazard_level 0.5, from `trading_company_hub.yaml`'s `hometown` region,
disambiguated by the `namespace: "trading"` module ref) — genuine, never-declared content gap.**
`trading_company_hub.yaml` declares `hazard_level: 0.5` but no `hazard_kind` at all (confirmed via
`git log`, 0 occurrences of `hazard_kind` across its history) → defaults to `PHYSICAL`. Its 6
`trading_pop_0` merchants (`merchant_league`, which declares **no** `hazard_immunities` at all in
the catalog) take unmitigated drain at a much lower rate (`0.5 * 10 = 5`/tick vs. `bandit_road`'s
`20`/tick), which is consistent with why this specific group of deaths trickles out over hundreds
of ticks instead of dying in the first 10 — explaining the "late straggler" (tick 250–300) in the
checkpoint data. Notably, `hazard_level=0.5` on a `type: "town"` settlement region is itself
anomalous: the sibling `hometown` region from `frontier_village_core.yaml` (same settlement
archetype) is `hazard_level: 0.0`. This reads as a plausible authoring inconsistency, not
obviously an intentional design choice — flagged as an open question below rather than assumed.

**town_council's 2 dead** (both, at every checkpoint) are exactly the 2 `frontier_guard` entities
stationed at `bandit_road` (`merchant_caravan_frontier_guard`, count 2) — `town_council` declares
no `hazard_immunities` either, so this loss is **not** fixed by the `bandit_road` recompile (which
only restores `bandit_company`'s own-faction exemption). Whether guard/merchant losses to a
"conflict"-type module's hazard (as opposed to combat) are intended attrition flavor or a further
gap is a design question, not a technical unknown — see Risks below.

**Arithmetic check for the floor.** Current dead at tick 300: `bandit_company:3,
merchant_league:8, town_council:2` = 13 dead, 17 alive (56.7%, matches ticket). If the
`bandit_road` recompile alone restores `bandit_company`'s exemption (removing 3 deaths), dead
drops to 10, alive = 20/30 = **66.7%**, clearing the 60% (18.0) floor with room to spare — i.e.
the recompile alone is very likely *sufficient* to pass `test_population_stability`, even without
touching `trading_company_hub.yaml`. The `trading_company_hub.yaml` gap remains a real, separate
defect (merchants dying to their own hometown over a long run) that the ticket's "fix each
world's genuine content/config gap" scope language covers, but it is not necessarily required to
clear this specific test's floor — implementation should verify both independently rather than
assume one implies the other.

## Mechanics / Engine Constraints

- `docs/mechanics/05_world_evolution.md` §3 "Hazard Impacts" / "Native Endurance to a Region's
  Hazard Kind" (lines 55–107) is the authoritative law governing this entire investigation: Passive
  HP Drain formula, the `hazard_kind`/`hazard_immunities` exemption mechanism, its unconditional
  nature (independent of hostility), and the explicit warning that `hazard_kind` defaults to
  `"PHYSICAL"` with nothing immune to it by default — "content must explicitly author both."
- `docs/mechanics/02_combat_laws.md` was read in full — **not implicated**. No combat-formula,
  wound, or AoE law is involved; the diagnostic run shows the dead factions (`bandit_company`,
  `undead_remnants`, `merchant_league`) die at a uniform, faction-wide rate consistent with
  per-tick environmental drain, not combat resolution (which would show partial/variable losses
  correlated with engagement, not a clean "100% of one faction dead by tick 10/30" pattern).
- `docs/mechanics/03_economic_laws.md` was read — **not implicated**. No resource-conservation or
  starvation mechanic explains a faction-uniform, near-instant wipeout; the direct-drive evidence
  fully explains the pattern via hazard drain alone, ruling out an economic root cause.
- `src/world/environment.py::EnvironmentService.calculate_hazard_drain` — the single mechanism
  responsible in both worlds.
- `src/worldassembly/resolver.py:798` — the resolver default (`"PHYSICAL"`) that makes an
  undeclared `hazard_kind` silently dangerous rather than erroring or warning.

## Parity Ledger Overlap

- `docs/parity_ledger/world_dynamics.yaml::WORLD-029` (P0, status `verified`) — "Calamity aura and
  regional hazards apply local debuffs/drain." `test_path` includes
  `tests/unit/worldassembly/test_corpus_diversity.py`. `v2_evidence` already documents the 7-module
  corpus sweep by name; it does **not** mention `ruins_mystery_quest`, `scalable_bandit_camp`, or
  `trading_company_hub`, and is silent on `urban_political`'s stale-compile state. Needs updating
  once the fix lands (either to add these 3 modules to the "extended corpus-wide" note, or to add a
  divergence/gap note if `trading_company_hub.yaml` is deliberately left out of scope).
- `docs/parity_ledger/world_dynamics.yaml::WORLD-060` (P0, status `verified`) — "Regional hazards
  drain HP/Readiness based on intensity." Same `test_path`, same gap in `v2_evidence` — same update
  needed.
- Both are **P0** — per the Authoritative Mechanics Rule, both require a passing `test_path`.
  `test_regional_consequences.py` passes today (it is a synthetic unit-level test of the mechanism
  itself, not corpus content, and is correct as-is — no change needed there). The corpus half of the
  `test_path`, `test_corpus_diversity.py`, currently has 2 `xfail(strict=False)` entries for exactly
  this defect — these are the markers this ticket's Scope item 3 requires removing.
- No parity ledger entry currently exists that specifically calls out `dungeon_crawl` or
  `urban_political` by name for this gap — the fix should add evidence to WORLD-029/WORLD-060
  rather than create new entries, since the underlying law is unchanged (content coverage, not
  mechanism behavior, is what's being fixed).

## Prior Work

- `stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS/investigation.md` Finding 3/4 — the
  precedent for this exact defect class (stale compile + missing `hazard_kind` on modules with
  `hazard_level`). That investigation's own "Anti-Drift Hazards" section warned "any module reused
  from the 'never anchored' list that declares `hazard_level > 0` must also declare `hazard_kind`...
  otherwise the new world will reproduce Finding 3's collapse pattern by construction" — `dungeon_crawl`
  and `urban_political` are exactly the case that warning anticipated, just not caught until
  `TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP` added coverage for them.
- `tickets/done/TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP.md` — added the parametrize
  coverage and the `xfail(strict=False)` markers this ticket must remove; correctly identified both
  failures as genuine and out of its own (test-coverage-only) scope.
- `TCK-20260701-HAZARD-NATIVE-IMMUNITY` / `TCK-20260701-HAZARD-KIND-RESOLVER-GAP` — introduced the
  `hazard_kind`/`hazard_immunities` mechanism itself and its resolver plumbing; not touched by this
  investigation, working as designed.
- No prior ticket has touched `ruins_mystery_quest.yaml`, `scalable_bandit_camp.yaml`, or
  `trading_company_hub.yaml`'s hazard fields — these are untouched, original-authoring gaps.

## Risks and Open Questions

1. **The ticket's premise that the two worlds' failures "must NOT be assumed to share a root
   cause" was correct as a starting discipline, but the evidence gathered shows they mechanically
   converge on the same underlying defect class** (resolver's `"PHYSICAL"` default hazard_kind
   colliding with a populating faction's declared immunities) — they are independent *instances* of
   the same *bug pattern*, not a shared *engine cause*, and the specific missing modules differ per
   world. This distinction matters for the fix (3 separate content edits + 2 recompiles, not one
   shared code change) but should not be mistaken for "no relationship" either. Flagging explicitly
   so the planner does not re-derive this from scratch or dismiss the connection.
2. **Open design question — should `town_council`/`merchant_league` be exempted from
   `bandit_road`'s hazard at all?** Recompiling restores `bandit_company`'s own-turf exemption
   (clearly correct — matches the documented "native fauna" design intent). It does **not** address
   `town_council`'s 2 dead `frontier_guard` or the `bandit_road`-stationed `merchant_league`
   entities, since neither faction declares any `hazard_immunities`. This may be intentional
   "conflict pressure" flavor (a guard/merchant escort posted to a bandit-contested road taking
   losses over a long campaign) rather than a bug — the investigation does not have evidence to
   decide this either way and does **not** assume an answer. Per the arithmetic above, this does
   not block clearing the test's 60% floor, so it can be deferred to a documented decision rather
   than block the ticket.
3. **Open design question — is `trading_hometown`'s `hazard_level: 0.5` intentional?** Its sibling
   settlement region (`hometown`, `frontier_village_core.yaml`) is `hazard_level: 0.0`. If 0.5 was
   an authoring slip (should have been 0.0 to match the settlement pattern), the fix is to zero it,
   not to add a `hazard_kind`. If it's intentional ambient trade-hub risk, the fix is
   `hazard_kind` + a matching `merchant_league.hazard_immunities` entry. The investigation
   recommends flagging this for a planner decision rather than picking one silently — the difference
   changes which file gets edited and what the resulting design invariant means for future worlds
   reusing `trading_company_hub.yaml`.
4. **`hero_guild_routing`** (`data/worlds/hero_guild_routing/world.yaml`) also composes
   `ruins_mystery_quest` and is currently a passing entry in `POPULATION_STABILITY_WORLDS` (not in
   `KNOWN_POPULATION_COLLAPSE_WORLDS`). Fixing `ruins_mystery_quest.yaml`'s `hazard_kind` only
   *removes* a death vector (adds an exemption, never removes one), so regression risk to
   `hero_guild_routing` is low, but it should be re-run through `test_population_stability` after
   the content fix + its own recompile as a sanity check, not assumed safe.
5. Neither world's stale/missing-`hazard_kind` regions were caught by `test_hazard_kind_completeness`
   because that test only asserts `region.hazard_kind` is truthy — it cannot detect a
   *populated-but-mismatched* `hazard_kind`/`hazard_immunities` pair (the resolver's `"PHYSICAL"`
   default satisfies the truthy check while still being lethal). This is a real test-coverage gap
   but is explicitly Out of Scope for this ticket (`test_hazard_kind_completeness` re-litigation is
   listed Out of Scope) — noted here only so a future ticket does not have to rediscover it.

## Anti-Drift Hazards

- Do not "fix" this by adding a blanket/wildcard hazard immunity (e.g. giving every faction
  `hazard_immunities: ["PHYSICAL"]`) — that would silently defeat the entire native-endurance
  mechanism corpus-wide and contradicts `test_hazard_drain_default_hazard_kind_no_regression`'s
  explicit intent ("the new field must not grant accidental universal immunity"). Fix must be
  per-module `hazard_kind` authoring matching each region's actual populating faction, following
  the existing pattern (`NATURAL_TERRAIN` for terrain-native factions, `UNDEAD_CORRUPTION` for
  undead) — not a mechanism-level change.
- Do not touch `src/world/environment.py::calculate_hazard_drain` or
  `src/worldassembly/resolver.py:798`'s default — both are working as documented and covered by
  their own unit tests (`test_hazard_drain_default_hazard_kind_no_regression` and siblings in
  `tests/unit/world/test_regional_consequences.py`). This is a content-authoring fix, not an engine
  fix.
- Any content edit to `ruins_mystery_quest.yaml`, `scalable_bandit_camp.yaml`, or
  `trading_company_hub.yaml` requires a **recompile** (re-run assembly + `WorldCompiler.compile`)
  of every world that composes it — `dungeon_crawl`, `hero_guild_routing` (both use
  `ruins_mystery_quest`; `dungeon_crawl` also uses `scalable_bandit_camp`), and `urban_political`
  (uses `trading_company_hub`) — to pick up the change. A source-only edit without recompiling
  reproduces this exact bug class again (per Finding 3's precedent).
- `urban_political`'s recompile picks up **all** of `bandit_road_trade_pressure.yaml`'s current
  content, not just `hazard_kind` — diff the full resolved output after recompiling to confirm no
  other unrelated resolved field shifted unexpectedly (e.g. `faction_tension_overrides`,
  `information_source_profiles` seeding) since those are hand-authored directly in
  `urban_political/world.yaml` and must survive the recompile unchanged.
- Removing the `xfail` markers in `test_corpus_diversity.py` must be done for **both** worlds
  together only once **both** are independently confirmed passing — do not remove one xfail while
  the other world's fix is still pending, and do not use `xfail(strict=False)`'s permissiveness as
  a reason to skip re-running the full 300-tick check for the world whose fix looks "obviously
  sufficient" from checkpoint-level math alone (verify, don't extrapolate).
