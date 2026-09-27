# Implementation Sequence — systemic-world-first-wave

These briefs are the first wave of `docs/plans/systemic_world/first_wave_plan.md`, which is still
`PROPOSED / FOR REVIEW`. **None starts until the owner has reviewed that plan's scope.** Each brief
states a semantic contract, the observed problem, bounded scope, acceptance evidence, and
unresolved risks. The implementation agent owns the technical resolution and regression design.

## Order

1. TCK-20260927-NATURAL-AGING-OLD-AGE-DISPATCH-RACE (M1). No dependencies.
2. TCK-20260927-LINEAGE-TWO-HOP-NATURAL-COMPOSITION (M4a). Depends on M1 only.
3. TCK-20260927-INHERITANCE-EVIDENCE-PATH-DESIGN (M2). No dependencies; never gates M4a.
4. TCK-20260927-SAME-TICK-DEATH-AUTHORITY-CHECK (M3a). No dependencies.
5. TCK-20260927-SAME-TICK-DIPLOMACY-AUTHORITY-CHECK (M3b). No dependencies.
6. TCK-20260927-SAME-TICK-REPUTATION-AUTHORITY-CHECK (M3c). No dependencies.

## Why This Order Matters

The only hard edge is M1 → M4a. The composed two-hop run cannot happen until natural-aging death
records a cause and dispatches succession.

M2 and M3a/b/c are independent of each other and of M1/M4a. They may run in parallel or in any
order; the numbering above is not a sequence among them.

World-side work (M1, M4a) never waits on a player-side result (M2).

## Integration back into planning

Each ticket's verified outcome is reported back to the planning agent. It is recorded in
`docs/plans/systemic_world/roadmap.md` (§3.1 audit table, §7 gate tables) and in the mechanism
registry through its normal process. Prototype or partial results are not treated as shipped
fixes.
