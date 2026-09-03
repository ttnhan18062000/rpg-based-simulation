---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS
artifact_type: investigation
tags: [lifecycle, adventure]
---

# Investigation — TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS

## Current Behavior

### `LifecycleComponent` — no "dependent" concept exists today
`src/core/state.py:153-193` (`LifecycleComponent`). Relevant existing fields:
- `heir_entity_id: Optional[int] = None` (line 161) — single-valued, semantically "who inherits on
  death," not "who I am responsible for while alive." Auto-assigned on death by
  `LifecycleSystem._select_default_heir()` (see below) when unset; never read by anything *before*
  death today.
- `parent_a_entity_id` / `parent_b_entity_id: Optional[int] = None` (lines 163-164) — added by
  `TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA` (DONE, same day). These identify the *parents of
  this entity* (child→parent direction), the opposite direction from what "personal dependents"
  needs (parent/guardian→dependent direction). Confirmed by reading that ticket's Implementation
  Notes and `src/core/builder.py`'s `birth_record()`/`build_parent_bond_updates_for_birth()` — no
  reverse-direction field (parent's list of children) was added.
- No plural/list-shaped field exists anywhere on `LifecycleComponent`, `SocialComponent`, or
  `EntityState` for "entities I am responsible for." `heir_entity_id` is `Optional[int]`
  (singular); the ticket itself flags this as the open architecture question.

### `SocialComponent` / `SocialBond` — general relationship data, not dependent-specific
`src/core/models/social.py:13-57`. `SocialBond` (frozen, line 14) carries `target_id`,
`familiarity`, `sentiment`, `last_interaction_tick`, `role: RelationshipRole` (`NEUTRAL` / `FRIEND`
/ `RIVAL` — line 7-11). `SocialComponent.bonds: Dict[int, SocialBond]` (line 43) is the "PH15
Recovery: First-class bonds" map, keyed by target entity id — this is the same structure
`LifecycleSystem._select_default_heir()` already reads. There is no `RelationshipRole` value or
bond flag that means "dependent" — reusing `SocialBond.role` as-is would conflate "this is a
person I'm responsible for" with the existing FRIEND/RIVAL sentiment-classification axis, which
answers a different question ("do I like them") than "am I responsible for their wellbeing."

### `LifecycleSystem.resolve_lifecycle()` — the write-path precedent to follow
`src/systems/lifecycle_systems/lifecycle.py:37-164`. `_select_default_heir()` (lines 21-35) reads
`deceased.social.bonds`, filters to live targets (`state.entities.get(target_id)` exists AND
`target.lifecycle.active is True`), scores `0.6*familiarity + 0.4*((sentiment+1.0)/2.0)`, and
returns the winner via total-order tie-break `(-score, -last_interaction_tick, target_id)`. The
selected id is written back only via `LifecycleUpdate.heir_entity_id_set` on the *dying* entity's
own `EntityUpdate` (line 108-111) — never a direct field mutation — then applied authoritatively by
`LifecyclePatch.apply()` (`src/engine/patches.py:69-97`, specifically line 84:
`heir_entity_id=u_life.heir_entity_id_set if u_life.heir_entity_id_set is not None else
new_lifecycle.heir_entity_id`). This is the concrete precedent Plan should follow for whatever new
"dependent" field is chosen: a `*_set` field on `LifecycleUpdate`, applied in
`LifecyclePatch.apply()`, never a bare state mutation.

### `AdventureRouteScorer.score()` — full pipeline and the escort-bias precedent (§9, SOC-230)
`src/domains/adventure/scoring.py:39-381`. Full additive/multiplicative formula (docstring lines
52-53): `score = urgency + benefit + personality_bias + plan_advance_bonus + memory_adjustment +
confidence_bonus - risk_penalty - blocker_penalty`, then two *multiplicative* group-synergy
adjustments (§8, SOC-229, lines 336-355), then one more *additive* group adjustment (§9, SOC-230,
lines 357-368).

**§9 Escort Scoring (lines 357-368)** is the closest and explicitly-named precedent:
```python
if (
    group is not None
    and group.escort_target_id is not None
    and entity.id != group.escort_target_id
):
    if route.family == RouteFamily.PROTECT_TARGET:
        final_score = round(final_score + 3.0, 4)
    elif route.family == RouteFamily.OWN_SURVIVAL:
        final_score = round(max(0.0, final_score - 1.0), 4)
```
Shape to follow: a guarded `if` block placed *after* final_score is computed (post §7's
`round(max(0.0, ...))` clamp), reading state the entity/group already carries (never a new
optional scorer parameter that risks going unwired — see Risks below), applying a flat additive
delta per matching `RouteFamily`, each independently `round()`-and-floored at 0.0. This ticket's
own scope text (line 34 of the ticket) explicitly names this block as the pattern to follow.

**§4 Personality Bias (lines 206-223)** is the ticket's other named precedent (per Step 0c's
directive) but is a materially different shape: it reads *subjective personality traits*
(`bravery`/`caution`/`greed`/etc., §1) and applies a small multiplicative-weight term per
`RouteFamily`, before `plan_advance_bonus`/`memory_adjustment` and before the final
`round(max(0.0, ...))` clamp. A dependent-bias term is not a personality trait — it is a fact about
durable entity state (whether a dependent exists) — so §9's shape (post-clamp, additive,
`RouteFamily`-keyed) fits better than §4's (pre-clamp, trait-weighted). Flag for Plan: if the
bias is meant to interact with `HUNT_WEAK_ENEMY` (currently NOT read by §4's personality-bias
block — `HUNT_WEAK_ENEMY` has no personality_bias term today) or `RECOVER` (`RouteFamily.RECOVER`
already gets `caution*0.25` in §4), a §9-shaped additive term avoids conflating with the existing
caution-driven RECOVER bonus.

