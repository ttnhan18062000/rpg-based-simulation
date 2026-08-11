---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS
artifact_type: investigation
tags: [cognition, strategy]
---

# Investigation — TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS

## Current Behavior

### C1 — Cognition-profile eligibility (landed, `src/domains/adventure/phase.py`)

- `CognitionProfileDefinition.supports_adventure_routing: bool = Field(False)` —
  `src/content/schema.py:100`.
- `data/content/living/cognition_profiles.yaml` — all 7 profiles now have an explicit authored
  value: `practical_humanoid` (L12) `true`, `instinctive_animal` (L24) `false`,
  `opportunistic_humanoid` (L36) `true`, `disciplined_guard` (L48) `true`, `trade_pragmatist`
  (L60) `true`, `arcane_scholar` (L72) `true`, `undead_fixated` (L84) `false`.
- `_resolve_cognition_profile_id(entity)` (`src/domains/adventure/phase.py:49-80`) — 3-tier
  resolution: Tier 1 `identity.properties["cognition_profile_id"]` if present; Tier 2
  `identity.properties["role_id"]` → `RoleDefinition.default_cognition_profile`; Tier 3
  `identity.role == EntityRole.HERO` → the `"hero"` role's own default (evidenced real-corpus
  gap for `hero_adventurers`-spawned entities that have neither key set).
- `_supports_adventure_routing(entity, cache)` (`phase.py:83-96`) — resolves the profile id, then
  looks up `get_cognition_profile_definition(profile_id).supports_adventure_routing`, caching by
  profile id per `apply()` call.
- `AdventureDecisionPhase.apply()`'s `heroes` filter (`phase.py:126-131`):
  ```python
  heroes = [
      e for e in state.entities.values()
      if _supports_adventure_routing(e, _profile_eligibility_cache)
      and e.combat.alive and e.lifecycle.active
  ]
  ```
  This is a strict **replacement** of the old `entity.identity.role == EntityRole.HERO` check
  (per Goal 1 of the design doc — "in place of," not "in addition to"). `EntityRole.HERO` still
  appears in the file, but only inside `_resolve_cognition_profile_id`'s Tier-3 fallback
  (`phase.py:76`), not in the eligibility filter itself.

### C2 — Generalized interruption bypass (landed, `src/systems/strategic_systems/intelligence.py`)

Module-level constants (`intelligence.py:29-53`):
```python
_ADVENTURE_ROUTE_SCORE_MAX: float = 2.9   # System A (AdventureRouteScorer) declared ceiling
_GOAL_UTILITY_SCORE_MAX: float = 100.0    # System B (GoalRegistry) declared ceiling / default
_INTERRUPTION_URGENCY_FLOOR_PCT: float = 0.8   # generalized urgency floor, == old score>80
```
`_score_scale_max(kind)` (`intelligence.py:89-107`) classifies by **enum class identity**
(`isinstance(kind, ProjectKind)`), not string value — `ProjectKind.HARVESTING`/`SOCIAL` and
`GoalKind.HARVESTING`/`SOCIAL` share string values but are different classes.

