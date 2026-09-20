---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, documentation, schema]
---

# Plan — Mechanism Identity Rule and Change Taxonomy

**Status, scoped 2026-09-17.** `TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY`'s own
deliverable. The registry holds 89 mechanisms and, until now, no stated rule for what one mechanism
*is* — granularity was inherited twice over (71 entries from atlas cards, 11 from directory
structure) with no criterion anyone applied deliberately. This doc states that rule, tests it
against the registry's own bundled entries, and records the seven-kind taxonomy for what a design
proposal does to a mechanism once one exists. Sibling to `docs/plans/mechanism_registry_initiative.md`
(the substrate), `docs/plans/mechanism_claims_as_tests_initiative.md` (the checking layer), and
`docs/plans/mechanism_tier_model_initiative.md` (the structure above this tier) — this one is the
identity layer underneath all three.

---

## 1. The identity rule

> A mechanism is the smallest unit that is both **(a)** intended as a capability by someone, and
> **(b)** able to independently succeed or fail.

Both clauses are load-bearing. Intent alone yields atlas cards, which bundle whatever the author
thought deserved one card. Independent failure alone yields every function in the codebase.

**Operational test: if the two (or more) halves of a bundled name could sit in different `state`
values, they are two mechanisms, not one.** This is self-justifying for this registry — recording
whether things work is its whole purpose, so anything requiring two different answers to "does it
work" requires two rows.

It reproduces both splits this project already made by instinct during Foundation
(`aging_death`/`succession`, `xp_leveling`/`breakthrough_bonuses`) — each split happened precisely
because one half was `done` and the other `orphan`, the exact shape the operational test targets.

