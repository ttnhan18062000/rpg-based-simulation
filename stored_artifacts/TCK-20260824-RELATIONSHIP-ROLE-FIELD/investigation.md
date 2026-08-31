---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260824-RELATIONSHIP-ROLE-FIELD
artifact_type: investigation
tags: [social]
---

# Investigation — TCK-20260824-RELATIONSHIP-ROLE-FIELD

## Current Behavior

### `SocialBond` — `src/core/models/social.py:5-11`
Frozen, `slots=True` dataclass, exactly 4 fields today: `target_id: int`, `familiarity: float = 0.0`,
`sentiment: float = -1.0..1.0 (0.0 default)`, `last_interaction_tick: int = 0`. No role/category
concept exists on it. `SocialComponent.bonds: Dict[int, SocialBond]` (line 34) is keyed by
counterparty entity id, held on the *viewer's own* `SocialComponent` — directed, not global.

Confirmed via a repo-wide grep (28 call sites across `src/` and `tests/`) that **every**
`SocialBond(...)` construction site uses keyword arguments exclusively — none rely on positional
ordering past `target_id`. This means a new field appended at the end with a default value is safe
for every existing construction site without modification (`src/certification/scenarios.py:248`,
`src/systems/social_systems/relationships.py:55`, and 26 more across
`tests/unit/social/*.py`, `tests/unit/progression/test_lifecycle.py`,
`tests/unit/strategic/test_social_contract_materialization.py`,
`tests/unit/ai/goals/test_social_contract_goal_scorer.py`).

### `SocialBondUpdate` / `SocialUpdate` — `src/core/updates.py:268-274` / `276-338`
`SocialBondUpdate` (frozen, slots) mirrors `SocialBond` as deltas: `target_id`, `familiarity_delta`,
`sentiment_delta`, `last_interaction_tick_set: Optional[int] = None`. The `last_interaction_tick_set`
field is the established "set-once, not a delta" pattern this ticket's `role_set` field should copy
exactly (same shape as `IdentityUpdate.life_stage_set: Optional[LifeStage] = None` at
`src/core/updates.py:227`, which is the existing precedent for an `Optional[<enum>]` set-field on an
Update dataclass).

### `RelationshipService.process_update()` — `src/systems/social_systems/relationships.py:16-99` (SOC-217, sole authoritative apply path)
Lines 51-61: rebuilds each bond via `dataclasses.replace(bond, familiarity=..., sentiment=...,
last_interaction_tick=...)` from `SocialBondUpdate` deltas, clamping familiarity to `[0.0, 1.0]` and
sentiment to `[-1.0, 1.0]`. There is no line handling a role concept today — a new
`role=b_upd.role_set if b_upd.role_set is not None else bond.role` clause slots directly into the
existing `replace(...)` call, exactly mirroring how `last_interaction_tick_set` is already handled
one line above. No other code path mutates `social.bonds` (confirmed: `prune_low_salience()`,
lines 101-118, only touches the five `*_history` dicts, never `bonds`).

### `PartyCompositionScorer` — `src/systems/social_systems/party_composition.py`
Already has an unrelated `PartyRole` enum (`str, Enum`: TANK/HEALER/DPS/SUPPORT — a *functional
combat* role, line 25-30) and an established additive-weighted-term pattern for actor-based scoring:
`TRUST_BONUS_WEIGHT: float = 0.15` (line 42), `_candidate_trust_value()` (108-121, reads
`actor.social.bonds.get(candidate.id)`, falls back to `trust_history`), `score_trust_bonds()`
(123-135, mean across the pool), folded into `score()` (137-159) as
`base_score + TRUST_BONUS_WEIGHT * trust_term`, clamped `[0.0, 1.0]`. `actor` is optional
keyword-only; every pre-existing call site omits it and reproduces the pre-existing exact output
(`generator.py:139` passes `candidates[:8]` positionally only in some paths, `actor=entity` in the
FORM_PARTY-specific one — see below). This is the identical shape a `role`-aware term needs: a new
`ROLE_AFFINITY_WEIGHT` constant, a `_candidate_role_value()` helper reading
`actor.social.bonds.get(candidate.id).role`, a `score_role_affinity()` mean-across-pool method, and
one more additive term in `score()`.

