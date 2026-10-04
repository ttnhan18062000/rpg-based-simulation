---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION
phase: done
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
DONE

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

## BLOCKER, 2026-10-04 — a closed P1 balance fix never took effect, and my own "keep 4" reasoning was wrong

**Found by the Investigate phase; every claim below re-verified by the orchestrator before being written
here.** This is the one thing on this ticket that needs a user decision before implementation, and it
invalidates part of the 2026-10-04 re-measurement's own conclusion.

**`TCK-20260627-P1I-WORLD-BALANCE-FIX` (DONE, P1) exists specifically to produce the catalog's `2`.**
D08 measured `dungeon_crawl` at **94–97% entity attrition by tick 100** (Score 14/15; the behavioural
adventure pipeline never activates because entities die before tick 201). That ticket's remedy: remove
`goblin_camp_conflict` and `old_mine_resource_loop`, reduce `scalable_bandit_camp`'s `danger_scale`
**4 → 2**, taking the entity count **32 → 12**. Verified in the closed ticket at lines 30, 33, 42, 73–75,
101–103.

**Its `## Files Changed` lists exactly one file: `data/content/world_compositions/dungeon_crawl.yaml`**
(lines 59 and 93). **It never touched `data/worlds/`.**

**Therefore the fix never took effect in production, and `dungeon_crawl` has been running the extinction
configuration ever since.** Confirmed directly: `data/worlds/dungeon_crawl/resolved/world.resolved.yaml`
— the file production actually loads — **still contains `goblin_camp_conflict` and
`old_mine_resource_loop`**, the two modules the fix removed.

**Why my own earlier inference was wrong, stated plainly.** The 2026-10-04 re-measurement correctly
established that the running definition is a recursive strict superset of the catalog copy. From that I
inferred "a strict-subset catalog copy holds no intent that was ever in effect, so there is nothing to
choose between". **That inference is false.** A subset can be a *deliberate reduction*, and for
`dungeon_crawl` it is exactly that. The measurement was a correct fact; the conclusion drawn from it was
not. **AC-5 as written ("catalog value never drove a run; running value (4) kept") would not drop a dead
value — it would re-ratify the precise configuration a closed P1 ticket was filed to eliminate.**

**There are THREE definitions of a world, not two** — also verified, and it changes the ADR sentence's
operative target:

| artifact | role |
|---|---|
| `data/content/world_compositions/<id>.yaml` | catalog copy; never loaded by production |
| `data/worlds/<id>/world.yaml` | source of record — but **NOT what production loads** for a `worldcomposition.v1` world |
| `data/worlds/<id>/resolved/world.resolved.yaml` | **what production actually loads** (`src/worldbuilding/repository.py:74-81` redirects to it, and raises if it is absent) |

So editing `data/worlds/<id>/world.yaml` alone changes **nothing** in production until its `resolved/`
snapshot is regenerated. `dungeon_crawl`'s snapshot is dated 2026-09-08 against a `world.yaml` of
2026-08-31, so they are not even generated in lockstep.

### Rule-owner ruling on the third artifact, 2026-10-04 — and a correction to my premise

Asked and answered by `world-rule-catalog-design`, checked at `origin/main`. **Both questions: yes.**

**My premise was too narrow, and this is the important part.** I framed the rule as "regenerate
`resolved/` whenever `world.yaml` changes". Wrong: **the snapshot is a function of `world.yaml` PLUS the
module and catalog content the resolver reads at resolve time.** So a snapshot can go stale from a module
or catalog edit with `world.yaml` never touched — and the 09-08-vs-08-31 dates do **not** show which
input moved. Any freshness rule written only against `world.yaml` would miss that whole class.

**Also noted:** the ADR **already** draws the source/projection line at
`docs/architecture/world_repository_layout.md:41-54` — a `worldcomposition.v1` source is never passed to
the compiler, and the resolver writes the `resolved/` output the loader reads. **What the ADR lacks is the
authority and freshness rule**, not the structure. The gap is narrower than I described it.

**(1) The ADR clause** — goes in **§1, directly after the normative sentence, as one rule, not a new
section.** Wording supplied by the rule owner:

> *"Within that directory, `world.yaml` is the authored definition. For a `worldcomposition.v1` world,
> `resolved/world.resolved.yaml` is a generated projection of it: it is never hand-edited, and it must
> equal what the resolver produces from the current `world.yaml` and the current module/catalog content.
> A committed projection that differs from a fresh resolve is a defect. It is not an alternative
> definition."*

Bible 06 states the invariant — *"the world the engine loads is the one its authored definition resolves
to"* — and cites the ADR, same pattern as the world-id ruling. **No catalog Rule is added:** this is
storage and build, below catalog scope, by analogy to `OWN-01`.

**(2) AC-6 must include agreement — it currently does not test its own invariant.** The rule owner's
reasoning, which is the decisive point: *"one `world_id` resolves to exactly one module set" is about the
world that runs. A check that compares two authored files while production loads a third would pass green
on exactly the failure you found.* So AC-6 is amended below. The comparison is **equality against a fresh
resolve**, never a field-by-field diff against `world.yaml`, because the projection legitimately contains
expanded content. **If a fresh resolve is not byte-deterministic today, that is a finding to file, not a
reason to weaken the check to a subset.** Mechanism (CI test, regenerate-and-diff make target, or both;
and whether the provenance/report sidecars join the comparison) is explicitly **not** the rule owner's —
it is this ticket's or test-architecture's.

### The decision needed (user / rule owner), before Implement

Does reconciliation **re-apply** the balance fix into the authoritative location — `data/worlds/dungeon_crawl/`
reduced to 2 modules with `danger_scale: 2`, plus a regenerated `resolved/` snapshot — or **abandon** it
with a recorded rationale?

- Re-applying is **fully consistent with `data/worlds/` being authoritative** and does *not* reopen the
  authority ruling. It is "put the delivered fix where it actually runs".
- Abandoning means accepting a measured 94–97% extinction config as intended, which needs saying out loud
  rather than happening as a side effect of a path cleanup.
- **This is balance-adjacent, and balance is parked by `owner_decision_memo.md` row 7** — which is
  precisely why it is escalated rather than decided here. But note the *defect* (a closed P1 fix that
  never applied) is not a balance question; it is wrong world truth.
- `test_plan.md` marks AC-5's oracle `oracle: unresolved` and says **do not write that test yet.**
- Side note, not pre-judged: the closed fix justified removing the two modules partly on an "unmet
  `requires: frontier_village_core`" grounds, but the 4-module running definition assembles and compiles
  cleanly today, so that stated justification looks questionable.

## Plan-phase findings, 2026-10-04 — two traps and a resolved internal contradiction

**1. `docs/mechanics/content_usage_matrix.md` is GENERATED, not hand-editable.** It is produced by
`tests/unit/content/test_content_usage_matrix.py::test_generate_and_save_report` (`:111-120`). The
Investigate phase listed it under "docs requiring update", and that must **not** be read as licence to
hand-edit it — a hand edit will be overwritten by the next test run and will look like a mystery revert.
Change the generator or the inputs, never the output file.