**What the rule does not do**: it does not require uniform granularity. A bundled name stays one
mechanism if its parts share one code path and cannot independently diverge in `state` — forcing a
split there would manufacture a distinction the code doesn't have, the same failure shape as
inventing a "primary symbol" for a file whose classes are genuinely one concept
(`implemented_by`'s own file-level-binding precedent, `docs/plans/mechanism_registry_initiative.md`).

### Multiple entry points are not, by themselves, a split signal

`combat_resolution` is reached by two structurally different callers at wildly different real
volumes — `tactical_decision` (0–2 calls per 1000–2000 ticks across three corpus worlds) and
`movement`'s own opportunity-attack mechanic (181–2177 calls in the same worlds; see
`TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`'s own 2026-09-17 addendum). Both callers
invoke the *identical* resolution logic (`CombatResolutionSystem.resolve_attack()` and
`resolve_multi_attack()` compute the same damage/death outcome), so there is no `state` divergence
the operational test can find — `combat_resolution` cannot be `done` when reached from `movement`
and `gap` when reached from `tactical_decision`, because it is the same code either way.

**Verdict: KEEP.** A mechanism's identity tracks its own internal correctness/completeness, not the
diversity or evenness of its callers. The real fact worth recording here — that one caller
overwhelmingly dominates real traffic — is a fact about the *callers*
(`tactical_decision`'s own `state: done`/`verified.verdict: contradicted`, recorded 2026-09-17;
its own ATTACK-intent branch is the thing that's actually dormant), not about `combat_resolution`
itself. Recording it again on the callee would duplicate information the caller's own registry
entry already carries, not add anything.

---

## 2. The change taxonomy

What a design proposal does to the registry once a mechanism exists, or is proposed. Seven kinds,
each with a predictable, checkable consequence:

| Kind | Registry effect |
|---|---|
| **Introduce** | new entry |
| **Extend** | same entry, may move `partial` → `done` |
| **Wire** | state change only (`orphan`/`gated` → `done`), no new logic |
| **Tune** | **no registry change** — values are not in the registry |
| **Split** | one entry becomes two, because the halves diverged |
| **Merge** | two entries become one, because they never independently diverge |
| **Retire** | entry → `gap`, plus a verdict recording why |
| **Interpose** | an **edge** change: `A → B` becomes `A → C → B` |

**`Wire` versus `Introduce` is the distinction that matters most historically.** Most of the
dormant-mechanism arc this registry epic ran was wiring — the code already existed and was
correct, and only the recorded state changed. Describing that as "implementing a feature" is how
documents came to claim things worked when only their own registry entry was stale
(`motivation_doctrine`'s own eight-day "confirmed live" claim after its code was deleted is the
standing cautionary example).

**`Interpose` is the only kind that changes graph structure rather than node content** — one edge
removed, two added, when an existing dependency is judged inefficient and a new mechanism is placed
between the two ends. It is `Introduce` plus a declared edge rewrite, and it needs naming
separately because `depends_on` — the graph itself — is the thing being restructured, not a single
node's own fields.

**`Merge` is `Split` read backwards, and until 2026-09-19 it had never been exercised.** §1's
operational test is symmetric by construction — "if the halves could sit in different `state`
values, they are two mechanisms" implies its converse, "if two declared ids share one
implementation and cannot independently succeed or fail, they are one mechanism" — but every real
case checked against this rule so far (§4, §6) tested the split direction: one bundled name, does
it need to become two. `commitment_betrayal`/`commitment_pressure_consequences` (found while
resolving `TCK-20260918-MECHANISM-UNCLASSIFIABLE-DEPENDS-ON-EDGES-RESOLUTION`'s own edges #7/#17)
is the first candidate for the reverse: `commitment_betrayal` has no implementation distinct from
`commitment_pressure_consequences`'s own bound files (`src/domains/commitment/*.py`) — checked
directly, not assumed. Flagged as a candidate here rather than performed: an actual merge changes
which id every referencing ticket/doc/`depends_on` edge should cite, a bigger blast radius than a
split's own "add one row" operation, and deserves its own investigation rather than a same-turn
registry edit. A wrong answer here is exactly as informative as `action_pacing_readiness` splitting
was for the forward direction — this is the rule's first real test of whether it holds symmetrically
or only in the direction it was originally validated on.

**Resolved 2026-09-20, NOT a merge** (`TCK-20260920-MECHANISM-ENTITY-LAYER-UNBOUND-CLAIMS-
RESOLUTION`): the premise above was itself wrong, not just unconfirmed. The original search that
produced "no implementation distinct from `commitment_pressure_consequences`" only covered
`src/domains/commitment/` — it never looked in `src/core/models/social.py`, where a real,
purpose-built `BetrayalRecord` (`contract_id`/`betrayer_id`/`victim_id`/`severity`/`tick`) exists
for exactly this concept. It has zero real constructors anywhere (`grep -rn "BetrayalRecord("
src/` finds none), so it is a real, present, unused type — `commitment_betrayal`'s own state moved
`done` → `orphan`, bound to this type, not merged into its sibling. This is the rule's first real
test of the reverse direction turning out negative: the two ids were never actually the same
mechanism, a search gap made them look that way. The general lesson generalizes past this one
case: **before concluding "no distinct implementation" for a merge candidate, search beyond the
directory the sibling's own binding lives in** — a namespace-adjacent-looking module
(`src/domains/commitment/`) crowded out a real hit sitting in an unrelated one
(`src/core/models/`).

---

## 3. `depends_on`'s own semantics — already defined, found violated once, corrected

Peer review raised this as an open question while resolving `TCK-20260915-CROSS-FACTION-COMBAT-
RARITY-INVESTIGATION`: two already-declared edges on `combat_resolution` (`movement`,
`tactical_decision`) don't obviously satisfy a "requires to exist" reading, and derived priority is
computed from these same edges — so if some declared dependencies are really execution-flow, the
"what to fix next" ranking measures something other than real blast radius.

**The definition was not missing — it was already stated precisely, and one edge violated it
without being caught.** `registries/mechanisms.yaml`'s own header (added by
`TCK-20260916-MECHANISM-DEPENDENCY-GRAPH-POPULATION`) declares three deliberately distinct axes and
warns against conflating them:

1. **Containment** ("Faction contains Entities") — not represented at all.
2. **Execution order** (wiring-map sequence arrows within one tick) — also not `depends_on`, and
   explicitly why `depends_on` stays sparse (~25 of 75 rows at the time) rather than populated from
   every visible arrow.
3. **Functional dependency** (`depends_on` itself) — *"this mechanism cannot produce a meaningful
   result without that one already existing/having run."* Hand-authored only for a defensible
   "consumes this mechanism's output/state" reading — explicitly not "converted from a wiring-map
   sequence arrow just because one exists."

Applying that stated test — not a new one — to the two contested edges:

- **`combat_resolution` depends_on `movement`: satisfies the definition. KEEP.**
  `CombatResolutionSystem`'s own resolution logic reads position/range data
  (`entity.navigation.position`, adjacency/range checks) that `movement`'s own domain establishes
  and maintains — combat resolution cannot produce a meaningful result without that state already
  existing, independent of which module's code happens to *call* the other. Call direction and
  `depends_on` direction diverge here (`movement.py` calls `resolve_multi_attack()`, not the
  reverse) precisely because `depends_on` was never meant to encode a call graph — it encodes what
  a mechanism's own output presupposes already existing, per the header's own axis 3 versus axis 2
  distinction above. This is the concrete case that shows the two can legitimately point in
  different directions, recorded here so it doesn't read as an error the next time someone traces
  the graph against the call graph and finds them mismatched.
- **`combat_resolution` depends_on `tactical_decision`: does not satisfy the definition. Removed.**
  `resolve_attack()`/`resolve_multi_attack()` take an attacker and a defender directly and compute
  a real, meaningful damage/death outcome regardless of how that pairing was decided — by
  `tactical_decision`, by a scripted/opportunity trigger, or by any other producer. Combat
  resolution does not require `tactical_decision`'s own output to "already exist/have run" for its
  own result to be meaningful; `tactical_decision` is a real *caller* of `combat_resolution`
  (execution order, axis 2), not a functional prerequisite for it (axis 3) — exactly the
  conflation the header's own closing line warns against ("do not convert a wiring-map sequence
  arrow into `depends_on` just because one exists"). Removed from `combat_resolution`'s own
  `depends_on` list; see the registry diff for this ticket.

**Consequence for derived priority, recorded rather than left implicit**: removing this edge
reduces `tactical_decision`'s own transitive-dependent count by one, lowering its derived priority
slightly. This is the *correct* direction given today's own separate finding
(`tactical_decision`'s state stays `done` but its `verified.verdict` is `contradicted` — its
ATTACK-intent branch is effectively dormant in real corpus play) — a mechanism found to be doing
little real work should not also be artificially propping up its own priority ranking via an edge
that was never a real functional dependency to begin with.

**Scope of this correction, stated plainly**: this fixes the one specific edge the open question
named, verified against the registry's own already-stated definition. It is not a full re-audit of
all 65 declared edges under this same lens — that is real, separate work (a natural follow-up, not
picked up here) and should be scoped as its own ticket if the same conflation is suspected
elsewhere, rather than expanded into this one unboundedly.

---

## 4. The bundled entries, tested against the rule

Applied §1's operational test to the seven bundled entries named in the identity-rules ticket's own
Scope §3, each investigated directly against real code (not assumed from the name, and not taken
on an unverified report — one investigation pass here initially returned an unevidenced "split
everything" claim and was independently re-checked before being trusted, per this arc's own
standing discipline).

**The test applied consistently: split only on a *found* state divergence, not merely structural
separability.** An early draft of this table split `attributes_biology` on the grounds that
`AttributeComponent` and `BiologicalComponent` are separate dataclasses with separate consumers —
true, but no actual divergence was ever found (both are fully wired, no orphan half). Reversed to
KEEP once checked properly: this matches the precedent splits (`aging_death`/`succession`,
`xp_leveling`/`breakthrough_bonuses`), each of which happened because a real, checked divergence
was *found*, not because two halves were merely separable in principle. Every SPLIT verdict below
is backed by a real, checked divergence — usually an already-filed, separately-investigated ticket
proving one half has a materially different state than the other.

| Mechanism | Verdict | Evidence |
|---|---|---|
| `inventory_trade_conservation` | **KEEP** | One unified enforcement mechanism (`ResourceTransactionResolver`/`ResourceTransactionSystem`, `src/core/conservation.py` + `src/engine/economy.py`) applied identically across every `ResourceTransferIntent` regardless of source (trade, harvest, craft, combat reward). Multi-word descriptive name, single code path, no seam where one clause could diverge in `state` from another. |
| `cognition_capacity_fatigue` | **KEEP** | `src/strategy/cognition_capacity.py::CapacityService.derive_profile()` computes bandwidth limits and applies the fatigue multiplier in the same function, returning one `CognitionProfile`, enforced downstream as one derive-then-enforce pipeline — not two independently-failable mechanisms. |
| `information_trust_deception` | **KEEP** | Checked repo-wide for a separate "deception" implementation: zero matches for `deception`/`deceptive`/`Deceit` anywhere in `src/domains/information/` (the one repo-wide match, `combat_engagement/power.py`, is a wholly unrelated apparent-power mechanic). `SourceTrustUpdateService` (`src/domains/information/trust.py`) *is* the mechanism; "deception" is descriptive flavor for what trust-scoring is for, not a second implemented capability. |
| `attributes_biology` | **KEEP** | `AttributeComponent`/`BiologicalComponent` (`src/core/state.py`) are separate dataclasses, but both are fully wired with no found divergence: biological pressures feed `engine/combat.py` (sleep_debt combat penalty), `engine/apply.py` (accrual/damage), `strategy/cognition_capacity.py`, town recovery (`town/inn.py`, `town/home.py`); attributes feed the separately-registered `derived_stats`. Structural separability alone, with no found divergence, does not warrant a split — see the note above. |
| `regional_trauma_hazards_sovereignty` | **SPLIT** → `regional_trauma` + `regional_sovereignty` | `region.trauma_score` (accumulation/decay, `src/world/consequences.py` + readers in `camp.py`/`boss.py`/`creature_territory.py`/`threat.py`) has a real, still-open divergent finding (`TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES`) distinct from ownership/topology tracking. `hazard_level` is not split out separately — checked directly (`worldbuilding/compiler.py`, `worldgeneration/generator.py`): it is static, world-compile-time-authored content with no dynamic producer of its own, folded into `regional_sovereignty`. |
| `buildings_town_services` | **SPLIT** → `buildings` + `town_services` | `building_sabotage` (a real dependent) reads/writes only `building.hp`/`BuildingUpdate` (`src/engine/sabotage.py`) — confirms it needs physical structures specifically, never a service transaction, a real functional seam. Within `town_services`, Church's own `BLESSING`/`RESURRECTION` services are separately confirmed dead (`TCK-20260907-CHURCH-CONTENT-AUTHORING`, closed — data-label strings with zero real code reading them, `CHURCH` not placed in any world module) while Inn/Guild/Shop/Blacksmith are live; flagged in `town_services`'s own registry note rather than split further, since no real dependent needs Church's services specifically. |
| `calamities_boss_spawns` | **SPLIT** → `calamity_intensity` + `world_boss_spawn` | Two separate classes/files: `CalamityService` (`src/world/calamity.py`) and `BossService` (`src/world/boss.py`). `calamity_intensity`'s own producer has a real, still-open defect (`TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES` — never left `0.0` in a real 5000-tick run) while `world_boss_spawn` was fixed and proven end-to-end (`TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY`, closed) — a real, already-established divergence bundled under one `done` row. |

### A correction found as a side effect of the `regional_sovereignty` split

Binding `regional_sovereignty`'s own `implemented_by` to the class whose name matched
("`RegionalSovereigntyService`") without checking its callers would have repeated exactly the
mistake this registry epic exists to catch. Direct check: `RegionalSovereigntyService`
(`src/world/regional_sovereignty.py`, regional taxation + macroscopic conquest debuffs) has **zero
real callers anywhere in `src/`** — a genuine orphan. The real, live ownership-tracking mechanism —
already investigated at length in the atlas's own card for this entry ("the sovereignty mechanism
described above is real and live exactly as documented") — is `FactionInfluenceService`
(`src/world/influence.py`), with three real callers. `regional_sovereignty`'s own `implemented_by`
and `verified` block are corrected to cite `FactionInfluenceService`; `RegionalSovereigntyService`'s
own orphan status is flagged in that same entry's note rather than filed as its own ticket here, to
keep this ticket's own scope bounded — worth a follow-up investigation, same shape as `camp`'s or
`motivation_doctrine`'s own orphan findings.

### `action_pacing_readiness` — the falsification test, and it splits

Per the identity-rules ticket's own Assumption #1: *"If the rule does not split this, the rule is
wrong."* `action_pacing_readiness` is one entry at `partial`, carrying a single `verified` block
that covers two things with **different, already-measured states**:

- **The readiness gate** (`src/engine/legality.py::LegalityServiceV2.verify_readiness`) —
  runtime-verified, `done`. A real Kernel-tick differential scenario
  (`tests/mechanic_scenarios/test_action_pacing_readiness_gate.py`) confirms it withholds an
  under-threshold attack and lets a threshold-met attack proceed. All 7 direct (25 transitive,
  pre-split) dependents actually need this half specifically.
- **The agility-scaling half** (`readiness_speed`, `TCK-20260831-READINESS-SPEED-FORMULA`) —
  formula exists and is unit-tested, but its only live application path
  (`engine/apply.py`'s `stats_dirty` recalculation) was directly measured (three real corpus
  worlds, 1000 ticks each) to never fire for any of 75 tested entities, later root-caused
  (2026-09-17) as content-composition/pacing starvation, not a wiring defect — but starvation is
  still a materially different real-world outcome than the gate's own confirmed-working state.

Under the operational test, this is exactly two mechanisms sharing one row: a verified `done` gate
and a starved half whose own real-world firing rate is a fact the current single row cannot state
without burying it in prose. **Split, performed below.**

---

## 5. The `action_pacing_readiness` split, performed

- `action_pacing_readiness` — kept as the id, now scoped to the readiness gate only. `state: done`
  (moved from `partial`, since the gate itself has no known deficiency). `verified` block kept,
  trimmed to describe only the gate's own scenario result.
- `readiness_speed_scaling` (new id) — the agility-derived `readiness_speed` recalculation.
  `state: partial`. Carries the corpus-pacing `verified` block (instrument: scenario+corpus_run,
  verdict: contradicted) that previously lived on the combined entry.
- **Dependents**: the pre-split 23 transitive dependents of `action_pacing_readiness` depended on
  the *gate*, not the scaling formula — re-pointed at `action_pacing_readiness` unchanged (no
  dependent actually needed `readiness_speed_scaling` to exist; none are re-pointed there).
  `readiness_speed_scaling` itself declares `depends_on: [action_pacing_readiness]` — the scaling
  recalculation is only meaningful once the gate's own readiness accounting exists.
- Consumer artifacts (atlas badge, capabilities tier) updated to reflect the split — see the
  registry diff and generated-view regeneration for this ticket.

---

## 6. The three §4 splits, performed

- **`regional_trauma_hazards_sovereignty` → `regional_trauma` (state `done`, `verified.verdict`
  `contradicted` — real accumulation code, defeated by the Lair region's own real-world data,
  camp-family) + `regional_sovereignty` (state `done`, `implemented_by` corrected to
  `FactionInfluenceService` per §4's own side-finding).** Dependents re-pointed with real evidence
  where found — `camp` → `regional_trauma` (`camp.py` reads `region.trauma_score` directly),
  `city` → `regional_sovereignty` (ownership/territorial concept). Kept pointing at **both**
  successors, conservatively, where no direct evidence distinguished which half was needed:
  `demographic_cohort_cycle`, `ruins_mines_battlefields` — not guessed narrower without real
  evidence, per this same ticket's own discipline.
- **`buildings_town_services` → `buildings` (state `done`) + `town_services` (state `done`, Church's
  own dead `BLESSING`/`RESURRECTION` sub-facet flagged in its note).** `building_sabotage`
  re-pointed to `buildings` specifically (confirmed via direct code read, §4).
- **`calamities_boss_spawns` → `calamity_intensity` (state `done`, `verified.verdict` `contradicted`,
  depends_on `regional_sovereignty` for `hazard_level`) + `world_boss_spawn` (state `done`,
  `verified.verdict` `observed`, depends_on `regional_trauma` for `trauma_score`).** No dependents
  to re-point (zero prior dependents on the combined entry).
- **Consumer artifacts**: each split card's own single existing atlas/capabilities badge was
  repointed at whichever successor id its own prose actually describes (`mechanism_atlas_card_mapping.py`,
  `mechanism_capabilities_card_mapping.py`) rather than left stale or arbitrarily assigned — see §4's
  own evidence per split. The other half of each split has no atlas/capabilities citation, the same
  state every other code-enumeration-found mechanism in this registry already carries.
- **Flagged, not resolved**: whether the existing `lair` mechanism (`state: gap`, "not yet built")
  is consistent with `boss.py::check_for_lair_spawn()` being real, fixed, and unit-tested code (per
  `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY`) is a genuine open question this ticket
  does not resolve — `lair`'s own gap classification may refer to the Lair place-kind never being
  composed into any world (a different, real, separate blocker) rather than the occupant-spawn code
  itself being unbuilt. Worth its own follow-up investigation.

---

## 7. `implemented_by` binding granularity — method-level, when to reach for it

Symbol-level binding (`path::Class`, `TCK-20260916-MECHANISM-IMPLEMENTED-BY-SYMBOL-LEVEL-BINDING`)
already separates "this whole file is the binding" from "one specific class/function in this file
is the binding." It stops being precise enough exactly when **one class implements more than one
registry mechanism through different methods** — binding at class level then would misattribute
one mechanism's logic to the other's entry, the same failure shape as §3.2's `trauma` incident, just
from imprecision rather than a wrong guess.

**Decision (`TCK-20260920-MECHANISM-ENTITY-LAYER-UNBOUND-CLAIMS-RESOLUTION`), settling the question
`TCK-20260917-MECHANISM-IMPLEMENTED-BY-COVERAGE-EXTENSION` left open ("leaning toward not building
it for two mechanisms alone, but not deciding that unilaterally"): build it.** The two-mechanism
case that ticket declined to act on has since recurred and grown — by this batch, 4 real mechanisms
across 2 classes needed it (`xp_leveling`/`skill_unlocks` on `LevelingService`;
`goal_hierarchy`/`strategic_intelligence_core` on `StrategicIntelligenceSystem`) — crossing the bar
the earlier ticket declined to cross for just two. `implemented_by` now accepts a third
`::`-delimited segment, `path::Class::method`, validated against the method's real definition
inside that class's own body (bounded by the next top-level class/def, so a same-named method on a
different class can't produce a false match — see `registry.py::_method_defined_in_class`). This
is a validator capability extension, not a schema change: `implemented_by` is still a plain list of
strings.

**When to reach for each level:**
- **File-level** (bare path): the file's own symbols are all genuinely one concept (no unrelated
  logic sharing the file).
- **Symbol-level** (`path::Class`): the file mixes unrelated top-level symbols, but the one this
  mechanism needs is a whole class/function to itself.
- **Method-level** (`path::Class::method`): even the *class* is multi-concern — it implements more
  than one registry mechanism via different methods (or a mechanism's own concern is genuinely one
  method's worth of logic within a larger class). A mechanism whose real code lives on a large,
  multi-concern class but whose own distinct concern spans *several* of that class's methods (not
  one) can list multiple `path::Class::method` entries — `implemented_by` is already a list; nothing
  about method-level binding requires exactly one entry per mechanism (`goal_hierarchy`'s own
  binding uses 5).
- **Leave unbound, with a note** when a class is multi-concern and it isn't yet clear which
  specific method(s) belong to which mechanism — guessing here is exactly the `trauma` misattribution
  risk one level finer; state the ambiguity instead of forcing a pick.

---

## Related

- `docs/plans/mechanism_registry_initiative.md` — the substrate this defines identity for
- `docs/plans/mechanism_claims_as_tests_initiative.md` — the checking layer built on top of stable
  identities
- `docs/plans/mechanism_tier_model_initiative.md` — the structure above this tier (axis, system)
- `TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY` — this doc's own governing ticket
- `TCK-20260917-MECHANISM-THREE-TIER-AXIS-SYSTEM-MECHANISM` — blocked on this doc landing
