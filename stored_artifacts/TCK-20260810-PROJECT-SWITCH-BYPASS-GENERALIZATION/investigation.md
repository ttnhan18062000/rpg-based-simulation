---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION
artifact_type: investigation
tags: [cognition, strategy]
---

# Investigation — TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION

## Current Behavior

### `StrategicIntelligenceSystem.evaluate_project_switch()` — `src/systems/strategic_systems/intelligence.py:881-935`

```python
if current.lock_until_tick > current_tick:
    # Bypass lock ONLY for high-urgency danger/safety projects
    if (candidate_project.kind == "danger" and candidate_project.score > 80) or candidate_project.kind == "detour":
        pass 
    else:
        return None 

# Logic ID: STRAT-005 (Project switching uses interruption resistance)
retention_margin = profile.interruption_resistance * profile.resistance_multiplier
# Logic ID: STRAT-006 (Current project gets retention priority)
effective_current_score = current.score + retention_margin

if candidate_project.score > effective_current_score:
    return StrategicUpdate(... current_project_id_set=candidate_project.id ...)
return None
```
(L913-935). Docstring cites Logic IDs STRAT-185/186/187 directly on this function (L888-890).

Default `CognitionProfile` (`src/core/strategic.py:309-323`): `interruption_resistance=0.3`,
`resistance_multiplier=30.0` → default `retention_margin = 9.0`.

Two call sites, both inside `evaluate_strategic_intent()`:
- L1270: `detour_proj = ProjectState(..., kind="detour", score=best.score + 50.0)` — always `kind="detour"`.
- L1351: `candidate_proj = ProjectState(..., kind=best_candidate.kind, score=best_candidate.utility)` where
  `best_candidate` comes from `GoalRegistry.get_all_scores()` (System B). `candidate_proj.score` is therefore
  **directly** a System B `GoalScore.utility` value, unmodified.

### `AdventureDecisionPhase.apply()` — `src/domains/adventure/phase.py`

Per-hero own-lock gate (L141-150, confirmed present, so the ticket's framing of "unconditional"
needs one caveat — see below):
```python
if strat and strat.current_project_id:
    active_proj = strat.projects.get(strat.current_project_id)
    if active_proj:
        if tick < active_proj.lock_until_tick and not _threat_resolved(hero, state):
            continue
```
This only checks the **hero's own current project's** lock, and only skips the entity entirely
for the tick — it never compares the new candidate's score to anything. Once this gate is
passed (lock genuinely expired, OR `_threat_resolved()` returns True even while
`lock_until_tick` is still in the future), the function proceeds to generate/score new routes and,
if one is selected, unconditionally commits it (L189-195):
```python
if result.proposed_project and result.proposed_objective:
    strat_upd = StrategicUpdate(
        projects_add_or_update=[result.proposed_project],
        current_project_id_set=result.proposed_project.id,
        current_objective_id_set=result.proposed_objective.id,
    )
```
`evaluate_project_switch()` is never imported or called anywhere in `phase.py` (confirmed by grep —
only match for `current_project_id_set` in the file is this one assignment). **Confirmed: the design
doc's open question #2 is correct as stated**, with the refinement that the gap is specifically the
*threat-released-but-lock-not-expired* path plus the general absence of any score comparison against
`current.score`/`effective_current_score` for whatever project is active when the hero re-evaluates.

**Sharper finding not anticipated by the design doc:** the `ProjectState` that
`AdventureDecisionPhase` actually commits does not even carry the real route score.
`RouteToProjectMapper.map_to_states()` (`src/domains/adventure/mapper.py:96-105`) hardcodes
`score=1.0` unconditionally:
```python
project = ProjectState(
    id=project_id, kind=p_kind, status=ProjectStatus.ACTIVE,
    score=1.0,   # <-- hardcoded, NOT selected.score (the real ~0-2.9 AdventureRouteScorer score)
    lock_until_tick=min(tick + 10, tick + 50), ...
)
```
The real, computed score (`AdventureRouteOption.score`, the ~0-2.9-range value) lives on
`AdventureDecisionResult.selected` and is used for route *selection* and for the trace/observability
record (`trace["selected_score"]`, `service.py:156`), but is discarded before the `ProjectState` is
built. So even after Implement routes `apply()` through `evaluate_project_switch()`, comparing
`candidate_project.score` (System A, real value) against `current.score` (if `current` is itself a
System A project, its stored `score` is always exactly `1.0`, not its real computed score) will be
comparing a real number against a placeholder unless this hardcoded `1.0` is also fixed. This is a
concrete blocker for AC2/AC3's "normalize before comparison" requirement — normalization can't fix a
value that was never carried through in the first place. **Flagging for Plan; not silently assumed
away.**

