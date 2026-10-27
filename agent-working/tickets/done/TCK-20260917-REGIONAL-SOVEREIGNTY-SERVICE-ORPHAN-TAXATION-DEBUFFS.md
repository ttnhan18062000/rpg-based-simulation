---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260917-REGIONAL-SOVEREIGNTY-SERVICE-ORPHAN-TAXATION-DEBUFFS
phase: done
date: 2026-09-17
tags: [world, architecture]
---

# TCK-20260917-REGIONAL-SOVEREIGNTY-SERVICE-ORPHAN-TAXATION-DEBUFFS

## Title
`RegionalSovereigntyService` (regional taxation + macroscopic conquest debuffs) has zero real
callers anywhere in `src/` — real, non-dead code, never invoked

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found as a side effect of `TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY`'s own
`regional_sovereignty` split. While binding that mechanism's `implemented_by`, the first, name-matched
candidate — `src/world/regional_sovereignty.py::RegionalSovereigntyService` — was checked for real
callers before trusting the binding (per this arc's own standing discipline), and found to have
**zero real callers anywhere in `src/`**.

`RegionalSovereigntyService` is real, correctly-written, non-dead code:

```python
class RegionalSovereigntyService:
    """Manages regional taxation and macroscopic sovereignty effects (Debuffs)."""
    TAX_INTERVAL = 100
    TAX_RATE_ENTITY = 2.0
    TAX_RATE_BUILDING = 10.0
    CONQUERED_ATK_DEF_MOD = 0.8
    CONQUERED_SPD_MOD = 0.9

    @staticmethod
    def process_taxation(state: AuthoritativeState) -> StateUpdate: ...
```

It implements two real capabilities per its own docstring: periodic taxation of entities/buildings
in owned regions, and combat-stat debuffs (`ATK`/`DEF`/`SPD` multipliers) for conquered regions.
Neither is invoked from anywhere in the live pipeline — no `run_phase(...)` registration, no direct
call from any engine module. This is distinct from the *actually-live* sovereignty mechanism
(`FactionInfluenceService`, `src/world/influence.py`, 3 real callers), which handles ownership
tracking and conquest/liberation threshold-crossing but does not implement taxation or combat
debuffs at all — so this is not a duplicate of already-working functionality, it is a real, separate
capability that was apparently built and never wired in.

`regional_sovereignty`'s own `implemented_by` binding in `registries/mechanisms.yaml` was corrected
to cite `FactionInfluenceService` (the real, live implementation) rather than
`RegionalSovereigntyService` — this ticket exists so `RegionalSovereigntyService`'s own orphan
status doesn't stay recorded only in that correction's prose.

## Scope
1. Confirm directly whether `RegionalSovereigntyService.process_taxation()` (or any other method
   on the class) is invoked anywhere in the real tick pipeline, a test, or a CLI tool — the
   `implemented_by` check found zero callers via a repo-wide grep, but confirm with a direct
   pipeline trace before concluding it's fully dead, per this arc's own "verify the negative"
   discipline.
2. If genuinely never invoked: determine whether wiring it in is warranted (a real design decision,
   not assumed here) — taxation and conquest debuffs are plausible, coherent mechanics that may
   simply have been left unfinished, not necessarily wrong to add.
3. If wiring it in is out of scope for this ticket, record the orphan finding in the registry (a
   new mechanism entry, or a corrected state on an existing one, per whatever the caller-trace in
   scope item 1 concludes) so it's visible rather than only living in `regional_sovereignty`'s own
   `implemented_by`-correction prose.

## Out of Scope
- Wiring `RegionalSovereigntyService` into the live pipeline as a fix, unless scope item 2's own
  investigation concludes that's the right call and it's scoped as its own follow-up if
  substantial.
- Re-litigating `regional_sovereignty`'s own corrected `implemented_by` binding
  (`FactionInfluenceService`) — already resolved by the identity-rules ticket, not reopened here.

## Acceptance Criteria
1. Whether `RegionalSovereigntyService` is genuinely dead (zero real callers, confirmed via a
   direct pipeline trace, not just a repo-wide grep) is settled with evidence.
2. A real, evidenced disposition is recorded: wire it in (own follow-up ticket if substantial), or
   record it as a real, confirmed orphan/gap in the registry so the finding survives past this
   ticket's own closure.

## Related Tickets
- `TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY` — found this while correcting
  `regional_sovereignty`'s own `implemented_by` binding.

## Related Docs
- `docs/plans/mechanism_identity_and_change_taxonomy.md` §4 — the correction's own full note.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/world/regional_sovereignty.py::RegionalSovereigntyService` — the orphaned code under
  investigation.
- `src/world/influence.py::FactionInfluenceService` — the real, live sovereignty mechanism this is
  distinct from, not a duplicate of.
- `registries/mechanisms.yaml` — `regional_sovereignty`'s own corrected entry.

## Assumptions / Open Questions
Not yet known whether this was intentionally deferred (a real design decision to build taxation
later) or simply never finished after being written — the code itself gives no indication either
way.

## Implementation Notes
### 2026-10-26: caller trace re-run at main 3533fde71, disposition recorded (U2 batch 1, no wiring)
**Zero callers confirmed.** `RegionalSovereigntyService`, `process_taxation` and `apply_sovereignty_debuffs` are named nowhere in `src/`, `tests/` or `tools/` outside their own definitions. The only other mentions: an allowlist string in `tests/architecture/test_legacy_enum_usage_boundaries.py:65` and a comment at `src/ai/goals/region_stabilization_scorer.py:28`. No string-keyed lookup reaches it, and `docs/audits/unreachable_code_inventory.{json,csv}` lists both methods as unreached.
**The 2026-09-30 note is partly stale.** Taxation is no longer a competing live implementation: owner decisions 51 and 58 (EXCH-02, amendment of 2026-10-09) removed the periodic per-head levy (#536, divergence 2.108); the live tax is a tenth of a sale or a wage (`src/engine/place_tax.py`, via `shop_sale.py` and `work_shift.py`). The conquered-region penalty is still live in `src/engine/town_resolution.py` (`region.suppression_active`: non-owner entities -20% atk/def, -10% speed; wired at `pipeline.py:339`). The orphan's `apply_sovereignty_debuffs` also returns an `EntityUpdate` with no fields set.
**Disposition: record, do not wire.** New registry entry `regional_levy_and_conquest_debuffs` (`state: orphan`, `implemented_by: RegionalSovereigntyService`). Wiring would revive a retired rule or duplicate a live one: a behaviour change, out of reach until decision 73. There is no wiring proposal, because none looks warranted; a periodic levy or a monster-held debuff would be a new declared feature. Whether to delete the class is a separate decision. Reviewed by rpg-planner-ubuntu before the commit.
**Doc fixed in this ticket:** `docs/world/regional_sovereignty_runtime_contract.md`. The effects table, the Taxation section and the Sovereignty-debuffs section now state today's rule (EXCH-02 place tax; `town_resolution.py` `suppression_active`) and keep the orphan's cadence and constants as a record of what it would do. The Regression tests list cited `test_long_run_stability.py` for "taxation cadence, gold transfer correctness, faction lock"; it covers long-run memory and population stability and determinism parity, none of those three, so the citation is corrected, and the live tax is pinned by `tests/unit/resource/test_tax_and_upkeep.py`. No test found asserts the `town_resolution.py` stat debuff (the suppression tests cover the action-legality gate).

### 2026-09-30 — classified via `TCK-20260929-UNREACHABLE-CLASSIFY-ZERO-CALLER` (epic `TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION`, child `T01`): verdict `UNDECLARED`

**The zero-caller claim holds, re-run at branch tip `3dbdff48a`.** `RegionalSovereigntyService`,
`process_taxation` and `apply_sovereignty_debuffs` have no reference in `src/`, `tests/` or `tools/` outside
their own definitions (the only other path-string hit is an allowlist entry in
`tests/architecture/test_legacy_enum_usage_boundaries.py:65`, not a call). No string-keyed or registry-style
lookup reaches the class. `docs/audits/unreachable_code_inventory.{json,csv}` (an independent earlier audit)
lists both methods as real and unreached. `src/world/regional_sovereignty.py` has no commits since filing
(2026-09-17). The ticket cites a `registries/mechanisms.yaml` *binding correction*, not a verdict, and that
correction is itself what this ticket is a follow-up to; registry-dating does not apply.

**What the ticket did not know: a second, live implementation of the same behaviour exists.**
`TownResolutionSystem.resolve()` is wired in the real pipeline (`src/engine/pipeline.py:339`,
`run_phase("town_resolution", ...)`) and implements regional taxation and a conquered-region combat penalty:
- taxation: `2.0` gold per entity whose faction differs from the region owner, `10.0` per functional building
  (`town_resolution.py:127-160`) — the same two constants the orphan class declares — but on a different
  cadence (`state.tick % (cadence.town_resolution * 2)`, i.e. 4-20 ticks depending on profile, not the
  orphan's fixed `TAX_INTERVAL = 100`) and a different trigger.
- penalty: when `region.suppression_active`, non-owner entities take atk/def `-20%` and speed `-10%`
  (`town_resolution.py:140-149`), versus the orphan's `CONQUERED_ATK_DEF_MOD = 0.8` / `CONQUERED_SPD_MOD = 0.9`
  gated on `owner_faction_id == MONSTER_HORDE`. The orphan's `apply_sovereignty_debuffs` also returns an
  `EntityUpdate` with no fields populated, so it would be a no-op even if called.

So this is not "a real, separate capability that was built and never wired in": taxation is already live
elsewhere, and two competing implementations exist with different numbers, triggers and cadence.
`docs/world/regional_sovereignty_runtime_contract.md` names `regional_sovereignty.py` as the taxation source
("Taxation — `regional_sovereignty.py`", every 100 ticks) — the dead one — and cites
`tests/integration/world/test_long_run_stability.py` for "taxation cadence, gold transfer correctness", a file
in which `grep -ci tax` returns `0`. Nothing declares which implementation is authoritative. Verdict
`UNDECLARED`; the doc's wrong source attribution is a `MISLABEL`-shaped symptom of the same undeclared state,
recorded here and not corrected (out of this epic's scope).

## Test Summary
- `make mechanism-registry-validate` passes (110 mechanisms); html `--check` up to date; no `orphan_with_callers` finding for the new entry.
- Pins moved from the real registry in `test_mechanism_registry_completeness_check.py` (wider unbound_files 250 to 249, candidates 70 to 69) and `test_mechanism_atlas_regenerate.py` (38 to 39 unmapped); both files pass. No src change.

## Files Changed
- registries/mechanisms.yaml (new entry, pointer sentence); regenerated docs/brainstorm views
- docs/world/regional_sovereignty_runtime_contract.md
- tests/unit/tools/test_mechanism_registry_completeness_check.py, tests/unit/tools/test_mechanism_atlas_regenerate.py

## Completion Summary
**Verdict as of 2026-10-26: confirmed orphan, superseded in part (by EXCH-02's place tax and the live `suppression_active` penalty).** Recorded in the registry as `regional_levy_and_conquest_debuffs`; the contract doc corrected; nothing wired. Any wiring is a separate ticket after decision 73.