**Trace/observability fields**: every existing named bias term (`personality_bias`,
`plan_advance_bonus`, `memory_adjustment`, `confidence_bonus`, `risk_penalty`,
`blocker_penalty`) has a dedicated `float` field on `AdventureRouteOption`
(`src/domains/adventure/schema.py:65-73`) populated via the `dataclasses.replace(...)` at the end
of `score()` (lines 370-381). The §9 escort adjustment is the one exception — it has **no**
dedicated trace field; it mutates `final_score` directly with no separate observable term. Plan
must decide whether the new dependent bias gets its own dedicated field (matching the
majority pattern: `plan_advance_bonus`, `memory_adjustment`, `confidence_bonus`) or follows §9's
no-trace-field precedent. The majority pattern is more debuggable and is recommended, but is an
explicit Plan decision, not assumed here.

### Live-wiring check — `entity` is always passed, `group`/`faction_directives` are not
`src/ai/goals/adventure_scorer.py` (`AdventureGoalScorer.score()`) is confirmed (via
`docs/mechanics/04_strategic_cognition.md` §6.10, and direct read of the live call path) as the
**sole live adventure-decision path** today (`TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`). It
calls `AdventureDecisionService.decide()` with `faction_directives=None` unconditionally — §6.10's
faction-directive urgency-scoring block (lines 719-730 of the mechanics doc) is real code that
never fires in production because nothing threads a real directive list into this call site. This
is a concrete cautionary precedent: **if the new dependent-bias term is implemented as a new
optional `AdventureRouteScorer.score()` parameter (e.g. `dependents: Optional[...] = None`) rather
than read directly off `entity`, it risks becoming an identically dead mechanic** unless the live
call path is also verified/updated to thread it through. `entity: EntityState` itself, by
contrast, is always passed at every call site (it is the primary scoring subject) — so a
dependent-bias term that reads `entity.lifecycle.<new_field>` (or wherever the dependent field
lands) directly off the already-passed `entity` argument is live-wired for free and does not
inherit this risk. This is a strong architectural argument for reading the new field off `entity`
rather than adding a new optional parameter, and should be flagged to Plan explicitly.

## Mechanics / Engine Constraints
- **§6.9 Escort Route Scoring (SOC-230)**, `docs/mechanics/04_strategic_cognition.md:700-716` — the
  authoritative doc for the precedent block this ticket must mirror in shape (table of
  `RouteFamily` → adjustment → rationale, "Source:" line citing file/ticket).
- **§5 Succession — Default Heir Assignment**, `docs/mechanics/05_world_evolution.md:160-206` — the
  authoritative doc for the `heir_entity_id` write-path precedent; establishes the pattern
  (`LifecycleUpdate.*_set` field, applied via `LifecyclePatch.apply()`, `state.entities`
  liveness-filtered) that any new durable "dependent" field must follow if state.py/updates.py
  gain a new field.
- **Durable State Rule** (CLAUDE.md) — "If something survives beyond the current tick or current
  function call, it must have a typed model, a stable location in entity/world/registry state, a
  defined lifecycle, inspection/debug visibility, and tests." Directly governs the "durable
  dependent concept" half of this ticket's scope — it cannot be a scorer-local heuristic or a
  `reason`/`metadata` string; it must be a real typed field with a defined write path, matching
  `heir_entity_id`'s and the birth-record schema's precedent exactly.