### Score scale — System A vs System B (open question #1)

`docs/mechanics/04_strategic_cognition.md` §6.6 (read directly, L244-256): System A
(`AdventureRouteScorer.score()`) documents **Total non-blocked: 0.0 to ~2.9** (urgency ≤2.0 + benefit
≤0.5 + personality_bias ≤0.25 + confidence_bonus ≤0.15, minus risk_penalty). This is the authoritative,
certified-parity chapter — confirmed as claimed by the ticket/design doc, not assumed.

System B (`src/ai/goals/scorers.py`, read directly, all 9 registered scorers in
`src/ai/goals/__init__.py:10-19`):
| Scorer | Formula | Approx range |
|---|---|---|
| `HarvestScorer` | `50.0 / dist` (dist ≥ 1) | 0 – 50 |
| `SleepScorer` | `sleep_debt` (+30 night bias) | 0 – ~130 |
| `EatScorer` | `hunger` | 0 – ~100 |
| `SocialScorer` | flat `10.0` | 10 |
| `TownScorer` | `(sleep+hunger)/2 + inv_ratio*40 + (1-hp_ratio)*60` | 0 – ~200 |
| `CombatEngageScorer` | `40 + bravery*40 + stamina_ratio*20` | 40 – 100 |
| `CombatRetreatScorer` | (not fully read; combat-derived) | unbounded-ish |
| `RecoverScorer` | HP-based | comparable to Town/Combat |
| `GuildNeedScorer` | flat `25.0` | 25 |

Confirms and sharpens the design doc's claim: System B's real range is not merely "up to 100" — some
scorers (`TownScorer`, `SleepScorer`) can exceed 100. The ~2.9 vs ~100 framing in the design doc is a
conservative floor of the real gap, not an overstatement.

**Is the raw cross-system comparison at L925 already lopsided in practice? Confirmed yes, with a
caveat.** The only place a System A-originated `ProjectState.score` can reach `evaluate_project_switch()`
today is as `current` (never as `candidate_project` — System A never calls this function at all, per
above). And because of the `mapper.py:100` hardcoded `score=1.0`, any System A project sitting as
`current` always evaluates as `effective_current_score = 1.0 + retention_margin` (≈10.0 by default) —
trivially beaten by almost any System B candidate (`HarvestScorer` alone clears this at `dist ≤ 5`).
So the practical lopsidedness is even more extreme than a raw ~2.9-vs-100 comparison would suggest: it
is effectively **1.0-vs-(10-200)** because of the placeholder score, not the real ~2.9 ceiling.

### The `"danger"` bypass branch is effectively dead code today

`ProjectState.kind` is typed `ProjectKind` (`src/core/strategic.py:244-253`) but is populated with raw
strings everywhere in practice (`"detour"`, `"harvesting"`, `GoalKind` values like `"combat_engage"` —
none of which is even a member of the `ProjectKind` enum, confirming the design doc's own
"`GoalKind`/`ProjectKind` vocabulary split" dormant-wiring finding is real and pre-existing, out of
this ticket's scope per its "Out of Scope" section referencing C4/D22).

Grepped every `ProjectState(` construction site in `src/` (7 sites: `mapper.py`, `intelligence.py`×2,
`events.py`×2, `contracts.py`, `quests.py`) plus `intelligence.py:1334`'s `kind=best_candidate.kind`
path. **`kind="danger"` never appears at any of them.** `"danger"` only ever appears as a `ConcernState.kind`
or `BlockerState.kind` value (`ConcernKind.DANGER = "danger"`, `src/core/strategic.py:150-153`) —
a different dataclass entirely, never passed into `evaluate_project_switch()`. Grepped
`tests/` for any test constructing `ProjectState(kind="danger", ...)`: **none found** — no existing
test locks in the "danger and score>80" bypass branch either. **Conclusion: the `"danger"` allowlist
branch at L915 is unreachable via any live production code path today** — it only exercises via a
directly hand-constructed `ProjectState` (as AC4's new regression test will need to do). This doesn't
change the ticket's scope (AC4 explicitly requires the regression test to hand-construct this
scenario), but it means "existing danger-bypass scenarios" is a specified contract, not an
observed-in-production behavior — worth stating precisely in the divergence note rather than implying
a live corpus scenario is affected.

## Mechanics / Engine Constraints

- `docs/mechanics/04_strategic_cognition.md` §6.6 — authoritative System A score range (Certified
  Level 1). Any change to how System A scores are compared/normalized must stay consistent with this
  chapter's numbers, or the chapter itself must be updated in the same session (Authoritative
  Mechanics Rule).
