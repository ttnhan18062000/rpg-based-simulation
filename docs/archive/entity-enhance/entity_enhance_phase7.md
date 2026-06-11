---
status: archive
authority: P2
audience: historical
layer: core
original_date: unknown
---

# Phase 7 — Party / Social Cooperation Adventure

Phase 1:

```text
world exposes options
```

Phase 2:

```text
entity understands itself
```

Phase 3:

```text
entity chooses adventure route family
```

Phase 4:

```text
entity judges combat engagement
```

Phase 5:

```text
entity handles uncertain information
```

Phase 6:

```text
entity converts reward into growth
```

Phase 7:

```text
entity understands when it should cooperate, who to cooperate with, how much to trust them, and how the cooperation changes future life decisions
```

Current code already has a social/contract foundation. The uploaded tests include recruitment contract appraisal, contract lifecycle, public-vs-private trust, low-trust recruiter penalties, and social bonds. The source also already has `PartyCoordinationSystem.apply_leadership_influence`, which injects a leader’s active objective into a member’s candidate goals through active recruitment contracts and trust-based boost.

So Phase 7 should **not** duplicate:

```text
basic contract appraisal
basic trust calculation
public/private trust priority
basic group coordination
basic recruitment acceptance/rejection
```

Phase 7 should test the missing life-loop layer:

```text
when does an entity seek help?
who does it choose?
does the party actually support the objective?
does cooperation change combat/travel/risk choices?
does betrayal/abandonment change future cooperation?
```

The cognition review also points out the current mismatch: social contracts are rich, but many downstream town/economy loops remain immediate and transactional instead of using long-term negotiation, betrayal, and cooperation meaningfully.

---

# Phase 7 goal

Phase 7 answers:

```text
Given a difficult objective,
does the entity choose to proceed alone, ask for help, join a party, hire support, avoid the objective, or defer?
```

Not:

```text
Does SocialAppraisalSystem accept a recruitment contract?
```

That already exists.

Not:

```text
Can groups form in arena?
```

That already has coverage.

Phase 7 is about **social cooperation as a life strategy**.

---

# Phase 7 success definition

Phase 7 is successful when the engine can produce a trace like:

```yaml
cooperation_decision:
  entity_id: 1
  objective: hunt_wolf
  reason_for_help:
    - combat.enemy_type.wolf capability is risky
    - prior near_death against wolf
    - reward is still valuable
  considered_partners:
    - entity_id: 2
      trust: 0.8
      role_fit: tank
      cost: 20
      availability: true
    - entity_id: 3
      trust: 0.3
      role_fit: damage
      cost: 5
      availability: true
  selected_partner: 2
  selected_route: request_help
  rejected:
    entity_3: low_trust
    solo_hunt: risk_too_high
```

After cooperation:

```yaml
cooperation_outcome:
  party_id: party_1
  outcome: success
  member_contribution:
    entity_1: damage
    entity_2: protected_leader
  trust_updates:
    entity_1_to_2: +0.08
  future_effect: entity_1 more likely to ask entity_2 for hard objectives
```

After betrayal/abandonment:

```yaml
cooperation_outcome:
  outcome: abandoned_during_danger
  trust_updates:
    entity_1_to_2: -0.25
  memory:
    - entity_2_unreliable_in_high_risk_contract
  future_effect: avoid entity_2 for dangerous quests
```

---

# Task 1 — Add Phase 7 coverage audit

## Description

Document what is already covered so Phase 7 does not duplicate existing social tests.

Existing uploaded tests already cover:

```text
contract appraisal by trust
contract appraisal by greed
contract lifecycle
low-trust recruiter penalty
public vs private trust priority
social bonds
arena group coordination
```

Phase 7 new tests should cover:

```text
help-seeking decision
partner selection
party objective alignment
party cohesion
party risk/reward effect
abandonment/betrayal memory
future cooperation changes
```

## Proposed document

