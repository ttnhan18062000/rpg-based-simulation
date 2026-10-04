---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261004-GENERATOR-AUTHORS-UNASSEMBLABLE-COMPOSITION-ON-REGION-ID-COLLISION
phase: open
date: 2026-10-04
tags: [world, content, root-cause]
---

# TCK-20261004-GENERATOR-AUTHORS-UNASSEMBLABLE-COMPOSITION-ON-REGION-ID-COLLISION

## Title

The procedural composition generator can author a composition that cannot assemble: it selects two
modules declaring the same region id and never sets a `namespace`, so the resolver fail-fasts on
`Duplicate region ID collision 'hometown'`

## Status

INPROGRESS

## Tier

standard

## Type

bug

## Priority

P1

## Request Summary

**Pre-existing latent defect, surfaced not caused** by
`TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION`'s Step 11, which made `generate()` resolve what
it authors. It was invisible because **nothing ever resolved the generator's output** — the composition
was written and never assembled, so an unassemblable one looked like a success.

**The collision, verified directly:**

| module | declares |
|---|---|
| `data/content/world_modules/frontier_village_core.yaml:9` | region `id: "hometown"` |
| `data/content/world_modules/trading_company_hub.yaml:19` | region `id: "hometown"` |

Today's `ModuleScorer` ranks those two **1 and 2** for the `generated_frontier_3_42` intent, so the
generator selects both. It emits every `ModuleRefSpec` with `namespace=None` and never sets one, and
Rule 5 fail-fasts only on duplicate `provides`, **not** on duplicate region ids. The resolver then
raises at `src/worldassembly/resolver.py:359`:

```
ValueError: Duplicate region ID collision 'hometown' detected during assembly merge.
```

**Hand-authored worlds already solve this, which is the proof the mechanism exists and the generator
simply does not use it:** `data/worlds/urban_political/world.yaml:16` composes the same two modules and
sets `namespace: "trading"`. `test_urban_political_composition`'s own docstring says so.

**Evidence it predates the surfacing ticket:** the selection code is byte-unchanged by that diff — the
only matching lines are docstrings. Separately, the **committed**
`generated_frontier_3_42/world.yaml`, authored before that ticket, does **not** contain
`trading_company_hub` at all. So either the corpus or the scorer's ranking moved after that file was
generated, and nothing noticed, because nothing resolved it.

## RULING, 2026-10-04 — Option 1 (namespace), with two conditions. AC-1 is satisfied.

Ruled by `world-rule-catalog-design`. **Options 2 and 3 are wrong on world-semantics grounds.** Every
factual claim below re-verified by the orchestrator before being recorded.

**My framing of the question was wrong, and this is the correction that matters.** I asked whether
namespacing "mints identity rather than selecting differently", guessing `ID-01`/`LOC-03` made option 1
the risky one. **The two `hometown` regions are two different places**, verified:

| module | `grid_bounds` | hazard |
|---|---|---|
| `frontier_village_core.yaml:9-14` | `[10, 10, 40, 40]` | `0.0` |
| `trading_company_hub.yaml:19-24` | `[45, 10, 80, 45]` | `0.5`, `NATURAL_TERRAIN` |

**Non-overlapping, materially different places.** They have never been one place under two names — they
are two places wrongly sharing one identifier. `ID-01`/`ID-02`: identity is not a name or a
classification, so two distinct subjects must not share an identity key. `LOC-01`: every
`spawn_region: "hometown"` reference must resolve to one unambiguous region. **So namespacing does not
mint a new identity for an existing place — it gives a second, already-distinct place the identity it was
missing.** The concern I raised would only be real if a generated world had ever *run* with a `hometown`
region whose id we were now changing. **None has** — by this ticket's own finding, the generator's output
never resolved, so there is no generated region identity to preserve. **`LOC-03` is not engaged:**
containment is unchanged and each module's places stay inside its own region.

**Why 2 and 3 are wrong:** they alter the **world's content** (its module set) to work around a **naming**
defect. That lets an identifier artifact decide what the world contains. The generator's ranking expressed
an intent, and a namespace clash is no reason to override it.