- **Authoritative Mutation Pipeline Contract** (`docs/engine/authoritative_mutation_pipeline_contract.md`,
  cited by the DEFAULT-HEIR-ASSIGNMENT ticket's Related Docs as governing this exact write-path
  shape) — any new field must be written only through `LifecycleUpdate`/`EntityUpdate` applied via
  the authoritative apply path, never a direct mutation of frozen state (this repo's dataclasses
  are frozen; `LifecycleSystem.resolve_lifecycle()` never mutates `entity` in place, only builds
  updates — confirmed by direct read).

## Docs Requiring Update
- `docs/mechanics/04_strategic_cognition.md`: needs a new subsection (parallel to §6.9 Escort Route
  Scoring) documenting the new dependent-bias `RouteFamily` adjustment table, formula, and source
  citation — this is where §6.9/§6.10 already live and is the ticket's own AC #4 primary target.
- `docs/mechanics/05_world_evolution.md`: the Succession section (§ "Default Heir Assignment") is
  the natural home for documenting whatever new durable "dependent" field/write-path is chosen
  (parallel structure to the existing heir-assignment subsection) — also named in the ticket's own
  AC #4 as an acceptable alternate location to 04_strategic_cognition.md for the mechanic
  description; given the mechanic spans both a state-schema change (05's territory) and a
  scoring-formula change (04's territory), both docs plausibly need a touch, and Plan should decide
  the split (e.g. schema in 05, scoring table in 04, with a cross-reference each way, matching the
  05§Succession section's own precedent of cross-referencing 04§7.2 at its end).
- `docs/parity_ledger/social_narrative.yaml`: a new `SOC-2xx` entry (next available id confirmed as
  `SOC-262` — highest existing id in the file is `SOC-261`, added by
  `TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA`) must be added documenting the new bias term,
  per the ticket's own AC #4 and CLAUDE.md's Authoritative Mechanics Rule ("If logic changes,
  update the corresponding doc AND the parity ledger entry ... in the same session"). Use
  `tools/parity_ledger_writer.py:write_entry()` (the sanctioned, schema-validating path — see the
  Anti-Drift Hazards section of the memory note on raw-YAML-rewrite risk), not a raw Edit.

The `docs/core/entities.md` doc (path: `docs/core/entities.md`, under `docs/`) is not required to
change for this ticket unless Plan chooses to add a brand-new field directly to
`LifecycleComponent`: that doc's Lifecycle component-table row was already updated by the
sibling `TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA` ticket for the parent-side fields, and
would only need a further edit if this ticket adds a *new* named field to the same table (as
opposed to reusing `heir_entity_id` or extending `SocialBond`/`RelationshipRole`, which do not
live in that table). Left as Format 2 here because whether a new field lands is exactly the open
architecture question Plan must resolve first; if Plan does add a new `LifecycleComponent` field,
whoever documents `04_strategic_cognition.md`/`05_world_evolution.md` per the Format 1 bullets
above should also add a one-line table-row update to `docs/core/entities.md` at that time.

The `docs/guidelines/intentional_divergences.md` doc (path:
`docs/guidelines/intentional_divergences.md`, under `docs/`) is not required to change for this
ticket: this is a genuinely new mechanic (a new bias term for a previously-nonexistent "dependent"
concept), not a divergence from a previously-documented legacy/V2 behavior, so it does not meet
that doc's own inclusion criterion ("intentional behavior change that differs from the Mechanics
Bible").

## Parity Ledger Overlap
- **SOC-230** (`docs/parity_ledger/social_narrative.yaml:2485-2513`), status `verified`, priority
  `P1`. Covers the exact §9 escort-scoring block this ticket's new bias term sits alongside in
  `AdventureRouteScorer.score()`. Not modified by this ticket (ticket's own Out of Scope explicitly
  says so), but its `test_path` (`tests/unit/social/test_party_lifecycle.py::test_escort_target_route_scores_above_survival`,
  among others) is a regression-surface item since the new bias term lands in the same function,
  immediately adjacent to this block.
- **SOC-245** (`docs/parity_ledger/social_narrative.yaml:3416-3432`), status `verified`, priority
  `P1`. Covers `LifecycleSystem._select_default_heir()`/`resolve_lifecycle()`'s default-heir
  write-path — the precedent for whatever new durable-field write path this ticket adds. Not
  modified by this ticket unless Plan chooses to literally reuse `heir_entity_id` for "dependent"
  (in which case SOC-245's `text` would need a note about the field's dual semantics — flag to
  Plan). `test_path`: `tests/unit/progression/test_lifecycle.py::test_default_heir_tie_break_deterministic`.
- **SOC-259 / SOC-261** (`docs/parity_ledger/social_narrative.yaml`, added by the sibling
  `TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA` ticket the same day): cover the new
  `parent_a_entity_id`/`parent_b_entity_id`/`birth_tick`/`birth_city_id`/`reproduction_cooldowns`
  fields and the `SocialBond` seeding pattern at 0.8/0.8 familiarity/sentiment. No P0 entries
  found among these — none require a passing `test_path` beyond normal regression coverage, but
  are worth Plan reviewing since they establish very recent sibling precedent for the exact kind
  of `LifecycleComponent` field extension this ticket may also need.
- No P0-priority parity entries were found overlapping this ticket's scope (SOC-230, SOC-245,
  SOC-259, SOC-261 are all P1).

## Prior Work
- `tickets/done/TCK-20260824-DEFAULT-HEIR-ASSIGNMENT.md` — direct precedent for a
  `LifecycleComponent`/`LifecycleUpdate` field write-path driven by `SocialComponent.bonds` data;
  confirms `heir_entity_id_set` now has a live consumer (contradicting the atlas card's stale
  "never called by anything live" framing, per this ticket's own Request Summary).
- `tickets/done/TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA.md` — confirms the durable schema
  landed today only covers the *child→parent* direction (`parent_a_entity_id`/
  `parent_b_entity_id`), not the *parent→dependents* direction this ticket needs. No plural/list
  "children"/"wards" field exists anywhere in the codebase as of this investigation — confirmed by
  direct read of `src/core/state.py`, `src/core/updates.py`, `src/core/builder.py`. The
  `SocialBond`-seeding-at-birth pattern (`build_parent_bond_updates_for_birth()`,
  `src/core/builder.py`) is a plausible reuse target if Plan decides to key "has an active
  dependent" off `SocialComponent.bonds` entries with a role/flag rather than a new
  `LifecycleComponent` field — but as of today no such role/flag exists (`RelationshipRole` is
  `NEUTRAL`/`FRIEND`/`RIVAL` only).
- `docs/REGISTRY.yaml` filtered by `related_code_areas` overlap (`src/domains/adventure/scoring.py`,
  `src/core/state.py`, `src/systems/lifecycle_systems/lifecycle.py`) and by tag overlap
  (`lifecycle`, `adventure`, `social`) surfaced no prior ticket that added a "dependent" concept,
  confirming this is genuinely new territory, not overlapping/duplicate work. Adjacent surfaced
  work of note: a still-open idea for "Marriage — new ContractKind.MARRIAGE propose/accept
  mechanism" (idea 33, tagged `lifecycle`/`social`) — explicitly out of scope per this ticket's own
  Out of Scope section (spousal-protection hook is a distinct idea).
- Search-before-grep (`search_docs`) surfaced `stored_artifacts/TCK-20260619-E41D-DEFECTION-ESCORT/investigation.md`
  as the top hit for the escort-scoring query — the original SOC-230 investigation, confirming §9's
  shape and rationale as documented above; and `docs/simulation/domains/party_contract.md` §5
  (Escort Behavior) as a second doc mirroring §6.9's table, worth Plan checking for a matching
  update if the new dependent bias is judged closely related enough to warrant a mention there too
  (not flagged as a required Docs bullet above since the ticket's AC only names the two
  `docs/mechanics/` files; noted here for Plan's awareness).

## Risks and Open Questions
- **Open architecture question (ticket's own, unresolved):** reuse `heir_entity_id` loosely for
  "dependent," or add a genuinely new field. Arguments against reuse (from direct code read):
  `heir_entity_id` is `Optional[int]` (singular) while "dependent" per the ticket and atlas is
  plural/general (children, wards); `heir_entity_id`'s only current semantic meaning is
  "who inherits on death" (read exactly once, post-death, by `LifecycleSystem.resolve_lifecycle()`)
  — giving it a second, pre-death, alive-relevance meaning ("who I am responsible for while alive")
  changes what every future reader of that field must assume it means, a real semantic-drift risk.
  This is a decision only Plan should make; flagging as blocking Plan, not assumed here.
- **Live-wiring risk** (see Current Behavior above): if the new bias term is implemented via a new
  optional scorer parameter rather than reading directly off `entity`, it risks silently never
  firing in production, mirroring the confirmed-dead `faction_directives` pattern
  (`docs/mechanics/04_strategic_cognition.md` §6.10). Recommend Plan require the bias term read
  `entity.<field>` directly (whatever field/component Plan chooses), not a new parameter, unless
  the chosen field genuinely cannot live on `entity` itself.
- **`RouteFamily` scope ambiguity:** the ticket names `HUNT_WEAK_ENEMY` as the risky-route example
  and "return/recovery-oriented routes" (plural, unspecified) as the possible positive-bias target.
  `RouteFamily` has 16 members (`src/domains/adventure/schema.py:16-33`); candidates for "risky"
  beyond `HUNT_WEAK_ENEMY` could include `SCOUT_LOCATION`/`GATHER_RESOURCE` (both carry
  `expected_risk`), and candidates for "return/recovery-oriented" include `RECOVER` and
  `RETURN_TOWN` — but the ticket's AC only requires "measurably lower on inherently risky route
  families (e.g. HUNT_WEAK_ENEMY) and/or higher on return/recovery-oriented routes," which is an
  "and/or," not a full enumeration. Exact family list is a Plan-level decision; investigation does
  not collapse it.
- **Trace-field decision** (noted in Current Behavior): whether the new term gets a dedicated
  `AdventureRouteOption` field (majority pattern) or follows §9's no-trace-field precedent is
  unresolved and affects the "measurably" wording in AC #2 — a dedicated field makes "measurably"
  trivially assertable in a unit test (read the field directly, matching
  `test_scoring_plan_bonus.py`'s pattern); no dedicated field means the test must diff
  `result.score` between with/without-dependent entities instead (still assertable, but a coarser
  signal, and more exposed to unrelated future changes to other additive terms causing spurious
  test breakage).
- **Non-parental dependent definition is undefined in code today.** The ticket scopes to "the
  non-relative/non-parental case (e.g. elder/veteran dependent)" but nothing in the current
  codebase distinguishes an "elder/veteran" entity as dependent-eligible versus any other entity —
  `LifeStage.ELDER` exists (`docs/mechanics/05_world_evolution.md:210-215`, Age Bracket Thresholds)
  but is a property of the *elder itself* (STR/AGI −30%, VIT/END −50%, WIS/CHA +30%), not a marker
  that some other entity is responsible for that elder. Plan must define how a "dependent"
  relationship is established (manually via a new builder/system call, or automatically e.g. when
  an entity transitions to `LifeStage.ELDER` a caretaker bond is created) — the ticket's Scope
  section is silent on the *trigger* for a non-parental dependent, only on the eventual scoring
  effect. Flagging as an open question for Plan, not assumed here.

## Anti-Drift Hazards
- **Do not touch the §9 escort-scoring block (SOC-230) itself** beyond adding a new, independent
  block alongside it — explicitly named in the ticket's Out of Scope. The new dependent-bias block
  should be its own `if` clause, not merged into or reordered with §9's existing conditional.
- **Do not implement birth-triggered parental auto-registration** — explicitly deferred to the
  Reproduction epic follow-up per the ticket's Out of Scope and AC #5. Any temptation to "just also
  wire it since `parent_a_entity_id`/`parent_b_entity_id` already exist" must be resisted; the
  ticket requires this be *documented* as deferred, not silently built anyway.
- **Do not touch `_ADVENTURE_ROUTE_SCORE_MAX` (2.9, `src/systems/strategic_systems/intelligence.py`)
  or `_ADVENTURE_ROUTE_TIER5_COMPETITION_MAX` (2.4, `src/ai/goals/adventure_scorer.py`)** — both are
  separate normalization constants pinned by `tests/architecture/test_adventure_route_score_max_unchanged.py`
  and its sibling tier-5 guard; the new bias term must not require touching either, and the AC
  explicitly requires the pinned test to pass unmodified. A large flat bonus (à la SOC-230's +3.0)
  is safe precedent since that ticket's own bonus already coexists with these constants unmodified.
- **Do not conflate "dependent" with Marriage's spousal-protection hook (idea 33)** — explicitly
  kept distinct per the ticket's Out of Scope; do not reuse or extend `ContractKind` for this.
- **Do not reuse `RelationshipRole` (`FRIEND`/`RIVAL`/`NEUTRAL`) to mean "dependent"** without an
  explicit new value — conflating sentiment-classification with responsibility-classification
  would make existing FRIEND/RIVAL consumers (if any read `.role`) silently pick up unintended
  dependent semantics. If Plan chooses the `SocialBond`-based route, prefer a genuinely new
  marker (new `RelationshipRole` member, or a separate boolean/flag field) over overloading an
  existing one.
- **Preserve the "targets don't protect themselves" symmetry SOC-230 established** (line 363:
  `entity.id != group.escort_target_id`) if the new bias reads a paired entity id (e.g. the
  dependent's own id should not receive its own guardian's risk-aversion bonus applied to itself,
  unless Plan explicitly intends symmetric dependent-of-a-dependent chaining, which is out of
  scope here).
