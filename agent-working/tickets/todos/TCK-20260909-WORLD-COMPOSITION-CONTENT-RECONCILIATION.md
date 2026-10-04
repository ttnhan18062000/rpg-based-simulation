---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION
phase: open
date: 2026-09-09
tags: [architecture, content]
---

# TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION

## Title
Reconcile 8 diverged world-composition content pairs (not a mechanical move), then retire `data/content/world_compositions/`

**Retitled 2026-09-12** (was "Consolidate `data/content/world_compositions/` into `data/worlds/`
per the existing ADR") — the original title read as a refactor. Real investigation (below) found
it is a content reconciliation requiring 8 separate per-world "which module set is authoritative"
decisions, with a directory cleanup only after those are made. Pulled out of the Batch-E-adjacent
consolidated PR for exactly this reason — see the 2026-09-12 findings block.

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
`docs/architecture/world_repository_layout.md`'s own ADR (`ACCEPTED` status) is explicit:
*"Rather than creating separate directories for raw templates, specs, and compositions, we will
maintain the existing unified world repository root at `data/worlds/`... The root source file
inside a world folder is always `world.yaml`. The schema version within the YAML determines how
the repository indexes it"* — and names `worldcomposition.v1` as one of the accepted schema
versions indexed there. `data/content/world_compositions/*.yaml` (read by `ScenarioSetupResolver`,
default `compositions_dir`) is the anomaly this ADR already argued against, not `data/worlds/`.

**Concrete evidence the split causes real harm, found during
`TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`**: `frontier_living_world` already has two
diverged copies — `data/worlds/frontier_living_world/world.yaml` (7 modules via the richer
`module_refs` form, including `trading_company_hub`, plus `information_source_profiles`/
`pending_information_responses`) vs. `data/content/world_compositions/frontier_living_world.yaml`
(6 modules via the plain `modules:` shorthand, missing `trading_company_hub` and both
Pattern-6 fields). Two sources of truth for the same `world_id`, indexed by two different readers,
already drifted with nothing to catch it.

Also related: `TCK-20260607-STRICT-MODE-PRODUCTION` records that
`CatalogRepository("data/content").load_all(strict=True)` raises precisely because
`world_compositions/*.yaml` are non-catalog files sitting inside the catalog content directory —
the split was already a known irritant before this ticket's own finding.

**Scope note (user decision, 2026-09-09)**: `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`
deliberately does NOT do this migration — it only points `ScenarioSetupResolver`'s own
`compositions_dir` at `data/worlds/` for Campaign's own resolution (and taught
`ScenarioSetupResolver._load_composition()` to accept both the flat `<id>.yaml` and the nested
`<id>/world.yaml` layout, trying nested first). This ticket is the actual repo-wide consolidation
the ADR calls for — moving every `data/content/world_compositions/*.yaml` into `data/worlds/<id>/
world.yaml` (or confirming they already have a `data/worlds/<id>/` counterpart, per
`frontier_living_world`'s own precedent) and retiring the `data/content/world_compositions/`
directory entirely, updating every caller (not just Campaign) to use the unified layout.

**2026-09-12 pre-implementation check — this is NOT mechanical, do not treat it as a batch-sized
refactor.** Before writing any migration, ran the cheap check peer review asked for: diffed every
`data/content/world_compositions/<id>.yaml` against its `data/worlds/<id>/world.yaml` counterpart.

- **8 of 9 pairs diverge**, not just `frontier_living_world`: `dungeon_crawl`, `frontier_extended`,
  `frontier_living_world`, `highland_traverse`, `swamp_border_world`, `urban_political`,
  `wilderness_survival` (all 7 top-level `.yaml` files), plus `generated_frontier_3_42` (one of the
  two files under the `generated/` subdirectory).
- **Only `simq_scale_stress_seed42` is byte-identical.**
- **Neither side is consistently the superset.** `dungeon_crawl` example, spelled out concretely
  (the kind of divergence, not a one-off formatting difference): `data/worlds/dungeon_crawl/
  world.yaml` has 3 modules (`goblin_camp_conflict`, `old_mine_resource_loop`,
  `scalable_bandit_camp`) where `data/content/world_compositions/dungeon_crawl.yaml` has only 1
  (`scalable_bandit_camp`); the two also disagree on `danger_scale` (2 vs. 4), and `data/worlds/`
  has a `faction_tension_overrides` block the other side lacks entirely. This is the same shape as
  every one of the 8 divergent pairs — a genuine per-world "which module set/settings are
  authoritative for this world" content decision, not a rename or a formatting reconciliation. A
  rule like "prefer the richer file" does not resolve this, since richness isn't consistently on
  one side.
- **Production is unaffected either way**: `CatalogScenarioStateBuilder`'s only real (non-test)
  caller is `CampaignOrchestrator`, which unconditionally overrides `compositions_dir=Path(
  "data/worlds")` — no fallback, no conditional. Nothing in live production code ever reads the
  default `data/content/world_compositions/` path.
- **But two real tests depend on the default, and this is the part most likely to be missed**:
  `tests/integration/scenarios/test_scenario_catalog_matrix.py` and `tests/integration/scenarios/
  test_scenario_setup_resolver.py` both construct `ScenarioSetupResolver()` with no
  `compositions_dir` override, relying on the current default (`data/content/world_compositions/`).
  Redirecting that default to `data/worlds/` — the naive "just point it at the unified layout"
  fix — would silently change what these tests load (the simpler 6/7-module version today, the
  richer/diverged version after) and potentially what they assert on. Anyone picking this ticket up
  must hit this before starting the redirect, not discover it after.

**Disposition**: pulled out of the Batch E-adjacent consolidated PR (`#174`) for exactly this
reason — 8 separate content-authority decisions do not belong inside a batch refactor PR. To be
scoped as its own initiative once the batch closes. No per-world detailed diff dump was produced
beyond the `dungeon_crawl` example above (peer review confirmed the list-plus-shape is sufficient
to route later; a full dump can be regenerated cheaply when this is picked up, via the same diff
loop over `data/content/world_compositions/*.yaml` vs. `data/worlds/<id>/world.yaml`).

## Merged in from `TCK-20260930-WORLD-ID-HAS-TWO-DIVERGENT-DEFINITIONS` (2026-10-03)

That ticket was filed 2026-09-30, found to duplicate this one the same day, and is **folded in here
per `TCK-20261002-EPIC-SEMANTIC-FOUNDATION-COMPLETION`'s Child A** ("merged toward the older ticket,
not run separately"). Its file is removed from `agent-working/tickets/todos/`; git history holds it.
Everything below is what it added that this ticket did not already have.

**1. This is a measurement-validity problem before it is a content problem — the reason it now goes
first.** This ticket framed the split as ADR compliance plus content consolidation, and concluded
"production is unaffected either way". That is true of *production* and false of *measurement*. A probe
run through `WorldAssemblyResolver.assemble()` describes a world that **never runs**, while production
loads via `WorldRepository.load_world_with_context` (`src/worldbuilding/repository.py:89-114`). Any
investigation that compiles a world through the catalog path is measuring a different world than the
simulation executes. This is why the owner's work order puts it ahead of every rule-map slice: each
slice gathers evidence by running worlds.

- How it was found: a region-count disagreement between two runtime probes of `dungeon_crawl` — 2
  regions / 12 population vs 4 regions / 32. Not a stale cache; two definitions.
- Production callers of the running path: `src/cli/entry.py:226`,
  `src/domains/campaigns/orchestrator.py:746`, `tools/execution_census.py`, the calibrate tools.
- **A known-affected artifact:**
  `agent-working/stored_artifacts/TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED/investigation.md`
  compiled via the catalog path (`data/content/world_compositions/frontier_living_world.yaml`). It is
  the one confirmed instance; the general case is AC-7 below.
- **15 `world_id`s exist only in `data/worlds/`** with no catalog composition at all. **Zero exist only
  in the catalog.** That asymmetry is itself evidence for which side is authoritative. *(Corrected
  2026-10-04 — the folded ticket said 17 and named two examples that are present on both sides. See the
  re-measurement section below for the measured list.)*
- Two of its conclusions were checked and **survive** this defect, so do not reopen them: the
  demographic-cohort truncation finding (its decisive probe used `load_world_with_context` across 21
  worlds) and the camp `STALE-PREMISE` closure (both its modules are present in *both* definitions of
  `frontier_living_world`).

**2. Re-confirmed still unfixed at 2026-09-30, and again at 2026-10-03** (`origin/main` `1a40d22d1`):
`data/content/world_compositions/` still holds the same 7 top-level + 2 `generated/` files as the
2026-09-12 inventory, and a crude list-item count still differs for 6 of the 7 top-level pairs. **That
count is an indicator, not the module-set diff** — it does not distinguish `modules:` shorthand from
`module_refs:`, and `wilderness_survival` reads equal (7/7) while 2026-09-12 recorded it as divergent.
Regenerate the real per-world diff at pickup, as this ticket already instructs; do not treat these
numbers as the inventory.

## Three gaps found 2026-10-03 that neither ticket recorded

Each verified directly in the working tree at `1a40d22d1`, not inferred.

**Gap 1 — live code *writes* to the directory this ticket retires, so "retire once nothing reads from
it" is not sufficient.** `src/worldgeneration/generator.py:536` does
`Path("data/content/world_compositions/generated").mkdir(parents=True, exist_ok=True)` and then writes
`{world_id}.yaml` into it. This is the generator's declared output contract, stated in its own docstring
at `:383`. **A world-generation run recreates the retired directory**, so the split regrows silently and
the AC-6 check below would start failing on worlds nobody hand-authored. This ticket's final "retire
once nothing reads from it" step must become "once nothing reads *or writes* it", and the generator
needs a decided output location — almost certainly `data/worlds/<id>/world.yaml`, but that is a real
decision because it changes where generated worlds land.

**Gap 2 — `docs/guides/content_authoring.md` §4 instructs authors to create compositions at exactly the
path being retired.** It says, as a numbered how-to: *"A composition assembles a set of modules into a
named world. File location: `data/content/world_compositions/<world_id>.yaml`"*, with a full YAML
template and a `make world-validate`/`world-compile` workflow. **Neither ticket mentioned this doc.**
Retiring the directory while the authoring guide still teaches it guarantees the divergence is
re-created by the next person who follows the documented process. Updating this guide is part of the
work, not a docs-follow-up.

**Gap 3 — a stale citation that will send a reader hunting for a ticket that does not exist.**
`src/domains/campaigns/orchestrator.py:186` points at
`TCK-20260909-WORLD-COMPOSITION-DIRECTORY-CONSOLIDATION` for "the repo-wide migration this ADR still
calls for". That is **this ticket's own pre-retitle name** — retitled in `24920f912` (PR #174), the file
deleted at the old path. No such ticket exists anywhere in the tree. Update the comment to this ticket's
current ID while touching that file (which this ticket does anyway, to revert the override).

## Correction to an attribution both tickets carried (2026-10-03)

**The ADR does not say what both tickets claim it says.** This ticket's Request Summary and the merged
ticket's duplicate banner both assert that `docs/architecture/world_repository_layout.md` names
`data/content/world_compositions/` as the anomaly to retire. **It does not mention that path at all** —
verified by grep over all 54 lines. What the ADR actually establishes is narrower: `data/worlds/<id>/
world.yaml` is the unified source root and `worldcomposition.v1` is one of the schema versions indexed
there. The "`world_compositions/` is the anomaly, not `data/worlds/`" wording is an **interpretation**,
and it originates in the code comment at `src/domains/campaigns/orchestrator.py:178`, not in the ADR.

**The conclusion still holds and is well-grounded** — the ADR's unified-root decision, every production
caller reading `data/worlds/`, and the 17-to-0 asymmetry all point the same way. Only the *citation* was
wrong. It is corrected here because AC-3 requires evidenced per-world decisions, and an authority
argument that cites a document which does not contain it would not survive review. **Note the genuine
tension this leaves:** the ADR (`ACCEPTED`) and `content_authoring.md` §4 (a live how-to) point at
different locations, and neither references the other. That conflict, not a missing decision, is what
AC-8 resolves.

## 2026-10-04 re-measurement — the 8 content decisions collapse to ONE

**This supersedes the 2026-09-12 block's central claim.** That block concluded "neither side is
consistently the superset" and "a rule like 'prefer the richer file' does not resolve this", and sized
the ticket at **8 separate per-world content-authority decisions, likely needing user or peer input per
world**. Re-measured against all 9 pairs at `1a40d22d1`: that is no longer true, and the sizing was the
main thing making this ticket expensive and hard to dispatch.

**Result: in 8 of the 9 pairs there is nothing on the catalog side at all** — no module, no key, no
value — that is not also in `data/worlds/`. The running definition is a strict superset. **Exactly one
real value conflict exists in the whole corpus:**

| pair | catalog-only content |
|---|---|
| `dungeon_crawl` | `scalable_bandit_camp.parameters.danger_scale` — **catalog `2`, running `4`** |
| the other 8 | **none** |

Module-set direction, same measurement: `catalog-only-modules` is **empty for all 9 pairs**. Five pairs
have the running side adding modules (`trading_company_hub` ×3, `goblin_camp_conflict` +
`old_mine_resource_loop`, `hero_adventurers`); four have identical module sets
(`highland_traverse`, `wilderness_survival`, `generated_frontier_3_42`, `simq_scale_stress_seed42`).

**Why that collapses the decisions rather than just shrinking them.** Combined with the
measurement-validity finding above — the catalog path has never driven a production run — a catalog copy
that is a strict subset of the running definition contains no intent that was ever in effect. There is
nothing to choose between, so AC-3's "per-world authoritative-content decision" is satisfied for 8
worlds by one recorded decision, not eight. The remaining `danger_scale` 2-vs-4 is the only place the
two definitions genuinely disagree, and even there the catalog's `2` has never executed — so it is a
**confirm**, not a design choice. Worth one explicit sentence in the record, not a round of input.

**Method, so this can be re-run and checked rather than trusted.** Load both YAMLs; normalise
`module_refs:` (dict form, with `parameters`) and `modules:` (string shorthand) to one `{module_id:
parameters}` map; recursively report anything present in the catalog copy and absent-or-different in the
running one. **Known limits, stated because the first version of this check was wrong:** it compares
lists by length, not by deep membership, and an earlier pass **excluded `module_refs` from the recursive
walk and so missed the `danger_scale` difference entirely** — it reported a clean strict superset for all
9 pairs, which was false. The per-module parameter comparison is a separate pass for that reason.
Re-run both passes at pickup; do not treat this table as the full diff the Scope already asks for.

**Correction to a number this ticket carried for one commit.** The merge block above originally said
**17** `world_id`s exist only in `data/worlds/`, citing `generated_frontier_3_42` and
`simq_scale_stress_seed42` as examples. Measured: it is **15**, and **both of those examples are wrong** —
each exists on both sides. The figure came from the folded ticket and I propagated it without checking.
The asymmetry conclusion it supports is unaffected and in fact cleaner: **15 running-only, 0
catalog-only.** The 15 are `camp_maturity_calibration_pilot`, `crowded_frontier`, `frontier_marches`,
`hero_guild_routing`, `lifecycle_full_coverage_world`,
`mechanic_scenario_combat_judgement_withdrawal`, `quest_dense_frontier`, `resource_dense_basin`,
`sandbox_world`, `simq_routing_test`, `unit_faction_tension`, `unit_information_density`,
`unit_information_routing_pilot`, `unit_information_source`, `unit_selfmodel_pilot`.

**What this does not change.** The two pinned tests still ride the default and still must be updated
before any redirect; Gaps 1-3 are untouched; the deletion is still gated on nothing reading *or writing*
the directory. The ticket got cheaper and much more dispatchable, not smaller in its other obligations.

## Rule-layer ruling, 2026-10-04 — where the normative sentence lives

**Source:** `world-rule-catalog-design`, owner of `docs/world_rules/`, checked at `origin/main`. Asked
before implementing, per the ordering this repo learned the hard way. `OWN-01` verified present at
`docs/world_rules/foundations/state-ownership.md:23` ("One authoritative source of durable truth").

- **No catalog Rule covers this, and none should be added.** World-definition *storage* is below the
  catalog's scope by design — the catalog states semantics *inside* a simulated world (subjects, places,
  causes). Which file defines a world before the simulation starts is content/configuration
  architecture. `ID-01` is about a first-class simulated subject and a `world_id` is not one; `LOC-01`
  is the analogous shape at the wrong scope.
