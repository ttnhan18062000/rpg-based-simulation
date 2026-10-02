---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261002-GOAL-WINNER-CONSUMPTION-DISCARDS-DECIDED-OBJECTIVE-KIND
artifact_type: plan
tags: [strategy, cognition, combat]
---

# Plan — goal-winner consumption discards the decided objective kind

Read `investigation.md` first; it holds the measurement this plan is built on. The ticket holds the two
scope guards. **This plan does not restate either.**

Two changes, in this order, **in one commit or one tightly-coupled pair that lands together**. Neither
may reach `main` without the other — the ticket records why.

## Step 1 — `CombatEngageScorer` publishes its objective kind and uses the catalog for hostility

`src/ai/goals/scorers.py`, `CombatEngageScorer.score` (lines ~101-131).

**1a. Replace the raw-enum hostility filter.** Current line 108:

```python
hostiles = [n for n in neighbors if n.identity.faction != entity.identity.faction and n.combat.alive]
```

The raw `Faction` IntEnum has four values, so content factions collapse. Replace the predicate with the
**same catalog test the engagement path uses** — do not write a second one. `LegalityServiceV2._is_engagement_hostile`
(`src/engine/legality.py:516-544`) is the reference implementation: `EntityIdentityResolver().resolve(e).faction_id`
with `get_faction_id_str` as the `IdentityResolutionError` fallback, then
`get_faction_semantics_service().is_hostile_compat(src, tgt, ctx)`.

**Decision required of the implementer, and it must be recorded in Implementation Notes:** that helper
is currently a private static on `LegalityServiceV2`. Either (i) call it, or (ii) lift it to a shared
home both callers import. Prefer (ii) if the scorer cannot reach it without an import cycle —
`src/content_semantics/faction.py` is the natural home since it already owns the service. **Do not
copy the body into `scorers.py`**: a duplicated hostility test is the exact defect class this ticket
exists to close, and `TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP` will have more callers.

Build the `RelationContext` with the **real** distance to the candidate and `combat_engaged=True`, not a
hardcoded `distance=1.0`. The investigation's percentages used the hardcoded value and are therefore
floors; using the real distance is both more correct and the reason the measured delta may be smaller
than those floors suggest.

**1b. Publish `obj_kind` in metadata.** Follow the three existing precedents exactly —
`occupation_change_scorer.py:98`, `region_stabilization_scorer.py:86`, `social_contract_scorer.py:75`.
Add `"obj_kind": ObjectiveKind.DEFEAT_ENEMY` to the returned `GoalScore`'s metadata. The scorer resolves
the objective kind; the consumer must not infer it.

Leave `target_id` and `target_pos` exactly as they are. The entity-id-as-target problem is the third
ticket's (`TCK-20261002-COMBAT-OBJECTIVE-TARGETS-ENTITY-VIA-FIXED-POINT-AND-NEVER-TERMINATES`), and
changing it here would make this batch's after-measurement unattributable.

## Step 2 — the generic branch derives the objective kind instead of hardcoding it

`src/systems/strategic_systems/intelligence.py`, the generic `else` at ~1707-1714. Change **one line**:

```python
kind="reach_location",
```
to read the scorer-published kind with an explicit fallback:
```python
kind=best_candidate.metadata.get("obj_kind") or ObjectiveKind.REACH_LOCATION,
```

Use `.get(...) or <default>` (or an equivalent explicit `None` check), not a bare `.get("obj_kind")`.

**Why additive and not a fourth `elif`:** the investigation's §6 audit found `reach_location` is
**correct for 9 of the 10** registered fall-through `GoalKind`s. A fallback-preserving derivation fixes
`COMBAT_ENGAGE` and leaves those nine byte-identical, while also letting any future scorer express a
correct kind. A fourth bespoke `elif` would fix only this one and grow the branch count the repo's
Strategic/Tactical rule warns against.

**Change nothing else in those eight lines.** `ProjectState.kind` stays `best_candidate.kind` (a
`GoalKind`) and `score` stays `best_candidate.utility` — the ticket's scope guard explains why touching
either silently flips the score scale from the 100.0 ceiling to 2.9.

## Step 3 — re-measure, and report whatever it shows

Re-run the investigation's probe method unchanged (same script shape, same worlds, seed 42, 2000 ticks,
**`LocalSequentialExecutor()` explicitly**) and report in `## Test Summary`:

1. `ATTACK` emissions from entities holding a won `COMBAT_ENGAGE` project. Before: **0 / 216** and
   **0 / 20**.
2. `hostiles` non-empty rate on those calls. Before: **0 / 216** and **0 / 20**. This is the real gate —
   if it is still ~0, the fix did not work regardless of what `obj.kind` now says.
3. Decision-path vs opportunity attacks. Before: **2 vs 119** and **3 vs 783**.
4. The catalog-hostile vs raw-only target ratio under the **real** distance context. Before, under the
   permissive context: 54.0% and 33.6% raw-only, both floors.
5. The arrived-noop rate. Before: 96.8% and 70%. Expect it to stay high — that is the **third ticket's**
   defect, not evidence this fix failed.

**A smaller-than-hoped delta is a finding, not a failure.** At ≥34-54% of selected targets not being
catalog-hostile, the reachable improvement is bounded by the catalog, and step 1a narrows the scorer's
candidate set deliberately — fewer, better targets. If `ATTACK` emissions rise from 0 to a small number,
that is success.

## Scope guards, restated as prohibitions

- Do **not** change `ProjectState.kind` or `score` in the generic branch.
- Do **not** touch `CombatEngageScorer`'s `target_id` / `target_pos`.
- Do **not** fix any other raw-enum site — `combat.py:507`, `intake.py:30/:44`, `legality.py:451`,
  `cognition.py:44/:117`, `cooperation/providers.py:50`, `intelligence.py:149/:439` all belong to
  `TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP`. Note `SensoryFilter.filter_saliency` runs on
  the line immediately above the one being changed (`scorers.py:107`) and is a sweep site, **not** this
  ticket's.
- Do **not** widen the `stats_dirty`-style trigger set or alter goal scoring weights.
- Do **not** regenerate a recorded-hash fixture that moves. Identify it and explain it.

## Acceptance-criteria map

| AC | Satisfied by |
|---|---|
| CE win materialises `DEFEAT_ENEMY` with the hostile's entity id as `target` | Steps 1b + 2 |
| Entity whose target the catalog agrees is hostile actually attacks, asserted through a real `Kernel.tick_once()` | Step 1a + 2; `test_plan.md` T4 |
| `hostiles` non-empty for such an entity | Step 1a; T3 |
| No kind that previously produced a correct `reach_location` changes | Step 2's fallback; T1, T2 |
| Attack-path volume measured before and after, reported whatever it shows | Step 3 |
| Determinism holds | T7 |
| Scope 4 per-`GoalKind` audit recorded | Already done — `investigation.md` §6 |
| Docs + `strategic_cognition.yaml` parity updated | Step 4 below |

## Step 4 — docs and parity

- `docs/mechanics/04_strategic_cognition.md` — the goal-hierarchy/dispatch section must say the
  objective kind is resolved by the scorer and carried through winner consumption, with
  `REACH_LOCATION` as the fallback for scorers that publish none.
- `docs/parity_ledger/strategic_cognition.yaml` — find the entry covering goal dispatch; update `status`
  and `v2_evidence` with the new test path. If no entry covers it, add one. If it is `P0` it needs a
  passing `test_path`.
- No `intentional_divergences.md` entry is expected: this makes code match the documented intent rather
  than depart from it. If the implementer concludes otherwise, say so rather than filing one silently.
