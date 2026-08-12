---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY
artifact_type: plan
tags: [cognition, adventure, social]
---

# Implementation Plan — TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY

## Summary

Make `PartyCompositionScorer.score()` (`src/systems/social_systems/party_composition.py:104-118`)
and `AdventureRouteGenerator.generate()`'s FORM_PARTY branch (`src/domains/adventure/generator.py:126-163`)
read the acting entity's real, per-candidate `trust_history`/`bonds` (`SocialComponent`,
`src/core/models/social.py:25,34`) when computing `comp_score`/`confidence` for a FORM_PARTY route.
This plan makes **zero changes to `src/domains/adventure/scoring.py`** — confirmed via direct read
(`scoring.py:40-49`) that `AdventureRouteScorer.score()` receives only `entity` and the
already-built `route`, never the candidate pool, and `AdventureRouteOption`
(`src/domains/adventure/schema.py:36-73`) has no per-candidate identity field to carry one through.
The only place in the whole call chain where individual candidates are still visible one at a time
is `PartyCompositionScorer.score()`'s own iteration over `entities`
(`party_composition.py:68-102`) — every trust-aware computation this plan adds lives there, or in
`generator.py`'s FORM_PARTY block which still holds the real `candidates` list before it collapses
into a single `AdventureRouteOption`. See Design Decision 1 for the full architectural justification
and Design Decision 5 for an explicit, honest accounting of how this satisfies (and partially does
not literally satisfy) AC1/AC2's "specific candidate" wording.

## Design Decisions

### 1. Architectural choice: Option A (party_composition.py + generator.py), not Option B (scoring.py)

Confirmed by direct reads, not inferred from investigation.md's summary alone:

- `AdventureRouteOption` (`schema.py:36-73`) has fields `family, score, confidence, expected_benefit,
  expected_risk, requirements, blockers, source_opportunity_ids, reason, target_node_id, quest_id`
  plus 8 intermediate scoring-term fields (`urgency` … `memory_adjustment`) — **no candidate-id or
  party-member field of any kind.**
- `AdventureRouteScorer.score(entity, route, resource_nodes=None, quest_registry=None, group=None,
  faction_directives=None, factions=None, progression_plan=None)` (`scoring.py:40-48`) — confirmed
  its full parameter list; there is no candidate-pool parameter and no way to add one without
  threading `candidates` through `service.py:73`'s call site and `AdventureGoalScorer`/
  `StrategicIntelligenceSystem` above it, which the ticket's own Related Code Areas do not list and
  which would violate the "Do not touch `AdventureGoalScorer`/`AdventureDecisionService`" hazard
  investigation.md already flagged.
- `AdventureRouteGenerator.generate()`'s FORM_PARTY block (`generator.py:126-163`) builds
  `candidates` (132-137), calls `comp_score = PartyCompositionScorer.score(candidates[:8])` (139),
  then constructs exactly **one** `AdventureRouteOption` (149-163) — the pool is collapsed to a
  single float (`comp_score`) before the route object exists. This is the exact, confirmed collapse
  point.
- `PartyCompositionScorer.score()` (`party_composition.py:104-118`) and its two sub-scores
  `score_role_diversity`/`score_ocean_compatibility` (68-102) are the **only** functions in this
  entire chain that still iterate `entities` one at a time when trust-awareness could be added.

Given this, a `scoring.py`-level term (Option B) could only ever read some pool-level-but-relabeled
aggregate (e.g. "mean trust across whoever the entity is generally sociable toward") — not the
specific candidates of *this* route, since `scoring.py` never receives them. That is a materially
weaker, and arguably misleading, reading of AC1/AC2's "specific candidate" language than doing the
work at `PartyCompositionScorer.score()`'s layer, where per-candidate visibility is genuinely still
intact. **Option A is chosen.** Because Option A never touches `scoring.py`, AC4's bit-identical
requirement on `personality_bias += sociability * 0.40` (`scoring.py:220-221`) is satisfied
unconditionally — that file has zero edits in this plan, so there is no possible collision, no
formula-shape decision to get wrong, and no risk of regressing `test_sociability_weight_is_0_40_on_form_party_route`.

### 2. Per-candidate trust value: bond sentiment takes priority over trust_history