```text
docs/test_coverage/phase7_party_social_cooperation_coverage.md
```

## Checklist

- [x] Existing contract appraisal tests listed.
- [x] Existing social bond tests listed.
- [x] Existing group coordination tests listed.
- [x] Phase 7 test scope limited to cooperation life-loop behavior.
- [x] No test duplicates basic `SocialAppraisalSystem.appraise_contract`.
- [x] No test duplicates raw arena group formation.
- [x] No test duplicates combat damage or quest reward logic.

---

# Task 2 — Define social cooperation domain boundary

## Description

Create a domain layer:

```text
src/domains/cooperation/
```

This domain decides whether social cooperation is useful.

It should not replace:

```text
SocialAppraisalSystem
ContractService
PartyCoordinationSystem
CombatResolutionSystem
StrategicIntelligenceSystem
```

It should call or feed them.

## Proposed service

```python
class CooperationDecisionService:
    def evaluate(
        self,
        entity: EntityState,
        state: AuthoritativeState,
        context: CooperationDecisionContext,
    ) -> CooperationDecisionResult:
        ...
```

## Inputs

```text
self-awareness
need interpretation
capability estimate
combat risk belief
knowledge model
active objective/project
available nearby entities
social bonds/trust
existing contracts
known party history
world opportunities
```

## Outputs

```text
selected cooperation posture
candidate partners
rejected partners
proposed contract intent
proposed strategic update
trace
```

## Checklist

- [x] Cooperation logic is isolated from raw social contract appraisal.
- [x] Service does not mutate state directly.
- [x] Service can return “go solo.”
- [x] Service can return “request help.”
- [x] Service can return “join existing party.”
- [x] Service can return “defer because no safe partner.”
- [x] Service consumes generic self-model and risk/capability estimates.
- [x] Same input + same seed gives deterministic result.

## TDD tests

```text
tests/unit/domains/cooperation/test_phase7_cooperation_boundary.py
```

Test cases:

```text
test_cooperation_service_does_not_mutate_state
test_cooperation_service_does_not_execute_contract_directly
test_cooperation_service_accepts_generic_self_model_inputs
test_cooperation_service_returns_trace_and_posture
```

---

# Task 3 — Define cooperation posture vocabulary

## Description

Cooperation should not be binary:

```text
solo / party
```

Use posture.

## Initial postures

```text
SOLO
REQUEST_HELP
OFFER_HELP
JOIN_PARTY
HIRE_SUPPORT
FOLLOW_LEADER
LEAD_PARTY
AVOID_PARTNER
DEFER_NO_PARTNER
ABANDON_PARTY
RESCUE_ALLY
GUARD_ALLY
```

## Meaning

| Posture            | Meaning                            |
| ------------------ | ---------------------------------- |
| `SOLO`             | objective is acceptable alone      |
| `REQUEST_HELP`     | ask another entity to assist       |
| `OFFER_HELP`       | help another entity’s objective    |
| `JOIN_PARTY`       | join existing group                |
| `HIRE_SUPPORT`     | pay for help                       |
| `FOLLOW_LEADER`    | align with leader objective        |
| `LEAD_PARTY`       | recruit/coordinate others          |
| `AVOID_PARTNER`    | reject risky/untrusted partner     |
| `DEFER_NO_PARTNER` | objective too risky without help   |
| `ABANDON_PARTY`    | leave because risk/trust violation |
| `RESCUE_ALLY`      | interrupt to help ally             |
| `GUARD_ALLY`       | protect ally during objective      |

## Checklist

- [x] Postures are canonical constants/enums.
- [x] Every posture has semantic definition.
- [x] Every posture maps to possible intent/project update.
- [x] No posture directly mutates social state.
- [x] Unknown posture fails fast.
- [x] Posture appears in trace.

## TDD tests

```text
tests/unit/domains/cooperation/test_phase7_cooperation_postures.py
```

Test cases:

```text
test_cooperation_postures_are_unique
test_each_posture_has_definition
test_each_posture_has_intent_mapping
test_unknown_posture_fails_fast
```

---

# Task 4 — Implement `HelpNeedEvaluator`

## Description

The entity needs to know when solo action is too risky or inefficient.

This is not the same as low combat capability. Help may be needed for:

```text
combat
travel
dangerous region
carrying capacity
unknown area
quest deadline
escort
resource gathering
healing/protection
```

## Proposed model

```python
@dataclass(frozen=True)
class HelpNeed:
    key: str
    severity: float
    reason: str
    required_support_tags: tuple[str, ...] = ()
    acceptable_postures: tuple[str, ...] = ()
```

Examples:

```text
combat_support_needed
escort_needed
healer_needed
guide_needed
carry_support_needed
scout_needed
```

## Service

```python
class HelpNeedEvaluator:
    def evaluate(
        self,
        entity: EntityState,
        state: AuthoritativeState,
        context: CooperationContext,
    ) -> tuple[HelpNeed, ...]:
        ...
```

## Checklist

- [x] High combat risk can create combat support need.
- [x] Low HP can create healer/protector need.
- [x] Unknown route can create guide/scout need.
- [x] Heavy load can create carry/logistics support need.
- [x] Urgent objective can increase help need severity.
- [x] Easy objective does not create unnecessary help need.
- [x] Output is deterministic.
- [x] Does not select partner directly.

## TDD tests

```text
tests/unit/domains/cooperation/test_phase7_help_need_evaluator.py
```

Test cases:

```text
test_risky_combat_creates_combat_support_need
test_low_hp_creates_protection_or_healer_need
test_unknown_region_creates_guide_or_scout_need
test_easy_objective_does_not_create_help_need
test_objective_urgency_increases_help_need_severity
```

---

# Task 5 — Implement `PartnerCandidateProvider`

## Description

The world/social layer needs to expose possible partners.

Do not scan all entities.

Use scoped candidates:

```text
nearby entities
known trusted entities
same town/guild
existing group members
entities with compatible objective
entities offering help
```

## Proposed candidate model

```python
@dataclass(frozen=True)
class PartnerCandidate:
    entity_id: int
    relationship_score: float
    trust_score: float
    role_fit_score: float
    availability_score: float
    cost_gold: int = 0
    risk_penalty: float = 0.0
    reason: str | None = None
```

## Service

```python
class PartnerCandidateProvider:
    def get_candidates(
        self,
        entity: EntityState,
        state: AuthoritativeState,
        help_needs: tuple[HelpNeed, ...],
        budget: CandidateBudget,
    ) -> tuple[PartnerCandidate, ...]:
        ...
```

## Checklist

- [x] Uses spatial/known-social scope.
- [x] Does not scan all entities by default.
- [x] Excludes dead/inactive entities.
- [x] Excludes hostile entities unless special case.
- [x] Includes trusted nearby entities.
- [x] Scores role fit.
- [x] Scores availability.
- [x] Scores cost.
- [x] Caps result count.
- [x] Deterministic sorting.

## TDD tests

```text
tests/unit/domains/cooperation/test_phase7_partner_candidate_provider.py
```

Test cases:

```text
test_provider_excludes_dead_entities
test_provider_excludes_hostile_entities
test_provider_prefers_trusted_nearby_candidate
test_provider_scores_role_fit
test_provider_caps_candidate_count
test_provider_does_not_global_scan_when_scope_given
```

---

# Task 6 — Implement `PartnerFitEvaluator`

## Description

A trusted partner is not always the right partner.

Fit depends on:

```text
role
class
combat style
healing ability
knowledge
risk tolerance
objective compatibility
trust
cost
availability
past behavior
```

## Proposed service

```python
class PartnerFitEvaluator:
    def evaluate(
        self,
        requester: EntityState,
        candidate: EntityState,
        help_needs: tuple[HelpNeed, ...],
        state: AuthoritativeState,
    ) -> PartnerFitReport:
        ...
```

