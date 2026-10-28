---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261005-WORLD-ASSEMBLY-LATENT-AND-DEAD-PATHS
phase: done
date: 2026-10-05
tags: [world, investigation]
---

# TCK-20261005-WORLD-ASSEMBLY-LATENT-AND-DEAD-PATHS

## Title
Five latent world-assembly paths that no corpus world exercises today — a duplicated module ref that
collapses, an ignored `requires`, an overridden `order`, a false "not found" on `enabled: false`, and
a dead legacy generator

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P3

## Request Summary
The latent half of a read-only world-assembly survey by `world-rule-catalog-design`, routed to
`rpg-planner` for filing. The survey's own triage called these **latent** — reachable in principle,
not exercised by any corpus content today — in contrast to the four it flagged as hard-bug
candidates, which are in `TCK-20261005-WORLD-COMPOSITION-SILENT-DROP-AND-OVERWRITE-CORPUS-PROBE`.

They are grouped in one ticket deliberately: each is small, none changes world truth today, and
splitting five P3s into five tickets costs more in ticket overhead than the defects cost in risk.
**If any one turns out to fire on corpus content, it leaves this ticket and gets its own**, at
whatever priority the measurement supports.

**(d) A module listed twice in `module_refs` collapses to the last ref** (`resolver.py:300-301`). The
stated intent at `:813-815` is that one module can be composed twice under two namespaces. That
cannot work as written. This is the sharpest of the five: it is not a missing guard but a documented
capability that does not function.

**(e) A dangling `requires` is silently ignored** in both the topological sort
(`worldmodules/utils.py:18`) and the generator (`generator.py:513-515`). Separately, the `order`
field is overridden by an alphabetical sort (`utils.py:26`, `:39`) — so a module author setting
`order` gets alphabetical ordering and no warning.

**(g) `ASM-COMP-001` (`resolver.py:131-138`) loops over all `module_refs` while `graph_map` holds
only enabled ones**, so a ref with `enabled: false` would raise a false "module not found". Latent
because no world uses `enabled: false`.

**(i) Dead code: `WorldProceduralGenerator` (`generator.py:59-370`)** has no production caller.

Sites are at `405cbd77b`. **Re-derive every line number**; `src/worldbuilding/` is under active change
by Lane B.

## Scope
1. For each of (d), (e), (g), confirm the reading at the current commit and confirm it is still
   unexercised — grep the 24 compositions for a duplicated `module_refs` entry, a dangling `requires`,
   an authored `order`, and `enabled: false`. **Record the per-check count.** A non-zero count moves
   that item out of this ticket.
2. Fix (d) or document it as unsupported. **Do not assume "fix" is the answer** — "compose one module
   twice under two namespaces" may be a capability nobody wants, in which case the honest change is to
   remove the claim at `:813-815` and raise on a duplicate ref. Decide against whether any content
   wants it, and record which way and why.
3. For (e)'s `order` override: either honour `order` or delete the field. A schema field that is
   silently ignored is worse than its absence.
4. For (g): fix the loop to iterate the same set `graph_map` holds. Small and unambiguous.
5. For (i): delete `WorldProceduralGenerator` only after confirming no caller, including the CLI, the
   lab, tests, and any `getattr`/string-dispatch reference that a plain grep for the class name
   misses. If anything references it, say so and leave it.
6. Add a regression test per item fixed. (g) and (e)'s `order` are each one test.

## Out of Scope
- The four hard-bug candidates — `TCK-20261005-WORLD-COMPOSITION-SILENT-DROP-AND-OVERWRITE-CORPUS-PROBE`.
- Region bounds overlap — `TCK-20261005-REGION-OVERLAP-VALIDATION-FLAG-HAS-NO-READER`.
- Region-id namespacing and the assembly contract doc — #335 and
  `TCK-20261005-ASSEMBLY-CONTRACT-OMITS-REGION-ID-COLLISION-RULE`.
- Any behaviour change to a corpus world. If a fix here changes a resolved world, stop: that means the
  path was not latent and the premise of this ticket is wrong.

## Acceptance Criteria
- [x] Scope 1's per-check counts over all 24 compositions are recorded, including zeros, with the
      commit stated.
- [x] (d) is either functional with a test, or documented as unsupported with the `:813-815` claim
      removed and a raise on a duplicate ref — and the choice is justified against whether any content
      wants it.