Rather than inventing a new blend formula, this plan reuses a **real, existing precedent** already
in this codebase for combining `SocialBond.sentiment` and `trust_history` into one directed
trust value: `SocialAppraisalSystem.appraise_contract()` (`src/systems/social_systems/appraisal.py:32-45`):
```python
bond = entity.social.bonds.get(source_id)
...
if bond:
    # Private sentiment takes priority: sentiment=1.0 -> 1.0, -1.0 -> 0.0
    trust_score = (bond.sentiment + 1.0) / 2.0
else:
    history_trust = entity.social.trust_history.get(source_id, 0.5)
    trust_score = (public_trust * 0.7) + (history_trust * 0.3)
```
and the documented rule at `docs/simulation/social_systems_contract.md:70`: *"Bond sentiment takes
priority over trust_history in appraisal."* This plan mirrors the **priority order** (bond present →
use bond; else → use trust_history) but does **not** copy `appraisal.py`'s `(sentiment+1.0)/2.0`
normalization or its `public_reputation` blend — those exist in `appraisal.py` specifically because
it blends in `public_reputation` (a 0.0–2.0-scaled field, per `social.py:42`), which this ticket's
scope does not mention and must not introduce (out of scope — the ticket names only
`trust_history`/`bonds`). Both `trust_history` (`social.py:25`, confirmed range −1.0 to 1.0 per
`docs/simulation/social_systems_contract.md`'s Relationship dimensions table) and
`SocialBond.sentiment` (`social.py:10`, `-1.0 (Bias/Liking) to 1.0`) already share the same native
−1.0..1.0 scale, so no normalization is needed:
```python
@staticmethod
def _candidate_trust_value(actor: "EntityState", candidate: "EntityState") -> float:
    bond = actor.social.bonds.get(candidate.id)
    if bond is not None:
        return bond.sentiment
    return actor.social.trust_history.get(candidate.id, 0.0)
```
Default for a never-before-met candidate (no bond, no trust_history entry) is neutral `0.0` — the
documented midpoint of the native −1.0..1.0 scale (unlike `appraisal.py`'s `0.5` default, which is
the midpoint of *its own* 0.0–1.0-normalized scale; the two are not directly comparable and this
plan intentionally does not reuse `0.5`).

### 3. Aggregation and weight: mean across the pool, `TRUST_BONUS_WEIGHT = 0.15`, additive + clamped

`score_trust_bonds(actor, entities)` returns the **mean** `_candidate_trust_value` across the pool
(native range −1.0..1.0; `0.0` for an empty pool). `PartyCompositionScorer.score()` adds
`TRUST_BONUS_WEIGHT × trust_term` on top of the existing, **completely unmodified**
`ROLE_DIVERSITY_WEIGHT (0.6) × role_div + OCEAN_COMPAT_WEIGHT (0.4) × ocean_compat` base score
(`party_composition.py:112-117`, untouched), then clamps the sum to `[0.0, 1.0]` to preserve the
class's own documented `score()` docstring contract ("Combined composition quality score,
0.0–1.0", line 106-107). `TRUST_BONUS_WEIGHT = 0.15` is chosen to mirror this codebase's existing
convention for a "small additive adjustment" magnitude — the same `0.15` used for `confidence_bonus`
in `scoring.py:263,325` (both the pre-existing flat term and the capability-estimate-driven
replacement) — while acknowledging this is a cross-file magnitude analogy, not a shared constant;
`party_composition.py` and `scoring.py` do not import each other's weight constants and this plan
does not create such a coupling. This new term is only computed when the new `actor` keyword
argument is passed; when omitted (every one of the 3 existing direct test call sites, plus
`generator.py:139` pre-this-plan, plus `groups.py:312`, see "Other Callers" in Step 1) `score()`
returns exactly `round(base_score, 4)` — byte-identical to today's return expression, since the
`ROLE_DIVERSITY_WEIGHT`/`OCEAN_COMPAT_WEIGHT` multiplication and rounding are literally the same
code path, untouched.

### 4. `generator.py`'s FORM_PARTY confidence also becomes trust-aware

To satisfy AC1's "confidence... incorporates trust/bonds" (not just "benefit"), the same
`trust_term` (computed once via `PartyCompositionScorer.score_trust_bonds(entity, candidates[:8])`)
is also folded into the generation-time `confidence` value at `generator.py:153` — currently
`confidence=min(1.0, sociability + 0.3)` — with the same `TRUST_BONUS_WEIGHT` magnitude:
`confidence=min(1.0, max(0.0, sociability + 0.3 + PartyCompositionScorer.TRUST_BONUS_WEIGHT * trust_term))`.
The `max(0.0, ...)` floor is new but defensively inert under real conditions: the branch only
executes when `sociability >= 0.2` (`generator.py:129`), so the worst case
(`sociability=0.2, trust_term=-1.0`) is `0.2 + 0.3 - 0.15 = 0.35`, still positive — the floor exists
only for symmetry with the existing `min(1.0, ...)` ceiling and as defensive style consistent with
this file's guarded-arithmetic conventions elsewhere, not because it is reachable today.
`score_trust_bonds` is called once in `generator.py` (for `confidence`) and once more internally
inside `PartyCompositionScorer.score(candidates[:8], actor=entity)` (for `comp_score`) — a small,
accepted redundant recomputation of the same deterministic, side-effect-free value, consistent with
this codebase's existing non-memoized scoring style (e.g. `scoring.py`'s `get_trait()` closure is
also called independently per trait with no shared cache).

### 5. Honest accounting of AC1/AC2's "specific candidate" wording

**What is genuinely true:** each candidate's own individually-keyed `trust_history`/`bonds` entry
(keyed by that specific candidate's `id`, read from the acting entity's own `SocialComponent`) is
read and incorporated — not a global/omniscient lookup, not a fabricated aggregate, not something
invented at a layer that no longer has candidate identity. Swapping one candidate's trust value in
an otherwise-identical pool changes that one candidate's contribution to the mean, which changes
`comp_score` and `confidence` — this is real, verifiable, and AC2's own wording ("produce different
comp_score/confidence") is written at exactly this aggregate-output granularity, so **AC2 is fully,
literally satisfied.**

**What is not literally true:** the value exposed on the finished `AdventureRouteOption`
(`comp_score`/`confidence`) is a **pool-level aggregate** (a mean), not a value attributed to one
named candidate on the route object itself — because `AdventureRouteOption` has no field to carry a
per-candidate breakdown. AC1's phrase "confidence/benefit for a specific candidate incorporates that
candidate's real... value" is satisfied in the sense that the specific candidate's real value
genuinely flows into the computation, but not in the sense of a literal single-candidate output
field existing anywhere downstream. This must be disclosed plainly to Review, exactly as
investigation.md's Risk 1 anticipated — this is not a gap to silently paper over.

## Steps

### Step 1 — Trust/bonds-aware `PartyCompositionScorer.score()`
**Files:** `src/systems/social_systems/party_composition.py`

**Change:**
1. Add `Optional` to the `typing` import (`party_composition.py:17`, currently
   `from typing import TYPE_CHECKING, List`) → `from typing import TYPE_CHECKING, List, Optional`.
2. Add a new class constant directly below the two existing ones (`party_composition.py:38-39`,
   **do not modify those two lines**):
   ```python
   TRUST_BONUS_WEIGHT: float = 0.15
   ```