**2. `resolved/world.resolved.yaml` has exactly ONE writer in the whole tree** —
`src/worldbuilding/cli.py:177-205`, via `make world-resolve` — against **five read-only consumers**
(`repository.py:78,132`, `lab/orchestrator.py:181-184`, `generate_corpus_registry.py:108,139`,
`calibrate_simq.py:150`, `perf/profile_sweep.py:73`). This is why AC-6's agreement half is feasible
without a locking story. Worth contrasting with the authored side, which has **no** single-writer
discipline — which is part of why the generator writing directly into `data/worlds/` (UQ-1, Option A)
deserves the rule owner's read rather than a unilateral choice.

**3. An internal contradiction in AC-5, resolved — the amended text wins.** The older rule-owner
sharpening recorded above says *"if repointed, `:452` must assert `4`"*. The later amended AC-5 says carry
**neither** `2` as authoritative **nor** `4` as confirmed-correct. **The amended reading is the correct one
and supersedes the earlier sharpening**, because the earlier one predates the discovery that the balance
fix never applied — at the time it was written, `4` genuinely looked like the confirmed running value.
Resolution: remove **both** numeric assertions with a pointer comment to
`TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION`, and make the
anti-relocation guard compare against whatever `data/worlds/dungeon_crawl/world.yaml` actually holds — so
it is correct in **either** landing order of the two tickets. The rule owner's no-stale-expectation
constraint is still honoured: no surviving copy of `== 2` anywhere.

## AC-6 mechanism, measured 2026-10-04 — a fresh resolve IS comparable, and there is a ready oracle

The rule owner left one sub-question open — *"whether the provenance/report sidecars join the comparison or
only `world.resolved.yaml`"* — and warned that if a fresh resolve is not byte-deterministic, that is itself
a finding to file. Measured, so the implementer does not have to discover it:

**There is exactly one nondeterministic field in the resolve output, and it is isolated.**
`src/worldassembly/resolver.py:709` sets `created_at = datetime.now(timezone.utc)...`. It lands **only in
`provenance_manifest.json`**. Confirmed: `created_at` does **not** appear in
`data/worlds/dungeon_crawl/resolved/world.resolved.yaml`, and the manifest is the only file under
`resolved/` containing it.

**So the comparison splits cleanly and no determinism finding needs filing:**

| artifact | comparison |
|---|---|
| `world.resolved.yaml` | **byte-comparable against a fresh resolve.** No timestamp. AC-6's primary oracle |
| `provenance_manifest.json` | **not** byte-comparable (`created_at`). Compare `content_fingerprint` instead |
| `assembly_report.json`, `validation_report.json`, `compile_context.json` | timestamp content **unverified** — exclude by default, or check before including |

**`content_fingerprint` is a ready-made staleness oracle, cheaper than a full diff.** Built at
`resolver.py:702-708` as `sha256(world_id + catalog_fingerprint + each module fingerprint, modules sorted)`
— fully deterministic, and it covers exactly the inputs the rule owner named: the authored composition
**plus** current module and catalog content. `manifest_id` is `prov_` + its first 16 chars, so one field
comparison detects staleness. A mismatch means the committed snapshot was not produced from today's inputs.

**It also confirms the `dungeon_crawl` defect a third time, via a different artifact.** The committed
manifest's `module_fingerprints` holds **4** modules, including `goblin_camp_conflict` and
`old_mine_resource_loop` — the two the closed P1 fix removed. `created_at: 2026-09-08T02:50:41Z`. Three
independent artifacts now agree that the pre-fix configuration is what production resolves.

**Implementer note:** use `content_fingerprint`/`manifest_id` equality as the fast path, with a
`world.resolved.yaml` byte-compare as authoritative confirmation. Do **not** include `created_at` in any
comparison, and do **not** "fix" determinism by removing the timestamp — it is legitimate provenance, just
not part of the projection's identity.

**Limitation of the fingerprint, corrected by the rule owner 2026-10-04 — read this before "optimising"
AC-6 down to a fingerprint check.** `content_fingerprint` is computed from the **inputs**, so it detects a
**stale** snapshot. It **cannot** detect a **hand-edited** `world.resolved.yaml` whose recorded fingerprint
still matches — and *"never hand-edited"* is half of the ADR clause. **So equality against a fresh resolve
stays the check.** The fingerprint is a cheap first pass **in front of** it, never a substitute for it. My
original framing presented the two as fast-path-plus-confirmation, which is compatible, but it did not say
*why* the confirmation is non-optional; it is non-optional because it is the only half that catches
hand-editing.

## UQ-1 RESOLVED, 2026-10-04 — Option A is conformant; "authored" names the file's ROLE

The Plan phase halted on this and it is now answered by `world-rule-catalog-design`.

**Ruling: "authored" names the file's ROLE, not who wrote the bytes. Option A is conformant** — the
generator may write `data/worlds/<id>/world.yaml` directly, with a provenance marker. Their reasoning:
the clause splits **source of record** from **derived projection**, and each is defined by an obligation,
not by authorship. A *projection* must equal a fresh derivation from other committed inputs, so it may
never be edited independently. A *source* has no such obligation — it is what everything else derives
from. Who typed the bytes plays no part in either definition.

**Clause wording tightened, so nobody later reads it as provenance.** Replace *"`world.yaml` is the
authored definition"* with:

> *"`world.yaml` is the source definition, whether written by hand or by a generator; once written it is
> edited, not regenerated."*

The rest of the clause recorded above is unchanged. **AC-8 must use this wording, not the earlier draft.**

**The one condition, and it is a real constraint on the design:** once the generator writes
`world.yaml`, **that file IS the definition** — the generator acted as a one-time author, not a continuing
projection. If the design instead expects `world.yaml` to be regenerable from a seed and params stored
elsewhere, **those params become the real definition and `world.yaml` becomes a projection of them**,
which re-creates a second definition location — Option C's problem by another route. Therefore:

- The provenance marker records **history** (generator, version, seed, params) as a fact about origin.
- **No check may assert `world.yaml == generate(marker)`.** That would convert the marker into a
  re-derivation obligation and make `world.yaml` a projection.
- **Nothing outside `data/worlds/<id>/` may hold generation inputs as a definition.**

**Explicitly engineering-only, not the rule owner's** (so do not ask them again):
whether `list_worlds()` needs to distinguish generated worlds (the marker suffices from the rule side;
structure is not required); whether `generate()` must also run resolve so the new world has its `resolved/`
sibling (without it `load_world()` raises); and single-writer discipline on the authored side.

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

**RESOLVED 2026-10-04 — REPOINT, and it is a consequence of the ADR, not a preference.** Ruled by
`world-rule-catalog-design` on the narrow question of whether its own ADR sentence reaches these tests.
It does, for some of them, and the file **survives**. The split is test-by-test:

**Reached by the ADR — these MUST be repointed at `data/worlds/`.** Each loads a file by a world's name
and asserts `spec.world_id == "<that world>"` plus design values. That is a claim about *what defines a
world*, and the ADR says only `data/worlds/<world_id>/` may make it. They are **not** parser fixtures
that merely sit in a non-authoritative file — their own docstrings say "the real composition" and their
whole premise is real content:

| site | test |
|---|---|
| `:28`, `:42`, `:59`, `:83` | `frontier_living_world` load / normalization / assembly / determinism-and-provenance |
| `:333` | `test_wilderness_survival` |
| `:374` | `test_urban_political` |
| `:424` | `test_dungeon_crawl_composition` (this is the one whose `:452` asserts `danger_scale == 2`) |

**NOT reached by the ADR — leave these alone.** They build their own specs and claim no authored
`world_id`, so the ADR says nothing about them. They are also the second reason deleting the file would
be wrong:

| site | test | why out of reach |
|---|---|---|
| `:171`, `:188`, `:205` | `test_parametric_*` | synthetic specs |
| `:224` | `test_pack_refs_disabled_pack_raises_at_assembly` | synthetic `world_id` `"pack_test_world"` |
| `:265`, `:300` | `test_generated_composition_*` | generated ids |

**Still open, and explicitly NOT world semantics — route to `test-architecture-reviewer`:**
1. Once the named-world tests point at `data/worlds/`, do they duplicate coverage that already exists,
   and should they be merged or moved?
2. Does the authoritative layout being a **directory** (`data/worlds/<id>/world.yaml`) rather than a
   single `<id>.yaml` change how those tests load their input?

Note the direction of this whole correction is **opposite** to the content-decision collapse above: the
content work shrank from 8 decisions to 1, and the test work grew. Both came from measuring rather than
from reading the ticket's own prose, which was wrong in both directions.

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
- [x] Every world composition has exactly one authoritative source under `data/worlds/<id>/
      world.yaml`; `data/content/world_compositions/` is empty or removed.
- [x] Every caller of `ScenarioSetupResolver` uses the unified layout, verified by a real test.
- [x] **One** recorded, evidenced authoritative-source decision covers the corpus, with the
      `dungeon_crawl` `danger_scale` 2-vs-4 conflict called out explicitly as the single genuine
      disagreement and its resolution stated. *(Amended 2026-10-04: was "each of the 8 diverged pairs has
      a per-world decision". Re-measurement found zero catalog-only content in 8 of 9 pairs, so eight
      separate decisions would be eight restatements of one.)*
- [x] `test_scenario_catalog_matrix.py`/`test_scenario_setup_resolver.py` (the two tests relying on
      the un-overridden default) are updated to match whatever content the reconciliation settles
      on, confirmed passing. **Amended 2026-10-04: these two are necessary but NOT sufficient** — see
      the test-surface section above. `test_real_content_world_compositions.py` pins the catalog path at
      seven sites and asserts `danger_scale == 2`; nine test files reference the directory. Every test
      that genuinely depends on it must be resolved, and the repoint-or-delete decision for
      `test_real_content_world_compositions.py` recorded with its reasoning.
- [x] **AC-5 — RESOLVED 2026-10-04 (owner decision), and REVERSED from what it said.** It previously read
      *"catalog value never drove a run; running value (4) kept"*. **That is wrong and must not be
      implemented** — see the BLOCKER section: the catalog's `2` is the delivered remedy of a closed P1
      ticket, so keeping `4` would re-ratify a measured 94–97% extinction configuration.
      **The owner's decision is to RE-APPLY the balance fix**, and delivering it is **not this ticket's
      job** — it is owned by `TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION`
      (P1), which lands first or together with this one.
      **This ticket's remaining obligation on `danger_scale` is narrow:** when the catalog copy is
      deleted, do **not** carry its `2` forward as the authoritative value and do **not** carry `4`
      forward as "confirmed correct" either. Record that the value is owned by the other ticket, and
      leave no test or doc asserting either number as intended design on this ticket's authority.
      The rule owner's constraint still binds and is unchanged: repointed, `:452` must assert whatever
      the authoritative definition actually holds **after** the other ticket lands, with a note saying
      why; deleted, no surviving copy of the `== 2` assertion may reappear in any of the nine referencing
      files.
      `test_plan.md` marks AC-5's oracle `oracle: unresolved` — it stays unresolved **for this ticket**,
      and that is now correct rather than a gap.
      **Sharpened by the rule owner 2026-10-04 — this holds under BOTH options for
      `test_real_content_world_compositions.py` and applies across all nine referencing files, not just
      that one:**
      - If the file is **repointed**, `:452` must assert **`4`**, carrying a comment or ticket note
        saying why (the catalog value never drove a run; the running value is kept).
      - If the file is **deleted**, **no surviving copy of the `== 2` assertion may reappear in another
        file.** Deleting the test must not quietly relocate the wrong expectation.
- [ ] Full scoped regression across every consumer of `ScenarioSetupResolver`/
      `CatalogScenarioStateBuilder`/`WorldAssemblyResolver` passes.
- [x] **AC-6 (merged; AMENDED 2026-10-04 by the rule owner):** a check fails when one `world_id` resolves
      to two different module sets. It must fail on today's content before the reconciliation lands, or it
      is not testing anything. **It must ALSO assert that re-resolving each composition world
      deterministically reproduces its committed `resolved/world.resolved.yaml`** — equality against a
      **fresh resolve**, not a field-by-field diff against `world.yaml`. Without that half, the check
      compares two authored files while production loads a third and **passes green on exactly the
      `dungeon_crawl` failure recorded above**, i.e. it does not test its own invariant. If a fresh
      resolve is not byte-deterministic today, **file that as a finding — do not weaken the check**.
- [x] **AC-7 (merged):** a written assessment of which prior measurements used the non-running
      definition, and whether any recorded conclusion changes. Conclusions that survive are stated as
      survivals, with what was re-checked.
- [x] **AC-8 (merged, amended twice):** `docs/mechanics/06_worldbuilding_foundation.md` **and**
      `docs/architecture/world_repository_layout.md` state which location is authoritative. The ADR is
      amended rather than merely cited, because it does not currently say this (see the attribution
      correction above), and `docs/guides/content_authoring.md` teaches the other way. All three must
      agree when this closes.
      **2026-10-04: the ADR edit is now TWO sentences in §1** — the authority sentence plus the rule
      owner's verbatim source/projection clause (quoted above). Bible 06 adds the invariant *"the world
      the engine loads is the one its authored definition resolves to"* and cites the ADR; it must not
      restate the location or the freshness mechanics.
      **Also 2026-10-04:** `content_authoring.md` teaches the retired path at **four** sites — `:27`,
      `:72`, `:164-167`, `:292` — not only §4. Fixing §4 alone leaves three live instructions pointing at
      a deleted directory.
- [x] **AC-9 (from Gap 1):** no code path writes into a retired `data/content/world_compositions/`. A
      world-generation run does not recreate it.