**Authored precedent — option 1 is the generator doing what the authors already do.** Verified on
`data/worlds/`: every authored world composing both modules keeps `frontier_village_core` **bare** and
gives `trading_company_hub` `namespace: "trading"` — `frontier_living_world/world.yaml:19-21`,
`frontier_extended/world.yaml:23-25`, `urban_political/world.yaml:16`.

### Condition 1 — identity must be deterministic in the module SET, never in rank or order

Which module gets namespaced, and with what namespace, **must be a function of the module set**. If
whichever module ranks lower loses the bare id, **a scorer change would silently swap which place is
`hometown`**. Matching the authored precedent is preferred if it can be expressed that way — e.g. a
per-module default namespace declared in the module content. **The mechanism is ours, the constraint is
the rule owner's.**

### Condition 2 — completeness, or `LOC-01` breaks quietly

Namespacing must rewrite **every intra-module reference** to the region — `spawn_region`, place
`region_id`, recipes — not just the region's own `id`. Otherwise references resolve to the *other*
module's place, or to nothing. **Assemblability is the minimum; the real test is that each module's
population lands in its own module's region.**

A fail-fast guard for undisambiguated duplicate region ids is **fine as validation** (the resolver already
raises at `:359`; moving the check earlier is engineering). It **must not** become a selection
fallthrough — that would just be option 2 wearing a different hat.

## Scope

- ~~Decide which of the three fixes is correct.~~ **Settled: option 1, per the ruling above.** Implement
  it under both conditions. Do not revisit 2 or 3.
- Implement the chosen fix and assert a generated composition **assembles**, not merely that it
  validates. The absent assertion is why this survived.
- Re-check whether the committed `generated_frontier_3_42/world.yaml` is now stale against what today's
  scorer produces, and decide whether a committed generated world is expected to be reproducible at all.

## Out of Scope

- Any change to `data/content/world_modules/frontier_village_core.yaml` or `trading_company_hub.yaml` to
  de-conflict the region id at source. Two modules legitimately offering a `hometown` is arguably correct
  — `namespace` exists precisely so they can coexist. Not pre-judged, but it is a different ticket.
- `TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION`'s own scope. It surfaced this and must not fix
  it; its two affected tests are `xfail`-marked pointing here.
- Balance: whether the resulting generated world is *good* is parked by `owner_decision_memo.md` row 7.

## Acceptance Criteria

1. ~~A recorded decision among the three options.~~ **SATISFIED 2026-10-04** — option 1, ruling recorded
   above with both conditions. Cite it; do not re-derive it.
2. A test asserting a generated composition **assembles end-to-end**, failing on today's code. Assert
   non-empty before any loop — a vacuous pass has shipped green in this repo before.
2a. **Condition 1 is tested, not just implemented:** namespace assignment is a function of the module
   **set**, proven by a test that changes the ranking/order and asserts the *same* module keeps the bare
   id. Without this, a later scorer change silently swaps which place is `hometown` and nothing notices.
2b. **Condition 2 is tested at the population level, not the assembly level:** assert each module's
   population lands in **its own module's region**, not merely that the world assembles. Assembly
   succeeding while `spawn_region` references point at the wrong place is the quiet `LOC-01` break this
   condition exists to prevent.
3. The two `xfail(strict=True)` marks in
   `tests/integration/worldassembly/test_real_content_world_compositions.py`
   (`test_generated_composition_is_valid_worldcompositionspec`,
   `test_generated_composition_determinism`) are **removed** as part of this fix. `strict=True` means
   they fail if they start passing, so they cannot rot silently — but they must not outlive this ticket.
4. The behaviour change is recorded in `docs/guidelines/intentional_divergences.md` with a rationale
   class, and the relevant `docs/parity_ledger/` entry updated. If option 1 is chosen, note that region
   ids in generated worlds change — that is a visible world-content change, not an internal refactor.

## Related Tickets

- `TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION` — surfaced this; Step 11 made the generator
  resolve what it authors. Its Deviations 10/11 record the finding.