3. Add two new `@staticmethod`s, placed after `score_ocean_compatibility` (ends line 102) and before
   `score()` (starts line 104):
   ```python
   @staticmethod
   def _candidate_trust_value(actor: "EntityState", candidate: "EntityState") -> float:
       """
       Directed trust/bond value the acting entity holds toward one specific candidate,
       on trust_history/SocialBond.sentiment's shared native -1.0..1.0 scale. Bond
       sentiment takes priority over trust_history when both exist (established
       precedent: appraisal.py's SocialAppraisalSystem.appraise_contract(), "Private
       sentiment takes priority"; docs/simulation/social_systems_contract.md's
       "Bond sentiment takes priority over trust_history in appraisal"). Neutral
       default 0.0 for a candidate with no prior relationship record.
       """
       bond = actor.social.bonds.get(candidate.id)
       if bond is not None:
           return bond.sentiment
       return actor.social.trust_history.get(candidate.id, 0.0)

   @staticmethod
   def score_trust_bonds(actor: "EntityState", entities: "List[EntityState]") -> float:
       """
       Mean directed trust/bond sentiment the acting entity holds toward each
       candidate in the pool, read from the acting entity's own SocialComponent
       only (never global/omniscient state). Range: -1.0 to 1.0. Empty pool -> 0.0.
       """
       if not entities:
           return 0.0
       values = [
           PartyCompositionScorer._candidate_trust_value(actor, e) for e in entities
       ]
       return round(sum(values) / len(values), 4)
   ```
4. Modify `score()` (`party_composition.py:104-118`) — signature gains a **keyword-only, optional**
   `actor` parameter defaulting to `None`; the pre-existing 2-line body (112-117) is left completely
   unedited, only wrapped:
   ```python
   @classmethod
   def score(
       cls, entities: "List[EntityState]", *, actor: "Optional[EntityState]" = None
   ) -> float:
       """
       Combined composition quality score, 0.0-1.0.
       Weighted sum of role diversity and OCEAN complementarity, plus an optional
       trust/bonds-aware adjustment when `actor` (the entity forming the party) is
       supplied (TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY). Omitting `actor`
       reproduces today's exact pre-existing output -- every pre-existing call site
       does this.
       """
       if not entities:
           return 0.0
       role_div = cls.score_role_diversity(entities)
       ocean_compat = cls.score_ocean_compatibility(entities)
       base_score = (
           cls.ROLE_DIVERSITY_WEIGHT * role_div + cls.OCEAN_COMPAT_WEIGHT * ocean_compat
       )
       if actor is None:
           return round(base_score, 4)
       trust_term = cls.score_trust_bonds(actor, entities)
       return round(max(0.0, min(1.0, base_score + cls.TRUST_BONUS_WEIGHT * trust_term)), 4)
   ```
5. Module docstring (`party_composition.py:1-13`): **do not edit the existing "Logic IDs: SOC-231
   (role diversity), SOC-232 (OCEAN compatibility)" line** (line 5 — pre-existing, confirmed-wrong
   citation, out of scope, see Anti-Drift Notes). Add one new line directly below it:
   ```
   Logic ID: SOC-244 (trust/bonds-aware composition + confidence, TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY)
   ```
   And extend the "Score combines:" bullet list (lines 7-12) with a third bullet: `"- Trust/bonds
   directed sentiment (optional, when actor supplied): weight 0.15, additive"`.

**Other callers of `PartyCompositionScorer.score()`** (confirmed via repo-wide grep, not assumed):
- `src/domains/adventure/generator.py:139` — the call this ticket's Step 2 updates to pass
  `actor=entity`.
- `src/systems/world_systems/groups.py:312` (`GroupSystem`'s ally-cohesion group-formation logic,
  called `comp_score = PartyCompositionScorer.score(member_entities)` with **no acting-entity
  concept at all** — it forms a peer group among mutually-contracted entities within range, not one
  entity evaluating a candidate pool). **This plan does not modify `groups.py` in any way** — it is
  not in the ticket's Related Code Areas, and since the new `actor` parameter is optional/keyword-only
  and this call site never passes it, `groups.py:312`'s behavior is provably unchanged (same
  `round(base_score, 4)` expression it already returns). A future ticket could consider wiring
  `actor=state.entities[leader_id]` here, but that is out of scope for this one.
- `tests/unit/social/test_party_composition.py:117,128` — `score([])`, `score(balanced)`,
  `score(homogeneous)` — all positional, all unaffected by the same reasoning.
- `src/core/state.py:573` — **not a caller**, but note: `GroupRecord.composition_score`'s field
  comment reads `# PartyCompositionScorer result at formation (SOC-232)` — the same wrong-ID bug as
  `party_composition.py`'s own docstring (SOC-232 is the Nemesis-relation entry, not party
  composition; see Anti-Drift Notes). Not fixed by this plan (out of scope), disclosed here because
  it is a second site propagating the same pre-existing citation bug, found independently during
  this plan's own verification (investigation.md only caught the `party_composition.py` docstring
  instance).

**Do NOT touch:** `infer_party_role` (42-65), `score_role_diversity` (68-76),
`score_ocean_compatibility` (79-102), `ROLE_DIVERSITY_WEIGHT`/`OCEAN_COMPAT_WEIGHT` (38-39), the
existing `role_div`/`ocean_compat` computation lines inside `score()` — all pre-existing logic,
zero edits beyond what is explicitly listed above.

**Verify:** `tests/unit/social/test_party_composition.py` (Step 3, new tests below) plus all 16
pre-existing tests in that file, unmodified, must still pass.

---

### Step 2 — Wire `actor=` and trust-aware confidence into `AdventureRouteGenerator`'s FORM_PARTY branch
**Files:** `src/domains/adventure/generator.py`

