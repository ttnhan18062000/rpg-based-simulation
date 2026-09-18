---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260917-REGIONAL-SOVEREIGNTY-SERVICE-ORPHAN-TAXATION-DEBUFFS
phase: open
date: 2026-09-17
tags: [world, architecture]
---

# TCK-20260917-REGIONAL-SOVEREIGNTY-SERVICE-ORPHAN-TAXATION-DEBUFFS

## Title
`RegionalSovereigntyService` (regional taxation + macroscopic conquest debuffs) has zero real
callers anywhere in `src/` — real, non-dead code, never invoked

## Status
OPEN

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
Not yet started.

## Test Summary
Not yet started.

## Files Changed
None yet (this ticket file only).

## Completion Summary
Open. Filed per peer review so this finding — caught only as a side effect of an unrelated
registry-identity ticket — doesn't stay recorded only in that closed ticket's own prose.