- `TCK-20260915-WORLDBUILDING-DUPLICATE-REGION-ID-ACROSS-MODULES` — **fold it into this ticket**
  (rule owner's assessment, 2026-10-04). Its question was what the compiler does on a duplicate region id:
  keep both, merge them, or let one silently win. **That is now answered by measurement** — the resolver
  fails fast at `resolver.py:359`, and authored worlds disambiguate by `namespace`. Two notes carried from
  that assessment:
  - **Its premise appears to be wrong.** It claims `frontier_living_world` collides, but
    `data/worlds/frontier_living_world/world.yaml:19-21` namespaces the hub, so it does not. The rule
    owner's unverified guess — flagged as a guess, not a finding — is that it was read off the **catalog
    copy** rather than the running definition. Worth confirming before folding, since it is the same
    catalog-vs-running confusion `TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION` exists to end.
  - **Its "audit other compositions" scope becomes this ticket's cross-module region-id sweep** (see
    Assumptions). That sweep **and** the ranking-stability question should land **before** anyone claims
    only one intent is affected.
- `TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION` — unrelated cause, same
  root shape: an artifact nothing validated, so an error in it stayed invisible.

## Related Docs

- `docs/world/generator_contract.md` — the two generation paths
- `docs/mechanics/06_worldbuilding_foundation.md` — declarative topology and integrity validation
- `docs/world_rules/foundations/identity.md` — `ID-01`; and `space-environment/location-topology.md` for
  `LOC-03` (containment is a real, authoritative relationship)

## Related Stored Artifacts

- `agent-working/staging_artifacts/TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION/plan.md` —
  Deviations 10 and 11

## Related Code Areas

- `src/worldassembly/resolver.py:359` — the fail-fast that surfaced it
- `src/worldgeneration/generator.py` — `ModuleScorer` ranking and the `ModuleRefSpec` emission that
  leaves `namespace=None`; Rule 5's duplicate-`provides` check
- `data/content/world_modules/frontier_village_core.yaml:9`,
  `data/content/world_modules/trading_company_hub.yaml:19`
- `data/worlds/urban_political/world.yaml:16` — the hand-authored `namespace: "trading"` precedent
- `data/content/world_compositions/generated/generated_frontier_3_42.yaml` *(retired by the surfacing
  ticket; read it from git history)* and `data/worlds/generated_frontier_3_42/world.yaml`

## Assumptions / Open Questions

- **Which option is right is genuinely open** and is this ticket's reason to exist. Not pre-judged.
- **Unverified: how many intents collide.** Only the `generated_frontier_3_42` intent was observed. The
  collision depends on `ModuleScorer`'s ranking, so other intents may or may not hit it. Measure before
  claiming scope — and note a low count is not a reason to deprioritise, since the failure is total for
  an affected intent.
- **Unverified: whether other region ids collide across module pairs.** `hometown` was found by one
  failing assembly, not by a sweep. A sweep over all module pairs would say whether this is one pair or a
  class.
- Unverified: whether `ModuleScorer`'s ranking is deterministic across runs. If it is not, which intents
  collide could vary run to run.

## Implementation Notes

- `ProceduralCompositionGenerator._assign_region_namespaces` (src/worldgeneration/generator.py): modules walked in
  `module_id` order; a module declaring a region id already claimed gets `namespace=<module_id>`.
  Function of the module set only (Condition 1). Residual collision raises `GenerationCompositionError`
  (validation, not a selection fallthrough).
- Condition 2: the resolver already prefixes region, place, `spawn_region` and recipe ids from the namespace;
  the integration test asserts population placement by bounds against the module's own region.
- Sweep: 5 region ids collide across the 22 modules (`hometown` x3, `haunted_battlefield`, `near_forest`,
  `wolf_den`, `bandit_road`) - a class, not one pair.
- Deviation from the authored precedent: authored worlds use `namespace: "trading"`; the generator uses the
  module id. Matching it would need a per-module default-namespace field (module content change, out of scope).
- **AC-3 not yet actionable**: the two `xfail(strict=True)` marks exist only on the #328 branch, not on
  origin/main. They must be removed when #328 lands (strict xfail would XPASS-fail otherwise).

## Test Summary

_(not started)_

## Files Changed

_(not started)_

## Completion Summary

_(not started)_