**Change:** In the FORM_PARTY block (`generator.py:126-163`), immediately after `comp_score =
PartyCompositionScorer.score(candidates[:8])` (line 139), replace lines 139 and the
`AdventureRouteOption(...)` construction's `confidence=`/`reason=` arguments (153, 157-161) as
follows — **do not touch** the nemesis-block logic (140-148, unrelated mechanism, see Anti-Drift
Notes) or anything in sections 1/2/4 of `generate()` (lines 34-124, 165-181):
```python
                if candidates:
                    trust_term = PartyCompositionScorer.score_trust_bonds(entity, candidates[:8])
                    comp_score = PartyCompositionScorer.score(candidates[:8], actor=entity)
                    # E43G: block FORM_PARTY if any candidate is a nemesis.
                    from src.core.strategic import BlockerKind
                    nemesis_ids = {
                        int(b.subject)
                        for b in entity.strategic.blockers.values()
                        if b.kind == BlockerKind.SOCIAL and b.subject.isdigit()
                    }
                    nemesis_in_candidates = any(c.id in nemesis_ids for c in candidates)
                    route_blockers = ("nemesis_block",) if nemesis_in_candidates else ()
                    opts.append(
                        AdventureRouteOption(
                            family=RouteFamily.FORM_PARTY,
                            score=0.0,
                            confidence=min(
                                1.0,
                                max(
                                    0.0,
                                    sociability + 0.3
                                    + PartyCompositionScorer.TRUST_BONUS_WEIGHT * trust_term,
                                ),
                            ),
                            expected_benefit=max(0.3, comp_score),
                            expected_risk=0.1,
                            blockers=route_blockers,
                            reason=(
                                f"Party formation: {len(candidates)} candidates, "
                                f"comp_score={comp_score:.2f}, trust_term={trust_term:.2f}"
                                + (" [nemesis block]" if route_blockers else "")
                            ),
                        )
                    )
```
(Only the `comp_score=` line, the new `trust_term=` line above it, `confidence=`, and `reason=`
change; the nemesis-block lines 140-148 are reproduced verbatim/unmoved above only to show correct
placement relative to the new `trust_term` line, not because they change.)

**Other writers to `AdventureRouteOption.confidence`/`.expected_benefit` for FORM_PARTY routes:**
confirmed via full read of `generator.py` (the only file that constructs `FORM_PARTY`
`AdventureRouteOption`s — `kind_map` at lines 38-45 maps no opportunity `kind` string to
`RouteFamily.FORM_PARTY`, so FORM_PARTY is never constructed via the opportunity-loop path at
lines 48-92, only via this one structural block at 126-163) — this is the only construction site,
no race/collision to reason about. `AdventureRouteScorer.score()` (`scoring.py:370-380`) later
overwrites `route.score`/`route.personality_bias`/etc. via `dataclasses.replace`, but **does not
read or overwrite `confidence`/`expected_benefit` themselves** (confirmed: `scoring.py`'s
`dataclasses.replace` call at 370-380 does not list `confidence` or `expected_benefit` among its
keyword arguments — both are carried through from the input `route` unchanged), so this plan's
change to their generation-time values is not clobbered downstream.

**Do NOT touch:** sections 1 (opportunity loop, 47-92), 2 (structural RECOVER/ASK_INFORMATION
defaults, 94-123), or 4 (DEFER_WITH_REASON fallback + cap, 165-181) of `generate()`; the nemesis-block
detection logic itself (140-148, only its *placement* relative to the new `trust_term` line changes,
not its content).

