---
status: active
layer: mechanics
authority: P1
audience: agent
tags: [content, architecture]
---

# Core RPG Knowledge/Belief Axis Proposal

Date: 2026-09-02

Status: brainstorming proposal for review

Scope: the expected simulation after the proposed core-RPG roadmap and accepted design portfolio are
available, focused specifically on what an entity knows or believes about the world, as distinct from what
is objectively true in `AuthoritativeState` and from `SocialComponent`'s territory (what an entity believes
about *specific other entities*)

Constraint: this document does not approve implementation, change an existing plan, create tickets, or
define a player-control system

## Purpose

A fourth cross-cutting dimension, the same shape as space, time, and social/relationship above: every
entity that reasons about the world does so through it, and it is real and live today, not aspirational.
Unlike the Social axis, the gap here is not missing documentation — the existing contract docs
(`docs/simulation/belief_and_detour_contract.md`, `docs/simulation/domains/information_contract.md`) are
accurate, thorough, and actively maintained, the opposite starting condition from Social's zero coverage.
The gap is structural: two independent knowledge representations exist side by side with zero
cross-reference between them, and a real determinism gap sits underneath one of them, larger in raw field
count than the Social axis's own already-flagged gap.

## Executive proposal

Confirm directly (not assumed) that belief-vs-ground-truth divergence is genuinely modeled in this engine,
twice, independently: `StrategicComponent.beliefs: Dict[str, BeliefEntry]` and
`KnowledgeModelComponent.facts: Dict[str, KnowledgeFact]`. Name the real seam between them, resolve the
canonical-hash gap on the `BeliefEntry` side, and confirm Chronicle sits downstream of this axis rather than
inside it.

## Design goals

- State plainly, with evidence, that this engine actually distinguishes what an entity believes from what
  is true — a real design achievement worth naming explicitly, not just assuming.
- Name the two-system seam (`BeliefEntry` vs. `KnowledgeFact`) the way the Social axis named
  `RelationshipRole`/`nemesis_ids` — a real structural question, not yet a confirmed bug.
- Resolve the `StrategicComponent` canonical-hash gap with the same rigor the Social axis applied to its own
  determinism finding.
- Cite the existing good documentation rather than re-deriving it — this document adds the cross-cutting
  account those per-file docs cannot provide individually, it does not replace them.

## Non-goals

- This document does not propose unifying `BeliefEntry` and `KnowledgeFact` into one system — it names the
  question of whether they should be, without answering it.
- It does not re-litigate Chronicle, which is confirmed downstream (a stateless compression/rendering
  pipeline over real recorded events, not subjective belief) — out of scope here, already correctly placed
  in the Social axis's own per-idea table as "Chronicle-adjacent."
- It does not propose new SimQ pillars, new rumor-propagation mechanics, or new trust-decay formulas —
  `information_contract.md`'s trust-propagation deltas are already documented as implementation-defined and
  configurable; this document does not pin new numbers to them.

## 1. The real model, verified directly

### 1.1 Two live, separate per-entity epistemic stores

**`StrategicComponent.beliefs: Dict[str, BeliefEntry]`** (`src/core/strategic.py:399`). Note:
`StrategicComponent`'s own type annotation for this field is the weaker `Dict[str, Any]`, unlike its
sibling fields `leads: Dict[str, LeadState]` and `hypotheses: Dict[str, HypothesisState]`, which are
properly typed — a real type-safety gap on this specific field, not shared by its neighbors.

`BeliefEntry` (`src/systems/strategic_systems/belief.py:23-33`, confirmed against
`docs/simulation/belief_and_detour_contract.md`, that doc verified accurate): `id`, `subject`, `claim`,
`certainty` (0.0–1.0), `source` (`observation`/`rumor`/`deduction`), `source_entity_id`, `created_tick`,
`last_refreshed_tick`, `contradictions`. Contradiction/decay formula spot-checked exact in
`apply_contradiction()` (`belief.py:149-193`): certainty −0.3 per contradiction; hypothesis confidence
−0.2; lead certainty demotes `PRECISE`→`APPROXIMATE`→`VAGUE`→`EXHAUSTED`.

**`KnowledgeModelComponent.facts: Dict[str, KnowledgeFact]`** (`src/core/self_model.py:178`, part of the
live, wired `SelfModelBundle`). The component's own docstring states explicitly: *"Distinct from the world
truth or provider internal state. Only contains what the entity has actually learned or explicitly doesn't
know."* — a deliberate, documented belief/truth split, not an accident of implementation.

### 1.2 Belief-vs-truth divergence is genuinely modeled, twice

This is the central question this document set out to answer, and the answer is yes, confirmed directly:
this engine does not simply let entities read ground truth — two independent systems bound what an entity
actually knows, separate from `AuthoritativeState`'s objective record.

## 2. Conflicts and required changes

### 2.1 Two parallel, unreconciled knowledge representations

`BeliefEntry` and `KnowledgeFact` are entirely separate types with zero cross-references: no import of
`BeliefEntry` anywhere in `src/domains/information/` (which uses `KnowledgeFact` exclusively, imported from
`src/core/self_model.py`); no import of `KnowledgeFact` in `belief.py`. Two live systems an entity uses to
represent "what I know," never reconciled with each other.

