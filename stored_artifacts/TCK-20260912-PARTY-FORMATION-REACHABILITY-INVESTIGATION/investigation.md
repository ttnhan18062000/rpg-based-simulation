# Investigation — TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION

## Step 1: re-measure at real density (this ticket's own blocking dependency)
Re-ran the exact same instrumentation script from the trust investigation (same scenario,
`frontier_living_world`, same seed 7, same 500 ticks) against the now-landed count-expansion fix
(`TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE`), for a controlled
before/after comparison:

| | Before (pre-count-expansion) | After (real density) |
|---|---|---|
| Entity count | 16 | 49 |
| `state.groups` at tick 500 | 0 | 0 |
| Entities with non-empty `trust_history` | 0 / 16 | 0 / 49 |

**Groups still do not form at real density.** This rules out the density-bug hypothesis
definitively: zero-groups was not a consequence of the under-population bug. The premise holds,
and this is a stronger negative than the original 16-entity measurement — the mechanism had a real
chance and still didn't fire.

## Step 2: root cause, confirmed with evidence at every step (not assumed)
Traced the real, live group-formation precondition directly, then instrumented the actual 500-tick
run to confirm each claim empirically rather than stopping at static code reading.

**`GroupSystem.update_groups()`** (`src/systems/world_systems/groups.py:260-324`, wired live via
`GroupPhase.resolve()` → `pipeline.py:475-476`'s `run_phase("groups", ...)`, ungated by any feature
flag) forms a group only when two entities share a contract with `status == ContractStatus.ACTIVE`
AND are within 10 units of each other. This is the sole real group-creation path found (the other
`GroupRecord(...)` construction site, `military_conflict.py:340`, is a separate, combat-triggered
mechanism, not investigated further here — out of this ticket's own scope).

**Cooperation's own real, live recruitment-offer creation is confirmed working**: `Cooperation
IntentBridge.map_decision()` (`src/domains/cooperation/services.py:179-198`) creates a real
`ContractState` via `ContractService.create_recruitment_contract()` whenever
`CooperationDecisionService.select()` picks `REQUEST_HELP`/`HIRE_SUPPORT` for an entity with a
help need. Confirmed via real 500-tick instrumentation: **235 real recruitment contracts created**.

**But every one of those offers is created with `status=ContractStatus.OFFERED`**
(`create_recruitment_contract()`, `contracts.py:132`), never `ACCEPTED`/`ACTIVE`, and expires in
just 10 ticks (`expiry_tick = tick + 10`, same function). `GroupSystem.update_groups()`'s own
precondition requires `ACTIVE`, not `OFFERED` — so these 235 real offers can never trigger group
formation regardless of proximity.

**Confirmed, not assumed, that nothing ever promotes an OFFERED recruitment offer to ACCEPTED/
ACTIVE**, via three independent lines of evidence:
1. `ContractService.accept_contract()` — the function whose own docstring says "Transition an
   OFFERED/COUNTERED contract to ACTIVE" — has **zero real callers anywhere in `src/`** (confirmed
   by grep) **and zero calls in the real 500-tick instrumented run** (confirmed by direct
   monkeypatch counter).
2. The only other real path that could reach `ContractStatus.ACTIVE` for a recruitment contract,
   `src/engine/domain/core_actions.py`'s `execute_recruit()` (dispatched from `ActionRouter` on an
   `ActionIntent(kind="RECRUIT")`), has **zero real construction sites for `kind="RECRUIT"`
   anywhere in `src/`** — nothing in live gameplay decision logic ever issues that intent.
3. **The system's own declared design intent confirms exactly what's missing, not a guess**:
   `CooperationPosture.JOIN_PARTY`'s `PostureDefinition` (`src/domains/cooperation/
   postures.py:47-50`) states its `intent_mapping` is `"accept_recruitment_offer"` — this posture
   was explicitly designed to be the target-side "accept a pending offer" action. But
   `JOIN_PARTY` is referenced **nowhere else in `src/`** — not in
   `CooperationDecisionService.select()` (never selected — no logic anywhere detects "I have a
   pending incoming offer" from the receiving entity's own perspective) and not in
   `CooperationIntentBridge.map_decision()` (no `elif posture == CooperationPosture.JOIN_PARTY:`
   branch exists — even if something did select it, nothing would translate the selection into a
   contract-status change). Dead on both ends: never chosen, and would no-op if chosen.

**Root cause, stated precisely**: cooperation's own recruitment/party-formation design has a real,
live, working *offer* half (`REQUEST_HELP`/`HIRE_SUPPORT` → `map_decision()` → OFFERED contract)
and a designed-but-never-connected *accept* half (`JOIN_PARTY`, whose own `intent_mapping` names
the missing function). The accept half was never wired — not partially broken, not rare, simply
never built past the enum/PostureDefinition stage. Every offer therefore expires unaccepted after
10 ticks, `GroupSystem.update_groups()` never sees a qualifying `ACTIVE` contract, and `state.groups`
stays permanently empty regardless of population density, proximity, or run length.

## Step 3: FORM_PARTY is a feeder into the same broken pipeline, not a separate mechanism
`RouteFamily.FORM_PARTY` (the adventure route named throughout this ticket's own Related Code
Areas) maps to `(ProjectKind.SOCIAL, ObjectiveKind.REACH_LOCATION)` (`src/domains/adventure/
mapper.py:42`) — when selected as a strategic route, it only makes the entity walk toward a
candidate ally. It does not itself create a contract or a group; the actual cooperation/contract
exchange is expected to happen once the entity is physically near its target, via the same
`CooperationPhase`/`map_decision()` pipeline traced above. FORM_PARTY is therefore not a third,
independently-broken mechanism — it feeds real entities toward the same broken acceptance gap, and
its entire purpose (position an entity to cooperate) is currently pointless regardless of how well
it scores or how often it's selected.

## Blast radius (per this ticket's own AC — enumerated, not all fixed here)
Everything gated on `state.groups` being non-empty, confirmed real and currently dormant as a
direct consequence of this one gap:
- `PartyCohesionService`'s own leader/member cohesion evaluation (`src/domains/cooperation/
  services.py`) — never runs its real logic since `CooperationPhase.execute()`'s own group loop
  (`for g_id, g_rec in state.groups.items():`) never iterates.
- Both live trust-writing mechanisms confirmed in `TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-
  ACCUMULATION-INVESTIGATION`: the party-cohesion-collapse penalty (now correctly routed through
  `CooperationLearningService.learn()` after that ticket's own fix) and the same-party-betrayal
  penalty (`SocialAppraisalSystem.process_betrayal()`, called from `combat_actions.py`, gated on
  shared `identity.group_id`).
- `RouteFamily.FORM_PARTY`'s entire purpose, as traced in Step 3.
- `SocialContractGoalScorer` (`src/ai/goals/social_contract_scorer.py`) — scores `ACTIVE`
  RECRUITMENT/LOAN contracts each tick as a strategic goal candidate; recruitment contracts never
  reach `ACTIVE`, so this scorer's own RECRUITMENT half is permanently starved (its LOAN half is
  unaffected, a separate contract kind not investigated here).
- Plausibly `SocialBond.role` promotion, per the original ticket's own framing — not directly
  traced in this investigation; flagged as likely but unconfirmed.

## Determination
**Genuinely broken, not reachable-but-rare** — confirmed via real 500-tick instrumentation at both
the old and new (real) population density, with the exact missing wiring identified from the
system's own declared design intent (`JOIN_PARTY`'s `intent_mapping`), not inferred or guessed.

Per this ticket's own Scope ("Once root-caused: decide the fix approach (if any) via peer review
before implementing"), reported to peer before any implementation. Reported also: whether groups
forming would also make trust accumulate — untestable without first fixing the accept-side gap,
since the two live trust writers are downstream of group formation, not independent of it.

## Step 4: implementation (user-approved: build the minimal accept path)
Built exactly the three missing pieces the scaffolding already specified (`JOIN_PARTY`'s own
`intent_mapping = "accept_recruitment_offer"`):
1. `CooperationDecisionService.find_pending_incoming_offer()` — new static method scanning
   `state.entities` for a live, unexpired OFFERED RECRUITMENT contract targeting the entity under
   evaluation (contracts are only ever stored on the offering entity's own record, never mirrored
   to the target). Minimal disqualifiers only, per the user's own standing rule deferring richer
   acceptance criteria: offering entity alive/active, entity not already grouped.
2. `CooperationDecisionService.select()` — checks this first, before the existing help-needs/SOLO
   branch, returning `JOIN_PARTY` with the contract id stashed in `trace`.
3. `CooperationPhase.execute()` — a new block handling `JOIN_PARTY`, promoting the offerer's
   contract via `ContractService.accept_contract()` (previously confirmed dead, now the real
   caller). Also relaxed the phase's own skip-gate so an entity with no help needs of its own is
   still evaluated when a pending incoming offer exists — otherwise it would never reach `select()`
   at all regardless of what `select()` would decide.

**Real bug found and fixed within this same implementation, before reporting any result**: the
first pass promoted the contract via a raw `dataclasses.replace(contract, status=ACTIVE)`. Real
instrumentation showed the immediate consequence: `PartyCohesionService.evaluate()` calls went from
0 to 234 (groups genuinely forming, evaluated as STABLE) but `state.groups` was still empty by tick
500 and trust still 0/49 — groups were forming and then dissolving within a few ticks. Root-caused,
not assumed: the raw `replace()` carried over the original ~10-tick OFFER-stage `expiry_tick`, and
`GroupSystem.update_groups()`'s own `contract_invalid` check treats a contract past its
`expiry_tick` as invalid regardless of `status`, dissolving the group. Fixed by switching to
`ContractService.accept_contract()`, which internally calls `SocialContractSystem
.transition_contract()` — already correctly resetting `expiry_tick = tick + terms["duration"]` on
the OFFERED→ACTIVE transition. Added a dedicated regression test
(`test_join_party_promotes_offerers_contract_to_active_with_extended_expiry`) asserting the
extended expiry specifically, since a naive re-fix could silently reintroduce this.

## Step 5: real verification, three-point controlled measurement
Same scenario, seed, and (for the first two points) instrumentation script throughout this entire
investigation arc — a controlled comparison, not three separate observations:

| | Entities | `state.groups` @ tick 500 | Cohesion statuses observed | `trust_history` populated |
|---|---|---|---|---|
| Before count expansion | 16 | 0 | none (never evaluated) | 0 / 16 |
| After count expansion, before this fix | 49 | 0 | none (never evaluated) | 0 / 49 |
| After this fix, expiry bug present | 49 | 0 (formed then dissolved within ticks) | 234 STABLE only | 0 / 49 |
| After this fix, expiry bug fixed | 49 | 1 (12 distinct ever formed, up to 16 concurrent, one surviving 400+ ticks) | 859 STABLE / 5 MEMBER_ABANDONING / 1 LEADER_LOST / 4 NEEDS_REGROUP | **3 / 49** |

This rules out density as the cause (rows 1→2) and isolates the accept-path fix as what actually
closes the gap (rows 2→4), with the expiry bug (row 3) caught and fixed before ever reporting a
result.

**Verified the trust-accumulation rate is exactly explained by its own real triggers, not just
non-zero** (per peer review's explicit follow-up question — checked with a dedicated correlation
script, not assumed from the aggregate counts alone): all 6 real `MEMBER_ABANDONING`/`LEADER_LOST`
cohesion events occurred in 2-member groups (1 leader + 1 non-leader member each), so the correct
predicted `CooperationLearningService.learn()` call count is exactly 6 — matched tick-for-tick and
entity-for-entity against the 6 actual `learn()` calls observed (same tick, same accepting entity,
same partner, in the same order, for every one of the 6 events). Trust fired exactly as often as
its real triggers occurred, not merely "some non-zero amount" — a materially stronger claim than
"trust is no longer always zero."

## Determination and closure
Confirmed genuinely broken (not rare, not a consequence of the density bug — both hypotheses tested
and ruled out before building anything), root-caused to a designed-but-never-wired accept path, and
fixed with the minimal shape the design itself specified. The transferred acceptance bar ("trust
demonstrably accumulates in a real run") is satisfied, verified at the level of individual causal
events, not just an aggregate non-zero count. Acceptance-criteria richness (trust/need/faction
checks) explicitly deferred to `docs/plans/deferred_tuning_decisions_register.md` D-09, per the
user's own standing rule.
