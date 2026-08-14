# Investigation — TCK-20260703-SIMQ-UPLIFT3-DUAL-GATE-AUDIT

## Verdict (up front)

**ECONOMY does NOT share the FACTION/INFORMATION "compiler never constructs the field" bug
class.** Every `AuthoritativeState` field ECONOMY's emission path touches
(`resource_nodes`, `buildings`, `entities`/`navigation.region_id`, `global_resources`) is
constructed with real, spec-derived, non-default values inside
`WorldCompiler.compile()`'s single `AuthoritativeState(...)` call
(`src/worldbuilding/compiler.py:455-470`). `EconomyScorer` itself never reads
`AuthoritativeState` at all — it is 100% event-driven off per-tick `intent_results`
(`src/observability/event_extractor.py:311-372`), which are a *behavioral* output of the
entity-routing pipeline, not a compile-time bootstrap artifact. The existing "duration/content,
not compiler bug" diagnosis in `docs/audits/D20_simq_integration.md` and
`docs/plans/audit_fix_plan.md` is reconfirmed, with fresh, field-by-field evidence, not
just re-asserted.

**SOCIAL's non-`urban_political` C grades are confirmed to be purely `ENABLE_SOCIAL_COOPERATION`
feature-flag gating, with no hidden compiler-seeding gap underneath** — same rigor applied,
same conclusion as the ticket's prior framing, now with direct evidence (1657
`cooperation_event` hits observed once the flag is flipped ON, proving no closed-loop bootstrap
problem exists, unlike the FACTION case).

No follow-up ticket is recommended for either pillar from this investigation.

---

## Current Behavior (file:line refs per field)

### Step 0 — What does `EconomyScorer` actually read?