## Output

```python
@dataclass(frozen=True)
class PartnerFitReport:
    candidate_id: int
    fit_score: float
    trust_score: float
    capability_match: float
    objective_alignment: float
    risk: float
    reasons: tuple[str, ...]
```

## Checklist

- [x] High trust increases fit.
- [x] Low trust decreases fit.
- [x] Compatible role increases fit.
- [x] Conflicting objective decreases fit.
- [x] Existing contract obligation can increase fit.
- [x] Past abandonment/betrayal decreases fit.
- [x] High cost decreases fit if low gold.
- [x] Output includes reason trace.

## TDD tests

```text
tests/unit/domains/cooperation/test_phase7_partner_fit_evaluator.py
```

Test cases:

```text
test_high_trust_increases_partner_fit
test_private_betrayal_decreases_partner_fit
test_role_fit_matters_for_combat_support
test_conflicting_active_objective_decreases_fit
test_high_cost_decreases_fit_when_requester_poor
test_fit_report_includes_reasons
```

Important: do not duplicate public/private trust unit tests. Here the test should verify that trust result influences **partner fit**, not that trust itself is computed correctly.

---

# Task 7 — Implement `CooperationDecisionService`

## Description

This chooses the cooperation posture.

Inputs:

```text
help needs
partner candidates
partner fit reports
objective value
risk estimate
social trust
cost
personality traits
```

## Scoring idea

```text
cooperation_score =
    help_need_severity
  + objective_value
  + partner_fit
  + trust_score
  + sociability_bias
  - cost_penalty
  - betrayal_risk
  - delay_penalty
```

## Personality effects

| Trait       | Effect                              |
| ----------- | ----------------------------------- |
| sociability | more likely to cooperate            |
| bravery     | more willing to go solo             |
| caution     | more likely to request help         |
| greed       | more sensitive to reward split/cost |
| loyalty     | more likely to help allies          |
| pride       | less likely to ask for help         |

## Checklist

- [x] Can choose `SOLO`.
- [x] Can choose `REQUEST_HELP`.
- [x] Can choose `HIRE_SUPPORT`.
- [x] Can choose `JOIN_PARTY`.
- [x] Can choose `DEFER_NO_PARTNER`.
- [x] Different traits can produce different valid decisions.
- [x] Rejected partners have reasons.
- [x] Does not execute recruitment directly.
- [x] Deterministic under fixed seed/input.

## TDD tests

```text
tests/unit/domains/cooperation/test_phase7_cooperation_decision_service.py
```

Test cases:

```text
test_easy_objective_selects_solo
test_risky_objective_selects_request_help_when_good_partner_exists
test_risky_objective_selects_defer_when_no_partner_exists
test_cautious_entity_prefers_help_over_solo
test_brave_entity_may_choose_solo_when_risk_moderate
test_greedy_entity_rejects_high_cost_partner
test_rejected_partner_reasons_are_preserved
```

---

# Task 8 — Map cooperation decision to contract/action intent

## Description

Existing contract services should remain authoritative.

Phase 7 should bridge cooperation decision into contract/action intent.

## Mapping

| Cooperation decision | Intent / update                               |
| -------------------- | --------------------------------------------- |
| `REQUEST_HELP`       | create recruitment/help contract offer        |
| `HIRE_SUPPORT`       | recruitment contract with payment terms       |
| `JOIN_PARTY`         | accept/join existing group if appraised       |
| `FOLLOW_LEADER`      | active party contract influences goal scoring |
| `DEFER_NO_PARTNER`   | blocker: no suitable partner                  |
| `ABANDON_PARTY`      | contract cancellation/betrayal outcome        |
| `RESCUE_ALLY`        | emergency project/objective                   |
| `GUARD_ALLY`         | tactical/strategic guard objective            |

The existing source already has recruitment contracts and party influence from active recruitment contracts, so use that rather than building a separate party membership system.