Callers: `AdventureRouteGenerator.generate()`'s FORM_PARTY branch
(`src/domains/adventure/generator.py:139`, passes `actor=entity`) and `GroupSystem`'s
ally-cohesion group formation (`src/systems/world_systems/groups.py:310`, confirmed via grep —
calls `PartyCompositionScorer.score(...)` with **no** `actor` kwarg, so it is structurally
unaffected by any new `actor`-gated term, same as it is already unaffected by the existing
trust/bonds term per `docs/simulation/social_systems_contract.md:148-149`).

### `SocialAppraisalSystem.appraise_contract()` — `src/systems/social_systems/appraisal.py:20-72`
Computes an internal `trust_score: float` (lines 39-45, reading `bond.sentiment` when a bond
exists) but the method's actual return type is `Tuple[ContractStatus, ReasonCode, Dict[str, Any]]`
— a categorical status plus a reason code, never a raw numeric score. A test asserting "measurably
different score" against this consumer would have to either inspect an intermediate local variable
(not exposed) or infer a score difference indirectly through which branch fires (e.g.
ACCEPTED vs COUNTERED at a threshold) — much weaker and more brittle than asserting a direct float
return. This confirms the ticket framing's implicit lean toward `PartyCompositionScorer`.

### `src/domains/cooperation/evaluators.py` (`PartnerFitEvaluator.evaluate()`)
Reads `requester.social.bonds.get(candidate.id)` directly (line 135-137) to override
`trust_score`. This is a **pre-existing direct read of `social.bonds`** from a domain evaluator —
explicitly named in the ticket's Out of Scope ("not a new violation to fix here, and not license to
add further coupling"). Confirmed current behavior only reads `.sentiment`; no role read exists, and
this ticket does not add one here.

### `src/systems/world_systems/groups.py`
Line 229: `bond = member.social.bonds.get(leader.id)` — read-only, used for group cohesion scoring,
unrelated to `PartyCompositionScorer`'s `actor` path (this call site never supplies `actor`, per
above). Lines 196-212/302-320: a *different* "role" concept entirely — `group.roles: Dict[id, str]`
storing tactical-combat role strings (`"LEADER"`, `"VANGUARD"`, etc., derived from
`entity.combat.tactical_role`), a 5th distinct "role" namespace already in the codebase, further
confirming why the ticket's naming constraint (avoid colliding with `PartyRole`) matters — there are
already three role-shaped concepts in play (`EntityRole` IntEnum on `identity.role`,
`PartyRole` str-Enum in `party_composition.py`, and this plain-string tactical role on
`GroupRecord.roles`), plus `IdentityUpdate.role_set: Optional[int]` (line 222) as a fourth. A new
`RelationshipRole` on `SocialBond` is a clearly distinct fifth concept, scoped only to the bond.

### `src/engine/combat.py` / `src/engine/tactical.py`
`combat.py` reads `attacker.social.bonds.items()` (line 99, ally-detection for friendly-fire/target
selection) and writes `SocialBondUpdate(sentiment_delta=-0.1, familiarity_delta=0.05)` in 4 places
(lines 199-201, 290-292, 431-435, 465-491, 549) as the authoritative reaction to being struck by an
ally — all through `SocialUpdate`/`RelationshipService.process_update()`, never direct mutation.
None of these sites reference a role concept; adding `role` as an additive optional field does not
require touching this file, since it never constructs `SocialBondUpdate` with more than
`sentiment_delta`/`familiarity_delta`/`last_interaction_tick_set` today and the new field defaults
to a no-op (`role_set=None`). `tactical.py` reads `entity.social.bonds.get(group.leader_id)` (line
358) for movement cohesion — also read-only, unaffected.

### `src/domains/adventure/generator.py`
Line 139: `trust_term = PartyCompositionScorer.score_trust_bonds(entity, candidates[:8])`, used to
compute `confidence` for the FORM_PARTY route, **separately** from the `comp_score` call that feeds
`expected_benefit`. This is the generation-time (not scoring-time) trust term documented in
`docs/mechanics/04_strategic_cognition.md` §7.2. This ticket does not need to touch this file — see
Risks/Recommendation below for why.

## Mechanics / Engine Constraints

- **SOC-217** (`docs/simulation/social_systems_contract.md:173-175`, "Mutation rules"): all social
  state changes go through `SocialUpdate → RelationshipService.process_update() → authoritative
  apply`; direct mutation of `SocialComponent` fields (including `bonds`) outside this path is
  prohibited. The new `role` field must only ever be set via `SocialBondUpdate.role_set` +
  `process_update()`, never via direct `dataclasses.replace()` elsewhere.