`src/simulation_quality/scorers/economy.py:41-140` — `EconomyScorer.score()` takes only two
arguments: `envelope: ObservabilityEventEnvelope` and `context: ScoringContext`. It reads
`envelope.event_type`, `envelope.tick`, `envelope.payload`, `envelope.entity_id`, and
`context.window_tag_counts[PillarId.ECONOMY]` — **no `AuthoritativeState` reference anywhere
in the file.** This is the first and most important finding: unlike the ticket's Scope item 1
framing ("enumerate every `AuthoritativeState`/event field ECONOMY's scorer reads... e.g. trade
ledgers, shop transaction records, resource conservation counters, Gini coefficient inputs"),
**no such fields exist on `AuthoritativeState` and none are read by the scorer.** Grepped
`src/core/state.py` for `trade_ledger`, `shop_transaction`, `gini`, `conservation` — zero hits.
The ticket's own examples describe a state shape that was never built; this is a fact to correct
in the ticket record, not a gap to fix.

So the correct object of investigation is **the 11 event types** `EconomyScorer` is registered
for (`EVENT_TYPES` tuple, `economy.py:18-31`): `resource_harvested`, `item_crafted`,
`trade_executed`, `shop_transaction`, `gold_transferred`, `resource_node_depleted`,
`gold_sink_fired`, `conservation_law_verified`, `conservation_law_violated`,
`paid_info_transaction`, `quest_reward_dispensed` — and the `AuthoritativeState` fields their
*emitters* (not the scorer) depend on.

### Field 1 — `resource_harvested` / `item_crafted` / `trade_executed` / `shop_transaction` / `quest_reward_dispensed` / `gold_sink_fired` / `paid_info_transaction`: all emitted from `intent_results`

`src/observability/event_extractor.py:311-372` — these seven event types are all derived from
`e_upd_ext.intent_results` (a **per-tick behavioral output**, not durable compile-time state),
classified by `ir.source_kind` (`NODE`, `CRAFTING`, `SHOP_BUY`/`SHOP_SELL`, `QUEST`,
`REPAIR_FEE`/`SERVICE_FEE`/`TAX`, `INFORMATION_PURCHASE`). `intent_results` is populated each
tick by the unconditional (no feature-flag gate) engine phases in
`src/engine/pipeline.py:164-299`: `blacksmith` (line 164), `town_resolution` (268), `gold_sink`
(273), `quest_rewards` (292), `shop` (293), `paid_information` (297),
`resource_transactions` (299). None of these phases are gated by `run_phase(..., "FLAG_NAME")`
the way `adventure_decision` (line 228-236, `ENABLE_ADVENTURE_ROUTING`) or `cooperation`
(line 158, `ENABLE_SOCIAL_COOPERATION`) are — **ECONOMY's engine phases always run.**

What they require to produce *accepted* intents is entities physically reaching
resource nodes / buildings and the town/behavior systems choosing to act
(`src/engine/town_resolution.py:64-90`: entities must be at a `town_tiles`/`building_tiles`
position with a routed `task` before any GATHER/REST/EAT action resolves). This is the classic
"takes travel + behavior time" ramp, not a permanently-blocked gate.

Compiler seeding check (`src/worldbuilding/compiler.py`):

- `resource_nodes: Dict[int, ResourceNodeState]` — constructed at **compiler.py:203-228** from
  `spec.resources`, with real RNG-placed `(x, y)` inside the target region's bounds,
  `remaining_charges=res_spec.count`, `regen_rate_per_tick=res_spec.regen_rate`. **Passed into
  the `AuthoritativeState(...)` call as `resource_nodes=resource_nodes` at compiler.py:459.**
  Not a silent default — genuinely populated when `spec.resources` is non-empty for the world.
- `buildings: Dict[int, BuildingState]` — constructed at **compiler.py:230-257** from
  `spec.buildings`, real placement, `functional=True`. **Passed as `buildings=buildings` at
  compiler.py:460.**
- `entities: Dict[int, EntityState]`, each with `.navigation(region_id=region_id)` set to the
  **real** `pop_spec.spawn_region` value (compiler.py:329) — not `None`. (This directly refutes
  the ECONOMY contract doc's own stale traceability note at
  `docs/simulation_quality/quality_scoring_contract.md:700` — "D04 found all None after
  compile" — that finding is **no longer true of the current compiler code**; either it was
  fixed since D04 or D04's finding applied to a since-patched code path. Either way, the present
  `compiler.py:329` unconditionally sets a real region_id.) **Passed as `entities=entities` at
  compiler.py:458.**
- `global_resources: Dict[str, float]` — constructed at **compiler.py:178-195**, seeded with
  per-faction starting gold vaults (`faction_<id>_gold`). **Passed as
  `global_resources=global_resources` at compiler.py:463.** No economy-specific counter
  (conservation totals, Gini inputs) exists on `AuthoritativeState` for this to omit — see
  Field 4 below.

**Verdict: all four backing fields are compiler-seeded correctly, with real content, not
silent defaults.** The FACTION/INFORMATION bug class requires a keyword argument to be *absent
from the constructor call entirely*; that is not the case for any of `resource_nodes`,
`buildings`, `entities`, or `global_resources`. These are the same four fields that were also
constructed correctly, unchanged, throughout the FACTION and INFORMATION investigations (both
of those investigations only found `factions=`/`information_source_profiles=`/
`pending_information_responses=` missing — never touched or found fault with these four).

### Field 2 — `gold_transferred`: translation-table event, not intent_results

`docs/simulation_quality/event_type_coverage.md:135` — `gold_transaction` →
(`_TRANSLATE_SIMPLE`) → `gold_transferred` → `EconomyScorer`. This is a direct engine-emitted
event (gold delta on an entity/faction), translated by `QualityHub._translate()`. It depends on
any system moving gold (shop, gold_sink, quest_rewards) actually firing — same duration/content
dependency as Field 1, no separate compiler-seeding gap.

### Field 3 — `resource_node_depleted`: state diff on `resource_nodes`

`docs/simulation_quality/event_type_coverage.md:109` — fires when
`ResourceNodeState.remaining_charges` drops to 0 (`event_extractor.py`, state-diff based). Reads
the same `state.resource_nodes` dict confirmed compiler-seeded in Field 1. No separate gap.

### Field 4 — `conservation_law_verified` / `conservation_law_violated`

`docs/simulation_quality/event_type_coverage.md:74,157` — `conservation_law_verified` fires on
a `tick % 50` guard plus "economy events present" in the current tick
(`TCK-20260701-SIMQ-EMIT-FACTION-ECONOMY`); `conservation_law_violated` fires from an
`InvariantViolation` whose `law_id` starts with `"CONSERVATION"` — both derived from the
resolution pipeline's per-tick invariant checks (`src/engine/apply.py` /
`hard_law_monitor`-adjacent invariant machinery), not from any dedicated
`AuthoritativeState` ledger field. Confirmed: **no `trade_ledger`/`gini`/`conservation counter`
field exists on `AuthoritativeState`** (grep above) for the compiler to have omitted. This
event type's gate is "did at least one economy event fire in this tick-window" — i.e. it is
downstream of Field 1's duration/content dependency, not an independent gap.

