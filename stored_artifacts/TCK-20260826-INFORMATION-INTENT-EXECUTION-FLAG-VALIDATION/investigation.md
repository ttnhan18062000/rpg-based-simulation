---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION
artifact_type: investigation
tags: [feature-flags]
---

# Investigation — TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION

## Method
Per CLAUDE.md's Context Scan, `mcp__knowledge-search__search_docs` (query: "ENABLE_INFORMATION_INTENT_EXECUTION
flag validation information intent execution") was called first and returned
`{"error":"index not found"}` — index unavailable this session (matching the orchestrator's own
prior confirmation this same session, and the same failure mode the SELF-MODEL/COMBAT-ENGAGEMENT
sibling tickets independently hit). The `python3 tools/knowledge_search.py` fallback was already
confirmed down this session too ("knowledge index not found — run make knowledge-index"), and
`make knowledge-index` is out of scope for this ticket, so it was not run. `graphify query
"ENABLE_INFORMATION_INTENT_EXECUTION information_intent_execution"` was re-run directly (47 nodes,
BFS depth=2 from `information_intent_execution.py`) and independently confirmed
`InformationIntentExecutionPhase`, `ActionIntentAdapter`, `ActionIntent`,
`InformationAssimilationService`, `InformationResponseNormalizer`, and the two backing test files
(`test_information_intent_execution_phase.py`, `test_phase5_information_belief_phase.py`) as the
primary code/test targets — consistent with what the direct reads below independently confirm. Both
semantic-search paths being down is disclosed here, not silently worked around.

## Current Behavior

### `InformationBeliefPhase.apply()` (`src/domains/information/phase.py`)
Four branches, all under `ENABLE_BELIEF_ASSIMILATION` gating in the pipeline (the phase itself has
no internal flag check):
- **Branch 2** ("active responses to assimilate", lines 57-84): for actors with a pending
  `InformationResponse`-shaped dict in `pending_responses`, normalizes it
  (`InformationResponseNormalizer`), assimilates it (`InformationAssimilationService`), and writes
  `self_model_bundle_set` + `property_updates` directly. No `ActionIntent` involved.