- **§7 formula shape** (`docs/mechanics/04_strategic_cognition.md:719-757`): `PartyCompositionScorer.score()`'s
  additive-term pattern is already the documented, certified shape:
  `base_score = 0.6*role_diversity + 0.4*ocean_compat`, then
  `score = clamp(base_score + 0.15*trust_term, 0.0, 1.0)` when `actor` is supplied. A new role-affinity
  term must slot in as a third additive term inside the same `clamp(...)`, not replace or rescale the
  existing two documented weights (AC4-equivalent bit-identity concern carried over from the sibling
  ticket's Anti-Drift Hazards).
- **Durable-state / read-only rule** (CLAUDE.md Architecture Rule): `PartyCompositionScorer.score()`
  and all its helper methods are pure/read-only (confirmed: no `dataclasses.replace`/`*Update`
  construction anywhere in `party_composition.py`). A role-affinity read must remain a throwaway
  local value, never written back to `entity.social`.
- **Extension rule 2** (`docs/simulation/social_systems_contract.md:190`, "To add a new relationship
  dimension: extend `SocialComponent`/`SocialUpdate`, add clamping in
  `RelationshipService.process_update()`. Update consumers that read the new dimension.") — this
  ticket is a direct, named instance of this documented extension path. Role is categorical (an
  enum, not a clamped float), so "clamping" in `process_update()` is replaced by a straight
  set-if-provided assignment (matching `last_interaction_tick_set`'s existing pattern, not the
  `max(...,min(...))` pattern used for the float fields).

## Docs Requiring Update

- `docs/mechanics/04_strategic_cognition.md`: needs a new §7.3 subsection (following the §7.1/§7.2
  precedent already in the file) documenting the `RelationshipRole` enum values, the new
  `ROLE_AFFINITY_WEIGHT` constant and its formula, and confirming §7.1's role-diversity/OCEAN
  weights and §7.2's `TRUST_BONUS_WEIGHT` term stay bit-identical.
- `docs/parity_ledger/social_narrative.yaml`: new entry `SOC-247` (confirmed next available id via
  `tools/gate_checks/parity_updater_static.py::next_available_id('social_narrative.yaml')`)
  documenting the `SocialBond.role` field, `SocialBondUpdate.role_set`, the
  `RelationshipService.process_update()` set-if-provided clause, and the
  `PartyCompositionScorer.score()` role-affinity term, with `status: verified`, `priority: P1` (same
  tier as sibling SOC-244), `proof_type: parity`, and a `test_path` pointing at the new dedicated
  test (see test_plan.md).
- `docs/simulation/social_systems_contract.md`: the existing `## Social bonds` subsection (lines
  68-71, under "Relationships — relationships.py") currently states `SocialBond` is
  "`familiarity`, `sentiment` (−1.0 to 1.0), `last_interaction_tick`" — this line must be updated to
  add `role` and its enum values, plus a one-line addition to the `## Party Composition —
  party_composition.py` section (lines 135-150) documenting the new additive term alongside the
  existing SOC-244 trust/bonds description.

The `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md` design doc
(path: `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`, under
`docs/architecture/`) is not required to change for this ticket: this ticket's recommended consumer
(`PartyCompositionScorer.score()` directly) does not touch `AdventureRouteGenerator.generate()` or
`AdventureRouteOption`/`scoring.py` at all (see Risks/Recommendation below), so none of that doc's
FORM_PARTY-related architectural caveats are affected.

The `docs/simulation/domains/adventure_contract.md` doc (path:
`docs/simulation/domains/adventure_contract.md`, under `docs/simulation/domains/`) is not required
to change for this ticket, for the same reason: the recommended wiring stays entirely inside
`party_composition.py` and does not touch `generator.py`'s FORM_PARTY candidate-selection/confidence
formula or `scoring.py`'s `AdventureRouteScorer.score()`.

The `docs/parity_ledger/strategic_cognition.yaml` doc (path:
`docs/parity_ledger/strategic_cognition.yaml`, under `docs/parity_ledger/`) is not required to
change: STRAT-227's route-scoring formula (`scoring.py`) is untouched by this ticket's recommended
scope — no new `scoring.py`-level term is added, unlike the sibling TCK-20260811 ticket which did
extend STRAT-227.

## Parity Ledger Overlap

- **SOC-217** (`social_narrative.yaml`, status `verified`, priority not re-checked here but treated
  as the authoritative-mutation-path law) — this ticket's `SocialBondUpdate.role_set` +
  `RelationshipService.process_update()` extension is a direct instance of the rule SOC-217
  documents; no change to SOC-217's own text is needed, it already states the general rule
  correctly.
- **SOC-244** (`social_narrative.yaml:3349-3383`, status `verified`, priority `P1`) — documents
  `PartyCompositionScorer.score()`'s existing `actor`-based trust/bonds term
  (`TRUST_BONUS_WEIGHT=0.15`). This ticket's new role-affinity term sits in the exact same method,
  immediately adjacent in the formula (`base_score + 0.15*trust_term + <new>*role_term`). **Decision:
  add a new SOC-247 entry rather than extending SOC-244** — SOC-244's `text`/`v2_evidence` describe
  a complete, already-shipped, already-tested mechanic (trust/bonds term only); the ticket's own AC
  explicitly asks for "a new SOC-### parity_ledger entry," and role-affinity is a materially
  different data source (categorical enum vs. continuous sentiment/trust float) deserving its own
  entry, consistent with how SOC-244 itself was minted fresh rather than folded into the pre-existing
  (and mis-cited) SOC-231/SOC-232.
- **SOC-231 / SOC-232 ID-collision hazard** (documented in
  `stored_artifacts/TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY/investigation.md`, "Parity Ledger
  Overlap"): `party_composition.py`'s own module docstring cites "Logic IDs: SOC-231 (role
  diversity), SOC-232 (OCEAN compatibility)" — both are real, unrelated entries (Grief/rage urgency
  and Nemesis relation, respectively). **Do not cite SOC-231/SOC-232 for the new role-affinity work.**
  This is a pre-existing docstring bug, not to be propagated or fixed by this ticket (out of scope,
  same as it was for the sibling ticket).
- No P0 entries are touched by this ticket's scope (SOC-217/SOC-244/new-SOC-247 are all P1 or the
  general-rule SOC-217).

## Prior Work

- `stored_artifacts/TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY/`: direct structural precedent for
  extending `PartyCompositionScorer.score()`'s `actor`-based additive-term pattern. Its
  investigation.md already fully worked out: (a) the `actor` kwarg is optional/keyword-only and
  every pre-existing call site is unaffected when omitted; (b) `RelationshipService` is
  authoritative-mutation-only and must not gain a new read/lookup method — raw dict access
  (`entity.social.bonds.get(candidate.id)`) is the established read pattern for scorers; (c) the
  SOC-231/SOC-232 ID-collision hazard above; (d) `GroupSystem`'s call site never passes `actor` and
  is structurally unaffected by any `actor`-gated term (directly reused above). Its plan.md/test_plan.md
  were not re-read in full (per role guidance — investigation.md carried the material findings;
  plan.md/test_plan.md for a *prior*, already-shipped ticket are lower marginal value for a new
  ticket's own Investigate phase), but the shipped `TRUST_BONUS_WEIGHT` implementation in
  `party_composition.py` (read directly, Current Behavior above) confirms the plan.md's design was
  followed exactly as documented in SOC-244 and §7.2.
- `tests/unit/social/test_party_composition.py`: 16 existing tests, all `PartyCompositionScorer.score(...)`
  calls use only positional `entities` or `actor=` keyword — confirmed no positional-arg test would
  break from a new keyword-only parameter/constant.
- No stored artifact exists yet documenting `SocialAppraisalSystem.appraise_contract()`'s internal
  `trust_score` in enough depth to compare it as a consumer candidate beyond what Current Behavior
  above already established directly from source.

## Recommendation — Two Required Design Decisions

### 1. Enum name and values: `RelationshipRole` (`src/core/models/social.py`, alongside `SocialBond`)

`class RelationshipRole(str, Enum)` — matches `PartyRole`'s existing `(str, Enum)` shape (confirmed
JSON/canonical-dict safe: `to_canonical_dict()` at `src/core/state.py:732` calls
`asdict(v)` on each bond; a `str`-subclassing Enum member serializes natively as its string value
under `json.dumps`, exactly as `PartyRole` already does elsewhere — no serialization code needs to
change).

Values:
- `NEUTRAL = "neutral"` — **default**, matches ACs "NEUTRAL/UNSET default" wording; every bond
  constructed without specifying `role` continues to canonicalize/serialize/compare identically to
  today (an omitted field with an enum default is exactly as additive as `last_interaction_tick`'s
  own `= 0` default was when it was added).
- `FRIEND = "friend"` — a bond the viewer actively favors socially beyond raw sentiment/trust.
- `RIVAL = "rival"` — a bond the viewer treats as an active social competitor/adversary.

**Reconciliation with `nemesis_ids`** (`SocialComponent.nemesis_ids: Set[int]`,
`src/core/models/social.py`, promoted from `grudge_history >= 3.0` per
`docs/simulation/social_systems_contract.md:84`): `RIVAL` is explicitly **not** a synonym or trigger
for nemesis status. `nemesis_ids` is a one-way ratchet with real mechanical side effects (adventure
routing avoidance, cooperation refusal, AVENGE directives) driven purely by accumulated
`grudge_history`. `RelationshipRole.RIVAL` is a lightweight, freely bidirectional-settable
categorical tag on a `SocialBond`, set only through the same authoritative `SocialUpdate` path as
`sentiment`/`familiarity`, with **no** read anywhere that promotes it into `nemesis_ids` or gates any
nemesis-only mechanic. The two dimensions may co-occur (a nemesis could also be tagged `RIVAL` on
its bond) but are independent durable facts, consistent with how `sentiment` (private) and
`public_reputation` (separate durable field, SOC-193) already coexist without one driving the
other. This ticket must not add any code path that reads `role == RIVAL` to set/check
`nemesis_ids`, or vice versa — that would be a second, competing implementation of the same
mechanical consequence and a durable-state modeling violation (CLAUDE.md's "one typed model per
durable fact").

I considered a 4th value (`ALLY`/`MENTOR`) but rejected it as unrequested scope beyond the ticket's
explicit AC wording ("enum, NEUTRAL/UNSET default") — YAGNI; three values (NEUTRAL default plus one
positive/one negative) is the minimum needed to make the consumer's "measurably different score" AC
concretely testable in both directions, and additional values are cheap to add later as a strictly
additive enum-member change if a future ticket needs them.

### 2. Consumer: `PartyCompositionScorer.score()` — **recommended over `SocialAppraisalSystem.appraise_contract()`**

Evidence (from Current Behavior above):
- `PartyCompositionScorer.score()` returns a direct `float` (0.0-1.0). A test can assert
  `score_a != score_b` for two pools differing only in one candidate's bond role, with fixed
  familiarity/sentiment, in one line — exactly the AC's literal wording ("produce a measurably
  different score ... asserted by a new test with fixed familiarity/sentiment").
- `appraise_contract()` returns `Tuple[ContractStatus, ReasonCode, Dict[str, Any]]` — no numeric
  score is exposed at the return boundary. Its internal `trust_score` float exists only as a local
  variable (lines 39-45); asserting a "measurable difference" would require either exposing that
  internal value (a signature change touching every caller) or asserting a branch/threshold crossing
  indirectly (`ContractStatus` changes), which is a weaker, more brittle test and a larger blast
  radius for a P2 ticket.
- `PartyCompositionScorer.score()` already has the exact `actor`-gated additive-term precedent
  (SOC-244/§7.2) to extend — lower implementation risk, smaller diff, and directly reuses an
  already-certified formula shape rather than inventing a new one inside `appraisal.py`.

**Recommended wiring scope**: extend `party_composition.py` only — add `ROLE_AFFINITY_WEIGHT`
(suggest `0.10`, one tier below `TRUST_BONUS_WEIGHT=0.15` since it is a coarser categorical signal
vs. a continuous one — Plan should confirm/finalize the exact constant), `_candidate_role_value()`
(reads `actor.social.bonds.get(candidate.id).role`, defaulting to `NEUTRAL`/`0.0` contribution when
no bond exists), `score_role_affinity()` (mean across pool: `FRIEND -> +1.0`, `RIVAL -> -1.0`,
`NEUTRAL -> 0.0`), folded into `score()`'s existing `if actor is None: return base_score` /
`else:` branch as a third additive term inside the same final `clamp(...)`. **Do not touch
`generator.py`'s `confidence` formula or `scoring.py`/`AdventureRouteScorer`/STRAT-227** — the
sibling ticket (TCK-20260811) touched both `comp_score` (via `expected_benefit`) and a separate
`confidence` formula in `generator.py` because its AC explicitly required FORM_PARTY route
generation-time behavior to change; this ticket's AC only requires *a* consumer to produce a
measurably different score, which `PartyCompositionScorer.score()` alone already satisfies. Keeping
`generator.py`/`scoring.py` untouched is the minimal-footprint reading of "wire **one** real
consumer" and avoids re-opening STRAT-227 or the FORM_PARTY confidence formula for a ticket whose
scope does not require it — Plan may revisit this if it finds a stronger reason to also flow the
term into `generator.py`, but should treat that as an explicit scope expansion requiring
justification, not a default.

## Risks and Open Questions

1. **Not blocking — `RelationshipService` still has no read/lookup helper.** Confirmed again for this
   ticket: `process_update()`/`prune_low_salience()` are the only two methods, both
   authoritative-mutation-only. The new role-affinity read must use raw `bond.role` dict/attribute
   access from within `party_composition.py`, matching every existing consumer's pattern
   (`_candidate_trust_value()` already does this for `sentiment`). Do not add a read method to
   `RelationshipService`.
2. **Not blocking — exact `ROLE_AFFINITY_WEIGHT` magnitude is a Plan-phase calibration decision.**
   I've recommended `0.10` (below `TRUST_BONUS_WEIGHT=0.15`) with a stated rationale (coarser signal),
   but this is not empirically derived from any existing formula in this codebase — Plan should treat
   it as a documented, deliberate default rather than a verified constant, same caveat the sibling
   ticket's investigation flagged for its own `TRUST_BONUS_WEIGHT` precedent-setting.
3. **Not blocking — `NEUTRAL` vs `UNSET` naming.** The AC text says "NEUTRAL/UNSET default" (an
   either/or), and I've recommended `NEUTRAL` as the concrete member name (paired with
   `familiarity`/`sentiment`'s own "0.0 = no signal" convention, i.e. `NEUTRAL` doubles as both "role
   deliberately neutral" and "role never set" — there is no behavioral difference between the two
   readings since nothing before this ticket ever wrote a bond, so no bond in existing save data can
   be distinguished as "explicitly neutral" vs "never touched"). If Plan or a later reviewer wants a
   harder split (e.g. `UNSET` meaning "never evaluated" vs `NEUTRAL` meaning "evaluated as neutral"),
   that is an additive enum change, not a blocker for this ticket.
4. **Disclosed, not blocking — `PartnerFitEvaluator` and `appraisal.py`'s `trust_score` remain
   role-blind after this ticket.** Per Out of Scope, this is intentional; a future ticket could wire
   role into either, but this ticket's single AC-required consumer is
   `PartyCompositionScorer.score()`.

## Anti-Drift Hazards

- **Do not let `RIVAL` read or write `nemesis_ids`, `grudge_history`, or trigger any of the
  nemesis-only mechanics (routing avoidance, cooperation refusal, AVENGE directives).** These remain
  exclusively driven by `grudge_history >= 3.0`, per `docs/simulation/social_systems_contract.md:84`.
  A `RIVAL`-tagged bond with `sentiment` still high and no accumulated grudge is not a nemesis and
  must not behave like one anywhere.
- **Do not touch `PartyRole` (TANK/HEALER/DPS/SUPPORT), `EntityRole` (`IntEnum`, HERO/MONSTER/...),
  `IdentityUpdate.role_set` (int), or `GroupRecord.roles` (tactical-role strings).** Four
  pre-existing, unrelated "role" concepts already coexist in this codebase (see Current Behavior);
  `RelationshipRole` must remain scoped to `SocialBond` only and never be confused with, aliased to,
  or read interchangeably with any of the four.
- **Do not add a read/lookup method to `RelationshipService`.** It is authoritative-mutation-only by
  established convention (SOC-217); raw dict/attribute access is the correct read pattern for
  `party_composition.py`.
- **Do not bypass `SocialUpdate`/`RelationshipService.process_update()` to set `role`.** Any direct
  `dataclasses.replace(bond, role=...)` outside `process_update()` violates SOC-217.
- **Do not touch `TRUST_BONUS_WEIGHT`, `ROLE_DIVERSITY_WEIGHT`, or `OCEAN_COMPAT_WEIGHT`** — the new
  term must be strictly additive alongside them, preserving §7.1/§7.2's bit-identical formulas when
  `role` is `NEUTRAL`/absent (i.e. `score_role_affinity()` must return `0.0` for an all-`NEUTRAL`
  pool, reproducing today's exact output for every pre-existing test).
- **Do not extend `generator.py`'s FORM_PARTY `confidence`/`expected_benefit` formulas or
  `scoring.py`/STRAT-227 as part of this ticket** unless Plan makes an explicit, justified decision
  to expand scope beyond "wire one real consumer" (see Recommendation above).
- **Do not deepen `PartnerFitEvaluator`'s existing direct `social.bonds` read** (explicit Out of
  Scope) — do not add a role read there as a "convenient" second consumer; the ticket asks for
  exactly one.