- **Cite the principle as "by analogy to `OWN-01`", never "`OWN-01` governs".** Two module sets for one
  `world_id`, with a genuine value conflict, is that violation's shape — but saying it governs would
  overstate the catalog's reach.
- **The ONE normative sentence lives in the ADR,** `docs/architecture/world_repository_layout.md` §1,
  which is already the storage-layout decision record. Make it explicit there, roughly: *"`data/worlds/
  <world_id>/` is the sole authoritative definition of a `world_id`; no other location may define a
  `world_id`."*
- **Everything else points at the ADR, and must not restate the location** (Define information once):
  - `docs/mechanics/06_worldbuilding_foundation.md` — the **integrity invariant only**: a `world_id`
    resolves to exactly one definition, and integrity validation enforces it (AC-6's check). Cite the
    ADR for *where*. Keeps the Bible from becoming a storage spec.
  - `docs/guides/content_authoring.md` §4 — correct the teaching path and **link** the ADR.
  - **Parity:** if Bible 06 gains the invariant sentence, add/update the matching ledger entry
    (`substrate.yaml` or wherever worldbuilding integrity lives) with AC-6's new check as its
    `test_path`.
- Authority itself: **confirmed, not decided** — the owner explicitly accepted the measured evidence
  rather than re-opening it.

## 2026-10-04 — the test surface is ~4.5x larger than this ticket records

**Found while running the catalog owner's own suggested check** ("if any test or doc cites the catalog's
`2` as intended design, reconcile it in the same change, not silently"). It does, and the surrounding
surface is much bigger than the 2026-09-12 block's "two real tests depend on the default".

**`tests/integration/worldassembly/test_real_content_world_compositions.py` exists to test the directory
this ticket deletes.** It hardcodes `Path("data/content/world_compositions/<id>.yaml")` at **seven** call
sites (`:30`, `:44`, `:62`, `:86`, `:345`, `:385`, `:436`) across `frontier_living_world`,
`wilderness_survival`, `urban_political` and `dungeon_crawl` — and at `:452` it asserts
**`bandit_ref.parameters.get("danger_scale") == 2`**, i.e. it pins the catalog copy's losing value as
expected design. That is the exact landmine the owner predicted.

**Nine test files reference `world_compositions` in total**, not two:
`tests/tools/test_content_inventory.py`, `tests/unit/content/test_content_usage_matrix.py`,
`tests/unit/content/test_content_paths.py`, `tests/unit/worldassembly/test_assembly.py`,
`tests/integration/content/test_swamp_border_pack.py`,
`tests/integration/content/test_expansion_gate.py`,
`tests/integration/worldassembly/test_real_content_world_compositions.py`,
`tests/integration/worldassembly/test_e2e_smoke.py`,
`tests/integration/scenarios/test_content_foundation.py`.
How many genuinely *depend* on the directory versus merely mention a path is **not yet measured** — that
is Investigate's job, and the nine is a reference count, deliberately not reported as nine breakages.

**The real open question this raises, which is a decision and not a mechanical edit:**
`test_real_content_world_compositions.py`'s whole subject is the catalog path. Repoint it at
`data/worlds/` (it then duplicates coverage that may already exist), or delete it as testing a retired
location? That is not pre-judged here. Note the direction of this correction is **opposite** to the
content-decision collapse above: the content work shrank from 8 decisions to 1, and the test work grew.
Both corrections came from measuring rather than from reading the ticket's own prose.

## Why this is now first, and why it is now P1

**Raised P2 → P1, 2026-10-03.** `TCK-20261002-EPIC-SEMANTIC-FOUNDATION-COMPLETION` makes this ticket
**Child A, first**, per the owner's work order (`roadmap.md` §8 item 5). P2 was correct while this was
ADR hygiene; it is wrong now that the whole foundation programme is sequenced behind it.

Not tidiness. Every later probe and rule-map slice in
`TCK-20261002-EPIC-SEMANTIC-FOUNDATION-COMPLETION` gathers evidence by running worlds. While one
`world_id` resolves to different module sets by entry point, two measurements of "the same world" are
not comparable and a slice's verdicts inherit that ambiguity. Fixing it afterwards would invalidate the
slices already taken.

## Scope
- **Record ONE decision: `data/worlds/<id>/world.yaml` is authoritative.** Grounds, all three
  independent: the ADR's unified-root decision; the catalog path has never driven a production run; and
  the running definition is a strict superset of the catalog copy in 8 of 9 pairs with zero catalog-only
  content anywhere. ~~A per-world decision for each of 8 diverged pairs, likely needing peer/user
  input.~~ **Superseded by the 2026-10-04 re-measurement above** — there is no content to choose between
  for 8 of the 9.
  - **The one genuine disagreement to confirm explicitly:** `dungeon_crawl`'s
    `scalable_bandit_camp.parameters.danger_scale`, catalog `2` vs running `4`. Keep `4` (it is what has
    been running) and say so in one sentence. Do not silently drop it — it is the only place the two
    definitions actually conflict, so it is the only place a reader could reasonably ask what happened.
- Inventory every file under `data/content/world_compositions/` and check whether a
  `data/worlds/<id>/world.yaml` counterpart already exists (mostly already done, see findings
  block — `simq_scale_stress_seed42` is the one byte-identical pair; confirm no new drift since
  2026-09-12 before treating the inventory as still current).
  - If it matches: delete the `data/content/` copy, no content change needed.
  - If it diverges: apply the per-world authoritative decision above, reconcile.
  - If no `data/worlds/<id>/` counterpart exists: create one, migrating the content.
- **Before redirecting `ScenarioSetupResolver`'s default `compositions_dir`, update
  `tests/integration/scenarios/test_scenario_catalog_matrix.py` and `tests/integration/scenarios/
  test_scenario_setup_resolver.py`** (both rely on the current default, unoverridden) to account
  for whatever the reconciled content ends up being — confirmed 2026-09-12 this is the part most
  likely to be missed, not an incidental regression check.
- Update every caller of `ScenarioSetupResolver`/`CatalogScenarioStateBuilder` that currently
  relies on the default `compositions_dir` (`data/content/world_compositions/`) to use the unified
  `data/worlds/` layout instead — including reverting `CampaignOrchestrator`'s own explicit
  `compositions_dir=Path("data/worlds")` override back to the (now-unified) default, once the
  default itself points at `data/worlds/`.
- Decide whether `ScenarioSetupResolver._load_composition()`'s dual-layout fallback (nested-first,
  flat-second — added by `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` specifically to make
  the Campaign-only override safe) should be simplified back to nested-only once every caller is
  migrated, or kept as permanent back-compat.
- **Decide the generator's output location** (Gap 1). `src/worldgeneration/generator.py:536` writes
  into the retired directory and recreates it; its docstring at `:383` declares that path as its
  contract. Both must change together, and the chosen location is a real decision, not a path swap.
- **Update `docs/guides/content_authoring.md` §4** (Gap 2) so the documented authoring path is the
  authoritative one. Without this the split regrows by design.
- **Fix the stale ticket citation at `src/domains/campaigns/orchestrator.py:186`** (Gap 3) while
  reverting that file's `compositions_dir` override.
- **Add the "one `world_id`, one module set" check** (merged AC-6) so this cannot silently reappear —
  the structural guard, separate from reconciling today's content.
- **Assess which prior measurements used the non-running definition** (merged AC-7). One confirmed
  instance is named above; the general case is unknown. State plainly which recorded conclusions were
  re-checked and whether any changes — a conclusion that survives is a result worth recording, not
  silence.
- Retire `data/content/world_compositions/` once nothing reads from it — this step alone (given
  production already never reads the default) is the "different and much smaller task" it could
  reduce to if the 8 content decisions are instead resolved by deferring/documenting rather than
  reconciling; not pre-judged here.

## Out of Scope
- Any Campaign-specific entity-spawn logic — already implemented and closed in
  `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`.
- Consolidating the "legacy" `build_scenario_state()`/`ArenaInjector` certification path or
  `V2EngineManager`'s own manual spawn logic into this unified layout — a separate, larger
  initiative the user explicitly declined to bundle into the Campaign-mode fix; may be worth
  revisiting once this ticket lands, but not decided here.

## Acceptance Criteria
- [ ] Every world composition has exactly one authoritative source under `data/worlds/<id>/
      world.yaml`; `data/content/world_compositions/` is empty or removed.
- [ ] Every caller of `ScenarioSetupResolver` uses the unified layout, verified by a real test.
- [ ] **One** recorded, evidenced authoritative-source decision covers the corpus, with the
      `dungeon_crawl` `danger_scale` 2-vs-4 conflict called out explicitly as the single genuine
      disagreement and its resolution stated. *(Amended 2026-10-04: was "each of the 8 diverged pairs has
      a per-world decision". Re-measurement found zero catalog-only content in 8 of 9 pairs, so eight
      separate decisions would be eight restatements of one.)*
- [ ] `test_scenario_catalog_matrix.py`/`test_scenario_setup_resolver.py` (the two tests relying on
      the un-overridden default) are updated to match whatever content the reconciliation settles
      on, confirmed passing. **Amended 2026-10-04: these two are necessary but NOT sufficient** — see
      the test-surface section above. `test_real_content_world_compositions.py` pins the catalog path at
      seven sites and asserts `danger_scale == 2`; nine test files reference the directory. Every test
      that genuinely depends on it must be resolved, and the repoint-or-delete decision for
      `test_real_content_world_compositions.py` recorded with its reasoning.
- [ ] The `dungeon_crawl` `danger_scale` resolution is recorded as **"catalog value never drove a run;
      running value (4) kept"**, and no test or doc is left asserting `2` as intended design.
      **Sharpened by the rule owner 2026-10-04 — this holds under BOTH options for
      `test_real_content_world_compositions.py` and applies across all nine referencing files, not just
      that one:**
      - If the file is **repointed**, `:452` must assert **`4`**, carrying a comment or ticket note
        saying why (the catalog value never drove a run; the running value is kept).
      - If the file is **deleted**, **no surviving copy of the `== 2` assertion may reappear in another
        file.** Deleting the test must not quietly relocate the wrong expectation.
- [ ] Full scoped regression across every consumer of `ScenarioSetupResolver`/
      `CatalogScenarioStateBuilder`/`WorldAssemblyResolver` passes.
- [ ] **AC-6 (merged):** a check fails when one `world_id` resolves to two different module sets. It
      must fail on today's content before the reconciliation lands, or it is not testing anything.
- [ ] **AC-7 (merged):** a written assessment of which prior measurements used the non-running
      definition, and whether any recorded conclusion changes. Conclusions that survive are stated as
      survivals, with what was re-checked.
- [ ] **AC-8 (merged, amended):** `docs/mechanics/06_worldbuilding_foundation.md` **and**
      `docs/architecture/world_repository_layout.md` state which location is authoritative. The ADR is
      amended rather than merely cited, because it does not currently say this (see the attribution
      correction above), and `docs/guides/content_authoring.md` §4 currently points the other way. All
      three must agree when this closes.
- [ ] **AC-9 (from Gap 1):** no code path writes into a retired `data/content/world_compositions/`. A
      world-generation run does not recreate it.

## Related Tickets
- `TCK-20261002-EPIC-SEMANTIC-FOUNDATION-COMPLETION` — **this ticket is its Child A, first.** The epic
  is sequenced behind this one landing
- `TCK-20260930-WORLD-ID-HAS-TWO-DIVERGENT-DEFINITIONS` — **folded into this ticket 2026-10-03**, file
  removed from `agent-working/tickets/todos/`; its unique content is in the merge block above and in
  AC-6/7/8. Do not re-file it
- `TCK-20260930-MECHANISM-ABSENCE-VERDICTS-NEED-RUNTIME-EVIDENCE` — a runtime instrument for absence
  verdicts must also load the world the way production does, or it measures a different world
- `TCK-20260920-VALUE-DIFFERENTIAL-VERIFICATION-INSTRUMENT-GAP` — the epic's child B2. Related but
  distinct: that one asks whether a mechanism has an *effect*; this one asks whether the *world* being
  measured is the one that runs. Both are measurement-validity, neither subsumes the other
- `TCK-20260915-WORLDBUILDING-DUPLICATE-REGION-ID-ACROSS-MODULES` — same family (one id, two meanings)
  one level down, at region rather than world scope
- `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` (found and worked around this split; this
  ticket is the real fix the ADR already called for)
- `TCK-20260607-STRICT-MODE-PRODUCTION` (documents the same split as a known irritant from a
  different angle — `CatalogRepository`'s own strict-mode content validation)

## Related Docs
- `docs/architecture/world_repository_layout.md` — the ADR this ticket implements, **and which AC-8
  amends.** Read the attribution correction above first: it does not currently name the catalog path
- `docs/guides/content_authoring.md` §4 — **actively teaches the path being retired** (Gap 2)
- `docs/mechanics/06_worldbuilding_foundation.md` — declarative topology and integrity validation; the
  natural home for a "one id, one definition" law
- `docs/plans/systemic_world/roadmap.md` §8 item 5 — the owner's work order placing this first
- `docs/plans/world_composition_precondition_gap_finding.md` — retired 2026-09-30, but its §3 discussed
  `frontier_living_world` composing `merchant_league` via `trading_company_hub`. That module is present
  only in the **running** definition, so §3 was describing `data/worlds/`

## Related Stored Artifacts
None yet — created when this ticket is picked up.

## Related Code Areas
- `src/scenarios/resolver.py` (`ScenarioSetupResolver`, `_compositions_dir`; default at `:34`)
- `src/domains/campaigns/orchestrator.py:173-200` (the Campaign-only override to revert once unified,
  and the stale citation at `:186` — Gap 3)
- `src/worldbuilding/repository.py:89-114` (`load_world_with_context`, **the production path**)
- `src/worldassembly/resolver.py` (`WorldAssemblyResolver.assemble`, the catalog path)
- `src/worldgeneration/generator.py:383,536` — **writes into the retired directory** (Gap 1)
- `src/content/paths.py:8` (`world_compositions_dir` default), `src/content/validator.py:38`
  (`load_all_compositions`), `src/content/repository.py:150` (`NON_CATALOG_DIRS`)
- `src/cli/entry.py:226`, `tools/execution_census.py` — production callers of the running path
- `tests/integration/scenarios/test_scenario_catalog_matrix.py:49`,
  `tests/integration/scenarios/test_scenario_setup_resolver.py:37` — **re-verified 2026-10-03**: both
  still construct `ScenarioSetupResolver(catalog, module_repo)` with no `compositions_dir`, so both
  still ride the default. This is the trap the 2026-09-12 block flagged, still live
- `data/content/world_compositions/` (7 top-level + `generated/`), `data/worlds/`

## Assumptions / Open Questions
- ~~Whether every `data/content/world_compositions/*.yaml` file has a `data/worlds/<id>/`
  counterpart, or some are genuinely orphaned/never-migrated, is not yet known — real inventory
  work for this ticket's own Investigate phase.~~ **Resolved 2026-09-12**: every file has a
  counterpart (9/9); 8 diverge, 1 matches. See the findings block above.
- Which content is authoritative for each of the 8 diverged pairs is the real open question this
  ticket now exists to answer — deliberately not pre-judged, may need peer/user input per world
  rather than a blanket rule.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
