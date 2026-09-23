---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, documentation, schema]
---

# Agent Operating Model — Simulation Semantic Control Plane

Part of [the epic](README.md). This is the workflow layer: how an agent actually uses
[architecture.md](architecture.md)'s model while implementing, debugging, tuning, or retiring
RPG-core simulation logic. Nothing here changes what the Mechanism Registry's own change taxonomy
or identity rule mean — it reuses both as-is and adds investigation-mode vocabulary around them.

---

## 1. Governing principle

> First determine what kind of problem is being solved. Then retrieve only the architectural
> context and evidence that problem type actually requires.

Never treat these as equivalent — each is a real, previously-conflated failure mode in this repo's
own history:

| Claim | Real prior incident where two of these were wrongly conflated |
|---|---|
| code exists | — |
| code is reachable | `race_archetype`, `country_lifecycle` — real code existed under a post-rename name a search never tried |
| mechanism executes | `camp` — reachable, correct code, never invoked because no world seeds `state.camps` |
| mechanism produces a state change | `combat_judgement` — executed every relevant tick, write-only across 4 real conditions |
| state change reaches a consumer | `readiness_speed_scaling` — real formula, real write path, zero real firings in any tested corpus world |
| observed behavior matches mechanism intent | `tactical_decision`'s ATTACK-intent branch — `state: done`, `verified.verdict: contradicted` |
| behavior conforms to World Rules | `TERR-01` — `owner_faction_id` is `state: done` code correctly doing something the target semantics forbid it from doing alone |
| behavior produces desirable balance | out of scope for this plane — SimQ's job, not this epic's |

## 2. Task classification

**Reuse the Mechanism Registry's existing 8-kind change taxonomy as authoritative, unchanged:**

```
INTRODUCE   EXTEND   WIRE   TUNE   SPLIT   MERGE   RETIRE   INTERPOSE
```

(`docs/plans/mechanism_identity_and_change_taxonomy.md` §2 — do not invent a rival taxonomy.)

**Add workflow/investigation modes, kept explicitly separate from the taxonomy above** — these are
how an agent classifies its *own current activity*, not a registry change kind:

```
DEBUG_EXECUTION   DEBUG_BEHAVIOR   DEBUG_SEMANTICS   DISCOVERY   REFACTOR   CAUSAL_CHAIN_DEBUG
```

`REFACTOR` in particular is neither an existing taxonomy kind nor a semantic change — it is
"implementation binding changes, everything else stays fixed" (§7 below).

## 3. Before introducing anything new, check whether it already exists

For a request that sounds new (example: *"add faction memory of dangerous people"*), resolve in
this order before writing code:

```
1. Does an existing Rule already govern this? (search docs/world_rules/, not memory)
2. Does an existing mechanism already own this capability?
3. If yes to both but disconnected → WIRE or INTERPOSE, not INTRODUCE
4. If a mechanism exists but is incomplete → EXTEND
5. Only if none of the above → INTRODUCE
```

This is how the architecture prevents parallel feature growth — the exact failure this repo's own
five-artifact status drift and its dead-code baseline (10–30% is the normal industry band per
`mechanism_claims_as_tests_initiative.md` §2, this repo currently sits at ~14% orphan/gated of 93)
already show is easy to fall into by accident.

Before `INTRODUCE`, define at minimum: semantic purpose, independent success/failure boundary
(the identity rule, `mechanism_identity_and_change_taxonomy.md` §1), inputs/preconditions, state
owner, outputs, upstream producers, downstream consumers, failure semantics, and which Rule(s) it
maps to. After landing: register the mechanism, bind `implemented_by`, add the Rule↔Mechanism
mapping entry, add/refresh verification.

## 4. The 9-step troubleshooting ladder

Investigate in this order unless evidence strongly indicates otherwise. Do not jump from a
player-visible symptom straight to tuning a parameter.

