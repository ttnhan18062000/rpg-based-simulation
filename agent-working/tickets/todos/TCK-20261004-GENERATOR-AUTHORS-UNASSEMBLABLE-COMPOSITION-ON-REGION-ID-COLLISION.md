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

OPEN

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

## Scope

- Decide **which** of the three fixes is correct — this is the whole point of the ticket and it is a
  world-semantics decision, not an implementation detail. All three change **which world a given intent
  generates**:
  1. **Auto-namespace** colliding modules in the generator (e.g. derive a namespace from the module id).
     Changes **region identity** itself, so region ids in generated worlds would differ from today's.
  2. **Extend Rule 5** to reject duplicate region ids and have selection fall through to the next-ranked
     candidate. Changes the module **set**.
  3. **Filter colliding candidates at selection time.** Also changes the module set, earlier in the
     pipeline.
- Put that decision to `world-rule-catalog-design` **before** implementing. Region identity and what a
  generated world contains are its area; see `ID-01`/`LOC-03` and the region-scope sibling ticket below.
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

1. A recorded decision among the three options, with the rule owner's ruling cited, made **before**
   implementation.
2. A test asserting a generated composition **assembles end-to-end**, failing on today's code. Assert
   non-empty before any loop — a vacuous pass has shipped green in this repo before.
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
- `TCK-20260915-WORLDBUILDING-DUPLICATE-REGION-ID-ACROSS-MODULES` — **same family at the same scope.**
  Read it first; it may already own part of this, in which case fold rather than duplicate.
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

_(not started)_

## Test Summary

_(not started)_

## Files Changed

_(not started)_

## Completion Summary

_(not started)_
