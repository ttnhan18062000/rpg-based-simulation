---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS
artifact_type: plan
tags: [cognition, strategy]
---

# Implementation Plan — TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS

## Summary

This is a pure-docs ticket: bring `docs/mechanics/04_strategic_cognition.md`,
`docs/simulation/domains/adventure_contract.md`, and
`docs/parity_ledger/strategic_cognition.yaml` into parity with C1 (cognition-profile eligibility,
landed in `src/domains/adventure/phase.py`) and C2 (generalized interruption bypass, landed in
`src/systems/strategic_systems/intelligence.py`, `mapper.py`, `service.py`). No `src/` file is
touched. Four steps: (1) rewrite the stale bypass line and add a short eligibility-gate note in
`04_strategic_cognition.md` §2, plus a one-line normalization cross-reference in §6.6; (2) replace
the eligibility table's `Role` row and correct the Purpose paragraph's hero-only framing in
`adventure_contract.md`; (3) add exactly two new parity-ledger entries, STRAT-252 and STRAT-253,
using the text/evidence/test_path already drafted and evidence-checked in `investigation.md`; (4)
run `make knowledge-index-update`. All three items the orchestrator flagged as needing an
Implement-time decision are resolved below rather than left open.

## Resolved Decisions (from investigation.md's flagged items)