## Checklist

- [x] Bridge emits intent/update, not direct mutation.
- [x] Contract creation uses existing `ContractService`.
- [x] Contract acceptance still uses existing appraisal.
- [x] Payment terms use existing transaction law.
- [x] `DEFER_NO_PARTNER` creates blocker/reason.
- [x] `FOLLOW_LEADER` reuses party influence path.
- [x] No duplicate contract lifecycle implementation.
- [x] Trace links decision to contract/intent.

## TDD tests

```text
tests/unit/domains/cooperation/test_phase7_cooperation_intent_bridge.py
```

Test cases:

```text
test_request_help_maps_to_recruitment_contract_offer
test_hire_support_includes_payment_terms
test_defer_no_partner_creates_blocker
test_follow_leader_uses_existing_contract_influence
test_bridge_does_not_bypass_social_appraisal
test_bridge_does_not_directly_transfer_gold
```

---

# Task 9 — Implement party objective alignment

## Description

Existing party influence injects leader objective into member scoring. Phase 7 needs a higher-level validation:

```text
Are party members actually aligned enough to cooperate?
```

This should not force perfect sync. Members still have agency.

## Proposed service

```python
class PartyObjectiveAlignmentService:
    def evaluate(
        self,
        leader: EntityState,
        members: tuple[EntityState, ...],
        state: AuthoritativeState,
    ) -> PartyAlignmentReport:
        ...
```

## Alignment dimensions

```text
same objective target
compatible route
acceptable risk
member survival needs
distance/cohesion
trust in leader
contract obligation
```

## Output

```python
@dataclass(frozen=True)
class PartyAlignmentReport:
    aligned_member_ids: tuple[int, ...]
    drifting_member_ids: tuple[int, ...]
    blocked_member_ids: tuple[int, ...]
    reasons: Mapping[int, str]
```

## Checklist

- [x] Leader objective is visible to members through existing contract path.
- [x] Member can reject/ignore leader objective if survival need critical.
- [x] Low trust reduces alignment.
- [x] Distance/cohesion affects alignment.
- [x] Blocked member reports reason.
- [x] Alignment does not directly teleport or force actions.
- [x] Output can create regroup/retreat/update hints.

## TDD tests

```text
tests/unit/domains/cooperation/test_phase7_party_objective_alignment.py
```

Test cases:

```text
test_member_aligns_with_trusted_leader_objective
test_member_survival_need_overrides_leader_objective
test_low_trust_member_has_lower_alignment
test_far_member_gets_regroup_hint
test_blocked_member_reports_reason
```

---

# Task 10 — Implement party cohesion and abandonment logic

## Description

Parties should not be perfect.

Members can drift, panic, abandon, betray, or rescue.

High-level causes:

```text
distance too high
leader dead
objective too risky
member low HP
member trust collapse
reward dispute
contract violation
panic
```

## Proposed service

```python
class PartyCohesionService:
    def evaluate(
        self,
        group_id: int,
        state: AuthoritativeState,
    ) -> PartyCohesionReport:
        ...
```

## Outputs

```text
stable
needs_regroup
member_drifting
member_abandoning
leader_lost
party_should_retreat
contract_violation_possible
```

## Checklist

- [x] Dead/inactive leader creates cohesion issue.
- [x] Member far from party creates regroup issue.
- [x] Member low HP can trigger retreat/abandon decision.
- [x] Low trust can increase abandonment risk.
- [x] Contract risk/pay mismatch can increase abandonment.
- [x] Abandonment creates social/consequence signal.
- [x] Does not force betrayal every time.
- [x] Deterministic under same inputs.

## TDD tests

```text
tests/unit/domains/cooperation/test_phase7_party_cohesion_service.py
```

Test cases:

```text
test_dead_leader_creates_leader_lost_issue
test_far_member_creates_regroup_issue
test_low_hp_member_may_abandon_or_request_retreat
test_low_trust_increases_abandonment_risk
test_good_trust_and_low_risk_keeps_party_stable
```