- STRAT-185/186/187 (interruption resistance bound, margin/emergency requirement, current-project
  reservation priority) are the compliance IDs directly cited in `evaluate_project_switch()`'s own
  docstring (L888-890) — this ticket's core logic change touches exactly these three IDs.
- STRAT-005/STRAT-006 (retention margin / current-project retention priority) — cited inline at
  L920-923, unaffected by this ticket's structural change (the margin formula itself isn't changing,
  only what conditions gate the lock-bypass branch above it).
- STRAT-234 / rejection-backoff (`_MAX_CONSECUTIVE_REJECTIONS`, referenced L1152-1167) is the closest
  existing precedent for a named module-level constant gating strategic behavior — a reasonable
  pattern to follow for the new urgency-floor constant (exact name/value deferred to Implement per
  ticket's own Assumptions section).

## Docs Requiring Update

- `docs/mechanics/04_strategic_cognition.md`: §6.6 (or a new subsection) must document the
  normalized/percentage-of-max comparison basis once Implement picks it, since the current-vs-candidate
  comparison basis is changing from raw score to a normalized one — the existing STRAT-185/186/187
  Logic-ID prose in this chapter (if any beyond §6.6) should reflect the new dual-condition
  (`score > effective_current_score AND clears urgency floor`) rule, not the old kind-allowlist. Note:
  the design doc's own §4 lists this doc as owned by the sibling ticket C3
  (`TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS`) for the *eligibility* sections — this ticket's own
  Out-of-Scope explicitly excludes "the narrative doc rewrite of 04_strategic_cognition.md's eligibility
  sections" but does NOT exclude updating §6.6's score-range/comparison-basis content, which is this
  ticket's own logic change, not C3's eligibility topic. Flagging for Plan to confirm boundary with C3
  so the two tickets don't collide or leave a gap.
- `docs/parity_ledger/strategic_cognition.yaml`: STRAT-185 (L1987), STRAT-186 (L1997), STRAT-187
  (L2007) all currently have `status: verified`, `priority: P0`, and **`test_path: null`** — this
  ticket changes exactly the logic these three IDs describe, so `v2_evidence` must be updated to
  reflect the new dual-condition rule and, per the Authoritative Mechanics Rule ("P0 entries require a
  passing test_path"), `test_path` should be populated pointing at whichever test(s) Implement adds/
  updates (`test_lock_prevents_switch`, `test_project_lock`, and/or the new synthetic-kind and
  danger-bypass-regression tests) — this closes a pre-existing P0-with-null-test_path gap as a
  byproduct, not just a formality.
- `docs/guidelines/intentional_divergences.md`: ticket's own Scope explicitly requires a new entry
  here (rationale class `Enforced` or `Bounded`) for the bypass-tightening behavior change (danger-kind
  candidates now additionally require `score > effective_current_score`, not just `score > 80`) — this
  ticket owns that entry per its Scope bullet.

## Parity Ledger Overlap

- **STRAT-185** (`Strategic project retention is bounded by interruption resistance`) — `status:
  verified`, `priority: P0`, `test_path: null` (L1987-1996). Directly touched by this ticket's core
  change.
- **STRAT-186** (`Strategic project switching requires margin or explicit emergency`) — `status:
  verified`, `priority: P0`, `test_path: null` (L1997-2006). This is literally the mechanism being
  generalized (the "explicit emergency" allowlist becomes the generic urgency-floor rule).
- **STRAT-187** (`Current project has reservation priority`) — `status: verified`, `priority: P0`,
  `test_path: null` (L2007-2016). Unaffected in spirit (current project still gets `retention_margin`)
  but the entry's `v2_evidence` references "exhaustive checklist audit Phase 1-11" rather than a
  concrete test — same gap as the other two.
- All three: **confirmed present** via direct grep of `docs/parity_ledger/strategic_cognition.yaml`
  (not assumed absent, per the ticket's own flagged open question). `docs/compliance/checklist.md`
  cross-references the same three IDs (L3003-3005) pointing `TEST:` at
  `tests/unit/strategic/test_strategic_hardening.py` — **read that file directly and confirmed it does
  NOT contain any test covering STRAT-185/186/187** (its only two tests, `test_interaction_interrupted_
  by_damage` and `test_strategic_bandwidth_leads`, are tagged `STRAT-221-224` at the file's own header
  comment). This is a pre-existing, stale compliance-checklist cross-reference, not caused by this
  ticket — noted for awareness (not in this ticket's Related Docs/Scope, so not added to "Docs
  Requiring Update" above to avoid scope creep; flagging under Risks below instead).
- **P0 requirement**: per CLAUDE.md, P0 entries require a passing `test_path`. All three are currently
  P0 with `test_path: null` — pre-existing gap, but since this ticket changes their underlying logic,
  Implement should not leave `test_path` null when updating `v2_evidence`.

## Prior Work

- No `docs/REGISTRY.yaml` present at time of investigation — used the fallback path
  (`tickets/done/` + `stored_artifacts/`).
- `TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION` (Related Ticket, referenced in this
  ticket and as the design doc's origin) is the investigation that first traced the compounding root
  causes this batch fixes — its own `stored_artifacts/.../investigation.md` is the canonical source
  for the System A/B split and the dormant `cognition_profile` finding; not re-read in full here since
  the design doc already distills the relevant parts, but its existence is the reason this ticket
  exists.
- Ticket 1 of this 4-ticket batch is DONE per `tickets/todos/cognition-adventure-eligibility/
  SEQUENCE.md` — it covers the eligibility-gate change (`supports_adventure_routing`), a separate axis
  from this ticket's bypass-generalization; no functional overlap with `evaluate_project_switch()`.
- `TCK-20260619-E11D-SCORING-CAL` is referenced in the design doc as the precedent for "empirical
  calibration deferred to Implement" — same pattern applies to this ticket's urgency-floor constant.
- No prior ticket found that previously attempted to generalize the kind-string allowlist in
  `evaluate_project_switch()` — this is new ground, not a repeat of earlier work.

## Risks and Open Questions

- **Blocking for Plan/Implement, not assumed away**: `mapper.py:100`'s hardcoded `score=1.0` means
  System A's real computed score never reaches `ProjectState.score` today. AC2/AC3 require
  normalization "before comparison" and routing `apply()` through `evaluate_project_switch()` — both
  are undermined if the placeholder score isn't also threaded through. Plan must decide: (a) extend
  `RouteToProjectMapper.map_to_states()` to accept and store the real `selected.score`, or (b) have
  `AdventureDecisionPhase.apply()` construct the candidate `ProjectState` with the real score via
  `replace()` before calling `evaluate_project_switch()`. Either is a small, targeted change, but
  leaving `score=1.0` in place while claiming "normalized comparison" would not actually fix the
  asymmetry — flagging so Plan makes this decision explicitly rather than by omission.
- **Percentage-of-declared-system-max needs a source of truth for "max".** System A's ~2.9 ceiling is
  documented (§6.6) but not enforced/clamped in code — it's an empirical estimate ("Estimated, No
  Blockers" per the section's own title), not a hard cap. System B has no single documented max at all
  (varies per scorer, some exceeding 100). Percentage-of-max normalization requires Implement to pick
  concrete max constants for each system and decide whether they live in code (a named constant near
  `evaluate_project_switch`) or content/config. This is a real design decision, not just an
  implementation detail — flagging as open per the ticket's own "exact floor deferred to Implement"
  framing, but the normalization *basis* (not just the floor value) is equally undecided and should be
  explicit in plan.md.
- **`AdventureDecisionPhase`'s own-lock check uses `_threat_resolved()` as an override that ignores
  `lock_until_tick` entirely.** Routing `apply()` through `evaluate_project_switch()` per AC3 doesn't
  automatically fix this — the existing `if tick < active_proj.lock_until_tick and not
  _threat_resolved(hero, state): continue` gate happens *before* any candidate is even generated. AC3's
  own test (hero with unexpired System-B lock, apply() must NOT overwrite while lock is active) only
  specifies the case where `_threat_resolved()` is False; Plan should confirm whether the
  `_threat_resolved()`-true-but-`lock_until_tick`-not-expired path is in scope too (it currently allows
  route generation to proceed and, post-fix, would need `evaluate_project_switch()` to independently
  re-block it via the `lock_until_tick > current_tick` check inside that function — which it will, once
  wired up, since that check doesn't depend on `_threat_resolved()`). Not blocking, but worth Plan
  making explicit that this is how the two gates interact post-fix, not a separate bug to fix.
- **The `"danger"` bypass branch is unreachable in live production code** (see Current Behavior above).
  AC4's regression test is therefore testing a specified contract, not a corpus-observed scenario —
  this doesn't change what Implement must build, but the intentional_divergences.md entry's rationale
  should describe it as tightening a *specified* bypass rule, not as changing observed live behavior,
  to keep the divergence note accurate.
- **`docs/compliance/checklist.md` STRAT-185/186/187 TEST pointer is stale** (points at a file with no
  matching tests) — pre-existing, out of this ticket's Related Docs/Scope; not fixing it here, but
  Implement/Finalize should be aware it exists so the parity-ledger `test_path` update (this ticket's
  own scope) doesn't get confused with the separate, unrelated compliance-checklist staleness.

## Anti-Drift Hazards

- **Do not touch `GoalKind`/`ProjectKind` vocabulary unification.** This is a confirmed, real,
  pre-existing gap (see Current Behavior) but is explicitly out of scope (tracked under D22/C4 per this
  ticket's own "Out of Scope" section referencing `TCK-20260810-D22-DORMANT-WIRING-AUDIT`). The
  generic bypass rule must work with `kind` as an unenforced string, not by first cleaning up the
  enum split.
- **Do not silently fix the C1 eligibility gate** (`CognitionProfileDefinition.supports_adventure_
  routing`, `src/domains/adventure/scoring.py` HERO checks) — explicitly out of scope per this ticket
  (owned by ticket 1 of the batch, already DONE — do not re-touch it even if it looks adjacent).
- **Do not rewrite `docs/mechanics/04_strategic_cognition.md`'s eligibility sections or
  `docs/simulation/domains/adventure_contract.md`'s eligibility table** — owned by C3
  (`TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS`). This ticket's own doc-update scope is limited to
  §6.6-adjacent score/comparison content and the parity-ledger/divergences entries tied to its own code
  change (see Docs Requiring Update above for the precise boundary).
- **Do not touch `docs/audits/D22_dormant_content_wiring.md`** — owned by C4.
  the "danger" kind's real unreachability could tempt a well-meaning cleanup of `ConcernKind` vs
  `ProjectKind` vocabulary while in this file; resist — same D22/C4 boundary as above.
- **Preserve the `retention_margin`/`effective_current_score` formula exactly** (STRAT-005/006,
  L920-923) — this ticket only changes what gates entry into the score comparison (the lock-bypass
  condition), not the comparison or margin formula itself.
- **`resume_project()` (L938-951) and `process_project_outcome()` (L954+) are untouched by this
  ticket** — they don't call `evaluate_project_switch()` and aren't part of the kind-allowlist; don't
  let scope drift into "while I'm in here" changes to adjacent functions in the same file.
- **The two other direct-overwrite `current_project_id_set` sites in `events.py`** (`stabilize_project`
  at L72-96 and, by extension, similar region-danger-driven pivots) are a third, independent instance
  of the same "direct overwrite, no `evaluate_project_switch()` call" pattern seen in `phase.py` — but
  they are NOT named in this ticket's Scope/Related Code Areas. Do not expand this ticket to cover them;
  flag for a future ticket if desired, but out of scope here.
