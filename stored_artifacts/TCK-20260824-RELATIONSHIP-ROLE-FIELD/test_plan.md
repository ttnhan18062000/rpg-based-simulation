---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260824-RELATIONSHIP-ROLE-FIELD
artifact_type: test_plan
tags: [social]
---

# Test Plan — TCK-20260824-RELATIONSHIP-ROLE-FIELD

## Regression Surface

**Unit — social:**
- `tests/unit/social/test_party_composition.py` — all 16 existing tests, including the 3 direct
  `PartyCompositionScorer.score(...)` cases and the `AdventureRouteGenerator.generate()` FORM_PARTY
  tests. Must stay green with a `NEUTRAL`-default role on every bond (no `role` kwarg passed).
- `tests/unit/social/test_relationships.py` — `RelationshipService.process_update()` bond-delta
  application/clamping. Must stay green: adding `role_set` handling must not perturb
  familiarity/sentiment/last_interaction_tick clamping logic already covered here.
- `tests/unit/social/test_social_bonds.py` — direct `SocialBond` construction/behavior tests.
- `tests/unit/social/test_party_agency.py` — delta application, clamping, place attachment (per
  `docs/simulation/social_systems_contract.md`'s own Regression Tests list).
- `tests/unit/social/test_social_party_regression.py`, `test_appraisal_logic.py`,
  `test_contract_lifecycle.py`, `test_contract_lifecycle_phase7.py`, `test_domain_7_social.py`,
  `test_reputation_learning.py`, `test_recruitment.py`, `test_betrayal_consequence.py`,
  `test_social_memory.py` — all construct `SocialBond(...)` via keyword args only; must remain
  unaffected by an additive default-valued field.
- `tests/unit/ai/goals/test_social_contract_goal_scorer.py` — constructs `SocialBond` via keyword
  args with `bonds={...}`; must remain unaffected.
- `tests/unit/progression/test_lifecycle.py` — heir-selection logic (SOC-245) reads
  `bond.familiarity`/`bond.sentiment`/`bond.last_interaction_tick` only; confirm it does not break
  on an added field (dataclass field access is unaffected by additive fields, but the test
  constructs `SocialBond(...)` directly with 4 positional-looking-but-keyword args — verify still
  keyword).
- `tests/unit/strategic/test_social_contract_materialization.py` — constructs bonds via `.social(...)`.

**Integration:**
- `tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py` — full contract
  lifecycle (offer → appraisal → accept/breach); must stay green since `appraise_contract()` is not
  modified by this ticket.

**Determinism / serialization:**
- Any test exercising `EntityState.to_canonical_dict()` / hash-based determinism checks that
  transitively include `social.bonds` (`asdict(v)` at `src/core/state.py:732`) — confirm the new
  `role` field serializes as a plain string (via `(str, Enum)`, matching `PartyRole`'s existing
  pattern) and does not break JSON/canonical-dict round-tripping or hash stability for bonds that
  omit `role` (default `NEUTRAL` must canonicalize identically across runs).

**Group/tactical (read-only bond consumers, should be entirely unaffected):**
- `tests/unit/social/test_groups.py` — trust pipeline, hard reject gates, bond formation (per
  `docs/simulation/social_systems_contract.md`'s Regression Tests list). `GroupSystem` never passes
  `actor` to `PartyCompositionScorer.score()`, so the new role-affinity term must not change any
  group-formation outcome here.

## New Tests Required

- **`test_social_bond_role_defaults_to_neutral`**
  Category: unit
  Verifies: `SocialBond(target_id=X)` constructed without `role` has `role == RelationshipRole.NEUTRAL`;
  existing 4-field construction/equality/serialization is unchanged.
  Location: `tests/unit/social/test_social_bonds.py`

- **`test_social_bond_role_set_via_authoritative_update_only`**
  Category: unit / architecture guard
  Verifies: `SocialBondUpdate(target_id=X, role_set=RelationshipRole.FRIEND)` passed through
  `RelationshipService.process_update()` produces a bond with `role == FRIEND`; a bond's `role` never
  changes as a side effect of `familiarity_delta`/`sentiment_delta`-only updates (role persists
  across unrelated deltas, mirroring how `last_interaction_tick` persists when
  `last_interaction_tick_set is None`).
  Location: `tests/unit/social/test_relationships.py`

- **`test_process_update_role_set_none_preserves_existing_role`**
  Category: unit
  Verifies: an update with `role_set=None` on a bond that already has `role=RIVAL` leaves `role`
  unchanged after `process_update()` — confirms the set-if-provided (not overwrite-with-default)
  semantics, same pattern as `last_interaction_tick_set`.
  Location: `tests/unit/social/test_relationships.py`

- **`test_party_composition_score_reflects_candidate_role`**
  Category: unit
  Verifies (directly satisfies the ticket's core AC): two otherwise-identical candidate pools —
  same `familiarity`/`sentiment` on every bond, same personalities/kinds — produce a measurably
  different `PartyCompositionScorer.score(entities, actor=actor)` when one candidate's bond `role`
  is `FRIEND` vs `RIVAL` vs `NEUTRAL` (fixed familiarity/sentiment held constant across all three
  cases). Assert `score(pool_with_friend) > score(pool_with_neutral) > score(pool_with_rival)`, or
  equivalent strict inequality per whatever sign convention Plan finalizes.
  Location: `tests/unit/social/test_party_composition.py`

- **`test_party_composition_score_role_term_is_zero_for_all_neutral_pool`**
  Category: unit / anti-drift guard
  Verifies: with every candidate's bond `role == NEUTRAL` (or no bond at all), `score()`'s output is
  bit-identical to the pre-existing (pre-this-ticket) formula output — i.e. the new term contributes
  exactly `0.0`, preserving §7.1/§7.2's bit-identical formulas. This is the regression guard that
  proves the new term is additive, not a silent rescale.
  Location: `tests/unit/social/test_party_composition.py`

- **`test_party_composition_score_role_term_requires_actor`**
  Category: unit
  Verifies: calling `score(entities)` without `actor` (every pre-existing call site's exact usage)
  ignores role entirely and reproduces the base role-diversity/OCEAN score, same as it already does
  for the pre-existing trust term (mirrors the existing actor-omitted test for SOC-244).
  Location: `tests/unit/social/test_party_composition.py`

- **`test_social_bond_role_canonical_dict_serializes_as_plain_string`**
  Category: unit / architecture guard
  Verifies: `EntityState.to_canonical_dict()` on an entity with a `FRIEND`/`RIVAL`-tagged bond
  produces a JSON-serializable dict where `bonds[...]["role"]` is the plain string value (e.g.
  `"friend"`), not an `Enum` object — confirms `(str, Enum)` choice preserves determinism-hash
  serialization behavior identically to how `PartyRole` already serializes elsewhere.
  Location: `tests/unit/social/test_social_bonds.py`

## Scoped Pytest Commands

```
pytest tests/unit/social/ -m "not slow" -v
pytest tests/unit/ai/goals/test_social_contract_goal_scorer.py -m "not slow" -v
pytest tests/unit/strategic/test_social_contract_materialization.py -m "not slow" -v
pytest tests/unit/progression/test_lifecycle.py -m "not slow" -v
pytest tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py -m "not slow" -v
```

Never: `pytest tests/`.

## Anti-Drift Test Guards

- **`test_party_composition_score_role_term_is_zero_for_all_neutral_pool`** (above) is the primary
  guard against the new term silently changing today's output for the overwhelmingly common
  all-`NEUTRAL` case (every bond in every save file predating this ticket).
- **A guard against `RIVAL` leaking into nemesis mechanics**: add or extend an existing nemesis test
  (e.g. in `tests/unit/social/test_social_memory.py` or `test_groups.py`, wherever
  `nemesis_ids`/routing-avoidance/cooperation-refusal is already tested) to assert that a bond tagged
  `RIVAL` with `grudge_history` below the `3.0` promotion threshold does **not** appear in
  `nemesis_ids` and does **not** trigger any nemesis-gated behavior (routing avoidance, cooperation
  refusal, AVENGE directive creation) — proves the two dimensions stay independent per the
  investigation's Reconciliation section.
- **A guard against `GroupSystem` drift**: confirm `tests/unit/social/test_groups.py`'s existing
  group-formation assertions are unaffected by candidates whose bonds carry a non-`NEUTRAL` `role` —
  since `GroupSystem` never passes `actor`, this proves the new term is correctly gated behind the
  `actor`-supplied branch and does not leak into the `actor=None` code path.
- **A guard against cross-role-concept confusion**: a lightweight test (or an assertion added to an
  existing test) confirming `RelationshipRole` and `PartyRole` are genuinely distinct enum classes
  with non-overlapping member sets (e.g. `set(RelationshipRole) & set(PartyRole) == set()` is not
  even meaningfully comparable since they're different types — the real guard is that no code
  anywhere does `RelationshipRole(some_party_role_value)` or vice versa; a static/import-level check
  is sufficient, no new runtime test strictly required beyond normal type-checking).
- **`appraise_contract()` and `PartnerFitEvaluator` untouched**: no new test should reference `role`
  from either of these — their existing test suites
  (`tests/unit/social/test_appraisal_logic.py`, any `PartnerFitEvaluator`-specific tests) passing
  unmodified is itself the guard that this ticket did not silently expand into the explicitly
  out-of-scope second consumer.