---

# Task 11 — Implement cooperation outcome learning

## Description

Cooperation must change future behavior.

Outcomes:

```text
partner helped successfully
partner protected entity
partner abandoned entity
partner stole reward later maybe
partner gave bad information
party succeeded
party failed
leader made bad decision
member saved leader
```

## Proposed service

```python
class CooperationLearningService:
    def learn(
        self,
        entity: EntityState,
        outcome: CooperationOutcomeEvent,
        state: AuthoritativeState,
    ) -> CooperationLearningResult:
        ...
```

## Updates

```text
social bond
trust history
cooperation memory
future partner preference
source/leader trust
betrayal record if severe
strategic concern/blocker if repeated
```

## Checklist

- [x] Successful cooperation increases trust slightly.
- [x] Rescue/protection increases trust more.
- [x] Abandonment decreases trust.
- [x] Betrayal creates stronger negative memory.
- [x] Repeated reliable partner increases future candidate score.
- [x] Repeated unreliable partner decreases future candidate score.
- [x] Learning is bounded.
- [x] One event does not create extreme trust swing unless severe.

## TDD tests

```text
tests/unit/domains/cooperation/test_phase7_cooperation_learning.py
```

Test cases:

```text
test_successful_party_increases_partner_trust_slightly
test_rescue_increases_partner_trust_more
test_abandonment_decreases_trust
test_betrayal_creates_negative_memory
test_reliable_partner_preferred_in_future
test_trust_delta_is_bounded
```

Do not duplicate existing social bond update tests. These tests should prove that **cooperation outcomes** feed future cooperation choice.

---

# Task 12 — Add cooperation integration phase

## Description

Add a bounded phase.

Do not evaluate all possible pairs every tick.

## Trigger conditions

```text
objective risk too high
help need created
new suitable partner nearby
contract offer received
party member far away
leader objective changed
member low HP
party combat outcome happened
cooperation outcome event happened
```

## Skip conditions

```text
entity dead/inactive
no help need
no active cooperation contract
cooperation cooldown active
budget exhausted
feature flag disabled
```

## Proposed phase

```text
CooperationPhase:
  1. evaluate help needs
  2. get scoped partner candidates
  3. evaluate partner fit
  4. choose cooperation posture
  5. map to contract/action intent
  6. evaluate party alignment/cohesion for active parties
  7. process cooperation outcome learning
  8. emit trace events
```

## Checklist

- [x] Phase is feature-flagged initially.
- [x] Phase uses scoped candidate search.
- [x] Phase does not run all-pairs partner matching.
- [x] Phase skips entities without help need or active party.
- [x] Phase respects existing contract appraisal.
- [x] Phase respects strategic budget.
- [x] Phase emits trace events.
- [x] Deterministic under same seed/input.

## TDD tests

```text
tests/integration/domains/cooperation/test_phase7_cooperation_phase.py
```

Test cases:

```text
test_phase_skips_entity_without_help_need
test_phase_runs_when_help_need_exists
test_phase_uses_scoped_partner_candidates
test_phase_respects_feature_flag
test_phase_does_not_all_pairs_scan
test_phase_outputs_contract_intent_not_direct_contract_mutation
test_phase_processes_party_cohesion_for_active_group
```

---

# Task 13 — Add Phase 7 scenario tests

These are the important TDD tests.

## Scenario 7.1 — Risky objective creates help request

```text
Entity:
- wants wolf hunt
- self capability says wolf is risky
- trusted ally nearby
- ally has compatible combat role

Expected:
- help need created
- trusted ally selected
- cooperation posture = REQUEST_HELP or HIRE_SUPPORT
- solo route rejected because risk too high
```

Forbidden:

```text
entity attacks risky target alone with no explanation
contract created without appraisal path
global scan of all entities
```

---

## Scenario 7.2 — No good partner causes defer

