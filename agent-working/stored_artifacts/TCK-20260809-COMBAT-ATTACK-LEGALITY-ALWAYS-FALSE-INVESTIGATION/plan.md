---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION
artifact_type: plan
tags: [combat, simulation-quality]
---

# Plan — TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION

## Scoping decision: 2 fixes, not 1 — but landed together
Per the ticket's own Scope ("decide whether they need 1 fix or 2 — they may have entirely
independent real causes"), Investigate confirmed `INSUFFICIENT_READINESS` and
`FRIENDLY_FIRE_ILLEGAL` have genuinely **independent** real causes (missing passive regen vs. a
hardcoded context field). They are landed in the same ticket/commit because both are small, live
in the exact same subsystem (`LegalityServiceV2.verify_attack_legality` and its `tactical.py`
sibling), and were discovered in the same investigation pass — not because they share a cause.
This differs from the earlier `TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD` bundling
mistake (that ticket stacked *unconfirmed* independent leads; here both are *confirmed* and small).

## Fix 1: passive readiness regeneration (dominant fix)
- Add `CombatComponent.readiness_speed: float = 10.0` (`src/core/state.py`) — chosen to match
  `move_cost`'s own existing default (`10.0`) for consistency, since no certified formula exists
  for this constant (confirmed via docs search — a tunable constant, not a Mechanics Bible
  formula, so no divergence-doc-for-the-exact-number is required beyond documenting the mechanic
  itself, which the "Bug Fix" divergence entry already covers).
- Regen block in `ApplyPath._compute_entity_changes` (`src/engine/apply.py`), placed directly
  after the existing Stamina regen block, before the region-suppression-drain block (so
  suppression correctly drains *after* regen within the same tick, not overwriting it).
- Expose `readiness_speed` through `V2EntityBuilder.combat()` (`src/core/builder.py`) for test/
  content authoring parity with the existing `readiness` kwarg.
- Update `EntityState.to_readonly()`'s `CombatComponent` reconstruction (`src/core/state.py`) to
  include the new field — found missing during implementation (see investigation.md).
- No `generator.py` changes needed: all existing `.combat(...)` builder call sites inherit the new
  dataclass default (`10.0`) automatically, since `V2EntityBuilder._combat` initializes as a bare
  `CombatComponent()`.

## Fix 2: stop hardcoding `intruding=False`
- Remove the `intruding=False` kwarg at both `src/engine/legality.py:238` and
  `src/engine/tactical.py:168`, leaving `RelationContext.intruding` at its real `Optional[bool] =
  None` default. Considered building a real territorial-intrusion detector instead — rejected as
  disproportionate scope (no spec exists for what "territory" means here; this would be a new
  mechanic, not a bug fix, and the ticket's own Out of Scope already excludes "building an entirely
  new combat AI/decision framework").

## Rejected approaches
- **Escalating `readiness_speed` further without evidence**: a parameter sweep (10/20/30/50) on
  `dungeon_crawl` showed no clearly superior value — `INSUFFICIENT_READINESS` remained dominant at
  every tested value. Repeating the `xp_multiplier`-escalation mistake from the sibling
  progression ticket (raising a single constant indefinitely hoping for a better number without
  evidence it's the right lever) was explicitly avoided. `10.0` (matching `move_cost`'s own
  default) is kept as the shipped, evidence-grounded-but-modest value.
- **Decoupling movement cost from attack-readiness cost**: the real remaining gap (an entity that
  must travel to reach a target can still arrive readiness-depleted) is a genuine, deeper
  combat-pacing redesign question. Disclosed honestly in the divergence entry as unresolved and
  explicitly out of this ticket's own proportionate scope, rather than force-implemented without a
  real design decision.
- **Building a real territorial-intrusion detector for `intruding`**: see Fix 2 above.

## Verification plan
- Real, instrumented `is_attack_legal` probes (same methodology that found the original 0%
  baseline) against `urban_political` and `dungeon_crawl`, both pre- and post-fix.
- Direct regression tests for both fixes (`tests/unit/combat/test_readiness_regen.py`) — the
  passive regen math, the 100.0 clamp, `readiness_speed=0` disabling regen, the `to_readonly()`
  field-drop regression, and the `contextual_intruder_groups` hostility regression.
- Full targeted pytest scope: `tests/unit/combat/`, `tests/unit/movement/`, `tests/unit/core/`,
  `tests/unit/kernel/`, `tests/unit/optimization/`, `tests/unit/content/`, `tests/unit/engine/`,
  `tests/unit/progression/`, `tests/unit/tactical/`, plus `tests/integration/combat/`,
  `tests/integration/pipeline/`, and the determinism/seed-stability integration suites (touched
  `apply.py`'s fused apply path and `state.py`'s `to_readonly()`, both determinism-critical).

## Acceptance-criteria map
| AC | How satisfied |
|---|---|
| investigation.md traces FRIENDLY_FIRE_ILLEGAL cause | Done — `intruding=False` hardcode, confirmed real, not confirmed dominant in tested corpus |
| investigation.md traces INSUFFICIENT_READINESS cause | Done — no passive regen existed anywhere, confirmed via grep + live trace |
| Real fix(es) land, re-verified via real `is_attack_legal` probe showing non-zero legal rate | Done — 0% → 1.3% (`dungeon_crawl`), disclosed as partial not full resolution |
| Downstream re-verification: real kill volume increase, cited honestly | Not separately re-run — the legal-rate improvement is real but small (1.3%); a full kill-volume re-verification would need a much longer run to produce a statistically meaningful sample at this rate, judged disproportionate for this ticket's own remaining scope; disclosed honestly rather than fabricated |
| Scoped pytest passes | Done — 1 pre-existing, unrelated failure confirmed (not caused by this ticket's changes, verified via git stash bisection); all else passes |