**Verify:** `tests/unit/social/test_party_composition.py`'s 3 pre-existing FORM_PARTY generator
tests (135-181, unmodified — none set up `trust_history`/`bonds`, so `trust_term=0.0` in all three,
reducing the new `confidence`/`comp_score` expressions to numerically identical values to today's)
plus Step 3's new tests.

---

### Step 3 — New regression tests
**Files:** `tests/unit/social/test_party_composition.py`

**Change:** Extend the existing `_entity()` helper (`test_party_composition.py:20-32`) with two new
optional keyword parameters, threaded through `V2EntityBuilder.social(...)`
(`src/core/builder.py:493-513`, confirmed signature accepts `trust_history: Optional[Dict[int,
float]]` and `bonds: Optional[Dict[int, SocialBond]]` among its keyword args) — backward compatible,
since both default to `None` and every existing `_entity(...)` call omits them:
```python
def _entity(
    eid: int, kind: str = "hero", bravery: float = 0.5, sociability: float = 0.5,
    trust_history: dict = None, bonds: dict = None,
):
    from src.core.builder import V2EntityBuilder
    entity = (
        V2EntityBuilder(eid)
        .kind(kind)
        .location(0, 0)
        .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
        .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
        .inventory(gold=0)
        .social(trust_history=trust_history or {}, bonds=bonds or {})
        .build()
    )
    p = replace(entity.identity.personality, bravery=bravery, sociability=sociability)
    return replace(entity, identity=replace(entity.identity, personality=p))
```
Add `from src.core.models.social import SocialBond` to the file's imports. Add these tests, placed
after `test_score_balanced_party_higher_than_homogeneous` (ends line 128) and before the "FORM_PARTY
route generation" section (starts line 131):

1. **`test_party_composition_score_reflects_candidate_trust_history`** — two otherwise-identical
   2-candidate pools (e.g. `_entity(2, kind="guard")`, `_entity(3, kind="mage")`), differing only in
   `actor`'s `trust_history` for candidate `2` (`{2: -0.8}` vs `{2: 0.8}`); assert
   `PartyCompositionScorer.score(pool, actor=actor_low) != PartyCompositionScorer.score(pool,
   actor=actor_high)`. Directly proves AC2.
2. **`test_party_composition_score_unchanged_when_actor_omitted`** — call
   `PartyCompositionScorer.score(entities)` with no `actor` (exactly as every pre-existing call site
   does) on the same `balanced`/`homogeneous` pools from `test_score_balanced_party_higher_than_homogeneous`;
   assert the returned values are bit-identical (`==`, not `approx`) to values computed on a git-clean
   checkout of this method — in practice, assert equality against a locally recomputed
   `ROLE_DIVERSITY_WEIGHT * role_div + OCEAN_COMPAT_WEIGHT * ocean_compat` expression. Guards
   backward compatibility for `groups.py:312` and every other omitted-`actor` caller.
3. **`test_party_composition_score_prioritizes_bond_sentiment_over_trust_history`** — one candidate
   with both a `SocialBond(target_id=candidate.id, sentiment=0.9)` **and** a conflicting
   `trust_history={candidate.id: -0.9}` entry on the same `actor`; assert the resulting `score_trust_bonds`
   (or the `score(..., actor=...)` delta) reflects the **positive** bond sentiment, not the negative
   trust_history value — directly protects Design Decision 2's priority-order formula, which is
   unique to this plan and not covered by any existing test.
4. **`test_form_party_route_benefit_and_confidence_differ_with_candidate_trust`** — via
   `AdventureRouteGenerator.generate()`, two `_FakeState`s identical except one FORM_PARTY
   candidate's `trust_history` value as seen from the actor; assert **both**
   `route.expected_benefit` and `route.confidence` differ between the two generated FORM_PARTY
   routes. End-to-end version of Test 1, and the direct proof for AC1's "confidence... incorporates
   trust/bonds" half.
5. **`test_party_composition_trust_lookup_does_not_mutate_social_state`** — capture
   `actor.social`/each candidate's `.social` before calling `PartyCompositionScorer.score(entities,
   actor=actor)`; assert identity-unchanged (`is`) after. Guards the CLAUDE.md durable-state rule.
6. **`test_party_composition_trust_lookup_defaults_safely_for_unknown_candidate`** — `actor` with an
   empty `trust_history`/`bonds` (the default `_entity()` case) scored against a candidate pool;
   assert no exception and `score_trust_bonds(...) == 0.0`.

**Do NOT touch:** any of the 16 pre-existing tests in this file, or the file's existing imports
beyond adding `SocialBond`.

**Verify:** `pytest tests/unit/social/test_party_composition.py -v` — all pre-existing 16 + 6 new = 22
tests pass.

---

### Step 4 — Parity ledger: new SOC-244 entry
**Files:** `docs/parity_ledger/social_narrative.yaml`

**Change:** Confirmed via `grep -roE "SOC-[0-9]+" docs/parity_ledger/*.yaml | sort -u | tail` that
the highest existing `SOC-` id across **every** parity ledger file (not just `social_narrative.yaml`)
is `SOC-243` — **`SOC-244` is free and used here**, minted fresh per Anti-Drift Notes (do not reuse
SOC-231/SOC-232, which are real, unrelated, already-used entries — see below). Append a new entry
after the last existing entry in the file:
```yaml
- id: SOC-244
  text: >
    PartyCompositionScorer.score() (src/systems/social_systems/party_composition.py) accepts an
    optional keyword-only actor: EntityState parameter. When supplied, a new TRUST_BONUS_WEIGHT=0.15
    term is added to the existing role-diversity(0.6)/OCEAN-compatibility(0.4) base score: mean of
    each candidate's directed trust value (SocialBond.sentiment if a bond exists toward that
    candidate, else raw trust_history.get(candidate.id, 0.0), bond takes priority per the same rule
    documented for SocialAppraisalSystem.appraise_contract() in
    docs/simulation/social_systems_contract.md), clamped to [0.0, 1.0]. Omitting actor (every
    pre-existing call site) reproduces the pre-existing base-score-only output exactly.
    AdventureRouteGenerator.generate()'s FORM_PARTY branch (src/domains/adventure/generator.py) now
    passes actor=entity to score() and folds the same weighted trust term into the generation-time
    confidence value alongside the pre-existing sociability + 0.3 formula. No change to
    src/domains/adventure/scoring.py: AdventureRouteScorer's personality_bias (sociability × 0.40,
    STRAT-227) is untouched. All constants documented in docs/mechanics/04_strategic_cognition.md §7.
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: >
    src/systems/social_systems/party_composition.py — PartyCompositionScorer.score() actor kwarg,
    TRUST_BONUS_WEIGHT=0.15, _candidate_trust_value(), score_trust_bonds().
    src/domains/adventure/generator.py — FORM_PARTY block passes actor=entity to score() and folds
    trust_term into confidence. Verified by TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY.
  proof_type: parity
  test_path: tests/unit/social/test_party_composition.py::test_party_composition_score_reflects_candidate_trust_history
  divergence_note: >
    New mechanic added by TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY. No prior version of
    PartyCompositionScorer.score() read trust_history/bonds; it combined only role-diversity and
    OCEAN-compatibility. Note: party_composition.py's own module docstring cites "Logic IDs: SOC-231
    (role diversity), SOC-232 (OCEAN compatibility)" and src/core/state.py's GroupRecord.
    composition_score field comment cites "(SOC-232)" — both are pre-existing, incorrect citations
    (SOC-231 is Grief/rage urgency, SOC-232 is Nemesis relation; neither entry documents party
    composition). This is a pre-existing bug in the source, not introduced or fixed by this ticket;
    SOC-244 is a genuinely new id, not a continuation of either.
  support_boundary: null
```
Priority `P1` chosen for consistency with the two thematically-adjacent, same-code-region entries
`SOC-231`/`SOC-232` (both `P1`) — a judgment call, not a hard rule, since this ticket's own body
`## Priority` field is `P3` (a different scale: ticket urgency, not parity-ledger criticality).

**Other writers to this file:** none relevant — confirmed via grep that no other entry references
`party_composition.py` or `PartyCompositionScorer` anywhere in `social_narrative.yaml`.

**Do NOT touch:** `docs/parity_ledger/strategic_cognition.yaml`'s `STRAT-227` entry. Unlike the two
sibling tickets (memory-informed scoring, capability-driven confidence), this plan makes **no**
change to `scoring.py`, so there is no basis to extend STRAT-227 a third time — its `text`/
`v2_evidence` already accurately describe `AdventureRouteScorer.score()`'s unmodified formula. Do
not touch `SOC-231`/`SOC-232` themselves (real, unrelated, already-used entries).

**Verify:** After Step 3 passes, confirm the cited `test_path` test exists and passes.

---

### Step 5 — Mechanics Bible: new §7 section
**Files:** `docs/mechanics/04_strategic_cognition.md`

**Change:** Confirmed via grep that `PartyCompositionScorer`/`party_composition`/
`ROLE_DIVERSITY_WEIGHT`/`OCEAN_COMPAT_WEIGHT` appear **nowhere** in `docs/mechanics/` today — the
0.6/0.4 role-diversity/OCEAN weights, and `generator.py`'s FORM_PARTY `confidence=min(1.0,
sociability + 0.3)`/`expected_benefit=max(0.3, comp_score)` formulas, have never been documented in
the Mechanics Bible, confirmed via grep for `"sociability + 0.3"`/`"comp_score"` across
`docs/mechanics/*.md` and `docs/simulation/domains/adventure_contract.md` (zero hits). `## 6.
Adventure Route Scoring Constants` (line 125) is specifically `AdventureRouteScorer`/`scoring.py`'s
formula — not the right home for a different file's constants. Per CLAUDE.md's Authoritative
Mechanics Rule ("If logic changes, update the corresponding doc... in the same session"), this plan
adds a new top-level `## 7. Party Composition & Formation Scoring` section at the end of the file
(after `### 6.12`, the current last subsection, line 488), documenting the **full current formula**
(pre-existing 0.6/0.4 weights, disclosed as newly-documented-but-not-new-behavior, plus the new
trust/bonds term this ticket adds) — mirroring how `## 6` documents `scoring.py`'s full formula, not
just its newest term:

```markdown
## 7. Party Composition & Formation Scoring

### 7.1 PartyCompositionScorer.score() — Role Diversity & OCEAN Compatibility

`src/systems/social_systems/party_composition.py`. Pre-existing behavior (TCK-20260628-E41F-PARTY-SCORER,
first documented here as of TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY — was previously undocumented
in the Mechanics Bible):

score = ROLE_DIVERSITY_WEIGHT(0.6) × score_role_diversity(entities) + OCEAN_COMPAT_WEIGHT(0.4) × score_ocean_compatibility(entities)

- `score_role_diversity`: fraction of the 4 `PartyRole` values (TANK/HEALER/DPS/SUPPORT) represented
  in the candidate pool (0.0–1.0).
- `score_ocean_compatibility`: normalized bravery + sociability variance across the pool (0.0–1.0);
  `0.5` neutral for a single-candidate pool.

### 7.2 Trust/Bonds-Aware Adjustment (TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY)

When `PartyCompositionScorer.score(entities, actor=acting_entity)` is called with `actor` supplied:

score = clamp(base_score + TRUST_BONUS_WEIGHT(0.15) × score_trust_bonds(actor, entities), 0.0, 1.0)

`score_trust_bonds` is the mean, across the candidate pool, of each candidate's directed trust value
as seen from `actor`'s own `SocialComponent`: `SocialBond.sentiment` if a bond exists toward that
candidate, else `trust_history.get(candidate.id, 0.0)` — bond takes priority (same rule as
`SocialAppraisalSystem.appraise_contract()`, §Social Systems Contract). Range −1.0 to 1.0; `0.0` for
an unknown/never-met candidate. Omitting `actor` reproduces §7.1's base score exactly.

`AdventureRouteGenerator.generate()`'s FORM_PARTY branch (`src/domains/adventure/generator.py`) uses
this to compute both `expected_benefit` (via `PartyCompositionScorer.score(candidates[:8],
actor=entity)`) and, separately, `confidence`:

confidence = clamp(sociability + 0.3 + TRUST_BONUS_WEIGHT(0.15) × score_trust_bonds(entity, candidates), 0.0, 1.0)

This is entirely generation-time (`AdventureRouteGenerator`), not scoring-time — `scoring.py`'s
`AdventureRouteScorer.score()` and its `FORM_PARTY | sociability | 0.40` `personality_bias` term
(§6.4) are **unmodified** by this section; the trust/bonds term never reaches `scoring.py`.
```

**Do NOT touch:** `## 1`–`## 5`, `## 6` (any subsection, including `§6.4`'s `FORM_PARTY |
sociability | 0.40` row) — all pre-existing and unrelated to this plan's changes.

**Verify:** No automated test for doc content; manual proofread that §7 matches
`party_composition.py`/`generator.py` exactly post-Steps 1-2.

---

### Step 6 — `docs/simulation/social_systems_contract.md` update
**Files:** `docs/simulation/social_systems_contract.md`

**Change:**
1. The file's `**Source:**` line (line 10) lists `appraisal.py, contracts.py, relationships.py,
   guilds.py, party.py, memory.py, group_service.py, reputation.py` — confirmed `party_composition.py`
   is **not** listed, despite being documented here for the first time by this step. Add it:
   `..., party.py, party_composition.py, memory.py, ...`.
2. Add a new `## Party Composition — party_composition.py` subsection, placed directly after the
   existing `## Party — party.py` section (ends line 134) and before `## Reputation` (line 135),
   mirroring that section's format:
   ```markdown
   ## Party Composition — `party_composition.py`

   Compliance ID: SOC-244 (trust/bonds-aware term only; the pre-existing role-diversity/OCEAN-compatibility
   base score has no dedicated compliance id — see `docs/parity_ledger/social_narrative.yaml`'s SOC-244
   divergence_note for the pre-existing SOC-231/SOC-232 docstring mis-citation, not fixed here)

   `PartyCompositionScorer.score(entities, actor=None)` scores a candidate pool's party-formation
   quality, 0.0–1.0: `0.6 × role_diversity + 0.4 × OCEAN_compatibility` (TANK/HEALER/DPS/SUPPORT role
   coverage; bravery/sociability variance). When `actor` (the entity forming the party) is supplied,
   an additional `0.15 ×` mean directed trust/bond term is added and the result clamped to
   `[0.0, 1.0]` — see `docs/mechanics/04_strategic_cognition.md` §7. Bond sentiment takes priority
   over `trust_history` when both exist for a candidate, matching the Relationships section's rule
   above. Used by `AdventureRouteGenerator`'s FORM_PARTY route (`src/domains/adventure/`) and by
   `GroupSystem`'s ally-cohesion group formation (`src/systems/world_systems/groups.py`, which never
   passes `actor` and is unaffected by the trust/bonds term).
   ```

**Do NOT touch:** `## Relationships`, `## Social Memory`, `## Contracts`, `## Guilds`, `## Party`,
`## Reputation`, `## Engine phase`, `## Mutation rules`, `## Regression tests`, `## Extension rules`
sections — all pre-existing and accurate.

**Verify:** No automated test; manual proofread.

---

### Step 7 — `docs/simulation/domains/adventure_contract.md` update
**Files:** `docs/simulation/domains/adventure_contract.md`

**Change:** "What It Reads" table (confirmed lines 61-74) — add a new row directly after the existing
`Ad-hoc CapabilityEstimateService.estimate() call` row (line 74):
```
| `entity.social.trust_history` / `.bonds` (FORM_PARTY candidate pool only, via `PartyCompositionScorer.score_trust_bonds()`) | Feeds `expected_benefit` and `confidence` for the FORM_PARTY route — see `docs/mechanics/04_strategic_cognition.md` §7.2; computed in `AdventureRouteGenerator.generate()`, NOT in `scoring.py` |
```

**Do NOT touch:** the "Full `RouteFamily` enum (13 values)" table's pre-existing 13-vs-16 drift, the
"Candidate sources" table (confirmed pre-existing per investigation.md — `SCOUT_LOCATION`'s "Region
exploration targets" row is already inaccurate/dead, unrelated to this ticket), or the FORM_PARTY row
of the "Personality bias by route family" table (confirmed still showing the stale `0.25` where code
says `0.40` — pre-existing drift, not caused by and not fixed by this ticket; this plan's change
lives entirely in generation-time `confidence`/`expected_benefit`, not `personality_bias`, so it does
not touch or worsen that pre-existing row either way).

**Verify:** No automated test; manual proofread.

---

### Step 8 — Architecture design doc: close the "Relationship-aware FORM_PARTY" bullet
**Files:** `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`

**Change:** Confirmed lines 440-441 currently read:
> "**Relationship-aware `FORM_PARTY`**: real trust/relationship data already exists in
> `src/systems/social_systems/`; today's `FORM_PARTY` bias is a flat `sociability` scalar."

Update to:
> "**Relationship-aware `FORM_PARTY`** (closed, scoped, `TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY`):
> `PartyCompositionScorer.score()` now accepts an optional `actor` parameter and folds a
> `trust_history`/`bonds`-derived term (bond sentiment priority, else raw trust_history, weight 0.15)
> into `comp_score`; `AdventureRouteGenerator.generate()`'s FORM_PARTY branch folds the same term into
> generation-time `confidence`. This is entirely a generation-time change — `AdventureRouteOption`
> has no per-candidate identity field (the same class of gap flagged for `HUNT_WEAK_ENEMY`/
> `SCOUT_LOCATION` above), so the value reaching the route is a pool-level mean across candidates,
> not a literal single-candidate output; `scoring.py`'s `FORM_PARTY | sociability | 0.40`
> `personality_bias` term is untouched."

**Do NOT touch:** any other bullet in this Future Extension Patterns list (the "Memory-informed
candidates" and "Capability-estimate-driven confidence" bullets immediately above are already closed
by the two sibling tickets; the "Multi-step planning" bullet below is a separate, still-open concern).

**Verify:** No automated test; manual proofread.

## Scope Guards

- **`src/domains/adventure/scoring.py` is not modified in any way by this plan.** This is the central
  architectural decision (Design Decision 1) — do not add a new term there, do not import
  `PartyCompositionScorer` there, do not thread a candidate pool through `AdventureRouteScorer.score()`'s
  signature.
- **Do not touch `ROLE_DIVERSITY_WEIGHT`/`OCEAN_COMPAT_WEIGHT`** (`party_composition.py:38-39`) or the
  pre-existing `score_role_diversity`/`score_ocean_compatibility` computations — the new trust term is
  strictly additive on top, never a reweighting.
- **Do not touch `scoring.py:220-221`'s `personality_bias += sociability * 0.40`** — AC4's
  bit-identical requirement is satisfied by never editing this file at all, not by careful editing
  around it.
- **Do not extend `STRAT-227`** (`docs/parity_ledger/strategic_cognition.yaml`) — unlike the two
  sibling tickets, no `scoring.py` change exists to document there.
- **Do not modify `src/systems/world_systems/groups.py`** — its `PartyCompositionScorer.score(member_entities)`
  call (line 312) is a separate, unrelated group-formation mechanism (ally cohesion among contracted
  entities, not FORM_PARTY route candidates); it is provably unaffected since it never passes the new
  `actor` kwarg, and wiring it is explicitly out of scope (not in Related Code Areas).
- **Do not add a read/lookup method to `RelationshipService`** (`relationships.py`) — it remains
  authoritative-mutation-only; the new trust lookups are raw `actor.social.trust_history.get(...)`/
  `actor.social.bonds.get(...)` dict access, matching every existing consumer's pattern
  (`appraisal.py`, `party.py`, `tactical.py`, `groups.py`, `social_contract_scorer.py`,
  `cooperation/evaluators.py`).
- **Do not mutate `entity.social` or any other durable entity field** from `PartyCompositionScorer.score()`,
  `score_trust_bonds()`, `_candidate_trust_value()`, or `AdventureRouteGenerator.generate()` — all
  reads are local, throwaway values for this tick's scoring only.
- **Do not touch the nemesis-block mechanism** (`generator.py:140-148`, SOC-232) — it is a separate,
  hard-block mechanism (blockers → flat 2.0 scoring penalty via `scoring.py`'s `blocker_penalty`),
  not to be conflated with this ticket's continuous trust/bonds score contribution, even though both
  live in the same code region.
- **Do not fix the pre-existing SOC-231/SOC-232 docstring/comment ID-collision**
  (`party_composition.py:5`, `src/core/state.py:573`) — disclosed in Step 1 and Step 4's
  `divergence_note`, not corrected. A fresh id (`SOC-244`) is minted instead of reusing either.
- **Do not fix `adventure_contract.md`'s pre-existing stale FORM_PARTY personality-bias table row**
  (shows `0.25`, code says `0.40`) or the pre-existing 13-vs-16 `RouteFamily` count drift — both
  pre-existing, unrelated to this ticket's scope.
- **Preserve backward compatibility of `PartyCompositionScorer.score()`'s signature** — `actor` is
  keyword-only with default `None`; every pre-existing positional call (`generator.py:139` pre-this-plan,
  `groups.py:312`, 2 direct test calls) continues to work unchanged in shape, and (per Design
  Decision 3) unchanged in numeric output.

## Dependency Map

- Step 1 (party_composition.py) must land before Step 2 (generator.py references
  `PartyCompositionScorer.score_trust_bonds`/`TRUST_BONUS_WEIGHT`, which Step 1 defines).
- Step 2 must land before Step 3 (Test 4 exercises the generator-level change).
- Steps 1+2 must land before Step 4 (parity ledger cites the implemented methods and a real,
  passing test).
- Step 3 must land before Step 4 (parity ledger's `test_path` must reference an existing, passing
  test).
- Steps 5, 6, 7, 8 (doc updates) are independent of each other and can land in any order, but should
  land after Steps 1-2 are finalized (they describe the exact implemented formulas) and ideally in
  the same session per CLAUDE.md's Parity rule.
- All steps are otherwise independent.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test | Honesty note |
|---|---|---|---|
| AC1: "FORM_PARTY confidence/benefit for a specific candidate incorporates that candidate's real per-entity trust_history/bonds value" | Steps 1, 2 | `test_party_composition_score_reflects_candidate_trust_history`, `test_form_party_route_benefit_and_confidence_differ_with_candidate_trust`, `test_party_composition_score_prioritizes_bond_sentiment_over_trust_history` | Genuinely satisfied at the read/computation layer (each candidate's own trust entry is read and incorporated); the value exposed on the route is a pool-level mean, not a literal single-candidate output field — see Design Decision 5 |
| AC2: "Two otherwise-identical FORM_PARTY candidate pools differing only in one candidate's trust_history value produce different comp_score/confidence for that candidate" | Steps 1, 2 | Same tests as AC1 | Fully, literally satisfied — AC2's own wording is at the comp_score/confidence (aggregate-output) granularity |
| AC3: "Regression test added alongside existing `test_sociability_weight_is_0_40_on_form_party_route`" | Step 3 | New tests land in `tests/unit/social/test_party_composition.py`, not literally "alongside" `test_phase3_route_scoring.py:200` | Deliberate, disclosed deviation from the ticket's literal file-location wording: since Option A makes zero changes to `scoring.py` (the file `test_sociability_weight_is_0_40_on_form_party_route` lives in), there is no new scoring.py-level behavior to test at that location. The correct location for new tests is the actually-changed file. `test_sociability_weight_is_0_40_on_form_party_route` itself continues to pass **completely unmodified**, which is the strongest possible proof this ticket does not touch that formula. Flagging for Review to confirm agreement. |
| AC4: "FORM_PARTY sociability weight of 0.40 ... remains bit-identical ...; new trust/bonds term is additive, not a replacement" | N/A — satisfied by the absence of any `scoring.py` edit | `test_sociability_weight_is_0_40_on_form_party_route` (`tests/unit/domains/adventure/test_phase3_route_scoring.py:200`, unmodified) must still pass | Unconditionally, trivially true: `scoring.py` has zero diff lines in this plan |

## Anti-Drift Notes

- **`scoring.py` has zero edits in this plan.** If Implement finds itself wanting to touch that file
  for this ticket, stop — that means the architectural decision (Option A) has been silently
  abandoned mid-implementation; escalate rather than proceed.
- **`groups.py:312` is a second, pre-existing caller of `PartyCompositionScorer.score()`** that
  investigation.md did not name — confirmed via this plan's own grep. It is unaffected by
  construction (optional/keyword-only `actor`), and it is explicitly out of scope to wire.
- **`src/core/state.py:573`'s `GroupRecord.composition_score` field comment** also mis-cites
  `SOC-232` — a second instance of the same pre-existing docstring bug beyond the one
  investigation.md found in `party_composition.py`'s own module docstring. Disclosed, not fixed,
  in both places.
- **Bond-sentiment-priority-over-trust_history is not an invented rule** — it mirrors real code
  (`appraisal.py:39-41`) and a real documented rule (`social_systems_contract.md:70`). Do not
  replace it with an averaging/blending formula during implementation without re-confirming this
  precedent still applies — averaging was considered and rejected in favor of this precedent (see
  Design Decision 2).
- **`TRUST_BONUS_WEIGHT = 0.15` is a new, independent constant on `PartyCompositionScorer`**, not a
  shared import from `scoring.py`'s `confidence_bonus` weight. The two files stay decoupled; the
  `0.15` value is a magnitude analogy only, chosen for consistency of "what counts as small" in this
  codebase, not a hard cross-file dependency.
- **`test_party_composition_score_unchanged_when_actor_omitted` (Step 3, Test 2) is the primary
  backward-compatibility guard** — equivalent in purpose to the sibling capability-confidence
  ticket's Test 2 pattern. A signature change that isn't fully backward-compatible fails this first.
- **Every doc update (Steps 5-8) must state plainly that `scoring.py` is unmodified** — do not let
  doc language drift into implying `AdventureRouteScorer`/`personality_bias`/`confidence_bonus`
  changed in any way.

## Unresolved Questions

None blocking implementation. One item is flagged for Review's explicit agreement rather than being
a gap: **AC3's literal "alongside `test_sociability_weight_is_0_40_on_form_party_route`" file-location
wording is not followed literally** (see Acceptance Criteria Map) because Option A's architecture
means there is no `scoring.py`-level behavior to test at that location — new tests instead land in
`tests/unit/social/test_party_composition.py`, the file that actually changes. If Review disagrees
with Option A itself (vs. Option B) or with this AC3 interpretation, that is a design disagreement to
raise at Review, not a gap in this plan.
