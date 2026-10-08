---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261008-RESOURCE-REGROWTH-IS-COMPUTED-BUT-NEVER-MERGED-INTO-THE-WORLD-DYNAMICS-UPDATE
phase: done
date: 2026-10-08
tags: [ecology, economy, resource]
---

# TCK-20261008-RESOURCE-REGROWTH-IS-COMPUTED-BUT-NEVER-MERGED-INTO-THE-WORLD-DYNAMICS-UPDATE

## Title
The resource regeneration the Resource Ecology Service computes is dropped by the world-dynamics merge, so no resource node ever regrows (Bible 03 section 3.1, TOWN-137).

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found while measuring the forage path for decision 27 (rpg-planner ruling B, 2026-10-08, PR 1 of a stack). `ResourceEcologyService.process_ecology` returns `node_updates` (the regen) and `world_events_add` (`RESOURCE_RECOVERED`), but `WorldDynamicsSystem.resolve_dynamics` folded in only `nodes_add` and `next_node_id_set`. In 1000 ticks no node of any kind (wood, herb, berry) gained a charge. Bible 03 section 3.1 says regen runs every `ECOLOGY_INTERVAL` (200 ticks) and emits `RESOURCE_RECOVERED`; TOWN-137 was marked verified against the service-level test only.

## Scope
1. `src/engine/world_dynamics.py`: merge the whole `ecology_update` into the update (`update = update.merge(ecology_update)`), replacing the two hand-picked fields. Net one line shorter.
2. A wiring test through the real tick path (`tests/unit/world/test_resource_regrowth_wiring.py`): the refined update carries the regen and the `RESOURCE_RECOVERED` event; a real `Kernel` run regrows a depleted node over the ecology interval; no regen off the interval, for a static node, or during a cooldown.
3. TOWN-137 re-pointed at the world-level test.
4. The all-gatherer effect, pinned, reported (not tuned).

## Out of Scope
- Node supply sizing, forage content, and the held-INTERACT defect (their own tickets and PRs).
- Any change to the ecology constants, density modifier or seeding.

## Acceptance Criteria
- [x] A depleted regen node gains charges over an ecology interval through the real tick path; `RESOURCE_RECOVERED` fires once per recovery (3 of the 4 new tests fail without the fix; all pass with it).
- [x] No existing test expectation moves: 3642 passed in the scoped run (world, resource, engine, systems, core, tools, strategic, worldassembly, worldbuilding, integration; not slow).
- [x] The pinned all-gatherer effect is reported (investigation.md): regrown charges 0 to 11.8 / 13.2 / 13.2 per run, outcomes within about 1 SD, 15 of 15 digests identical across two runs.
- [x] TOWN-137 `v2_evidence` and `test_path` point at the end-to-end test and the note says it was service-level only before.

## Related Tickets
- `TCK-20261007-A-NEED-WITH-NO-OPEN-WAY-PULLS-TOWARD-THE-STEP-THAT-OPENS-ONE-SURV-07-AMENDMENT` and `TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL` (stacked on this).

## Related Docs
- `docs/mechanics/03_economic_laws.md` section 3.1; `docs/parity_ledger/town_resource.yaml` TOWN-137.

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261008-RESOURCE-REGROWTH-IS-COMPUTED-BUT-NEVER-MERGED-INTO-THE-WORLD-DYNAMICS-UPDATE/` (plan, investigation, test plan, probes).

## Related Code Areas
- `src/engine/world_dynamics.py`, `src/world/ecology.py`.

## Assumptions / Open Questions
- The code was behind the Bible, so this is a parity repair, not a design change: no divergence entry (rpg-planner ruling).
- Regrowth moves the economy baseline for every world: harvested charges rise about 50 percent. That is expected and correct.

## Implementation Notes
`StateUpdate.merge` takes `nodes_add` by extension and `next_node_id_set` from the other update when set, the same result as the two lines it replaces, and also carries `node_updates` and `world_events_add`.

## Test Summary
New: 4 tests. Scoped run: 3642 passed, 10 skipped. CI is the first real run of ruff, mypy and the code-health gates.

## Files Changed
`src/engine/world_dynamics.py`, `tests/unit/world/test_resource_regrowth_wiring.py`, `docs/parity_ledger/town_resource.yaml`, this ticket and its stored artifacts, `docs/REGISTRY.yaml`.

## Completion Summary
Resource regrowth now reaches the world: a depleted node gains its charges at each ecology interval and `RESOURCE_RECOVERED` fires, through the real tick path. One line shorter in `resolve_dynamics`; 4 new tests (3 fail without the fix); 3642 existing tests pass with no expectation moved; the all-gatherer effect is pinned and within about 1 SD (charges harvested up about 50 percent). TOWN-137 re-pointed at the world-level test. CI is the first real run of the full gate set; the local ratchet reported 0 new, 0 worse and import-linter 17 kept, 0 broken.