```
1. EXISTENCE       Does the mechanism/code exist?
2. REACHABILITY     Can execution reach it?
3. ACTIVATION       Do real generated worlds trigger it?
4. EFFECT           Does it commit meaningful state?
5. CONSUMPTION      Does anything read/use that state?
6. BEHAVIOR         Does observed behavior match the mechanism's own claimed intent?
7. SEMANTICS        Does that behavior conform to World Rules?
8. DISTRIBUTION     Does it happen at the intended frequency/magnitude?
9. EXPERIENCE       Does the composed result create the intended systemic effect?
```

This formalizes a ladder this repo has already walked for real, repeatedly, one incident at a
time (`camp` stops at step 3, `combat_judgement` stops at step 4, `readiness_speed_scaling` stops
at step 5, `tactical_decision`'s ATTACK branch stops at step 6, `TERR-01`'s `owner_faction_id`
stops at step 7). Report the **first failed rung**, not the final visible symptom.

**Evidence strength must match the claim being made — never use a weaker instrument for a
stronger claim:**

| Claim | Minimum evidence |
|---|---|
| "the symbol exists" | source inspection |
| "the call path exists" | structural/call analysis (`graphify query`, not a code trace alone — see the mechanism registry's own catalogue of search-scope failures) |
| "it fires in generated worlds" | runtime evidence (`scenario` / `corpus_run` / `census`) |
| "it affects later decisions" | end-to-end scenario or corpus evidence |
| "behavior conforms to World Rules" | direct semantic comparison against the Rule's own text |
| "it's balanced" | population/distribution evidence — SimQ's domain, not this ladder's |

A `code_trace` can prove the path exists. It can **never** prove the simulation actually reaches
it, and per the Mechanism Registry's own "shape 7" search-failure finding, a citation that stops
one hop short of the real entry point (a class nothing instantiates, a flag defaulted off) passes
a naive check cleanly while being just as dormant as code with no citation at all.

## 5. Debugging is layered — never collapse these four questions

```
EXECUTION CORRECTNESS    Did it run?
BEHAVIORAL CORRECTNESS   Did it do what the mechanism claims?
SEMANTIC CORRECTNESS     Is that behavior legal under the target World Rules?
BALANCE / DESIGN QUALITY Is the magnitude/frequency/desirability right?
```

A mechanism can pass the first three and still need tuning. It can pass runtime verification and
still violate a Rule (`TERR-01` again — the code is correct and the semantics are wrong). Record
each finding at its own layer; do not let a passing lower layer stand in for an unproven higher
one, and do not use a tuning fix to paper over a wiring or semantic defect (§6).

## 6. Balance complaints are often wiring bugs in disguise

Example: *"NPCs almost never learn skills."* Do not tune the learning-rate constant first. Walk
the ladder:

```
Does the learning mechanism execute?
→ Does it receive real opportunities?
→ Does the capability gate pass?
→ Does the learning state actually change?
→ Is the change consumed downstream?
→ Only then inspect the tuning value.
```

A finding of "learning chance is a perfectly reasonable value, but the opportunity event is never
produced" is `WIRE`, not `TUNE` — the exact shape of the `xp_leveling`/`evolution` starvation
finding already on record (busiest tested entity in any world never crossed even one XP
threshold; the formula was never wrong, the volume never arrived).

## 7. Refactoring preserves everything except the implementation binding

```
World Rules            unchanged
Mechanism identity      unchanged
Rule↔Mechanism mapping  unchanged
Observed behavior       unchanged
```

Only `implemented_by` (and, if the refactor's own scope requires it, verification) changes.
Architectural documents should not need broad edits for a pure refactor — that is the entire
benefit of keeping semantic identity, mechanism identity, and implementation symbol as three
separate things (`architecture.md` §2).

## 8. Discovery — unregistered code is `UNKNOWN`, never automatically invalid

Because the Mechanism Registry's own completeness sweep covers 2 of roughly 15 real source
directories, an unfamiliar class outside `src/domains/`/`src/systems/` is not evidence of
anything by itself. Investigate:

```
What capability does this represent?
Can it independently succeed/fail? (the identity rule)
Does an existing mechanism already represent it?
Is it implementation detail only, or genuinely a missing registry entry?
Is it dead code?
Is evidence simply insufficient right now?
```

Only classify after investigating. Never write a new registry entry just because a class name
looks important (the identity rule again — file structure and naming similarity are not identity
evidence, per `mechanism_identity_and_change_taxonomy.md` §1's `attributes_biology`
non-split precedent).

## 9. Strange emergent outcomes are not automatically bugs

```
powerful ruler loses territory
famous person becomes forgotten
a settlement collapses despite a growth trend
a weak actor defeats a stronger one through circumstance
```

Check: does the causal chain that produced this exist and is it valid? Does any REQUIRED Rule
fail? If the chain is valid and no REQUIRED Rule is violated, this is **not a bug**, however
unusual the narrative reads. The simulation judges causal validity, not narrative desirability —
this is one of the primary reasons the World Rule Catalog exists at all.

The inverse also holds: `NPC reacts to information with no valid perception/report/knowledge
path` can execute perfectly at every mechanism level and still be a real semantic violation
(a Knowledge/Reach Rule conflict) — find the **earliest invalid causal edge**, not the final
visible reaction.

## 10. "Why did X happen" / "why did X not happen" are first-class debug queries

For a decision: trace knowledge/belief → motivation → relationship → capability/opportunity →
authority/constraints → selected action, and explicitly distinguish **world truth** from **what
the acting subject knew**.

For a non-event (*"why didn't faction A retaliate?"*): trace the expected chain and report the
**first missing transition**, not just "retaliation didn't happen":

```
harm occurred                    ✓
faction learned about it         ✗   ← report this, not "no retaliation"
standing changed                 ?
retaliation opportunity generated ?
decision selected                ?
capability/reach allowed it      ?
```

## 11. Cross-domain regression — no single mechanism is locally broken

Example: an economy change silently removes equipment acquisition, which silently changes combat
capability distribution — every individual mechanism verifies clean in isolation. This is
`CAUSAL_CHAIN_DEBUG`: trace producer → committed state → propagation → consumer → downstream
consequence across the composition, using integration scenarios and the Rule↔Mechanism mapping,
not mechanism-local verification alone.

## 12. Deletion is first-class, not an afterthought

Before retiring a mechanism, query impact:

```
Rules realized/constrained by it
systems containing it
mechanisms that depend_on it
scenario coverage
implementation bindings
```

A `RETIRE` must never silently leave a `REQUIRED` Rule with zero realization — if it would, that
has to surface as a finding before the retirement lands, not be discovered later as a regression.

## 13. Rule changes are rare and controlled after freeze

If implementation work discovers that desired behavior contradicts a frozen Rule, do not silently
implement around it. Raise a semantic-change proposal → impact analysis → explicit decision →
Rule revision → update affected mapping/scenarios. Frozen means *controlled* change, not
*impossible* change — implementation convenience never silently redefines a Rule.

## 14. Completion output — reuse existing homes, never a new orphan artifact

Per the Mechanism Registry's own governing constraint ("no orphan document data" —
`mechanism_claims_as_tests_initiative.md` §1): do not create a new permanent document for every
task. For meaningful RPG-core work, record the structured summary below inside the ticket's
existing `## Implementation Notes` / `## Completion Summary` sections, or as ephemeral agent
output for smaller tasks — never a standalone file nothing else reads:

```
Task classification:        (§2)
Affected Rules:
Affected mechanisms:
Affected state ownership:

Finding:
First failed rung (§4):

Change performed:
Registry impact:
Rule↔Mechanism mapping impact:

Verification performed:     (source / runtime / semantic / balance, as applicable)
Remaining uncertainty:
```

Do not force this for trivial edits — proportional to whether the task touches simulation
semantics or mechanism behavior at all.

## Related

- [architecture.md](architecture.md) — the data model this workflow operates against.
- [rollout_plan.md](rollout_plan.md) — where drift detection for these claims gets built, and when.
- `docs/plans/mechanism_identity_and_change_taxonomy.md` — the identity rule and 8-kind taxonomy
  this document reuses verbatim.
- `docs/plans/mechanism_claims_as_tests_initiative.md` — the full search/attribution failure
  catalogue behind §4's evidence-strength table.