- [ ] (e)'s `order` field is honoured or removed. Not left silently overridden. (not met: non-latent by the ticket's rule; documented, not honoured or removed, and split into TCK-20261027-WORLD-COMPOSITION-AUTHORED-FIELDS-SILENTLY-IGNORED by rpg-planner's ruling)
- [x] (g) iterates one consistent set, with a test using `enabled: false`.
- [x] (i) is deleted with the no-caller sweep recorded, or kept with the caller named. (kept, with the caller named: tests/unit/worldgeneration/test_generator.py)
- [x] No resolved corpus world changes. `test_resolved_snapshot_freshness` (24 worlds re-resolve
      byte-identically) stays green — it is the direct guard for this ticket's latency premise.
- [ ] Determinism sweep green; any moved hash explained, not regenerated. (the paired --neutral run is run once for the whole batch and recorded in the PR; not run for this ticket alone)

## Related Tickets
- `TCK-20261005-WORLD-COMPOSITION-SILENT-DROP-AND-OVERWRITE-CORPUS-PROBE` — the measured half of the
  same survey.
- `TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION` (#335) — region namespacing; (d) concerns
  the same namespace mechanism from the module-ref side.
- `TCK-20260915-WORLDBUILDING-DANGLING-REGION-REFERENCE-SILENT-FALLTHROUGH` (done 2026-10-05) — added
  `_assert_region_references_resolve`; the same silent-skip family, already fixed, and a model for how
  (e)'s dangling `requires` could be handled.

## Related Docs
- `docs/world/assembly_contract.md`, `docs/world/compiler_contract.md`
- `docs/mechanics/06_worldbuilding_foundation.md` — declarative topology and integrity validation
- `docs/architecture/world_repository_layout.md`

## Related Stored Artifacts
_(none)_

## Related Code Areas
- `src/worldbuilding/resolver.py:300-301` (d), `:813-815` (the claim), `:131-138` (g)
- `src/worldmodules/utils.py:18`, `:26`, `:39` (e)
- `src/worldgeneration/generator.py:513-515` (e), `:59-370` (i)

## Assumptions / Open Questions
- The survey re-read (d) directly; (e), (g) and (i) were not starred, so they are a single reading and
  should be confirmed before acting.
- (i) sits in `src/worldgeneration/`, which `world-rule-catalog-design`'s registry split records as an
  authoring tool reached only through the CLI. If the legacy generator is reachable from the CLI after
  all, (i) is not dead and the registry entry for `procedural_world_generation` needs a look too.
- Nothing here is urgent. If it conflicts with a higher-priority Lane B ticket for the same files,
  it yields.

## Implementation Notes
Scope step (origin/main 3b5fab1e9, all 24 `data/worlds` compositions; rows in the stored `latent_paths_results.jsonl`): (d) duplicate `module_refs` 0; (g) `enabled: false` 0; (e) dangling `requires` absent from the repository 0, but 2 composed-away requires in `wilderness_survival` (`wolf_den_near_forest` and `undead_battlefield` both require `frontier_village_core`, which that world does not compose); `order` set explicitly on 72 refs in 11 worlds (61 non-zero), authored sequence differs from the merge sequence in 14 of 24 worlds, and an experiment that lets the authored order win topological ties changes the resolved world in those same 14. Sites: the resolver is `src/worldassembly/resolver.py`, not `src/worldbuilding/`.

Rulings and relay chain. The rulings below are rpg-planner's (u24), relayed rpg-planner (u24) -> lead-planner-u24 -> lead-planner -> rpg-planner-ubuntu on 2026-10-27, checked at 3b5fab1e9; they are not owner approvals.
- (g): fixed. `missing_module_issues` (in `src/worldassembly/schema.py`) checks the enabled refs `graph_map` holds, so a disabled ref to a real module is no longer reported as ASM-COMP-001. Test: `tests/integration/worldassembly/test_module_refs_enabled_and_unique.py`.
- (d): option (a) approved. `require_one_ref_per_module` raises a `ValueError` at the start of `assemble()`, before any merge, naming the world, the module id and both refs. The "composed multiple times" claim in the place-id comment is removed. No other doc or Bible 06 text made the multi-composition claim; `docs/world/assembly_contract.md` now states the one-ref rule. Test: same file. Hash neutrality: all 24 worlds resolved before and after the change give identical `world.resolved.yaml` text (`resolved_world_hashes_before_after.jsonl`); the paired --neutral proof is run once for the batch.
- `order` and the dangling `requires`: leave this ticket by its own rule (non-latent). Option (a) for `order`: documented only, in the `ModuleRefSpec.order` description and in `docs/world/assembly_contract.md`; no code path and no world changed. Dangling `requires`: option (c), code untouched, the finding recorded. One follow-up ticket covers both: `TCK-20261027-WORLD-COMPOSITION-AUTHORED-FIELDS-SILENTLY-IGNORED` (filed by rpg-planner-ubuntu, carried in this PR, not dispatched).
- (i): option (b) approved, `WorldProceduralGenerator` kept: it is constructed by `tests/unit/worldgeneration/test_generator.py` and preserved per `docs/world/generator_contract.md` (WORLD-GEN-003/004, SUBSTRATE-NEW-002). The one approved `registries/mechanisms.yaml` edit replaces the "Dead code inside" sentence in the `procedural_world_generation` entry (rpg-planner-ubuntu's message said `world_assembly`; the sentence is under `procedural_world_generation`, which I edited). Not edited, and now stale: the `world_composition_assembly` note still says a module listed twice collapses to the last ref and lists the ASM-COMP-001 enabled:false reading as an unconfirmed candidate; both are now fixed in code (rpg-planner's content, for its next pass).

### 2026-10-05 — three more dead or latent paths routed in by `rpg-implementer-2` (evidence only; not yet in Scope; the planner approved editing this ticket)

Found while closing `TCK-20261005-WORLD-COMPOSITION-SILENT-DROP-AND-OVERWRITE-CORPUS-PROBE` and auditing `TCK-20261005-REGION-OVERLAP-VALIDATION-FLAG-HAS-NO-READER`. Sites at `94f7a3fe3`.
Per this ticket's own rule, any one of them that fires on corpus content leaves for its own ticket; none does today.
- **(j) The faction first-wins merge is structurally unreachable** (`src/worldassembly/resolver.py:381-390`). `:322-326` pre-seeds `factions` with every catalog faction; each module's faction
  contribution is built from the same catalog (`:833-838`, `FactionSpec(id, type=alignment_bucket)`); a module naming a faction outside the catalog raises `ResolverError` (`:836`). So
  `if fac.id not in factions` is never true for a valid composition, a "differing definition" cannot exist, and the provenance records that branch would write never appear. Measured over the 24
  corpus worlds: 147 module faction contributions, 0 not pre-seeded, 0 differing, 0 faction provenance records with a `source_module`
  (`agent-working/stored_artifacts/TCK-20261005-WORLD-COMPOSITION-SILENT-DROP-AND-OVERWRITE-CORPUS-PROBE/corpus_probe_results.jsonl`; `tests/tools/test_world_composition_corpus_probe.py` pins the `ResolverError`).
  Dead code, not a defect; options are to delete the branch or to keep it as a guard for a future module-defined faction, which is a design choice.
- **(k) `RegionService.find_region_at`** (`src/world/regions.py:16`): closed bounds, first match in `state.regions` order, then a **nearest-region-centre fallback** that never returns `None`. Zero production callers.
  It is a third position-to-region membership convention alongside the live lookup and `DomainView.get_region_for_position`; leaving it risks someone wiring it up and reintroducing a different answer for points outside every region.
- **(l) `RegionalSovereigntyService`** (`src/world/regional_sovereignty.py:24` `process_taxation`, `:78` `apply_sovereignty_debuffs`): calls `.id` directly on `LegalityServiceV2.get_region_for_position(...)` at `:46` and `:67`, which returns `None`
  for a point outside every region (AttributeError). Nothing outside the file references the class, so it is latent.

## Test Summary
- `tests/integration/worldassembly/test_module_refs_enabled_and_unique.py`: 3 passed (disabled ref to a real module raises nothing and adds nothing; an enabled ref to an unknown module is still refused; a duplicate module id is refused naming the world, the id and both refs).
- `tests/integration/worldassembly` 111 passed; with `tests/unit/worldassembly` and `tests/unit/worldmodules` 341 passed before the (d) change.
- 24 resolved worlds identical before and after the (d) change (sha256 of each `world.resolved.yaml` text).
- `make code-health`: 0 new, 0 worse. `make lint-imports`: 17 kept. Registry views regenerated; `mechanism-registry-validate` and `-html-check` pass.

## Files Changed
- `src/worldassembly/resolver.py`, `src/worldassembly/schema.py` (the `order` description and the two ref checks)
- `tests/integration/worldassembly/test_module_refs_enabled_and_unique.py` (new)
- `docs/world/assembly_contract.md`, `registries/mechanisms.yaml` (one sentence), `docs/brainstorm/mechanism_verification_view.md` (regenerated)
- `agent-working/tickets/todos/TCK-20261027-WORLD-COMPOSITION-AUTHORED-FIELDS-SILENTLY-IGNORED.md` (carried in, not dispatched)

## Completion Summary
A disabled module ref no longer raises a false "module not found", and a module listed twice in `module_refs` is refused before any merge instead of silently collapsing to the last ref. The `order` field is documented as not deciding the merge sequence, and the non-latent `order` and dangling-`requires` findings are split into their own follow-up ticket. `WorldProceduralGenerator` is kept on purpose and the registry note says so. No resolved corpus world changed.