**1. §1 scope.** Re-read `docs/mechanics/04_strategic_cognition.md:15-24` (Goal Hierarchy table)
directly for this plan: it lists four concern tiers (Survival/Biological/Social/Economic) and
carries no `EntityRole`/`hero`/role-gating claim of any kind — confirmed by
`grep -n -i "hero\|EntityRole" docs/mechanics/04_strategic_cognition.md`, whose only hits are at
lines 209-301 (§6.7/§6.9, the `QUEST_OPPORTUNITY` capability-match *scoring bonus*, a different
concept from adventure-routing *eligibility* and out of this ticket's scope). **Decision: §1 is
not edited.** The ticket's "§1-2" Scope wording is satisfied entirely by the §2 edit in Step 1
below, which adds the eligibility-gate note the AC requires. Do not invent a §1 table row or
tier change — none is warranted by current file content.

**2. "L56 hero-only framing" citation drift.** Re-read `adventure_contract.md:50-71` directly: line
56 is `| entity.identity.personality | Personality traits: ... |`, a "What It Reads" table row with
no hero-only claim — the ticket's cited line number has drifted. The two real correction targets,
confirmed by direct read, are the **Purpose paragraph** (`adventure_contract.md:19`, "The adventure
domain implements subjective route selection for heroes...") and the **eligibility table's Role
row** (`adventure_contract.md:31`, `EntityRole = 0` (hero)). **Decision: Step 2 edits target these
two exact spots, not line 56.** Per the investigation's Anti-Drift Hazard, the code's own parameter
name (`AdventureRouteGenerator.generate(hero, state)`, confirmed still present) means "hero" stays
as the domain's established shorthand everywhere else in the file — Step 2 must not globally
search-replace the word "hero".

**3. SKILL.md drift.** `.claude/skills/cognition-strategy/SKILL.md` and its `.agents/` mirror carry
the same stale "score > 80" bypass sentence this ticket fixes in the Mechanics Bible.
`tests/tools/test_cognition_strategy_skill_content.py` does not pin that sentence (confirmed by
investigation.md), so no test forces either fix. This ticket's own Scope/Related Docs/Related Code
Areas do not name `.claude/skills/` or `.agents/skills/` anywhere. **Decision: leave both SKILL.md
files untouched.** Editing agent-facing skill instructions is a distinct maintenance surface from
the Mechanics Bible/parity ledger this ticket's Scope actually names, and doing it here would be
undeclared scope expansion. This is recorded as a residual gap in Implementation Notes for a future
ticket (see Scope Guards below), not silently dropped.

## Steps

### Step 1 — Rewrite the stale bypass line and add eligibility-gate framing in `04_strategic_cognition.md` §2

**Files:** `docs/mechanics/04_strategic_cognition.md`

**Change:**
Current content at lines 37-39 (verified by direct read this session):
```
*   **Profile Resistance**: A value (0.0 to 1.0) defined by the entity's personality or class.
*   **resistance_multiplier**: A profile-defined constant (not a hard-coded 30.0); value varies by entity profile.
*   **Emergency Bypass**: High-urgency "Danger" concerns (score > 80) ignore the interruption margin.
```
Replace with:
1. A new lead-in sentence directly after the `## 2. Interruption Resistance` heading's existing
   intro paragraph (line 28), before the `Switch_Allowed` code block, stating: only entities whose
   resolved `CognitionProfileDefinition.supports_adventure_routing` is `True` are subject to this
   law for adventure-domain project routing (cite `src/content/schema.py:100` — the
   `supports_adventure_routing: bool = Field(False)` field — and cross-reference
   `docs/simulation/domains/adventure_contract.md` for the full eligibility gate). Do not claim
   this note applies to every strategic-goal switch in the engine (System B/`GoalRegistry` also
   uses `Switch_Allowed`); scope the sentence to "adventure-domain project routing" specifically,
   since `supports_adventure_routing` is an adventure-domain concept, not a general goal-switching
   gate.
2. Keep the two unchanged bullets (`Profile Resistance`, `resistance_multiplier`) verbatim.
3. Replace the `**Emergency Bypass**` bullet (line 39) with a `**Generalized Bypass**` bullet
   describing the actual landed rule, sourced from `src/systems/strategic_systems/
   intelligence.py:978-994` (cited in investigation.md's Current Behavior section, re-verified
   against `_score_scale_max()` at `intelligence.py:89-107` and the module constants at
   `intelligence.py:29-53`):
   - `kind="detour"` is the sole candidate exempt from the lock's added normalized floor/percentage
     requirement below — it is not exempt from anything else. A `detour` candidate still must clear
     the same base retention-priority comparison (`candidate_project.score > effective_current_score`,
     STRAT-005/006/187, byte-identical pre/post-ticket) that has always gated every candidate,
     locked or not — a low-score detour that doesn't clear that base comparison still does not
     switch. Do not write "detour always switches regardless of score" — that is not what the code
     does (`intelligence.py:978-1004`: the `kind=="detour"` branch only skips the `else` block's
     normalized floor/percentage gate; the final `if candidate_project.score > effective_current_score`
     check at the bottom of the function still applies unconditionally to every candidate, including
     detour).
   - Every other candidate kind, from either scoring system (System A/`AdventureRouteScorer`,
     declared ceiling `~2.9`, cross-referenced to §6.6; System B/`GoalRegistry`, ceiling `100.0`),
     must ADDITIONALLY clear a dual condition (on top of the same base comparison above) while a
     lock is active, normalized to its own system's ceiling: its normalized score must exceed both
     (a) the current project's normalized effective score
     (`current.score/current_max + retention_margin/current_max`) and (b) the fixed
     `_INTERRUPTION_URGENCY_FLOOR_PCT = 0.8` floor.
   - This generalizes the old "Danger score > 80" special case (which only ever applied to one
     concern kind on one 0-100 scale) to any kind on either scale.
4. Do not alter the `Switch_Allowed`/`Interruption_Margin` code block (lines 30-36) — STRAT-005/006
   /187 already document this formula as byte-identical pre/post-ticket (confirmed in
   investigation.md's Current Behavior section); this plan only touches the bypass bullet and adds
   the eligibility lead-in sentence.

**Do NOT touch:** §1 Goal Hierarchy table (lines 15-24, see Resolved Decision 1 above); §3-6.5;
the `Switch_Allowed`/`Interruption_Margin` formula block itself; §6.7-6.9's `QUEST_OPPORTUNITY`
role-based scoring-bonus tables (lines 209-301) — those describe a scoring multiplier, not the
eligibility gate, and are out of scope.

**Verify:** `grep -n "score > 80" docs/mechanics/04_strategic_cognition.md` returns no match in
§2 after the edit (per test_plan.md's AC2 verification); manual diff review against
investigation.md's Current Behavior C1/C2 citations (no automated test pins this prose — confirmed
in test_plan.md).

### Step 2 — Add the §6.6 normalization cross-reference

**Files:** `docs/mechanics/04_strategic_cognition.md`

**Change:** After the "Score Range Summary" table (ends at line 255, `**Total blocked** | clamped
to 0 | ~0.9`) and before the `---` separator at line 257, add one short note stating that the
`~2.9` "Total non-blocked" ceiling documented in this table is also the normalization anchor
(`_ADVENTURE_ROUTE_SCORE_MAX = 2.9`, `src/systems/strategic_systems/intelligence.py:29-31` per
investigation.md's Current Behavior citation) that System A candidate scores are divided by inside
`_score_scale_max()` when evaluated against the §2 generalized bypass gate. This is a documentation
addition only — the numeric ceiling itself (`~2.9`) is unchanged, confirmed by investigation.md's
Mechanics/Engine Constraints section ("This value is unchanged by C1/C2 — no §6.6 numeric
correction is needed, only an added note").

**Do NOT touch:** the table's numeric values themselves (lines 246-255); §6.7-6.9 immediately
following.

**Verify:** manual review — same AC2 verification as Step 1 (no dedicated automated test for this
prose per test_plan.md).

### Step 3 — Replace the eligibility table's Role row and correct the Purpose paragraph in `adventure_contract.md`

**Files:** `docs/simulation/domains/adventure_contract.md`

**Change:**
1. Purpose paragraph, current text at line 19 (verified by direct read this session):
   > "The adventure domain implements **subjective route selection** for heroes. Each eligible
   > tick, it generates candidate routes the hero could pursue, scores them through a
   > personality-biased formula, selects the highest-scoring non-deferred route, and emits a
   > `StateUpdate` carrying a `StrategicUpdate` that sets the hero's active project and objective.
   > Downstream tactical systems read the project to determine immediate actions."

   Replace only the first sentence's framing to state eligibility is driven by
   `CognitionProfileDefinition.supports_adventure_routing` (not role), and add a one-clause note
   that "hero" is retained as this domain's established shorthand for the routed entity — matching
   the code's own parameter naming (`AdventureRouteGenerator.generate(hero, state)`,
   `src/domains/adventure/` per this file's own Source line 11). Leave the rest of the paragraph
   (sentences 2-3, "Each eligible tick..." onward) unchanged — they describe route generation
   mechanics unaffected by C1/C2.

2. Eligibility table, current content at lines 29-34 (verified by direct read this session):
   ```
   | Criterion | Check |
   |---|---|
   | Role | `EntityRole = 0` (hero) |
   | Alive | `entity.combat.alive = True` |
   | Active | `entity.lifecycle.active = True` |
   | Project lock | `tick >= active_project.lock_until_tick` (or no active project) |
   ```
   Replace the `Role` row with a row describing the real 3-tier resolution landed in C1 (source:
   investigation.md's Current Behavior section, citing
   `src/domains/adventure/phase.py:49-80,83-96,126-131`): resolved
   `CognitionProfileDefinition.supports_adventure_routing = True`, resolved via (a) explicit
   `identity.properties["cognition_profile_id"]`, else (b) `identity.properties["role_id"]` →
   `RoleDefinition.default_cognition_profile`, else (c) legacy `EntityRole.HERO` → the `"hero"`
   role's own default. Rename the row label from `Role` to `Cognition eligibility` (or equivalent)
   so it no longer reads as a role check. Leave the `Alive`/`Active`/`Project lock` rows unchanged
   — C1/C2 did not touch those checks (confirmed: `phase.py:126-131`'s filter still ANDs
   `e.combat.alive and e.lifecycle.active`, per investigation.md).

**Do NOT touch:** any other "hero" noun in this file outside these two specific spots — per
Resolved Decision 2 above, the code's own parameter/identifier naming (`hero`,
`_threat_resolved(hero, state)`, etc., confirmed by investigation.md's Anti-Drift Hazards) means
"hero" remains this domain's correct shorthand elsewhere; a global find-replace would introduce
inaccuracy, not fix it. Do not touch "What It Owns" (lines 40-47), "What It Reads" (lines 50-72), or
any section past line 72.

**Verify:** `grep -n "EntityRole = 0" docs/simulation/domains/adventure_contract.md` returns no
match after the edit (per test_plan.md's AC3 verification); manual review against
investigation.md's Current Behavior citations.

### Step 4 — Add STRAT-252 and STRAT-253 to `strategic_cognition.yaml`

**Files:** `docs/parity_ledger/strategic_cognition.yaml`

**Change:** Append two new entries after the file's current last entry (highest existing id
confirmed `STRAT-251` by `grep -n "^  - id:" docs/parity_ledger/strategic_cognition.yaml | tail`
this session), using the exact field pattern of `STRAT-243`/`STRAT-251` (`id`, `text`, `status`,
`priority`, `legacy_evidence`, `v2_evidence`, `proof_type`, `test_path`, `divergence_note`,
`support_boundary`), with content drafted and evidence-checked in investigation.md's Parity Ledger
Overlap section (re-verified this session — all cited test functions confirmed present by
`grep -n "def test_..."` against their named files: `test_apply_respects_active_system_b_lock` and
`test_apply_switches_when_candidate_clears_bar` in
`tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py`,
`test_apply_commit_branch_does_not_construct_strategic_update_directly` in
`tests/unit/domains/adventure/test_phase3_project_switch_routing_guard.py`,
`test_map_to_states_carries_real_score_not_hardcoded_placeholder` and
`test_adventure_decision_service_carries_selected_score_into_proposed_project` in
`tests/unit/domains/adventure/test_phase3_route_families.py`):

```yaml
- id: STRAT-252
  text: >
    AdventureDecisionPhase.apply()'s project-commit branch routes through
    StrategicIntelligenceSystem.evaluate_project_switch() instead of unconditionally overwriting
    current_project_id, so System A's project handoff is now subject to the same
    interruption-resistance/lock-bypass gate as System B, closing the asymmetry where only System
    B respected an active lock (TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION).
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: >
    src/domains/adventure/phase.py:190-196 — the commit branch calls
    StrategicIntelligenceSystem.evaluate_project_switch(hero, result.proposed_project, tick) and
    continues the hero loop (skipping entity_updates for that hero) when it returns None, instead
    of constructing StrategicUpdate(current_project_id_set=...) directly and unconditionally.
    tests/unit/domains/adventure/test_phase3_project_switch_routing_guard.py AST-checks that the
    commit branch never again constructs StrategicUpdate( directly.
  proof_type: contract
  test_path: >-
    tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py::test_apply_respects_active_system_b_lock,
    tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py::test_apply_switches_when_candidate_clears_bar,
    tests/unit/domains/adventure/test_phase3_project_switch_routing_guard.py::test_apply_commit_branch_does_not_construct_strategic_update_directly
  divergence_note: null
  support_boundary: null
- id: STRAT-253
  text: >
    RouteToProjectMapper.map_to_states() threads the real AdventureRouteOption.score (via
    AdventureDecisionService.decide()'s score=selected.score) into ProjectState.score, replacing a
    previously-hardcoded score=1.0 for every System-A candidate — a prerequisite for STRAT-185/186's
    cross-system normalized score comparison to be meaningful for System A
    (TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION).
  status: verified
  priority: P2
  legacy_evidence: null
  v2_evidence: >
    src/domains/adventure/mapper.py:74,101 — map_to_states() gained a score: float = 1.0
    parameter threaded into ProjectState(score=score, ...); src/domains/adventure/service.py:147 —
    AdventureDecisionService.decide() passes score=selected.score at its one call site.
  proof_type: contract
  test_path: >-
    tests/unit/domains/adventure/test_phase3_route_families.py::test_map_to_states_carries_real_score_not_hardcoded_placeholder,
    tests/unit/domains/adventure/test_phase3_route_families.py::test_adventure_decision_service_carries_selected_score_into_proposed_project
  divergence_note: null
  support_boundary: null
```

**Do NOT touch:** `STRAT-243` (lines 2823-2851, C1's territory — already correctly landed per
investigation.md; the cosmetic `phase.py:126-130` vs `126-131` line-number drift noted there is
flagged, not fixed, by this ticket) or `STRAT-185/186/187` (lines 1987-2036, C2's territory —
already correctly landed). Do not renumber or reorder any existing entry. Do not touch any other
canonical ledger file (`substrate.yaml`, `combat_movement.yaml`, `town_resource.yaml`,
`progression.yaml`, `social_narrative.yaml`, `world_dynamics.yaml`, `infrastructure.yaml`).

**Schema compliance check (done at write time, not deferred to a gate):** per
`docs/parity_ledger/schema.json:6-9` (required: `id`, `text`, `status`, `priority`) and the
`v2_evidence`/`test_path` typing at schema.json's `properties` block (both typed
`["string", "null"]`, not enforced non-null by JSON Schema itself, but required in practice by this
repo's own `status: verified` convention — confirmed by every existing `verified` entry in this
file, e.g. STRAT-243/251, carrying non-null `v2_evidence` and `test_path`): both STRAT-252 and
STRAT-253 above have non-null `v2_evidence` and non-null `test_path`; both `id` values
(`STRAT-252`, `STRAT-253`) match the `^[A-Z]+-[0-9]{3}$` pattern; both `status: verified` and
`priority` in `{P0,P1,P2}` are valid enum members; `proof_type: contract` matches the enum
`["parity", "contract", "differential", "regression", null]` and mirrors STRAT-185/186/187's own
`proof_type` per investigation.md's Parity Ledger Overlap section, since these are present-code
contract facts, not differential/regression findings.

**Verify:** `pytest tests/tools/test_parity_index.py tests/tools/test_parity_ledger_scan.py
tests/tools/test_parity_index_baseline.py -v` (per test_plan.md's AC4 verification and Scoped
Pytest Commands) — the duplicate-id check confirms `STRAT-252`/`STRAT-253` don't collide with any
existing id (confirmed pre-edit highest is `STRAT-251`).

### Step 5 — Run `make knowledge-index-update`

**Files:** none directly (regenerates the knowledge-search index).

**Change:** Run `make knowledge-index-update` after Steps 1-4 land, per this ticket's own Scope
bullet and CLAUDE.md's "After Work" rule ("If any files under `docs/` were created or modified: run
`make knowledge-index-update`").

**Do NOT touch:** anything else in this step — it is index regeneration only, not a content edit.

**Verify:** command exits 0; no test_path required (index regeneration is not itself a test
target in test_plan.md).

## Scope Guards

- Do not touch `src/domains/adventure/phase.py`, `src/content/schema.py`, or
  `src/systems/strategic_systems/intelligence.py` — ticket's Out of Scope forbids all code changes;
  this is a pure-docs ticket. `git diff --stat -- src/` must be empty at Finalize (per
  test_plan.md's Anti-Drift Test Guards).
- Do not rewrite `STRAT-243` (C1's territory, already correctly landed) beyond what investigation.md
  flagged as a cosmetic line-number note — do not touch its `text`/`v2_evidence` at all in this
  ticket.
- Do not rewrite `STRAT-185/186/187` (C2's territory, already correctly landed) — only add the two
  new STRAT-252/253 entries; do not duplicate what they already say.
- Do not add an `intentional_divergences.md` entry — that belongs to C2, already closed at §2.40,
  per this ticket's own Out of Scope.
- Do not touch `docs/audits/D22_dormant_content_wiring.md` — C4's scope.
- Do not touch `.claude/skills/cognition-strategy/SKILL.md` or its `.agents/skills/` mirror — see
  Resolved Decision 3 above; flagged as a residual gap for a future ticket, not fixed here.
- When editing `adventure_contract.md`, do not globally replace the word "hero" — only the Purpose
  paragraph's eligibility framing and the eligibility table's Role row (see Resolved Decision 2).
- Do not invent a §1 (Goal Hierarchy table) edit in `04_strategic_cognition.md` — see Resolved
  Decision 1; no role/eligibility claim currently exists there to correct.
- Never: `pytest tests/` (full suite) — scoped commands only, per test_plan.md.

## Dependency Map

All four content steps (1-4) are independent of each other — they touch three disjoint files (two
sections of `04_strategic_cognition.md` in Steps 1-2, `adventure_contract.md` in Step 3,
`strategic_cognition.yaml` in Step 4) and can be done and verified in any order. Step 5
(`make knowledge-index-update`) depends on Steps 1-4 being complete, since it indexes their output;
run it last.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: §1-2 describes eligibility via `supports_adventure_routing` + real bypass rule | Step 1 (eligibility lead-in sentence + bypass bullet rewrite in §2; §1 confirmed to need no edit per Resolved Decision 1) | Manual diff review against investigation.md's Current Behavior citations (test_plan.md: no automated prose test) |
| AC2: stale L39 line replaced; §6.6 normalization resolution documented if applicable | Step 1 (bypass bullet replacement) + Step 2 (§6.6 cross-reference note) | `grep -n "score > 80" docs/mechanics/04_strategic_cognition.md` → no match in §2 |
| AC3: adventure_contract.md Role row replaced; hero-only framing corrected | Step 3 (Purpose paragraph + eligibility table Role row; targets re-derived from current file content per Resolved Decision 2, not the ticket's stale L56 citation) | `grep -n "EntityRole = 0" docs/simulation/domains/adventure_contract.md` → no match |
| AC4: strategic_cognition.yaml gains STRAT-252+ entries, v2_evidence from actual landed code | Step 4 | `pytest tests/tools/test_parity_index.py tests/tools/test_parity_ledger_scan.py tests/tools/test_parity_index_baseline.py -v` + manual content review |
| AC5: the 4 named test files continue to pass | Steps 1-4 (all edits confined to docs, none touch SKILL.md or `src/`) | `pytest tests/tools/test_cognition_strategy_skill_content.py tests/tools/test_parity_ledger_scan.py tests/tools/test_parity_index.py tests/tools/test_parity_index_baseline.py -v` |

## Anti-Drift Notes

- `EntityRole.HERO` still legitimately appears in the landed code as a Tier-3 fallback inside
  `_resolve_cognition_profile_id` (`phase.py:76`) — the docs should describe this fallback tier
  accurately (Step 3's table row includes it as tier (c)), not claim `EntityRole.HERO` is entirely
  gone from the resolution logic.
- The `_score_scale_max()` classification is by **enum class identity**
  (`isinstance(kind, ProjectKind)`), not string value — `ProjectKind.HARVESTING`/`SOCIAL` and
  `GoalKind.HARVESTING`/`SOCIAL` share string values but are different classes. If Step 1's bypass
  bullet mentions "kind", it must not imply the classification is string-based.
  (`intelligence.py:89-107` per investigation.md.)
- The raw `retention_margin`/`effective_current_score` formula and the final unconditional
  `candidate_project.score > effective_current_score` comparison
  (`intelligence.py:996-1004`, STRAT-005/006/187) are byte-identical to pre-ticket code —
  normalization is confined entirely to the lock-bypass branch (`intelligence.py:978-994`). Step 1
  must not describe the base `Switch_Allowed` formula itself as changed.
- `docs/mechanics/04_strategic_cognition.md` and `docs/simulation/domains/adventure_contract.md`
  both carry `last_verified`/`status` frontmatter (`status: authoritative`,
  `last_verified: 2026-08-09` and `status: active`, `last_verified: 2026-07-03` respectively,
  confirmed by direct read this session) — per test_plan.md's Frontmatter validation note, bump
  `last_verified` to today's date (2026-08-10) on both files if that is this repo's existing
  convention for content edits (confirm against other recently-edited docs at Implement time before
  assuming).
- STRAT-252/253 numbering is not a hard requirement beyond "next available id following the
  pattern" — if Implement's own re-read finds a third genuinely-uncovered claim, add STRAT-254
  following the same field pattern rather than force-fitting it into 252/253; if either proposed
  entry is judged already adequately covered by STRAT-185/186/187's existing prose, that is a
  legitimate scope-narrowing call to record explicitly in Implementation Notes, not to silently
  drop.

## Deviations

- **Step 1 wording, self-caught during verification.** The first draft of the Generalized Bypass
  bullet's closing clause ("generalizes the old 'Danger score > 80' special case") accidentally
  reproduced the literal stale substring `score > 80` that this same step's own verify command
  (`grep -n "score > 80" ... # should return no match in §2`) checks for. Not a change of content
  or intent — reworded to "Danger score above 80" (same meaning) so the plan's own verification
  passes. No other step deviated from this plan's content.