- [x] **AC-10 (parity ledger, made explicit 2026-10-04):** the matching `docs/parity_ledger/` entry is
      added or updated — `substrate.yaml`, or wherever worldbuilding integrity actually lives — carrying
      **AC-6's new one-`world_id`-one-module-set check as its `test_path`**. The rule-layer ruling implied
      this (it is the consequence of Bible 06 gaining the integrity-invariant sentence) but AC-8 named
      only the three docs. Stated as its own AC because the pipeline's Parity phase **hard-blocks**
      (`PARITY_INCOMPLETE`) when a changed `src/` file maps to a ledger subsystem and no ledger file is
      touched — so leaving this implicit would stall the run late rather than guide it.

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
All three exist and migrate to `agent-working/stored_artifacts/TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION/`
at Finalize *(corrected 2026-10-04 — this section still read "None yet, created when this ticket is
picked up", which was true when filed and stale once the pipeline ran)*:

- `investigation.md` — the three-artifact analysis, the 7-of-9 genuine test-dependency classification,
  the parity-entry inventory, and the two corrections to its own "Docs Requiring Update" judgements
- `plan.md` — 15 ordered steps, `## Resolved Decisions` (UQ-1's ruling and its three hard constraints),
  Scope Guards, Dependency Map, and 12 numbered Deviations
- `test_plan.md` — Regression Surface, New Tests Required per AC, five scoped commands, Anti-Drift
  Test Guards; AC-5's oracle is deliberately marked `unresolved`

Also relevant, from the ticket this one absorbed:
- `agent-working/stored_artifacts/TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED/investigation.md` — the
  one confirmed prior investigation that compiled via the retired catalog path (AC-7's named instance)

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

## Known residual after Architecture-Verify, 2026-10-04 (disclosed, not a violation)

**One write-ordering window survives V3's atomicity fix, and it is narrower than V3's but the same
shape.** Architecture-Verify confirmed the implemented ordering is correct — the `output_path.exists()`
refusal fires first, `resolve_composition(...)` runs to completion, and only then does `world.yaml` land,
with every `mkdir`/`write_text`/`json.dump` in `src/worldassembly/resolve_io.py` confined to
`write_resolved_artifacts` (`:89-114`), so a **resolve** failure leaves the filesystem untouched and the
world stays regenerable. That is exactly what V3 asked for.

**The residual:** if **`write_resolved_artifacts` itself** fails (disk full, permissions) *after*
`world.yaml` has landed, the result is a `world.yaml` with no `resolved/` sibling — which
`repository.py`'s redirect then refuses to load, and which the `exists()` guard then refuses to
regenerate. Same un-regenerable end state V3 identified, reached one step later.

**Not a durable-state-rule violation and not a `NEEDS_CHANGES` trigger** (Architecture-Verify's
judgement): `world.yaml` is a typed definition at a stable authoritative location with a defined
lifecycle, and the code comment is honest that atomicity is absent rather than claiming it. Recorded here
so it is a known, disclosed residual rather than a surprise.

**If it is closed later, the fix named is:** write `world.yaml` **last**, or write into a temp directory
renamed on success. Either removes the window entirely. **Deliberately not done in this ticket** — it
changes write ordering in a durable path and so wants its own test, which is more than a reorder, and
Architecture-Verify had already approved the diff. The `exists()` check is also TOCTOU, which is
immaterial for a single-author generator with no concurrent-invocation contract.

**Separately, a note about the checker rather than the code:**
`architecture_reviewer_static.py`'s `durable_state_mutation` condition **fails on any file that mutates an
intentionally-mutable owned container**. It fired here on `src/domains/campaigns/orchestrator.py` for
three pre-existing assignments, because it matches attribute-chain shape (`.grief_urgencies`,
`.nemesis_relations`) and cannot resolve whether the target is frozen. `CampaignState`
(`src/domains/campaigns/state.py:364`) is a bare `@dataclass` whose docstring says verbatim *"NOT frozen —
mutation by CampaignOrchestrator is intentional. Sub-records are frozen"* — the project's typed-record
pattern working as designed. **Expect this FAIL on any future diff touching that file; it is a disclosed
checker limitation, not debt.**

## Assumptions / Open Questions
- ~~Whether every `data/content/world_compositions/*.yaml` file has a `data/worlds/<id>/`
  counterpart, or some are genuinely orphaned/never-migrated, is not yet known — real inventory
  work for this ticket's own Investigate phase.~~ **Resolved 2026-09-12**: every file has a
  counterpart (9/9); 8 diverge, 1 matches. See the findings block above.
- ~~Which content is authoritative for each of the 8 diverged pairs is the real open question this
  ticket now exists to answer — deliberately not pre-judged, may need peer/user input per world
  rather than a blanket rule.~~ **ANSWERED 2026-10-04 — do not re-open this.** The 2026-10-04
  re-measurement found the running definition is a recursive strict superset in 8 of 9 pairs with
  **zero catalog-only content anywhere**, so there is nothing to choose between for those 8. The one
  genuine value conflict (`dungeon_crawl`'s `danger_scale` 2 vs 4) is settled by the catalog copy never
  having driven a run. AC-3 is amended to one recorded decision plus that confirm. **No peer or user
  input per world is needed.** (Flagged as stale by the Scope phase — the Scope section struck it
  through on 2026-10-04 but this section was missed.)
- **Still genuinely open, and it is not a content question:** the generator's output location (Gap 1,
  `src/worldgeneration/generator.py:383,536`). That is a real undecided decision, not a path swap,
  because it changes where generated worlds land.

## Implementation Notes

Implemented against `agent-working/staging_artifacts/TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION/plan.md`,
Steps 1-14. **Step 15 (full scoped regression, all green) is NOT satisfied** — see "Blocking
conflict" below. Nine commits, one per step group; the Step 2 guard commit is deliberately
standalone.

### Step 1 — the shared resolve path

`handle_resolve`'s inline load → validate → assemble → dump sequence is now
`src/worldassembly/resolve_io.py`. `resolve_composition(composition, catalog, module_repo)` takes
an **already-validated** `WorldCompositionSpec` and returns `(bundle, rendered_yaml_text)`;
`load_composition_spec` + `resolve_composition_file` are the thin path-loading wrappers the CLI
uses; `write_resolved_artifacts` writes the five sidecars. One renderer, so the CLI, the guard and
the generator cannot drift in serialization. Three now-unused imports (`CatalogRepository`,
`WorldAssemblyResolver`, `WorldCompositionSpec`) were dropped from `cli.py`.

Measured: a fresh resolve of `wilderness_survival` through the new helper is **byte-identical** to
the committed `resolved/world.resolved.yaml`, and writes all five sidecars.

### Step 2 — the AC-6 guard, observed RED on the untouched tree

Landed in its own commit (`2e9bc2fe3`), touching nothing under `data/` and no other test, so the
red state is reproducible from history. Verbatim from that run:

```
E       AssertionError: World composition definitions found outside data/worlds/<world_id>/world.yaml —
        data/worlds/<world_id>/ is the sole authoritative definition of a world_id
        (docs/architecture/world_repository_layout.md §1):
E           data/content/world_compositions/dungeon_crawl.yaml
E           data/content/world_compositions/frontier_extended.yaml
E           data/content/world_compositions/frontier_living_world.yaml
E           data/content/world_compositions/generated/generated_frontier_3_42.yaml
E           data/content/world_compositions/generated/simq_scale_stress_seed42.yaml
E           data/content/world_compositions/highland_traverse.yaml
E           data/content/world_compositions/swamp_border_world.yaml
E           data/content/world_compositions/urban_political.yaml
E           data/content/world_compositions/wilderness_survival.yaml

E       AssertionError: These world_ids already have an authoritative definition under data/worlds/
        and are defined a second time elsewhere:
E           dungeon_crawl redefined at data/content/world_compositions/dungeon_crawl.yaml
E           frontier_extended redefined at data/content/world_compositions/frontier_extended.yaml
E           frontier_living_world redefined at data/content/world_compositions/frontier_living_world.yaml
E           generated_frontier_3_42 redefined at data/content/world_compositions/generated/generated_frontier_3_42.yaml
E           simq_scale_stress_seed42 redefined at data/content/world_compositions/generated/simq_scale_stress_seed42.yaml
E           highland_traverse redefined at data/content/world_compositions/highland_traverse.yaml
E           swamp_border_world redefined at data/content/world_compositions/swamp_border_world.yaml
E           urban_political redefined at data/content/world_compositions/urban_political.yaml
E           wilderness_survival redefined at data/content/world_compositions/wilderness_survival.yaml

2 failed, 1 passed in 9.68s
```

The guard walks only `data/` and `content/` and keys on the **parsed** `schema_version`, never on
the substring — `docs/` holds a dozen prose mentions including the ADR itself.

**Guard 3 was GREEN from the start**, for all 24 composition worlds: every committed
`resolved/world.resolved.yaml` byte-equals a fresh resolve, and a fresh resolve is
byte-deterministic. **No determinism or staleness finding to file, and no snapshot was
regenerated.** The guard is a full fresh-resolve equality, not a fingerprint comparison; no
fingerprint fast path was added, since the full run costs ~10s for the whole corpus.

Guards 1 and 2 stayed red from `2e9bc2fe3` until the Step 12 deletion — the intended state for the
middle of this ticket, noted here so a mid-stream CI run is not misdiagnosed.

### Steps 3-6 — the law stated once

ADR §1 carries the authority sentence plus the rule owner's verbatim source/projection clause, in
the revised *"source definition, whether written by hand or by a generator"* wording. Bible 06
gains **§11**, placed after §10 (itself the chapter's precedent sibling gate) so nothing is
renumbered: one invariant sentence, a citation to the ADR, and an explicit statement that it is
**not** a compile-pipeline gate — no rule id, no severity, nothing aborts on it. It is not in §7's
ladder. `content_authoring.md` was corrected at all four sites (`:27`, `:72`, `:167`, `:292`) and §4
links the ADR; the `make world-validate`/`world-compile` workflow block was left alone because it
already drives `data/worlds/`.

Two docs guards pin this: `test_authoritative_world_location_stated_once` (ADR has the sentence,
Bible 06 does not restate the path and does cite the ADR, no `docs/guides/` file still teaches the
retired directory) and `test_bible_06_does_not_present_the_invariant_as_a_compile_gate` (the
invariant's enclosing section is not §7, carries no `WORLD-*` id and no `ERROR`/`WARNING`/`Level 2`
wording).

### Steps 7-8 — the test surface

Seven named-world sites repointed. Measured assertion deltas applied: `frontier_living_world`
module/fingerprint counts 6 → 7, `urban_political` 3 → 4, `wilderness_survival` 4 unchanged.
`test_real_world_compositions_normalization` had no subject left (every authoritative definition
uses structured `module_refs` with explicit orders), so it became
`test_shorthand_modules_normalization` against a **synthetic** shorthand fixture — option (b);
`WorldCompositionNormalizer` still supports both shapes, so the coverage is kept, not silently
dropped. `test_dungeon_crawl_composition` lost both content-value assertions and its balance
docstring, with a comment naming
`TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION` as the oracle's owner;
the `scalable_bandit_camp` lookup is kept as that ticket's seam. Neither `2` nor `4` is carried
forward. The six out-of-reach tests were not edited.

`test_e2e_smoke.py`'s two helpers collapsed into one (the `generated/` special case disappears —
both generated ids are real `data/worlds/` directories) and its numeric docstring prose was made
non-numeric. `test_assembly.py`'s two real-composition sites repointed; `:1185`/`:1190` left alone.
`test_swamp_border_pack.py` and `test_expansion_gate.py`'s Gates 08 and 11 iterate
`data/worlds/*/world.yaml`.

**Two consequences the plan did not predict, both fixed rather than relaxed:**
`test_real_composition_normalization_preserves_perspectives` needed 6 → 7 **and** its
mixed-shorthand-conflict case now adds the `modules` key explicitly, because the authoritative file
carries only the structured form and the conflict could no longer arise. Gate 08/11 needed a
`schema_version` filter plus a non-zero assertion: iterating all of `data/worlds/` would otherwise
validate non-composition worlds against `WorldCompositionSpec` (all 24 are compositions today, so
this is a correctness guard against the 25th).

### Step 9 — the resolver default, in the mandated order

9.1 landed in its own commit (`fa1be2047`) **before** 9.2 (`4995dac08`). No loader change was
needed; the flat-layout fallback is kept and its stale comment rewritten. 9.2 dropped Campaign's
`compositions_dir=Path("data/worlds")` override, removed the now-dead `from pathlib import Path`,
replaced the dead
`TCK-20260909-WORLD-COMPOSITION-DIRECTORY-CONSOLIDATION` citation, and removed the
"`data/content/world_compositions/` is the anomaly" mis-attribution (which originated in that very
comment, not in the ADR) in favour of pointing at ADR §1 as amended.

`tests/unit/scenarios/test_resolver_defaults.py` asserts the constant and that an unoverridden
resolver loads the authoritative `frontier_living_world`, comparing `len(module_refs)` against the
count **parsed from the file** with a `> 0` guard first — `module_refs` is
`Field(default_factory=list)`, so the comparison is structurally capable of degrading to `0 == 0`.
`test_campaign_orchestrator_uses_resolver_default_not_an_override` asserts at the AST level that no
second hard-coded path replaced the override.

### Step 10 — the content-layer path registration

`ContentPathConfig.world_compositions_dir` **removed, not repointed** — that registry declares only
children of its own `content_root`, and
`test_non_catalog_dirs_constant_matches_path_config` *derives* its expectation from those
basenames. `DEFAULT_WORLDS_ROOT = "data/worlds"` was **introduced** in
`src/worldbuilding/repository.py` (the review's premise that a `WorldRepository` default already
existed was wrong — `__init__` takes a required `worlds_dir`) and is consumed at
`src/content/validator.py`'s two sites only. The 10+ existing literals were deliberately not swept.
`NON_CATALOG_DIRS` dropped `world_compositions` in lockstep, leaving the derivation fully derived
over two fields. The inventory tool's two counters collapsed to one over `data/worlds/*/world.yaml`
with a non-zero assertion; `test_all_categories_present` lost the now-absent
`"World compositions (generated)"` key. `docs/content/pipeline_contract.md`'s table row is retired
with a note on where the worlds root lives.

### Step 11 — Option A, the generator authors the source definition

`GenerationProvenanceSpec` is a frozen, **declared**, **optional** field on `WorldCompositionSpec`
(declared because the model is `extra="forbid"`; optional so all 24 existing definitions stay valid
and `exclude_none=True` leaves every committed snapshot byte-identical — which guard 3
byte-compares). `generation_seed` was not overloaded. The marker is popped in
`WorldCompositionNormalizer` because `NormalizedWorldComposition` is also `extra="forbid"` and
origin history is not a compilation input — the same treatment `pack_refs` already gets.

`generate(..., output_dir=None)` writes `<root>/<world_id>/world.yaml`, refuses to overwrite an
existing definition, and **resolves from the in-memory composition before committing either
write** (option (a), not (b), and not the forbidden (c)). No re-derivation check exists anywhere;
the test class says so explicitly so a later author does not add one.

**Two things the plan did not anticipate, both handled rather than papered over:**

1. `_make_repo` in both `tests/unit/worldgeneration/` files returned a `MagicMock`, which a real
   resolve cannot traverse (`TypeError: Expected dict or list for resources, got MagicMock`). It is
   now an in-memory-populated real `WorldModuleRepository` — no file I/O, and no mock at all. This
   is strictly better than the mock it replaced.
2. `generation_provenance.generated_at` makes the authored YAML no longer byte-identical across
   runs, which contradicted `generator_contract.md`'s determinism clause and
   `test_two_calls_produce_identical_output`. Resolved the way this repo already resolves the
   identical problem for `provenance_manifest.created_at`: the timestamp is legitimate provenance
   outside the artifact's identity, so the determinism test and the contract doc exclude that one
   field. The timestamp was **not** deleted to make a comparison easy.
   `test_no_bounds_no_default_leaves_absent` now observes the same fact through the resolve
   (`AssemblyParameterError` naming the absent param), since leaving a required param absent is
   exactly what makes the composition unassemblable.

### Step 12 — the deletion

`git rm -r data/content/world_compositions/` (7 top-level + 2 under `generated/`), after Step 11
stopped the single writer. `test_catalog_world_compositions_directory_is_absent` and
`test_no_test_contradicts_the_authoritative_danger_scale` added; the latter compares every
`danger_scale ==` literal under `tests/` against whatever
`data/worlds/dungeon_crawl/world.yaml` actually holds, with a not-None guard first, so it is
correct in **either** landing order of this ticket and the balance-fix ticket. All seven guards in
the file are green.

### Step 14 — parity

`SUB-394` added (max live id was `SUB-393`; the legacy `SUBSTRATE-NEW-0NN` series was not
extended), P1, `test_path` = the one-definition guard's node id. Validated through
`parity_ledger_writer.validate_entry()` but appended by hand so the diff is 40 lines rather than a
full-file `safe_dump` rewrite of a 5000-line shard; `tools/parity_index.py build` then reports
**FRESH**. `SUBSTRATE-NEW-010`/`011` updated for the new output location, the provenance marker and
the one run-varying field.

Reviewed and deliberately unchanged: `SUB-390` and `FAC-012` describe mechanisms and already cite
`data/worlds/` paths — neither carries stale wording; `INFRA-256`/`INFRA-257`'s `test_path`s still
resolve.

**`INFRA-373` is a tripwire, and it did not move.** `pytest tests/unit/rendering/test_variants.py`
is 13/13 green, so `TVD(sandbox_world, dungeon_crawl) == 0.23161981243456373` is intact —
independent confirmation that this ticket edited no `data/worlds/` content.

**Reported, NOT fixed:** `SUBSTRATE-NEW-001` and `INFRA-187` are both P0 with `test_path: None`.
That is a pre-existing ledger violation which predates this ticket; it is **not this ticket's
debt** and the Parity phase must not read it as such.

### Recorded decisions

- **The one authority decision (AC-3).** `data/worlds/<id>/world.yaml` is authoritative, on three
  independent grounds: the ADR's unified-root decision; the catalog path never drove a production
  run; and zero catalog-only content exists in 9 of 9 pairs (15 running-only `world_id`s vs 0
  catalog-only).
- **`dungeon_crawl`'s `danger_scale` (AC-5).** The catalog copy held `2`, the running definition
  `4`. This ticket carries **neither** forward: not `2` as authoritative, not `4` as
  confirmed-correct. The value is owned by
  `TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION`.
  `data/worlds/dungeon_crawl/` was not touched.
- **The dual layout in `_load_composition()` is kept** as permanent back-compat — three lines, and
  it is the seam ad-hoc/third-party `compositions_dir` overrides use.
- **`list_worlds()` does not distinguish generated worlds**; the in-YAML marker suffices.

### AC-7 — measurement-validity assessment, with its sweep bound stated

**Method and bound.** `agent-working/stored_artifacts/` was grepped for `world_compositions` (34
files) and for `WorldAssemblyResolver`, then narrowed to the files that cite the catalog **path**
specifically: 34 files across 34 ticket artifact sets. This is a *bounded* sweep, not an exhaustive
re-audit — a path citation in a plan or test_plan is usually a work instruction, not a measurement,
and only measurements can be invalidated. The general case remains unbounded; this is what was
actually re-checked.

- **One confirmed affected artifact:**
  `agent-working/stored_artifacts/TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED/investigation.md`
  compiled via `data/content/world_compositions/frontier_living_world.yaml` — the 6-module copy,
  not the 7-module definition production loads. Its verdicts inherit that ambiguity.
- **First sweep: the five sibling `UNREACHABLE-CLASSIFY-*` artifact sets** (`DEAD-GUARD`,
  `WAVE-CONFIRM`, `ZERO-CALLER`, `PERCEPTION-AUTHORITY`, `ROLLUP`). Measured: **none of the five
  cites the catalog path at all.** `NEVER-SEEDED` is the only one of the six, so the defect did not
  spread across that family.
- **Two conclusions re-checked and recorded as SURVIVING** (not re-litigated):
  - the **demographic-cohort truncation** finding — its decisive probe used
    `load_world_with_context` across 21 worlds, i.e. the production path, so it never read the
    catalog copy. **Survives.**
  - the camp **`STALE-PREMISE`** closure — both modules it turns on are present in *both*
    definitions of `frontier_living_world`. **Survives.**

### Catalog injection — the conflict I reported was real, but my diagnosis was one level too shallow

My first Implement report framed the two failing `test_generated_composition_*` tests as an
overbroad Scope Guard 3 and recommended relaxing the guard. **The coordinator overrode that, and
the evidence proves them right.**
`git show c86fa3a21:src/worldgeneration/generator.py | grep -nE "CatalogRepository\("` returns
**nothing** — no catalog was constructed anywhere in that module before this ticket. The
`CatalogRepository("data/content")` I added at `:565` was therefore a **cwd-dependent hidden
dependency introduced inside a library function** by this very diff. The two tests
`monkeypatch.chdir(tmp_path)` to isolate their output, which is correct behaviour, and they caught
a real design problem. Relaxing the guard would have preserved the smell and spent the guard's
credibility doing it.

Fixed in the production code instead:

- `ProceduralCompositionGenerator.generate()` now takes `catalog_repo: CatalogRepository` as a
  **required** parameter, with **no default** — a default would re-introduce the same cwd
  dependency less visibly. The in-function construction is gone. This restores the module's own
  convention: `WorldProceduralGenerator.__init__` at `:65` already takes an injected
  `catalog_repo`, and the comment at `:148` already calls that class "constructor-injectable with
  ANY CatalogRepository". My `:565` line was the only thing in the module violating it.
- `src/worldbuilding/cli.py`'s `generate` handler passes the catalog it loads through
  `load_content_repositories()`. The CLI is the boundary where resolving content paths against the
  process cwd is legitimate; the library function no longer does it. Two now-unused imports
  dropped.
- The two integration tests changed **minimally**: their `repos` fixture already loads the real
  catalog *before* any chdir and both were discarding it (`_, mod = repos`); they now do
  `cat, mod = repos` and pass it. The `monkeypatch.chdir(tmp_path)` is kept.
- The generator's unit tests gained an explicit `_make_catalog()` (a loaded, empty
  `CatalogRepository` pointed at a nonexistent directory) — explicit rather than cwd-relative, for
  the same reason. All 42 pass.

**Scope Guard 3 was NOT weakened on its own axis.** Its rationale is the ADR's reach over *which
file defines a world*, which still holds: the other four named tests (`:171`, `:188`, `:205`,
`:224`) are byte-unchanged. These two changed because Step 11 legitimately changes `generate()`'s
**signature** — Step 11's own surface, not the ADR's.

### A real generator defect the injection surfaced — routed, filed, and xfail-marked

With the real catalog injected, the same two tests failed for a different and deeper reason:

```
ValueError: Duplicate region ID collision 'hometown' detected during assembly merge.
src/worldassembly/resolver.py:359
```

Measured, not inferred:

- `frontier_village_core.yaml:9` and `trading_company_hub.yaml:19` **both declare region id
  `hometown`** (line numbers independently confirmed by the coordinator before filing).
- Today's `ModuleScorer` ranks them **1 and 2** for this intent (`generated_frontier_3_42`, seed
  42, `settlement_style="frontier"`), so the generator selects both.
- The generator emits every `ModuleRefSpec` with `namespace=None` and never sets one; its Rule 5
  fail-fast guards duplicate **`provides`** strings only, not duplicate region ids.
- `data/worlds/urban_political/world.yaml:16` composes the same pair and resolves it with
  `namespace: "trading"` — as `test_urban_political_composition`'s docstring states.
- The **committed** `data/worlds/generated_frontier_3_42/world.yaml`, authored by the generator
  before this ticket, contains `frontier_village_core` but **not** `trading_company_hub`. The
  module corpus and/or scorer has moved since, so today's selection picks a colliding pair.

**Pre-existing latent defect, surfaced not caused.** The selection code is byte-unchanged by this
diff: `git diff c86fa3a21 HEAD -- src/worldgeneration/generator.py` shows no change to
`ModuleScorer` use, the ranking, `selected_ids`, `BUDGET` or Rule 5 — the only matching diff lines
are docstring text. It was invisible because nothing ever resolved what the generator authored;
Step 11 item 4 made it visible, which is exactly what that item exists for.

**Filed and owned elsewhere:** `TCK-20261004-GENERATOR-AUTHORS-UNASSEMBLABLE-COMPOSITION-ON-REGION-ID-COLLISION` (P1,
standard, committed at `a8910130c`). Fixing it here would mean deciding world semantics — which
world a given intent generates, and under the auto-namespacing option region identity itself —
without the rule owner.

**Resolved in this ticket by marking, not fixing (coordinator decision).** Both
`test_generated_composition_is_valid_worldcompositionspec` and
`test_generated_composition_determinism` carry
`@pytest.mark.xfail(strict=True, reason=...)` naming that ticket and the one-line cause. The marks
are the whole change: no assertion inside either test was touched, and the other four
Scope-Guard-3 tests are byte-unchanged. `strict=True` is mandatory — if the defect is fixed and
these start passing, the xfail itself fails, so the marks cannot outlive the ticket. **AC-3 of
TCK-20261004-GENERATOR-AUTHORS-UNASSEMBLABLE-COMPOSITION-ON-REGION-ID-COLLISION requires these marks to be
removed when the defect is fixed.**

Verified: both report **xfailed**, not xpassed, so the defect is deterministic rather than
intermittent — which the new ticket's Assumptions depend on.

### Pre-existing failures, verified not caused by this ticket

- **11 failures in `tests/unit/worldassembly/test_corpus_diversity.py` and
  `test_hero_guild_routing_population_stability.py`**, measured twice in the foreground
  (`11 failed, 83 passed` in 1338s, then again in 1321s on the final tree). The two runs' `FAILED`
  lines are **byte-identical after sorting** — the same 11 tests, not merely the same count, so
  this is a stable set rather than flake. Evidence they predate this diff, rather than an assertion:
  (i) `git diff --stat c86fa3a21 HEAD -- <both test files> data/worlds/` is **empty** — the tests
  and every world definition and snapshot they read are byte-identical to the commit before this
  ticket; (ii) an import-closure probe loading both test modules pulls in **230** modules and
  **none** of this ticket's ten changed `src/` modules; (iii) of the four changed modules that
  pytest's `conftest.py` could additionally pull in, the exact diffs are inert for a world loaded
  from `data/worlds/` — `paths.py` only removes an unread field, `repository.py` only shrinks
  `NON_CATALOG_DIRS` (strict-mode ignored-file reporting), `worldbuilding/repository.py` only adds
  a module-level constant, and `worldassembly/schema.py` adds a new model plus an **optional**
  field that is `None` on every existing definition, making its normalizer `pop` a no-op.
  *(Caveat, stated rather than hidden: the conftest-inclusive variant of the closure probe failed
  to import under a bare interpreter, so (ii) is the closure without `conftest.py` and (iii) is the
  diff-level argument that covers the remainder. I did not re-run these two files at `c86fa3a21`
  — that is a 22-minute run whose outcome (i)-(iii) already determine.)* Their own module docstring
  independently documents 13 failures + 1 error as accepted fallout from
  `TCK-20260824-TOWN-CENTER-POINTER-FIX`, 10 of 13 deliberately left unfixed.
- **`tests/integration/content/test_swamp_border_pack.py::test_base_strict_matrix_unaffected_by_pack_content`**
  errors only when run in the same process as those failing stability tests; the content suite is
  109/109 green on its own.
- **`tests/integration/scenarios/test_entity_differentiation.py::test_bravery_quartile_combat_rate_2x`**
  — builds its own spec and never constructs a `ScenarioSetupResolver`.
- **`tests/integration/campaigns/test_catalog_entity_spawn_wiring.py::test_real_campaign_episode_event_stream_is_plausible_not_degenerate`**
  — reproduced identically (`combat_initiated 0 >= 3`) with `orchestrator.py` and `resolver.py`
  checked out at `c86fa3a21`, i.e. before any of this ticket's commits.

## Test Summary

New: `tests/architecture/test_world_definition_single_source.py` (7 guards),
`tests/unit/scenarios/test_resolver_defaults.py`,
`test_campaign_orchestrator_uses_resolver_default_not_an_override`,
`test_default_worlds_root_is_the_authoritative_world_location`, and a five-test
`TestAuthoritativeOutputLocation` class in
`tests/unit/worldgeneration/test_composition_generator.py` (explicit-absence, resolved sibling,
provenance history, refuse-to-overwrite, resolve-failure cleanup). Deliberately **absent**: any
`world.yaml == generate(marker)` test.

| command | result |
|---|---|
| `pytest tests/architecture/test_world_definition_single_source.py -q` | **7 passed** (guards 1-2 red before Step 12, by design) |
| `pytest tests/integration/worldassembly/ tests/unit/worldassembly/ -q -rxX` (minus the 2 stability families) | **133 passed, 2 xfailed** |
| `pytest tests/unit/content/ tests/integration/content/ tests/tools/test_content_inventory.py tests/unit/worldgeneration/ tests/unit/worldbuilding/ tests/unit/scenarios/ tests/unit/domains/campaigns/test_campaign_orchestrator.py tests/architecture/test_world_definition_single_source.py tests/unit/rendering/test_variants.py -q` | **727 passed** |
| `pytest tests/integration/scenarios/ -q` | 172 passed, 2 skipped, 1 xfailed, **1 pre-existing failure** |
| `pytest tests/integration/campaigns/ -q` | 21 passed, **1 pre-existing failure** (reproduced at `c86fa3a21`) |
| `pytest tests/unit/worldassembly/test_corpus_diversity.py tests/unit/worldassembly/test_hero_guild_routing_population_stability.py -q` | **11 failed, 83 passed** in 1321s — pre-existing, evidence below |
| `tools/parity_index.py check-staleness` | FRESH |

Every command above was run in the **foreground** on the final tree.

**Caused by this diff: zero failures.** The two tests this ticket's own work affects report
**xfailed**, not failed and not xpassed — so the defect they track is deterministic rather than
intermittent, which is what `TCK-20261004-GENERATOR-AUTHORS-UNASSEMBLABLE-COMPOSITION-ON-REGION-ID-COLLISION`'s
Assumptions depend on. The remaining 13 failures are the pre-existing set enumerated below.

**All tests pass except two xfail-marked cases tracking a filed P1 defect**
(TCK-20261004-GENERATOR-AUTHORS-UNASSEMBLABLE-COMPOSITION-ON-REGION-ID-COLLISION), plus the
enumerated pre-existing set. The suite is NOT described as clean: those two marks encode a real
defect that is now visible rather than silent. The "Full scoped regression" AC remains unchecked
for that reason.

## Files Changed

**Source (11)**
- `src/worldassembly/resolve_io.py` *(new)* — the single resolve/render/write path
- `src/worldassembly/schema.py` — `GenerationProvenanceSpec`, optional `generation_provenance`, normalizer pops
- `src/worldbuilding/cli.py` — `handle_resolve` calls the helper; three dead imports removed
- `src/worldbuilding/repository.py` — `DEFAULT_WORLDS_ROOT`
- `src/worldgeneration/generator.py` — authors `data/worlds/<id>/world.yaml` + `resolved/`, provenance marker, refuse-to-overwrite, resolve-before-commit
- `src/scenarios/resolver.py` — default `compositions_dir` → `data/worlds`
- `src/domains/campaigns/orchestrator.py` — override dropped, dead citation and mis-attribution removed
- `src/content/paths.py` — `world_compositions_dir` removed
- `src/content/validator.py` — consumes `DEFAULT_WORLDS_ROOT`
- `src/content/repository.py` — `NON_CATALOG_DIRS`
- `tools/generate_content_inventory.py` — two counters collapse to one

**Tests (13)**
- `tests/architecture/test_world_definition_single_source.py` *(new)*
- `tests/unit/scenarios/test_resolver_defaults.py` *(new)*
- `tests/integration/worldassembly/test_real_content_world_compositions.py`
- `tests/integration/worldassembly/test_e2e_smoke.py`
- `tests/unit/worldassembly/test_assembly.py`
- `tests/integration/content/test_swamp_border_pack.py`
- `tests/integration/content/test_expansion_gate.py`
- `tests/unit/content/test_content_paths.py`
- `tests/tools/test_content_inventory.py`
- `tests/unit/domains/campaigns/test_campaign_orchestrator.py`
- `tests/unit/worldbuilding/test_world_repository.py`
- `tests/unit/worldgeneration/test_composition_generator.py`
- `tests/unit/worldgeneration/test_seed_params.py`

**Docs (9)**
- `docs/architecture/world_repository_layout.md` — §1, the two normative sentences
- `docs/mechanics/06_worldbuilding_foundation.md` — new §11 sibling law
- `docs/guides/content_authoring.md` — four sites
- `docs/content/pipeline_contract.md` — path-layout table row retired
- `docs/world/generator_contract.md` — output contract, three constraints, determinism clause
- `docs/parity_ledger/substrate.yaml` — `SUB-394` added; `SUBSTRATE-NEW-010`/`011` refreshed
- `docs/parity_ledger/infrastructure.yaml` — `INFRA-184` updated: world definitions are no longer
  addressed as content at all (`ContentPathConfig.world_compositions_dir` retired, the
  `world_compositions` member removed from `CatalogRepository.NON_CATALOG_DIRS` because its
  strict-mode ignore-exemption became dead config once the directory was gone, and
  `load_all_compositions` now defaults to `DEFAULT_WORLDS_ROOT`). Gains two `v2_evidence` lines and a
  second `test_path` on
  `tests/architecture/test_world_definition_single_source.py::test_catalog_world_compositions_directory_is_absent`;
  points at `SUB-394` as the owner of the law itself so the law is not restated in two shards.
  *(Added 2026-10-04 after the Verify gate caught its omission — the Parity phase's edit landed after
  the earlier `docs_to_update_coverage` measurement, so that measurement was stale, not wrong.)*
- `docs/world/compiler_contract.md` — the `generate` subcommand's stated output location
  (`status: authoritative`; the investigation's "no claim about the directory's location" judgment
  did not hold for this one line, found during the doc-verification sweep)
- `docs/world/raid_boss_camp_contract.md` — the `frontier_living_world` module-ref evidence
  citation repointed to the surviving file, same two modules, new line numbers

**Data (9 deleted)**
- `data/content/world_compositions/` — 7 top-level + 2 under `generated/`

**Ticket and staging artifacts (4)**
- `agent-working/tickets/inprogress/TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION.md`
- `agent-working/staging_artifacts/TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION/investigation.md`
- `agent-working/staging_artifacts/TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION/plan.md`
- `agent-working/staging_artifacts/TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION/test_plan.md`

Not touched, on purpose: `data/worlds/` (including `dungeon_crawl/` and every `resolved/`
snapshot), the six out-of-reach tests in `test_real_content_world_compositions.py`, the
flat-layout fallback in `_load_composition()`, the 10+ existing `"data/worlds"` literals,
`docs/mechanics/content_usage_matrix.md` (generated), `docs/archive|audits|brainstorm/`.

## Completion Summary

`data/worlds/<world_id>/` is now the sole authoritative definition of a `world_id`, stated once in
`docs/architecture/world_repository_layout.md` §1 with the rule owner's verbatim source/projection
clause, cited (not restated) by Bible 06's new §11 and by `content_authoring.md`. Seven
architecture guards enforce both halves — one definition per `world_id`, and every committed
`resolved/world.resolved.yaml` byte-equal to a fresh resolve across all 24 composition worlds. The
one-definition guards were observed RED on the untouched tree in their own commit, naming all 9
catalog duplicates, which is AC-6's mandatory negative control; the projection guard was green from
the start, so no determinism finding was filed and no snapshot was regenerated.
`data/content/world_compositions/` is deleted, after every reader was repointed, the resolver
default was flipped ahead of the Campaign override being dropped, the `data/content`-relative path
field was retired in favour of a `DEFAULT_WORLDS_ROOT` owned by the worldbuilding layer, and the
generator was changed to author `data/worlds/<id>/world.yaml` directly with a history-only
provenance marker, refusing to overwrite and resolving before committing either write.
`SUB-394` records the law with the guard as its `test_path`.

**Not complete, and deliberately so.** All tests pass except two xfail-marked cases tracking a
filed P1 defect — `TCK-20261004-GENERATOR-AUTHORS-UNASSEMBLABLE-COMPOSITION-ON-REGION-ID-COLLISION`
(committed `a8910130c`) — so the "Full scoped regression" AC stays unchecked. The first cause I
reported, a cwd-dependent `CatalogRepository` I had added inside `generate()`, is **fixed** by
injecting the catalog as a required parameter with no default; my own earlier recommendation to
relax Scope Guard 3 instead was wrong, and that guard was not weakened. What remains is a genuine
pre-existing generator defect the fix made visible: today's `ModuleScorer` ranks
`frontier_village_core` and `trading_company_hub` first and second, both declare region id
`hometown`, and the generator never sets a `namespace`, so it authors a composition that cannot
assemble. Both affected tests are `xfail(strict=True)` against that ticket, whose AC-3 requires the
marks removed when the defect is fixed. AC-5's oracle stays `unresolved` for this ticket, which is
correct rather than a gap.