Structurally the same shape as the Social axis's finding on `RelationshipRole` vs. `nemesis_ids` — two
independent signals with no stated precedence rule — but larger in scope: two entire parallel data models,
not two enum-like fields. Required direction: name which system a given consumer should prefer when both
could plausibly hold an answer about the same subject, or state explicitly that they cover genuinely
disjoint territory (e.g. `BeliefEntry` for provisional/contradictable claims, `KnowledgeFact` for confirmed
learned facts) and document that boundary where neither current doc states it.

### 2.2 A real, undocumented determinism gap on the `StrategicComponent` side

`StrategicComponent`'s canonical hash (`src/core/state.py:768-783`) covers only `current_project_id`,
`current_objective_id`, `projects`, `directives`, `blockers`, `leads`, `concerns`, `boredom`, `beliefs`.
**Not covered, with no comment explaining why**: `hypotheses`, `source_trust`, `contracts`,
`turning_points`, `candidate_zones`, `committed_intentions` — six fields excluded, larger in raw count than
the Social axis's own 5-of-15 gap.

This is not merely structural — `source_trust` (`SourceTrustEntry`) is a real, live scoring input to detour
selection (`belief_and_detour_contract.md`'s own documented `source_trust_bonus` term). Excluding it from
the canonical hash means a real behavioral input can silently diverge between two same-seed runs without
detection. Required direction: add the 6 fields to `to_canonical_dict()`, or document each one specifically
as intentionally non-authoritative — the same two-way decision the Social axis's own gap needs, applied
here with a larger field count and at least one field (`source_trust`) already confirmed behaviorally
load-bearing.

By contrast, `KnowledgeModelComponent.facts` is fully covered by its own `to_canonical_dict()`
(`self_model.py:182-190`) — the gap is specific to the `StrategicComponent`/`BeliefEntry` side, not a
property of this whole axis.

### 2.3 Chronicle confirmed downstream, not part of this axis

`docs/simulation/domains/chronicle_contract.md` (accurate, `last_verified: 2026-06-22`, its
significance-scoring formula spot-checked exact against `src/domains/chronicle/significance.py`): Chronicle
is a stateless compression/rendering pipeline over `NarrativeLedger` — real recorded events, not subjective
belief. It does not model historical bias or error the way a genuine chronicle-with-a-narrator might. This
confirms, rather than changes, the Social axis proposal's own placement of ideas 57/62 as
"Chronicle-adjacent, not `SocialComponent`."

## 3. Status: existing, planned, and new

- **Existing, live, and well-documented**: `BeliefEntry`/`belief_and_detour_contract.md`,
  `KnowledgeFact`/`information_contract.md`, Chronicle/`chronicle_contract.md` — all spot-checked accurate
  against real code in this investigation, zero discrepancies found (contrast with the Social axis, which
  found two factual errors in its one existing contract doc).
- **Existing but unreconciled**: the two-system seam (§2.1) — genuinely new territory, not previously named
  anywhere in the existing docs, since each doc is accurate about its own file and neither mentions the
  other's parallel existence.
- **Existing but incomplete**: `StrategicComponent`'s 6-field canonical-hash gap (§2.2) — not yet fixed,
  pending the same kind of decision the Social axis's 5-field gap needs.
- **Not independently verified this pass**: `ContractState`/`turning_points`/`candidate_zones`'s actual
  real-world usage and whether their canonical-hash exclusion has ever caused an observed replay mismatch;
  `HypothesisState` exclusion's real-world impact; `information_contract.md`'s trust-propagation delta
  values (documented as implementation-defined, not independently pinned to exact numbers here).

## Decisions accepted in this brainstorm

- Belief-vs-truth divergence is confirmed genuinely modeled — this is a real design property of the engine
  worth stating explicitly in any future onboarding or architecture document, not just implicitly true.
- Chronicle is confirmed downstream of this axis, not part of it — no reconciliation between Chronicle and
  either `BeliefEntry` or `KnowledgeFact` is proposed.
- The existing per-file contracts (`belief_and_detour_contract.md`, `information_contract.md`,
  `chronicle_contract.md`) are confirmed accurate and should be cited by any future ticket, not rewritten.

## Decisions still requiring review

- Whether `BeliefEntry` and `KnowledgeFact` should be formally reconciled (a stated precedence/scope rule)
  or left as genuinely disjoint systems with their boundary simply documented — not resolved here.
- Whether all 6 missing `StrategicComponent` canonical-hash fields should be added, or some legitimately
  excluded as non-authoritative — `source_trust` is the one field this investigation confirms is
  behaviorally load-bearing enough that silent exclusion looks like a real risk, not a judgment call; the
  other 5 are not independently assessed to the same confidence.
- Whether `StrategicComponent.beliefs`'s weak `Dict[str, Any]` typing (§1.1) should be tightened to match
  its sibling fields — a small, low-risk type-safety fix flagged but not scoped as a ticket here.

## References

- `docs/brainstorm/2026-09-02-core-rpg-social-relationship-axis-proposal.md` — the structural template
  this document follows, and the source of the `RelationshipRole`/`nemesis_ids` precedent this document's
  §2.1 finding mirrors
- `docs/simulation/belief_and_detour_contract.md`, `docs/simulation/domains/information_contract.md`,
  `docs/simulation/domains/chronicle_contract.md` — existing, accurate, actively-maintained contracts this
  document cites rather than replaces
- `src/core/strategic.py`, `src/systems/strategic_systems/belief.py`, `src/core/self_model.py`,
  `src/domains/chronicle/significance.py`
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` — parent roadmap, axis sections