### Calibration evidence that this is duration, not a permanent zero

`docs/audits/D20_simq_integration.md:393-398,405-406` (2026-07-02 multi-seed matrix,
`TCK-20260702-SIMQ-EVAL-MATRIX`): "**ECONOMY activates at 1000t for all seeds (duration effect,
not noise)**" for `urban_political`, and "sandbox_world COGNITION and ECONOMY plateau at B at
2000t" — i.e. given enough ticks, `calibration_hits` for ECONOMY's event types go from 0 to
non-zero and the grade moves C→B, in the *same* compiled `AuthoritativeState`, with *no code or
compiler change*, purely from letting the run continue. This is the direct empirical signature
of a duration/content gap, and it is the opposite signature of the FACTION/INFORMATION bug
(which stayed at exactly 0 forever, in every run, at every tick count, until the compiler fix
shipped — see `docs/simulation_quality/event_type_coverage.md:63` "Prior to the kernel fix, this
measured 0 despite the seed/assimilation mechanism working correctly" language, contrasted with
ECONOMY's monotonic-with-time improvement).

---

## Verdict Table

| Field / dependency | Read by | Compiler constructor call (compiler.py:455-470) | Verdict |
|---|---|---|---|
| `resource_nodes` | Field 1 emitters (`resource_harvested`, `resource_node_depleted`) via `town_resolution`/`resource_transactions` phases | `resource_nodes=resource_nodes` (real, from `spec.resources`, compiler.py:203-228,459) | **compiler-seeded correctly** |
| `buildings` | Field 1 emitters (`shop_transaction`, `trade_executed`, `item_crafted` via blacksmith/shop) | `buildings=buildings` (real, from `spec.buildings`, compiler.py:230-257,460) | **compiler-seeded correctly** |
| `entities` / `navigation.region_id` | routing/behavior that must reach a node/building before any economy intent is accepted | `entities=entities`, `.navigation(region_id=region_id)` real value (compiler.py:329,458) | **compiler-seeded correctly** (contract doc's "D04 found all None" note is stale — refuted by current code) |
| `global_resources` | `gold_transferred`, `gold_sink_fired` | `global_resources=global_resources` (real faction gold vaults, compiler.py:178-195,463) | **compiler-seeded correctly** |
| trade ledger / shop transaction record / Gini input / conservation counter (ticket's Scope item 1 examples) | *nothing* — no such field exists on `AuthoritativeState`; `EconomyScorer` never reads `AuthoritativeState` at all | N/A — field does not exist in the schema | **not applicable / ticket's premise is inaccurate**, not a gap |
| `conservation_law_verified`/`violated` gate | tick-cadence + invariant-monitor derived, downstream of Field 1 firing at all | N/A (no dedicated state field) | **genuinely content/duration-driven**, not compiler-seeding |
| Engine phases emitting ECONOMY events (`blacksmith`, `town_resolution`, `gold_sink`, `quest_rewards`, `shop`, `paid_information`, `resource_transactions`) | — | All run unconditionally, no `run_phase(..., "FLAG")` gate (pipeline.py:164-299) | **not feature-flag-gated at all** — rules out a P0-A-style gate as the cause |

**No field matches the FACTION/INFORMATION bug class.** ECONOMY's C ceiling at low tick counts
is fully explained by (a) entities needing travel + behavior time to reach resource nodes and
buildings before any intent is accepted, and (b) `conservation_law_verified`'s own tick-cadence
gate being downstream of (a). Both are genuine duration/content properties of a fresh world,
not compiler omissions.

---

## SOCIAL re-confirmation

The ticket's Out of Scope explicitly excludes re-auditing SOCIAL's `urban_political`-only
activation as "already understood as a feature-flag gate," but instructs confirming this with
the same rigor rather than assuming it. Performed the same checklist:

1. **Flag existence and gate location**: `src/engine/pipeline.py:155-159` —
   `run_phase("cooperation", update, lambda u: CooperationPhase.execute(state, u),
   "ENABLE_SOCIAL_COOPERATION")` — `CooperationPhase` is explicitly feature-flag gated, unlike
   any of ECONOMY's phases.
2. **Compiler-seeding check for SOCIAL's backing state**: `AuthoritativeState.groups: Dict[int,
   GroupRecord]` (`src/core/state.py:1122`) defaults to `field(default_factory=dict)` and is
   **not passed** in `WorldCompiler.compile()`'s constructor call (compiler.py:455-470) — so
   `state.groups` is `{}` at compile time for every world, structurally similar in shape to the
   pre-fix FACTION gap. Contract-relevant social state (`entity.strategic.contracts`) is
   per-entity, not compiler-seeded either — both start empty at tick 0.
3. **Is this a closed-loop bootstrap problem (FACTION's actual failure mode), or does
   `CooperationPhase` create its own first records from scratch?** This is the decisive check:
   FACTION's `compute_transitions()`/`FactionAwarenessService` could only ever *update* existing
   `FactionState` entries (via `existing = new_factions.get(fu.faction_id)` merge pattern,
   `apply.py:335`) — never create the first one from nothing, hence "permanent zero forever
   regardless of flag." SOCIAL is different: **empirical calibration data already exists proving
   `CooperationPhase` creates cooperation events from proximity/personality conditions with
   zero pre-existing `groups`/`contracts` state** —
   `docs/simulation_quality/event_type_coverage.md:65`: `cooperation_event` — **1657 hits** in
   `urban_political_seed42_500t` with `ENABLE_SOCIAL_COOPERATION=ON`
   (`TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO`), and `contract_expired_offer` — 234 hits, same run.
   This is direct proof the mechanism is fully functional once the flag is ON, with **no**
   FACTION-style bootstrap gap underneath — `state.groups={}` and empty
   `entity.strategic.contracts` at compile time are legitimate, harmless starting conditions
   (cooperation/contract creation is a live, in-tick decision, not a "read existing records to
   decide whether to act" closed loop).
4. **Non-`urban_political` worlds staying C**: consistent with the flag defaulting `OFF`
   globally (`src/domains/optimization/feature_flags.py`) and only `urban_political`'s
   calibration runs enabling it explicitly — this is intentional per-world profile scoping
   (§SOCIAL "expected" row, `docs/audits/D20_simq_integration.md:344`), not a bug.

**Confirmed: SOCIAL's C ceiling outside `urban_political` is purely
`ENABLE_SOCIAL_COOPERATION` flag-gating with a functioning, bootstrap-free mechanism
underneath. No hidden compiler-seeding bug found, refuting nothing in the ticket's existing
framing — this re-confirmation adds the missing evidence (the 1657/234-hit calibration data
as proof-of-no-bootstrap-gap) rather than leaving the claim as an unverified assumption.**

---

## Recommended Follow-up

**None.** No bug matching the FACTION/INFORMATION class was found in either ECONOMY or SOCIAL.
No follow-up ticket is recommended from this investigation. The existing diagnoses stand,
now with field-by-field evidence:

- `docs/audits/D20_simq_integration.md` §Finding 1 ("Systemic C ceiling... 100% attributable to
  ... 27 engine emission gaps") — **reconfirmed for ECONOMY specifically**: no engine emission
  gap remains for ECONOMY per `event_type_coverage.md`'s Summary (`engine_emission_gap: 0`);
  the residual C-at-low-tick-count behavior is a duration/content property of the compiled
  world (entities need travel+behavior time), not a missing emitter.
- `docs/plans/audit_fix_plan.md` — the "27 engine emission gaps" claim is about *emission*
  (event types with no engine path at all), already fully closed per
  `event_type_coverage.md:19` (`engine_emission_gap: 0`). ECONOMY's remaining low-tick-count C
  grade is a **separate, already-understood** phenomenon (ramp-up duration), not a re-opening of
  Finding 1.

One small, optional, non-blocking housekeeping item (not a new ticket, just noted for whoever
next touches this doc): `docs/simulation_quality/quality_scoring_contract.md:700`'s
traceability note "Check entity navigation.region_id (D04 found all None after compile)" is
stale against the current `compiler.py:329`, which always sets a real `region_id`. Worth a
one-line doc correction next time that section is edited; not worth a standalone ticket.

---

## Anti-Drift Hazards

- Do not conflate "ECONOMY's scorer reads `AuthoritativeState`" (it does not — it is 100%
  `ObservabilityEventEnvelope`-driven) with "ECONOMY's *emitters* depend on
  `AuthoritativeState`" (they do, indirectly, via `resource_nodes`/`buildings`/`entities`,
  all of which are correctly seeded). The ticket's Scope item 1 phrasing blurs this distinction
  — future work should keep "what the scorer reads" and "what the upstream engine phase reads"
  as separate questions, since Pattern 6 targets the scorer/downstream-state-field relationship,
  not the (much broader, and here irrelevant) engine-phase/state relationship.
- Do not invent a `trade_ledger`/`gini`/`conservation counter` field on `AuthoritativeState` to
  "fix" this investigation's non-finding — no such field is read by any scorer or emitter
  today; adding one with no reader would violate the Durable State Rule (durable state with a
  defined lifecycle requires a reader, not just a writer).
- If a future ticket wants to *accelerate* ECONOMY's C→B transition (a legitimate tuning goal,
  distinct from a bug fix), the correct lever is world content (more resource nodes near town
  tiles, faster travel, worker-role assignment density) or calibration tick-count choice — not
  a compiler constructor-argument fix, since there is no missing constructor argument to add.
- The `docs/simulation_quality/quality_scoring_contract.md:700` stale D04 reference (see
  Recommended Follow-up) should not be read as "there's still a `navigation.region_id=None`
  bug live somewhere" — this investigation directly confirmed the current compiler code path
  always sets a real value. Don't re-derive this as a live bug in a future ticket without first
  re-grepping `compiler.py:329`.
- SOCIAL's `state.groups={}`/empty `contracts` at compile time (found while re-confirming
  SOCIAL) is **not** the same bug class as FACTION's empty `state.factions={}` despite the
  superficial similarity (both are compiler-omitted dict fields). The distinguishing fact is
  whether the phase that would populate them requires *pre-existing* entries to act (FACTION:
  yes, permanently dead) or can create the first entry from a live in-tick condition (SOCIAL/
  cooperation: yes, proven by the 1657-hit calibration run). Do not flag SOCIAL's empty
  `groups=` as a new FACTION-class bug in a future pass without re-deriving this distinction —
  it was already checked here.