- **Branch 3** ("unresolved unknowns, route new query", lines 86-108 — "Branch B" per the module's
  own comments and `information_intent_execution.py`'s docstring): if the actor has no active
  response this tick and `actor.self_model.knowledge.unknowns` is non-empty, selects the first
  unknown, routes candidates via `InformationQueryRouter.route()`, and tries
  `InformationIntentResolver.resolve()` on each candidate until one yields a real `ActionIntent`
  (line 98), which is stored raw into `EntityUpdate.intent_results=[result]` (lines 99-106) — **not
  executed here**. This is the exact call site `information_intent_execution.py`'s phase later
  consumes.
- **Branch 4** (observation synthesis via `ObservationBeliefBridge`/`BeliefContradictionService`,
  lines 110-166): for untested leads, synthesizes `claim_failed_search`/`region_danger_seen`
  observation events and merges the resulting `strategic` update into whatever `EntityUpdate` the
  actor already has from branches 2/3 (`entity_updates.get(actor.id)`, `.merge(...)` — not a bare
  assignment, per the module's own comment at lines 110-114). Unrelated to `ActionIntent`/Branch B.

### `InformationIntentExecutionPhase.execute()` (`src/engine/pipeline_phases/information_intent_execution.py:39-72`)
Gives Branch B's raw `ActionIntent` a production call site. For every entity (iterated in
`sorted(update.entity_updates.keys())` order, line 43 — determinism law,
`docs/engine/kernel.md` line 19), filters `ent_upd.intent_results` by
`isinstance(candidate, ActionIntent)` (line 53 — mandatory, per the class docstring lines 30-36,
since `economy.py`/`patches.py` populate the same `intent_results` field with an unrelated
`IntentResult` dataclass), then calls `ActionIntentAdapter.execute()` (line 56) and merges the
returned `Dict[int, EntityUpdate]` back via `existing_upd.merge(action_upd)` (line 67) — the same
pattern `ActionRoutingPhase.route()` uses. Returns the original `update` unchanged (line 70) if
nothing changed, avoiding a spurious `StateUpdate` replace.

### Pipeline wiring (`src/engine/pipeline.py:161-184`)
`ENABLE_SELF_MODEL_COGNITION` gates `self_model` (line 164), `ENABLE_BELIEF_ASSIMILATION` gates
`information_belief` (line 173), and `ENABLE_INFORMATION_INTENT_EXECUTION` gates
`information_intent_execution` (lines 179-183) — three independently-gated phases, in that exact
tick order, immediately before `cooperation` (`ENABLE_SOCIAL_COOPERATION`, line 189). Each is a
separate `run_phase(...)` call with its own flag name — the three flags are structurally
independent gates, not a single combined switch.

### `FeatureFlagManager` (`src/domains/optimization/feature_flags.py`)
`ENABLE_INFORMATION_INTENT_EXECUTION` defaults `FeatureMode.OFF` (line 42), with an inline comment
already citing this exact ticket as the deferred follow-up (lines 38-41). `ENABLE_BELIEF_ASSIMILATION`
(line 37) defaults `FeatureMode.ON` per `DEV-003` — a **different flag gating a different phase**;
they share the `information` domain but are not the same system, confirmed by the phase.py/pipeline.py
reads above: `ENABLE_BELIEF_ASSIMILATION` controls whether Branch B *populates* `intent_results` at
all (as part of `information_belief` running), while `ENABLE_INFORMATION_INTENT_EXECUTION` controls
whether an already-populated `ActionIntent` is *executed*. With `ENABLE_BELIEF_ASSIMILATION` ON and
`ENABLE_INFORMATION_INTENT_EXECUTION` OFF (today's default combination), Branch B's `ActionIntent`
is routed into `intent_results` every tick it fires, but sits inert — confirmed directly by
`test_action_intent_execution_phase_off_by_default_is_a_noop` (see Regression Surface below).

### The distinction from `ENABLE_BELIEF_ASSIMILATION` — confirmed, not assumed
This was this ticket's own first Scope item ("Confirm precisely... what `information_intent_execution`
actually does differently"). Confirmed via the phase.py/pipeline.py reads above:
`ENABLE_BELIEF_ASSIMILATION`'s scope covers all 4 branches of `InformationBeliefPhase` (response
assimilation, query-routing/production of the `ActionIntent`, and observation synthesis);
`ENABLE_INFORMATION_INTENT_EXECUTION`'s scope is narrower — only the execution of the `ActionIntent`
Branch B already produced. Flipping `ENABLE_BELIEF_ASSIMILATION` ON (already done, `DEV-003`) alone
does not activate this ticket's flag or its call site; they must both be ON for the loop to close
(gold deduction + `self_model_bundle_set` fact-assimilation from the query response), confirmed by
`test_action_intent_execution_phase_fires_in_real_tick_pipeline`.

### What it takes for Branch B to actually fire — confirmed, not assumed
Branch B only routes a query when `actor.self_model.knowledge.unknowns` is non-empty
(`phase.py:90`). Grepped `src/` directly for what populates `unknowns[...]`: three producers exist —
`src/cognition/knowledge_model.py:97` (`KnowledgeModelService`, invoked only from
`SelfModelUpdatePhase.run()` Step 1, `self_model_phase.py:103-141`, itself gated by
`ENABLE_SELF_MODEL_COGNITION`, default OFF); `src/domains/information/assimilation.py:65-68`
(`InformationAssimilationService`, re-adds an unknown on contradictory/insufficient responses —
requires an existing response cycle already in flight, not a cold-start producer); and
`src/engine/pipeline_phases/lead_contradiction.py:197` (a `LeadContradictionPhase` producer,
independent of self-model cognition). **`ENABLE_SELF_MODEL_COGNITION` being OFF does not make Branch
B totally unreachable** (the `lead_contradiction` and `assimilation.py` producers are independent
paths not gated by it), but it does remove the primary/most-general producer. This matches
`INFRA-266`'s and the `SELF-MODEL-COGNITION` sibling ticket's own finding: in `urban_political`'s real
compiled state at seed 42 over a 200-tick window, Branch B did not route a query at all (0
`ActionIntentAdapter` traces) even with `ENABLE_SELF_MODEL_COGNITION` deliberately ON via the
`urban_political_selfmodel_execution_probe.yaml` profile — the corpus/seed/window combination simply
never produced a qualifying unknown+viable-candidate state within that window, independent of which
flags were set. This is directly relevant to trial design: a corpus trial run against
`urban_political` (or any shipped world without seeded `unknowns` content) is very likely to show
`ActionIntentAdapter.get_traces()` empty for this flag regardless of ON/OFF, the same "not
reachable in this corpus" finding already on file — not new evidence, and should not be
mis-reported as a fresh negative result.

### `tools/calibrate_simq.py` — env-var override gap for this flag (verified, not assumed)
`_KNOWN_FLAGS` (`tools/calibrate_simq.py:243-250`) is the allowlist `main()`'s env-var-override loop
(lines 272-277) iterates. Read directly: it lists `ENABLE_WORLD_CAPABILITY_LAYER`,
`ENABLE_SELF_MODEL_COGNITION`, `ENABLE_ADVENTURE_ROUTING`, `ENABLE_COMBAT_ENGAGEMENT`,
`ENABLE_BELIEF_ASSIMILATION`, `ENABLE_PROGRESSION_EVOLUTION`, `ENABLE_SOCIAL_COOPERATION`,
`ENABLE_WORLD_EMERGENCE`, `ENABLE_LIFE_ARC_CAMPAIGNS`, `ENABLE_ENHANCED_TRACE_EVENTS`,
`ENABLE_PUSH_EVENT_SHAPERS` — **`ENABLE_INFORMATION_INTENT_EXECUTION` is absent.** An env-var
override (`ENABLE_INFORMATION_INTENT_EXECUTION=ON python3 tools/calibrate_simq.py ...`, the method
the `COMBAT-ENGAGEMENT`/`WORLD-EMERGENCE`/`PROGRESSION-EVOLUTION` sibling tickets all used for their
own flags) is silently ignored for this specific flag — `_parse_flag_value` never runs against it,
so `combined_flag_overrides` never gains the key. Only `_load_profile_feature_flags()`
(`calibrate_simq.py:51-71`, reads a profile YAML's own `feature_flags:` block) has no such
allowlist restriction and can actually set this flag for a calibration run. This is a real tooling
gap, disclosed here per the task's own instruction — **not fixed by this ticket** (out of scope);
Plan must design any trial using a profile-YAML-level `feature_flags:` override (a new or existing
probe profile), never a bare env-var override, for this specific flag.

### A trial already exists on file for this exact flag — confirmed, not assumed
`config/simulation_quality/profiles/urban_political_selfmodel_execution_probe.yaml` (created by
`TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE`) already sets `ENABLE_INFORMATION_INTENT_EXECUTION: "ON"`
(alongside `ENABLE_SELF_MODEL_COGNITION: "ON"` and `ENABLE_BELIEF_ASSIMILATION: "ON"`), and was
already **run fresh** by the `TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION` sibling ticket this
same session-family (`stored_artifacts/TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION/trial_evidence.md`,
run key `urban_political_selfmodel_execution_probe_seed42_200t`, `run_1788018253_5169`). That run
exercised `ENABLE_INFORMATION_INTENT_EXECUTION=ON` end-to-end against `urban_political`'s real
compiled state (seed 42, 200 ticks), confirmed the world loaded correctly (`entities=10`), and its
own profile-echo log line confirms the flag was actually set. Per `INFRA-270`'s own
`support_boundary`, Branch B did not route a query in that specific run (0 traces) — a "no
suppression, not reached" finding, matching this ticket's own trace above. This is real,
standing, already-on-file corpus-profile evidence for `ENABLE_INFORMATION_INTENT_EXECUTION`
specifically, produced incidentally by a sibling ticket's own trial for a *different* flag's
validation — Plan's central open question (see Risks below) is whether re-citing this existing run
satisfies this ticket's own AC2 ("A real corpus-profile ON trial is run and documented"), or whether
a trial run *by this ticket itself* is still required to independently satisfy the acceptance
criterion's literal wording, mirroring the 4 prior sibling tickets' own precedent of running (not
just citing) their trial.

## Mechanics / Engine Constraints
- **Kernel 7-phase loop** (`docs/engine/kernel.md`): `information_intent_execution` runs inside the
  Resolution phase of `AuthoritativeApplyPipeline.refine()`, between `information_belief` and
  `cooperation` (`pipeline.py:176-184`), consistent with `INFRA-270`'s own `v2_evidence`.
- **Determinism law** (`docs/engine/kernel.md` line 19): `InformationIntentExecutionPhase.execute()`
  iterates `sorted(update.entity_updates.keys())` (line 43) — verified directly, and independently
  covered by `test_action_intent_execution_phase_preserves_deterministic_entity_order`.
- **Durable State Rule**: `ActionIntentAdapter.execute()`'s returned `EntityUpdate`s (inventory
  deltas, `self_model_bundle_set`) flow back through the authoritative `merge()`/apply path, not a
  local mutation — consistent with the boundary this rule draws. No new durable state type is
  introduced by this ticket (evidence-gathering only).
- **Mechanics Bible** §4 (`docs/mechanics/04_strategic_cognition.md`, "Knowledge management,
  perception"): this ticket's evidence-gathering scope proposes no formula change, so no
  chapter-level parity check is required.

## Docs Requiring Update
- `docs/architecture/rollout_flag_decisions_m1.md`: this file's own `ENABLE_INFORMATION_INTENT_EXECUTION`
  table row (`| ENABLE_INFORMATION_INTENT_EXECUTION | **Kept OFF, deferred** | No production
  evidence... Follow-up: TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION. |`) explicitly
  names this ticket as the open follow-up that must update it. Per the 4 prior sibling tickets'
  exact precedent (`## ENABLE_COMBAT_ENGAGEMENT — Validation Trial Result`, `## ENABLE_SELF_MODEL_COGNITION
  — Validation Trial Result`, etc.), this ticket must update the row's Verdict/Rationale cell in
  place and add a new `## ENABLE_INFORMATION_INTENT_EXECUTION — Validation Trial Result (TCK-20260826)`
  section documenting the trial evidence (existing + whatever Plan runs), the confirmed
  distinction-from-`ENABLE_BELIEF_ASSIMILATION` finding, and the `_KNOWN_FLAGS` tooling-gap
  disclosure above. Leaving the row unchanged after this ticket closes would make the decision
  artifact stale — the exact failure mode the source ticket's own precedent exists to prevent.

Whether `docs/guidelines/intentional_divergences.md` needs a new `DEV-00N` entry depends on the
final recommendation, which this investigation does not pre-decide (Uncertainty Rule). If the
recommendation is "keep OFF, deferred" (the evidence assembled here — no shipped profile turns this
flag on, only a non-shipped probe profile — points this way, matching all 4 prior sibling outcomes),
no new divergence entry is needed: the flag's behavior versus the Mechanics Bible does not change
either way, only the evidentiary basis for staying deferred does, which lives in
`rollout_flag_decisions_m1.md` per precedent. If the trial instead drove a flip recommendation
(not expected), a new `DEV-00N` entry would be required — not written here, since flipping the
default is explicitly Out of Scope for this ticket regardless of the trial's findings.

The `docs/parity_ledger/infrastructure.yaml` entry `INFRA-270` (path:
`docs/parity_ledger/infrastructure.yaml`) is **not** required to change for this ticket: re-read
directly this session and confirmed still accurate to the current code/config state — its
`support_boundary` text already correctly states the flag "remains OFF in every shipped
config/simulation_quality/profiles/*.yaml and data/worlds/*.yaml calibration chain" (still true,
`urban_political_selfmodel_execution_probe.yaml` is explicitly non-shipped) and already documents
the 0-traces-in-`urban_political` finding this investigation independently re-confirms. `INFRA-266`
and `INFRA-267` (same file) are likewise unchanged — their own lineage-succession text
(`INFRA-266 -> INFRA-267 -> INFRA-270`) already accounts for this flag's existence; nothing this
ticket found requires a new addendum to any of the three. If a genuinely new finding emerges from
Plan's chosen trial (not expected, given how much of this ground `INFRA-270`/the self-model
sibling's own run already covers), a new `v2_evidence`/`support_boundary` addendum would be needed
then — not assumed here.

## Parity Ledger Overlap
- `INFRA-270` (`status: verified`, `priority: P1`) — the authoritative entry for this exact
  flag/phase. Still accurate; its `test_path` (5 test files/functions, all read directly this
  session — see Regression Surface in test_plan.md) is confirmed to exist and pass. No `test_path`
  gap found (unlike some sibling tickets' investigations, which flagged stale `test_path` entries —
  not the case here).
- `INFRA-266` (`status: verified`, `priority: P1`) — Branch B's original real-world generalization
  split verdict; establishes the "does NOT generalize to urban_political at seed 42" precedent this
  ticket's trial design must account for.
- `INFRA-267` (`status: verified`, `priority: P1` implied) — the query-routing closure fix that made
  Branch B mechanically correct (fallback-past-candidates[0], structured insufficient-gold signal).
  Unrelated to this flag's own execution-side gating but establishes why Branch B can in principle
  produce a real `ActionIntent` when it does fire.
- No `P0` parity entry names `ENABLE_INFORMATION_INTENT_EXECUTION` specifically (`INFRA-270` is
  `P1`) — no `test_path` requirement blocks this ticket under the `P0` rule, though `INFRA-270`'s
  existing `P1` `test_path` list should still be re-run as regression surface (see test_plan.md).

## Prior Work
- **`TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE`** (`INFRA-266`) — the real-world
  generalization trial establishing Branch B's split verdict against `urban_political`.
- **`TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE`** (`INFRA-267`) — fixed Branch B's 3 routing-half
  root causes plus an observability gap.
- **`TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE`** (`INFRA-270`, `Logic ID` on
  `information_intent_execution.py`) — the ticket that built this exact phase, registered the flag,
  and created `urban_political_selfmodel_execution_probe.yaml` as a permanent grade-anchor fixture.
- **`TCK-20260824-ROLLOUT-FLAG-DECISIONS`** — reviewed all 8 Phase-10 flags including this one,
  deferred it with "no production evidence" as the stated rationale, named this ticket as the
  follow-up.
- **`TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION`** — sibling ticket whose own trial
  incidentally exercised `ENABLE_INFORMATION_INTENT_EXECUTION=ON` (via the shared
  `urban_political_selfmodel_execution_probe.yaml` profile) while validating a *different* flag
  (`ENABLE_SELF_MODEL_COGNITION`). Its `trial_evidence.md` and `investigation.md` are the closest
  direct precedent for this ticket's own trial design and evidence format, and its existing run is
  the central open question below (re-cite vs. re-run).
- **`TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION`** / **`TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION`**
  / **`TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION`** — the other 3 sibling tickets in this
  same batch, establishing the "5 signals x 4 legs, 2 worlds, OFF-then-ON" evidence-format precedent
  and the shared DEV-003 flip-bar standard this ticket's own recommendation must be measured against.

## Risks and Open Questions
- **Open question (Plan's job, not pre-decided here): does the already-on-file
  `urban_political_selfmodel_execution_probe_seed42_200t` run (produced by the SELF-MODEL-COGNITION
  sibling ticket) satisfy this ticket's own AC2 ("A real corpus-profile ON trial is run and
  documented"), or must this ticket run its own fresh trial?** Two considerations for Plan to weigh,
  not resolved here: (a) the existing run genuinely does exercise
  `ENABLE_INFORMATION_INTENT_EXECUTION=ON` end-to-end against real `urban_political` compiled state,
  and re-citing it (with fresh independent verification of the raw data, not just trusting the
  sibling's prose) would be cheap and non-duplicative; (b) all 4 prior sibling tickets in this batch
  ran their *own* trial rather than solely citing another ticket's incidental byproduct, and this
  ticket's own Scope explicitly calls for confirming "no unexpected interaction between the two"
  flags (`ENABLE_BELIEF_ASSIMILATION` now-ON + this flag) specifically — the existing probe run does
  test that exact combination, but was designed and reported from the self-model flag's perspective,
  not this one's. A minimal, low-cost option Plan should consider: re-run the same
  `urban_political_selfmodel_execution_probe` profile fresh under this ticket's own execution
  (cheap, reuses the already-established mechanism, produces this ticket's own primary-source
  evidence rather than solely re-citing a sibling's), consistent with how the self-model sibling
  itself treated `INFRA-266`'s own prior trial (cited as prior work, but still ran its own fresh
  confirming legs).
- **Risk**: `urban_political` at seed 42 is very likely to reproduce the "0 traces, Branch B does not
  route a query in this corpus/window" finding regardless of which flags are ON, per the trace above
  — a trial limited to this one world/seed cannot independently confirm
  `ActionIntentAdapter.execute()` fires with *real, non-hand-built* routed content (only that the
  phase runs without regressing calibration when wired in and gated ON, which `INFRA-270`'s existing
  hand-built-scenario test already proves deterministically). Plan should decide whether a
  second, higher-`unknowns`-density world/seed is worth the added trial cost to close this
  specific gap, or whether the existing hand-built-scenario proof
  (`test_information_intent_execution_fires_through_kernel_tick_once`) plus the calibration-safety
  proof (`test_urban_political_selfmodel_execution_isolated_grade_anchor`) together already meet the
  evidentiary bar this ticket's AC requires — this investigation does not pre-decide it.
- **Risk**: per the same DEV-003 flip standard the 4 sibling tickets were measured against (a
  *shipped* profile already exercising the flag in real production, not a probe-only fixture),
  `urban_political_selfmodel_execution_probe.yaml` is explicitly non-shipped (not referenced by any
  world's default calibration inheritance chain, per its own header comment). No shipped profile
  turns `ENABLE_INFORMATION_INTENT_EXECUTION` on anywhere. The expected recommendation, absent a
  surprising finding, is therefore "Keep OFF, deferred" — the same class of outcome as all 4 prior
  sibling flags — not a flip. This is Plan's judgment call to state explicitly, not assumed as fixed
  here.
- **Risk**: `tools/calibrate_simq.py`'s `_KNOWN_FLAGS` gap (documented above) means any trial command
  Plan writes must use `--profile <name-with-this-flag-in-its-feature_flags-block>`, never a bare
  `ENABLE_INFORMATION_INTENT_EXECUTION=ON python3 tools/calibrate_simq.py ...` env-var invocation —
  the latter would silently no-op for this flag specifically and produce a false "OFF-identical"
  result that looks like evidence but isn't. This is a real trap the trial design must avoid, not
  merely a documentation nicety.

## Anti-Drift Hazards
- **Do not conflate this ticket with fixing or extending `InformationBeliefPhase`/
  `InformationIntentExecutionPhase`/`ActionIntentAdapter` themselves.** Out of Scope excludes
  flipping the flag's default; this is an evidence-gathering ticket only.
- **Do not re-litigate `ENABLE_BELIEF_ASSIMILATION`'s already-decided ON default** — Out of Scope
  says so explicitly. The trial should hold it at its now-ON default throughout, never toggle it OFF
  to isolate this flag artificially (that would misrepresent the real production combination).
- **Do not use a bare env-var override (`ENABLE_INFORMATION_INTENT_EXECUTION=ON python3
  tools/calibrate_simq.py ...`) for any trial leg** — confirmed above, `_KNOWN_FLAGS` silently drops
  it. Only a profile YAML's own `feature_flags:` block reaches this flag.
- **Do not mistake "0 `ActionIntentAdapter` traces in `urban_political`" for a suppression finding.**
  Per `INFRA-270`'s own `support_boundary` and this investigation's independent trace-through, this
  is an expected "not reached in this corpus" result, not evidence the phase is broken or the flag
  gate is faulty — mirroring `INFRA-266`'s original "does NOT generalize" finding for the same
  corpus/seed. The deterministic hand-built-scenario test remains the correct proof that execution
  itself works when Branch B does fire.
- **Do not add `ENABLE_INFORMATION_INTENT_EXECUTION` to any `_DELIBERATE_ON_DEFAULT_FLAGS` allowlist
  copy** (`tests/unit/config/test_phase10_feature_flags.py`,
  `tests/integration/test_scenario_feature_flag_defaults.py`,
  `tests/certification/test_phase10_enhanced_determinism_parity.py`) under the expected "keep OFF"
  outcome — that only happens in a future, separate flip ticket.
- **Do not create or edit any *shipped* `config/simulation_quality/profiles/*.yaml` to make a real
  archetype world ship this flag ON** — that would fabricate the "shipped production evidence" this
  ticket exists to honestly assess, not find. The existing non-shipped probe profile is the correct,
  already-established vehicle for any trial.
- **Clean up `data/runs/*`/`data/calibration/*` trial output at Finalize**, per Definition of Done —
  same as all 4 prior sibling tickets' own precedent.