`evaluate_project_switch()`'s lock-bypass branch (`intelligence.py:978-994`):
```python
if current.lock_until_tick > current_tick:
    if candidate_project.kind == "detour":
        pass
    else:
        candidate_max = _score_scale_max(candidate_project.kind)
        current_max = _score_scale_max(current.kind)
        candidate_pct = candidate_project.score / candidate_max
        normalized_effective_current_pct = (current.score / current_max) + (retention_margin / current_max)
        if not (candidate_pct > normalized_effective_current_pct
                and candidate_pct > _INTERRUPTION_URGENCY_FLOOR_PCT):
            return None
```
`"detour"` is the sole unconditional structural bypass. Every other `kind` (regardless of which
system produced it, or whether it's a synthetic/future kind) must clear both its own normalized
percentage of the current project's normalized effective score, AND the 0.8 floor. The raw
`retention_margin`/`effective_current_score` formula and the final unconditional
`candidate_project.score > effective_current_score` comparison (`intelligence.py:996-1004`,
STRAT-005/006/187) are byte-identical to pre-ticket code — normalization is confined entirely to
the lock-bypass branch.

Two supporting fixes made the above meaningful:
- **Score threading** (`src/domains/adventure/mapper.py:74,101`; `src/domains/adventure/
  service.py:147`): `RouteToProjectMapper.map_to_states()` gained a `score: float = 1.0`
  parameter threaded into `ProjectState(score=score, ...)` (was hardcoded `score=1.0`
  unconditionally before this ticket); `AdventureDecisionService.decide()` now passes
  `score=selected.score` at its one call site. Without this, every System-A candidate would
  always present as `score=1.0` regardless of its real `AdventureRouteScorer` output, making the
  new normalized comparison meaningless for System A.
- **Routing through the shared gate** (`src/domains/adventure/phase.py:190-196`):
  `AdventureDecisionPhase.apply()` previously constructed
  `StrategicUpdate(current_project_id_set=...)` directly, unconditionally overwriting
  `current_project_id` regardless of any active System-B lock. It now calls
  `StrategicIntelligenceSystem.evaluate_project_switch(hero, result.proposed_project, tick)` and
  `continue`s the hero loop (skipping `entity_updates` for that hero) when it returns `None`. This
  closes the second asymmetry the design doc's open question flagged: System A is now subject to
  the same interruption-resistance/lock-bypass gate as System B, not just System B subject to it.

An architecture guard (`tests/unit/domains/adventure/
test_phase3_project_switch_routing_guard.py`) AST-checks that `phase.py`'s commit branch never
again constructs `StrategicUpdate(` directly and does call `evaluate_project_switch`.

## Mechanics / Engine Constraints

- `docs/mechanics/04_strategic_cognition.md` §2 (Interruption Resistance,
  `docs/mechanics/04_strategic_cognition.md:27-39`) is the authoritative source for the
  `Switch_Allowed`/`Interruption_Margin` law and currently documents the pre-generalization
  "Emergency Bypass" special case (see stale text below) — this is the Mechanics Bible chapter
  this ticket's own Scope names for the rewrite.
- §6.6 (`docs/mechanics/04_strategic_cognition.md:244-256`, "Score Range Summary") is the
  authoritative source for System A's declared max (`~2.9`, "Total non-blocked"), which
  `_ADVENTURE_ROUTE_SCORE_MAX` in the landed code cites directly by comment. This value is
  unchanged by C1/C2 — no §6.6 numeric correction is needed, only an added note that this range
  is now also the normalization basis for the generalized lock-bypass gate.
- Per CLAUDE.md's Authoritative Mechanics Rule, since C1/C2 changed logic, the corresponding docs
  and parity ledger must be brought to parity "in the same session" as the logic change — C2's own
  plan.md explicitly deferred that entire narrative-doc obligation to this ticket (see Prior Work).

## Docs Requiring Update

- `docs/mechanics/04_strategic_cognition.md`: §1-2 eligibility framing and the L39 stale
  "Emergency Bypass (score>80)" line must describe the real cognition-profile eligibility gate and
  the generalized dual-condition/normalized bypass rule; §6.6 needs a short note that its declared
  max is now also the normalization anchor for the bypass gate.
- `docs/simulation/domains/adventure_contract.md`: the eligibility table's `Role = EntityRole = 0
  (hero)` row must be replaced with the real `supports_adventure_routing` cognition-profile check;
  the Purpose/eligibility framing must stop implying role=HERO is the gate.
- `docs/parity_ledger/strategic_cognition.yaml`: needs 2 new entries (STRAT-252, STRAT-253) — see
  "Parity Ledger Overlap" below for exactly what is and is not already covered.

## Parity Ledger Overlap

**STRAT-243** (`strategic_cognition.yaml:2823-2848`) — **already updated, by C1** (its own
Implementation Notes Step 12, `tickets/done/TCK-20260810-COGNITION-PROFILE-ADVENTURE-
ELIGIBILITY.md`). Text and `v2_evidence` accurately describe the 3-tier resolution and the
`supports_adventure_routing` eligibility gate as actually landed. Minor drift only: the entry's
`v2_evidence` cites `phase.py:126-130`/`82-95`/`48-79`; the current file has these one line lower
(`126-131`/`83-96`/`49-80`) — cosmetic off-by-one from intervening edits, not a factual error. Not
worth a full rewrite; flag only, do not "fix" by touching STRAT-243 (C1's territory, already
closed).

**STRAT-185/186/187** (`strategic_cognition.yaml:1987-2036`) — **already updated, by C2** (its own
Implementation Notes Step 12, `tickets/done/TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION.md`).
`v2_evidence` and `test_path` accurately describe the generalized lock-bypass gate, the
`_score_scale_max` classifier, and the retention-priority formula's byte-identical preservation.
These are P0 entries with passing `test_path`s (confirmed present:
`tests/unit/strategic/test_interruption_resistance.py::TestGenericInterruptionBypass::*`,
`tests/unit/strategic/test_interruption_resistance.py::TestInterruptionResistance::
test_switch_when_candidate_exceeds_margin`).

**Genuinely uncovered by any existing entry** (highest existing id in the file is STRAT-251; no
STRAT-252+ exists yet):

1. **The `AdventureDecisionPhase` → `evaluate_project_switch()` routing integration.** STRAT-185/
   186/187 describe `evaluate_project_switch()`'s own internal mechanism; none of them state the
   separate, previously-true-in-neither-direction fact that System A's project handoff is *now
   subject to* that mechanism at all (closing the "phase.py always overwrites, ignoring any active
   lock" asymmetry the design doc's open question named). This is a distinct, testable claim
   (`phase.py:190-196` + the architecture guard test) that C1's plan.md Step 12 explicitly
   reserved for this ticket ("Any broader parity-ledger pass... entries covering C2's own
   bypass-generalization logic remains the sibling docs ticket's job").
2. **The `RouteToProjectMapper` score-threading fix.** Neither STRAT-185/186/187 nor STRAT-243
   states that `ProjectState.score` for System-A candidates now carries the real
   `AdventureRouteScorer` output rather than a hardcoded `1.0` — a prerequisite fact for
   STRAT-185/186's normalized comparison to be meaningful for System A at all, and itself a
   distinct, separately-testable claim (`test_map_to_states_carries_real_score_not_hardcoded_
   placeholder`, `test_adventure_decision_service_carries_selected_score_into_proposed_project`).

Proposed new entries (field pattern matches STRAT-243/250/251 exactly):

- **STRAT-252** — text: `AdventureDecisionPhase.apply()`'s project-commit branch routes through
  `StrategicIntelligenceSystem.evaluate_project_switch()` instead of unconditionally overwriting
  `current_project_id`, so System A's project handoff is now subject to the same
  interruption-resistance/lock-bypass gate as System B (closing the asymmetry where only System B
  respected an active lock). `v2_evidence`: cite `phase.py:191-196` real code + the AST
  architecture guard. `test_path`:
  `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py::
  test_apply_respects_active_system_b_lock,
  tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py::
  test_apply_switches_when_candidate_clears_bar,
  tests/unit/domains/adventure/test_phase3_project_switch_routing_guard.py::
  test_apply_commit_branch_does_not_construct_strategic_update_directly`. `priority: P1` (same
  tier as STRAT-243, the sibling eligibility entry). `status: verified`.
- **STRAT-253** — text: `RouteToProjectMapper.map_to_states()` threads the real
  `AdventureRouteOption.score` (via `AdventureDecisionService.decide()`'s `score=selected.score`)
  into `ProjectState.score`, replacing a previously-hardcoded `score=1.0` for every System-A
  candidate — a prerequisite for STRAT-185/186's cross-system normalized score comparison to be
  meaningful for System A. `v2_evidence`: cite `mapper.py:74,101` and `service.py:147`.
  `test_path`: `tests/unit/domains/adventure/test_phase3_route_families.py::
  test_map_to_states_carries_real_score_not_hardcoded_placeholder,
  tests/unit/domains/adventure/test_phase3_route_families.py::
  test_adventure_decision_service_carries_selected_score_into_proposed_project`. `priority: P2`
  (a supporting/plumbing fact, not itself a strategic law — matches STRAT-251's P2 precedent for a
  narrower, mechanism-level fix). `status: verified`.

Both should have `legacy_evidence: null`, `proof_type: contract` (matching STRAT-185/186/187's
`proof_type`, since these describe present-code contract facts, not a differential/regression
finding), `divergence_note: null` (the underlying divergence is already recorded once, under C2's
`intentional_divergences.md` §2.40 — STRAT-186 already cross-references it; a new entry does not
need to re-point to it unless Implement judges it materially separate), `support_boundary: null`.

## Stale Text Requiring Replacement (quoted verbatim, current state)

**`docs/mechanics/04_strategic_cognition.md:39`**:
> `*   **Emergency Bypass**: High-urgency "Danger" concerns (score > 80) ignore the interruption margin.`

**`docs/mechanics/04_strategic_cognition.md` §1** (Goal Hierarchy table,
`docs/mechanics/04_strategic_cognition.md:18-23`) does not itself claim role=HERO gating — it
describes concern tiers, which are unaffected by C1/C2. The ticket's Scope names "§1-2" together;
the actual eligibility-gate claim needing replacement lives in §2 (L39) and, more diffusely, in the
chapter's framing that treats "entities" generically already (no explicit role=HERO language found
in §1 to correct). Implement should re-confirm §1 needs no edit beyond context, and should not
invent a §1 change that isn't there.

**`docs/simulation/domains/adventure_contract.md:27-36`** (eligibility table):
```
| Criterion | Check |
|---|---|
| Role | `EntityRole = 0` (hero) |
| Alive | `entity.combat.alive = True` |
| Active | `entity.lifecycle.active = True` |
| Project lock | `tick >= active_project.lock_until_tick` (or no active project) |
```
The `Role` row is stale and must be replaced with the real `supports_adventure_routing`
cognition-profile check (per STRAT-243's landed text).

**Note on the ticket's own cited "L56 'What It Reads' hero-only framing"**: at the file's current
state, line 56 is `| \`entity.identity.personality\` | Personality traits: ... |` — a table row
with no hero-only claim. No line in the current "What It Reads" section (`adventure_contract.md:
50-71`) makes an explicit hero-only assertion; the closest framing issue is the **Purpose**
paragraph (`adventure_contract.md:19`, "The adventure domain implements subjective route selection
for heroes...") and the eligibility-table Role row itself (L31 in current numbering). This is
either (a) drift in the ticket's own cited line number since it was written, or (b) referring to
the generic "hero" variable-name usage throughout the file, which is a code-naming fact (the
`AdventureDecisionPhase`/`AdventureRouteGenerator` code still literally names its parameter
`hero`), not a documentation error, and should not be globally search-replaced. **Open question for
Implement**: treat "hero" as the domain's established shorthand for "the routed entity" (used
consistently in code identifiers too) and only correct the specific eligibility-determining claims
(Purpose line 19's implicit role framing, and the Role table row), not every incidental "hero" noun
in the file.

## Prior Work

- `docs/architecture/2026-08-10-cognition-driven-adventure-eligibility-design.md` — the batch
  design doc (read in full). §4 lists the doc-update deliverables this ticket implements, but is a
  flat list, not a per-ticket ownership split (confirmed by C2's own plan.md Step 11 removal note,
  which found and removed an earlier draft's incorrect claim that §4 assigned sections to specific
  tickets).
- `stored_artifacts/TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY/plan.md` Step 12/12b —
  C1's own STRAT-243 rewrite, confirmed landed verbatim in the current ledger. Step 12's own text
  explicitly excludes "narrative rewrite of 04_strategic_cognition.md... or adventure_contract.md"
  and "new STRAT-25X entries for the generalized-eligibility concept as a whole" from its own
  scope, assigning both to this ticket.
- `stored_artifacts/TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION/plan.md` and the done
  ticket's own Implementation Notes — C2's 13-step sequence, confirmed landed with only 2 minor
  test-arithmetic deviations (documented in its own plan.md Deviations section; no logic
  deviation). Step 11 (removed) and the ticket's own Out of Scope/Scope Guards confirm
  `docs/mechanics/04_strategic_cognition.md` and `adventure_contract.md` were deliberately left
  untouched by C2, reserved for this ticket.
- `docs/guidelines/intentional_divergences.md` §2.40 (added by C2) — already records the
  bypass-tightening rationale (class `Enforced`); this ticket's own Out of Scope confirms it does
  not own that entry and should not duplicate it.

## Risks and Open Questions

- **SKILL.md drift (out of this ticket's Scope, flagged not fixed)**: `.claude/skills/
  cognition-strategy/SKILL.md` and its mirror `.agents/skills/cognition-strategy/SKILL.md` both
  contain the same stale claim this ticket is fixing in the Mechanics Bible: `"**Emergency
  bypass**: Danger concerns scoring > 80 ignore the interruption margin entirely."` (both files,
  near line 70-73). `tests/tools/test_cognition_strategy_skill_content.py` does **not** pin this
  specific sentence (it only asserts `"Interruption_Margin = Profile_Resistance *
  resistance_multiplier"` and `"not a hardcoded 30.0"` are present), so this ticket's edits will
  not break that test either way. This ticket's own Related Docs/Scope does not name SKILL.md, and
  editing it is not requested — flagging only, since leaving it stale means the Mechanics Bible and
  its own downstream skill-doc mirror will disagree on the bypass rule after this ticket lands. If
  the batch owner wants this closed, it needs its own ticket or an explicit scope-expansion
  decision — not a silent inclusion here.
- **"L56 hero-only framing" citation appears stale relative to the current file** (see Stale Text
  section above) — flagged, not assumed away; Implement should re-derive the actual correction
  target from the file's current content rather than trusting the ticket's line number literally.
- **STRAT-252/253 numbering is a judgment call, not a hard requirement.** The ticket only requires
  "STRAT-252+ entries... following the field pattern" for whatever is genuinely uncovered; this
  investigation found exactly 2 genuinely-new claims (see Parity Ledger Overlap). If Implement's
  own re-read finds a third, add STRAT-254 following the same pattern; if either of the two
  proposed here is judged to already be adequately covered by STRAT-185/186/187's existing prose,
  that is a legitimate scope-narrowing call to make explicitly in Implementation Notes, not to
  silently skip.

## Anti-Drift Hazards

- Do not touch `src/domains/adventure/phase.py`, `src/content/schema.py`, or
  `src/systems/strategic_systems/intelligence.py` — this is a pure-docs ticket; the ticket's own
  Out of Scope forbids code changes to all three.
- Do not re-litigate or "fix" STRAT-243 (C1's territory, already correctly landed) beyond the
  cosmetic line-number note above — do not rewrite its `text`/`v2_evidence` wholesale.
- Do not re-litigate or "fix" STRAT-185/186/187 (C2's territory, already correctly landed) — only
  add new STRAT-252+ entries for genuinely uncovered facts; do not duplicate what they already say.
- Do not add an `intentional_divergences.md` entry — that belongs to C2, already closed (§2.40),
  per this ticket's own Out of Scope.
- Do not touch `docs/audits/D22_dormant_content_wiring.md` — C4's scope.
- When editing `adventure_contract.md`, do not globally replace every "hero" noun — the code
  itself still names its parameter `hero` (`AdventureRouteGenerator.generate(hero, state)`,
  `_threat_resolved(hero, state)`, etc.); only correct claims that assert role=HERO is the
  eligibility gate.
- `docs/parity_ledger/schema.json` requires `v2_evidence` and `test_path` non-null for any
  `status: verified`/`divergent` entry, and `divergence_note` non-null for `status: divergent` —
  the two new entries proposed above are `status: verified`, so both `v2_evidence` and `test_path`
  are mandatory; `id` must match `^[A-Z]+-[0-9]{3}$` (STRAT-252, STRAT-253 satisfy this).
- Run `make knowledge-index-update` after editing any `docs/` file, per this ticket's own Scope
  and CLAUDE.md's "After Work" rule.