```text
Entity:
- risky objective
- no trusted/available partner

Expected:
- cooperation posture = DEFER_NO_PARTNER or choose safer route
- blocker records no suitable partner
```

---

## Scenario 7.3 — Brave vs cautious cooperation difference

```text
Same world:
- brave entity
- cautious entity

Expected:
- brave entity may go solo or probe
- cautious entity more likely requests help/defer
- both choices valid and traceable
```

---

## Scenario 7.4 — Low-trust partner rejected despite good role fit

```text
Candidate:
- strong combat fit
- low trust / prior betrayal

Expected:
- candidate rejected or heavily penalized
- reason includes trust/betrayal
```

---

## Scenario 7.5 — Party member follows leader but survival can override

```text
Member:
- active recruitment contract
- leader has objective
- member has critical low HP

Expected:
- leader objective is considered
- member survival need can override
- no forced suicidal sync
```

This directly extends the existing leadership-influence idea without duplicating it.

---

## Scenario 7.6 — Abandonment changes future cooperation

```text
Entity A hires B.
B abandons A during danger.
Later A needs help again.

Expected:
- A’s trust in B decreases
- B is rejected or lower ranked next time
- trace references prior abandonment
```

---

## Scenario 7.7 — Successful rescue creates preferred ally

```text
Entity A nearly dies.
Entity B helps/protects A.
Later A needs support.

Expected:
- B has higher partner score
- A prefers B over neutral candidate if cost/role comparable
```

## Test file

```text
tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py
```

## Checklist

- [x] Scenarios assert cooperation posture, not exact movement.
- [x] Scenarios assert partner selection/rejection reasons.
- [x] Scenarios assert future behavior changes after outcome.
- [x] Scenarios do not duplicate basic contract appraisal.
- [x] Scenarios do not duplicate arena group coordination.
- [x] Scenarios are deterministic.
- [x] Each scenario has at least one forbidden behavior assertion.

---

# Task 14 — Add cooperation trace events

## Event types

```text
HelpNeedDetected
PartnerCandidateConsidered
PartnerSelected
PartnerRejected
CooperationDecisionSelected
CooperationContractProposed
PartyObjectiveAligned
PartyCohesionIssueDetected
PartyAbandonmentDetected
CooperationOutcomeLearned
PartnerTrustUpdated
```

## Example

```yaml
event_type: PartnerRejected
entity_id: 1
candidate_id: 3
reason: "low trust from prior abandonment"
fit_score: 0.28
trust_score: 0.15
```

## Checklist

- [x] Events include reason.
- [x] Events include selected/rejected candidates.
- [x] Events include trust/fit score.
- [x] Events include objective/help need link.
- [x] Events emitted only on meaningful change.
- [x] Events do not mutate authoritative state.
- [x] Event volume bounded.
- [x] Existing observability parity tests still pass.

## TDD tests

```text
tests/unit/domains/cooperation/test_phase7_cooperation_events.py
```

Test cases:

```text
test_partner_selected_event_contains_fit_and_reason
test_partner_rejected_event_contains_trust_reason
test_help_need_event_links_to_objective
test_cooperation_learning_event_contains_future_effect
test_event_generation_does_not_change_state_hash
```

---

# Task 15 — Add Phase 7 performance gates

## Required metrics

```text
cooperation_evaluations_total
help_needs_detected_total
partner_candidates_considered_total
partner_fit_evaluations_total
cooperation_decisions_total
party_cohesion_checks_total
cooperation_learning_updates_total
avg_cooperation_phase_ms
p95_cooperation_phase_ms
max_candidates_per_entity
skipped_due_to_budget
```

## Performance tests

```text
10 entities, 500 ticks
100 entities, 500 ticks
500 entities, 200 ticks
100 entities with many possible allies
50 active parties
```

## Checklist

- [x] Partner candidates capped.
- [x] Candidate search scoped by spatial/social index.
- [x] No all-pairs scan.
- [x] Party cohesion checked only for active parties.
- [x] Feature flag OFF matches old behavior.
- [x] Feature flag ON stays inside agreed overhead.
- [x] Determinism hash stable.
- [x] Performance report written.

## Test file

```text
tests/perf/test_phase7_social_cooperation_budget.py
```

---

# Phase 7 test files to add

```text
tests/unit/domains/cooperation/test_phase7_cooperation_boundary.py
tests/unit/domains/cooperation/test_phase7_cooperation_postures.py
tests/unit/domains/cooperation/test_phase7_help_need_evaluator.py
tests/unit/domains/cooperation/test_phase7_partner_candidate_provider.py
tests/unit/domains/cooperation/test_phase7_partner_fit_evaluator.py
tests/unit/domains/cooperation/test_phase7_cooperation_decision_service.py
tests/unit/domains/cooperation/test_phase7_cooperation_intent_bridge.py
tests/unit/domains/cooperation/test_phase7_party_objective_alignment.py
tests/unit/domains/cooperation/test_phase7_party_cohesion_service.py
tests/unit/domains/cooperation/test_phase7_cooperation_learning.py
tests/unit/domains/cooperation/test_phase7_cooperation_events.py

tests/integration/domains/cooperation/test_phase7_cooperation_phase.py
tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py
tests/perf/test_phase7_social_cooperation_budget.py

docs/test_coverage/phase7_party_social_cooperation_coverage.md
```

---

# Phase 7 non-goals

Do **not** implement these yet:

```text
full diplomacy system
complex faction politics
romance/family simulation
large-scale reputation economy
guild hierarchy
multi-party negotiation
party loot split economy
social deception network
political propaganda
settlement leadership
```

Also do **not** duplicate existing tests for:

```text
basic recruitment appraisal
basic contract lifecycle
public vs private trust priority
basic social bond update
arena group formation
combat damage
quest reward
```

Those already exist in the uploaded test export and current source/test surface.

---

# Phase 7 completion criteria

Phase 7 is done when this is true:

```text
An entity can recognize that an objective is too risky or inefficient alone,
identify suitable partners,
choose whether to ask for help or go solo,
form cooperation through existing contract systems,
coordinate with a leader without losing individual agency,
learn from cooperation outcomes,
and change future partner choice.
```

Minimum proof:

```text
risky objective creates help need
trusted compatible partner is selected
bad partner is rejected with reason
no partner leads to defer/safer route
survival can override leader objective
abandonment reduces future partner preference
rescue/success increases future partner preference
cooperation overhead remains bounded
```

---

# Priority Plan

## What changes in Phase 7

Before Phase 7:

```text
social contracts exist
party influence exists
```

After Phase 7:

```text
social cooperation becomes a meaningful route for survival, risk handling, and progression
```

## Implementation order

```text
1. Coverage audit
2. Cooperation domain boundary
3. Cooperation posture vocabulary
4. HelpNeedEvaluator
5. PartnerCandidateProvider
6. PartnerFitEvaluator
7. CooperationDecisionService
8. Cooperation intent/contract bridge
9. Party objective alignment
10. Party cohesion/abandonment logic
11. Cooperation outcome learning
12. Cooperation phase integration
13. Scenario tests
14. Trace events
15. Performance gates
```

## What to stop

Stop treating party behavior as only:

```text
active contract -> follow leader objective
```

That is useful but incomplete.

The better loop is:

```text
risk/objective need
-> help need
-> partner selection
-> contract/cooperation
-> aligned action
-> outcome
-> trust/memory update
-> future cooperation changes
```

## Consequence if ignored

The engine will have social contracts and groups, but cooperation will still feel mechanical.

Entities may technically recruit or follow, but they will not seem to understand:

```text
I need help.
I trust this person.
This person abandoned me before.
This objective is too dangerous alone.
This ally saved me.
I should cooperate differently next time.
```

Phase 7 turns social systems into life-changing behavior.
