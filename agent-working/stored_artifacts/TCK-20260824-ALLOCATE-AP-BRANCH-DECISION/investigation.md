---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260824-ALLOCATE-AP-BRANCH-DECISION
artifact_type: investigation
tags: [progression]
---

# Investigation — TCK-20260824-ALLOCATE-AP-BRANCH-DECISION

## Current Behavior

**Three separate, non-communicating implementations of "spend AP on an attribute" exist.** None of
them is fully correct against the Mechanics Bible's own stated gates, and only one has any live
(if flag-gated-off) route toward it.

### 1. `CoreActions.execute_allocate_ap` (`src/engine/domain/core_actions.py:146-176`) — wired, no live driver

- Dispatched from `ActionRouter.execute_action` on `payload["action"] == "ALLOCATE_AP"`
  (`src/engine/domain/action_router.py:49-50`), which is itself reachable from
  `SimulationDomainLogic.execute_action` (`src/engine/domain_logic.py:42-56`) and from
  `ActionIntentAdapter.execute`'s fallback `router_payload["action"] = intent.kind` branch
  (`src/engine/intent/action_intent.py:257-260`) — two real, live entry points, exactly as the
  ticket describes.
- **Gate PROG-067 (sufficient AP) is honored**: `entity.identity.unspent_ap < amount` → returns
  `NavigationUpdate(failure_reason="INSUFFICIENT_AP")` (core_actions.py:154-158).
- **Gate PROG-068 (valid attribute name) is NOT honored**: only `"strength"` and `"vitality"` have
  an `if`/`elif` branch (core_actions.py:164-169). For any of the other 7 attribute names
  (agility, endurance, intelligence, spirit, wisdom, perception, charisma), execution falls through
  both branches with `attr_up`/`combat_up` left at their all-zero defaults, **but the
  `IdentityUpdate(unspent_ap_delta=-amount)` at line 173 is unconditional** — AP is spent with zero
  attribute gain. This is a second, independent "cosmetic decrement" bug, distinct from the one the
  ticket names in `resolver.py`, and it lives in the code path the ticket is asking whether to wire.
- **Gate PROG-069 (aptitude multiplier) is NOT implemented at all** — `amount` is applied as a flat
  delta; there is no aptitude lookup anywhere in this function.
- **No producer in `src/` ever constructs `{"action": "ALLOCATE_AP", ...}`.** Confirmed via
  `grep -rn "ALLOCATE_AP" src/` (4 hits: `generator.py`, `resolver.py`, `schema.py`,
  `action_router.py` — none of them build an action-router payload). The only call site that builds
  this exact payload shape is a test: `tests/unit/quest/test_progression_regression.py:47`
  (`payload = {"action": "ALLOCATE_AP", "attribute": "strength", "amount": 3}`, fed directly to
  `SimulationDomainLogic.execute_action`). No AI goal/decision system, no intent resolver, nothing
  in `src/ai/`, `src/cognition/`, or `src/strategy/` ever selects this action string.

### 2. `ConversionIntentResolver` (`src/domains/progression/resolver.py:82-89`) — the one real gap→resolution pipeline, resolves through a different, cosmetic path

- `GrowthGapEvaluator.evaluate` (`src/domains/progression/gaps.py:102-111`) detects a real
  `level_gap` whenever `entity.identity.unspent_ap > 0`.
- `ConversionOptionGenerator.generate` (`src/domains/progression/generator.py:77-83`) turns an
  `"allocate"`-tagged interpretation meaning into a `ConversionOption(kind=ConversionKind.
  ALLOCATE_AP, ...)`.
- `ConversionDecisionService.select` may choose it; `ConversionIntentResolver.resolve` then maps
  `ConversionKind.ALLOCATE_AP` to `EntityUpdate(identity=IdentityUpdate(unspent_ap_delta=-1))`
  **only** — no `attributes=` field is set at all (resolver.py:82-89). This is the ticket's named
  "cosmetic" branch: AP is decremented, zero attribute gain, confirmed by exact line citation.
- Critically, **this path never calls `ActionRouter`/`CoreActions.execute_allocate_ap`** —
  `ConversionIntentResolver.resolve` returns an `EntityUpdate` directly
  (`src/domains/progression/phase.py:73`, merged into the tick's `StateUpdate` at line 76). It
  bypasses the action-router/core_actions branch entirely, on a wholly separate call path.
- This whole phase — `ProgressionConversionPhase.execute`, wired at
  `src/engine/pipeline.py:321-322` as `run_phase("progression_conversion", ..., "ENABLE_PROGRESSION_EVOLUTION")`
  — is gated behind `ENABLE_PROGRESSION_EVOLUTION`, which **defaults to `FeatureMode.OFF`**
  (`src/domains/optimization/feature_flags.py:42`). No `config/simulation_quality/profiles/*.yaml`
  corpus profile turns it on (grep-confirmed; only `tools/calibrate_simq.py`, parity/event-ledger
  docs, the flag-manager file itself, its own pipeline wiring, and test files reference the flag
  name). **So even the one real gap-resolution pipeline that could reach ALLOCATE_AP-shaped
  behavior is currently off in every live simulation run**, independent of the action-router
  question.

### 3. `AllocateAttributeAction` (`src/actions/attributes.py:9-59`) — dead code, holds the only correct aptitude-multiplier logic

- `grep -rln "from src.actions.attributes" .` returns exactly one hit outside its own file:
  `tests/unit/progression/test_attribute_growth.py`. Zero callers in `src/` — nothing constructs or
  `.execute()`s it in any production path.
- It correctly implements: unspent-AP gate (line 18), valid-attribute-name gate (line 22, via
  `hasattr`), **and** the PROG-015/PROG-069 aptitude multiplier (lines 39-43:
  `points_to_add = max(1, int(1 * apt_val))`, looked up per-attribute from `entity.aptitude` via a
  9-entry name→aptitude-field mapping covering all 9 attributes, not just strength/vitality).
- Its own inline comment (lines 49-51) reads as an acknowledged half-finished draft: "Note:
  unspent_ap_delta is a custom field I added logic for in ApplyPath / I should probably update
  IdentityUpdate to officially include it... / For now, I'll use a property update or just assume
  IdentityUpdate has it." `IdentityUpdate.unspent_ap_delta` in fact already exists and is used
  correctly by both `core_actions.py` and `resolver.py` — this comment is stale/pre-dates a since-
  completed refactor, not a live caveat.
- It was the **originally-scoped canonical implementation**: `tickets/done/TCK-20260425-PROG-
  ATTRIBUTE-POINTS.md` (2026-04-25, DONE) explicitly scoped "Implement `AllocateAttributeAction`
  with aptitude multipliers" and checked off AC "Spending AP increases attributes based on Aptitude
  (PROG-015)" against exactly this file. `core_actions.py::execute_allocate_ap` was added later
  (exact ticket not identified in this investigation's search — not needed for the wire/dormant
  call) as a second, inferior implementation that became the one wired into `ActionRouter`, orphaning
  the original.
- Its own 5 regression tests (`tests/unit/progression/test_attribute_growth.py`) all still pass and
  exercise real behavior (PROG-015 aptitude multiplier, PROG-046 cap-at-100) — they are correct
  unit tests of dead code, not broken tests.

## Mechanics / Engine Constraints

`docs/mechanics/attribute_progression_contract.md` (companion to `01_entity_anatomy.md`, chapter
authority P1, `last_verified: 2026-06-13`) is the authoritative spec here. Section "Attribute Point
Allocation Gates" (lines 112-118) states AP spend is validated "in the apply path" with four gates:
`PROG-067` (sufficient AP), `PROG-068` (valid attribute name), `PROG-069` (aptitude multiplier),
`PROG-070` (cap of 99 enforced).

Checked the actual apply path (`AttributePatch.apply`, `src/engine/patches.py:570-585`, and
`RewardPatch.apply`, `src/engine/patches.py:601-611`, the only two apply-path sites that touch
`attributes`/`unspent_ap`): **none of the four gates are enforced there.** `AttributePatch.apply`
does an unconditional `min(100, new_att.X + delta)` per field — that is PROG-070's cap (at 100, not
99 as the doc's Edge Cases table states — a separate, tangential numbering/value mismatch, not
central to this ticket's scope, flagged but not resolved here). There is no AP-sufficiency check,
no attribute-name validity check, and no aptitude multiplier anywhere in the apply path. All four
gates, to the extent they are enforced at all, live in the *domain handler* layer
(`core_actions.py` for PROG-067 only; `AllocateAttributeAction` for PROG-067/068/069, but that code
is dead) — not "the apply path" as the mechanics doc states. This is a genuine mechanics-doc/code
mismatch, independent of the wire-vs-dormant question, surfaced by this investigation.

`docs/parity_ledger/progression.yaml` currently marks `PROG-067`, `PROG-068`, `PROG-069`, `PROG-070`
all `status: verified`, `priority: P0`, with `v2_evidence: "Implementation proven via exhaustive
checklist audit Phase 1-11"` and `test_path: null` for all four (lines 695-734). Given the above:
`PROG-067` and `PROG-070` are true of the live/wired path (`core_actions.py`/`patches.py`
respectively); `PROG-068` and `PROG-069` are **only** true of the dead `AllocateAttributeAction`
path — the live, action-router-wired path does not honor them. A `verified` P0 status with no
`test_path` and evidence pointing at a generic historical audit, for claims that do not hold against
the current live code, is a real parity-ledger accuracy gap this ticket's own scope
("[AllocateAttributeAction's] disposition... not left as a third silent implementation") makes
relevant to resolve, regardless of which of the three implementations is ultimately kept live.

## Docs Requiring Update

- `docs/guidelines/intentional_divergences.md`: needs a new entry recording the disposition of the
  `ALLOCATE_AP` action-router branch and of `AllocateAttributeAction` — required under this
  investigation's evidence-favored "dormant" resolution (see Risks and Open Questions), and
  explicitly required by the ticket's own AC under that branch ("If dormant: an
  intentional_divergences.md entry is added").
- `docs/parity_ledger/progression.yaml`: `PROG-068` and `PROG-069`'s `status: verified` (P0, lines
  705-724) does not hold against the current live/wired path (`core_actions.py::execute_
  allocate_ap` skips attribute-name validation and applies no aptitude multiplier) — only the dead
  `AllocateAttributeAction` honors them. This needs correcting to reflect which implementation is
  kept live once the Plan phase's wire/dormant call is made, independent of that call's outcome.
- `docs/mechanics/attribute_progression_contract.md`: the "Attribute Point Allocation Gates"
  section (lines 112-118) claims all four PROG-067–070 gates are enforced "in the apply path" —
  confirmed false against current code (see Mechanics/Engine Constraints above); needs correction to
  state where each gate actually lives (domain-handler layer, not apply path) and which
  implementation currently satisfies which gate.

Considered and NOT required to change under this investigation's evidence-favored dormant
resolution: `docs/parity_ledger/substrate.yaml` (`SUB-376`) already accurately documents the
wired-no-driver state of `execute_allocate_ap` and the cosmetic `resolver.py` path — no forced
change unless the Plan phase instead resolves to "wire," in which case the ticket's own AC already
requires updating its `v2_evidence`. Likewise `docs/event_ledger/entity.yaml` (`ENTITY-008`)
already correctly notes "1 (`core_actions.py::execute_allocate_ap`) is wired but has no live AI
driver; 2 ... are confirmed dead code" — accurate as written, no forced change under dormant.

## Parity Ledger Overlap

- **SUB-376** (`docs/parity_ledger/substrate.yaml`, status `verified`, priority `P2`,
  `test_path: tests/unit/observability/test_event_extractor_attributes.py`) — this is the ticket
  (`TCK-20260808-ENTITY-ATTRIBUTES-OBSERVABILITY-GAP`) that first surfaced and documented this
  exact reachability finding (3 of 4 `AttributeUpdate` producers non-live/dead). Its `text` already
  states the cosmetic-`resolver.py`-bypass finding verbatim. Not P0 — no test-passing requirement
  beyond what's already satisfied.
- **ENTITY-008** (`docs/event_ledger/entity.yaml`, status `observed`) — sibling entry to SUB-376,
  same investigation, same conclusion. Not flagged P0 in this ledger (event ledger doesn't carry a
  priority field the way parity_ledger does).
- **PROG-067/068/069/070** (`docs/parity_ledger/progression.yaml`, lines 695-734, all `status:
  verified`, **priority: P0**) — flagged above as a real accuracy gap. **These are P0**, meaning any
  status change away from `verified` requires a passing `test_path` per the project's parity rule.
  `PROG-068`/`PROG-069` currently have `test_path: null`; if their status is corrected (e.g. to
  `divergent`, scoped to the live path specifically), a real test_path must be supplied — the
  existing `tests/unit/progression/test_attribute_growth.py::test_aptitude_multiplier_PROG_015`
  tests the dead-code path, not the live one, so it cannot serve as that evidence without also
  resolving which implementation stays live.
- **PROG-015** (`docs/parity_ledger/progression.yaml:150-160`, `status: verified`, **priority:
  P0**) — same class of issue as PROG-069 (aptitude multiplier), same caveat: verified evidence is
  generic ("exhaustive checklist audit"), and the only code that actually implements the multiplier
  is dead. Not explicitly named in the ticket's Related Docs but directly overlaps in subject matter
  with PROG-069; flagged here for completeness, not asserted as independently in-scope to fix.

## Prior Work

- **`stored_artifacts/TCK-20260808-ENTITY-ATTRIBUTES-OBSERVABILITY-GAP/investigation.md`** — the
  direct source of SUB-376/ENTITY-008. Already did the "grep all 4 `AttributeUpdate(` producers,
  verify each for real reachability" methodology this ticket was asked to repeat; findings match
  exactly (evolution.py live, core_actions.py wired-no-driver, cohort.py + attributes.py dead). This
  ticket's own investigation reproduces and extends that finding (adds the PROG-068/069 gate-parity
  angle and the `execute_allocate_ap`-itself-has-a-cosmetic-bug angle, neither covered there since
  that ticket's scope was observability, not correctness).
- **`stored_artifacts/TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD/investigation.md`** —
  independently reconfirmed the same 3-producer/1-live split while investigating a *different*
  question (why `attribute_changed` events are empirically zero in real corpus runs). Traces the
  shared root cause (the `unspent_ap`/`level_gap` gate is real but the resolution pipeline that
  would drain it goes through the cosmetic path) back to the same combat-legality-always-false root
  cause chain (`TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION`) — i.e., even level-
  ups themselves are empirically almost unreachable in real corpus play, which independently weakens
  the case for urgently wiring a real ALLOCATE_AP producer (there would be very little unspent AP to
  spend in practice even if one existed).
- **`tickets/done/TCK-20260824-ROLLOUT-FLAG-DECISIONS.md` +
  `stored_artifacts/TCK-20260824-ROLLOUT-FLAG-DECISIONS/investigation.md` +
  `docs/architecture/rollout_flag_decisions_m1.md`** — **this is the closest prior "wire vs dormant"
  style decision already made, and this ticket's decision doc should point to/ratify it rather than
  re-decide from scratch for the `ENABLE_PROGRESSION_EVOLUTION` piece specifically.** That ticket
  reviewed 8 Phase-10 feature flags including `ENABLE_PROGRESSION_EVOLUTION` (the flag gating the
  entire `ProgressionConversionPhase`, i.e. the one real gap-resolution pipeline that touches
  `ConversionKind.ALLOCATE_AP`) and explicitly decided **"Kept OFF, deferred"** — recorded in
  `docs/guidelines/intentional_divergences.md` DEV-003 (which references DEV-002's broader all-OFF
  policy) — with a **named follow-up ticket already filed and still open**:
  `tickets/todos/TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION.md`. That ticket's own scope is
  to run a real corpus-profile ON trial and produce a keep/flip recommendation — it has not run yet.
  **This existing decision does NOT by itself answer this ticket's questions** — it only settles
  whether the *feature-flag-gated conversion phase* runs at all; it says nothing about the
  action-router `ALLOCATE_AP` dispatch reachable via other paths (e.g. a future non-flag-gated AI
  producer), nor about `resolver.py`'s cosmetic-branch correctness, nor about
  `AllocateAttributeAction`'s disposition. But it is strong, directly-relevant evidence that the
  project has *already and recently* chosen "defer, don't wire yet, wait for real evidence" as its
  standing policy for this exact system, via the exact process (named follow-up ticket, evidence-
  first) this ticket's own AC structure mirrors.
- **`tickets/done/TCK-20260425-PROG-ATTRIBUTE-POINTS.md`** — origin ticket for
  `AllocateAttributeAction`, establishing it (not `core_actions.py`) as the originally-intended
  canonical implementation.

## Risks and Open Questions

**This is not a fully clear-cut call for the whole ticket, but the evidence has a clear lean for
the wiring sub-question, and a genuinely open sub-question for the other two ACs:**

1. **Wire vs. dormant for the `ALLOCATE_AP` branch itself — evidence leans dormant, not
   ambiguous.** Building a real, non-mocked `Kernel.tick_once()` run that reaches
   `execute_allocate_ap` would require either (a) flipping `ENABLE_PROGRESSION_EVOLUTION` ON and
   also fixing `resolver.py`'s cosmetic branch to route through `ActionRouter` instead of
   hand-rolling its own `EntityUpdate` — which duplicates/preempts the scope and evidence-gathering
   job of the already-filed, not-yet-run `TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION`
   ticket — or (b) building an entirely new, currently-nonexistent AI/goal producer that emits
   `{"action": "ALLOCATE_AP", ...}` payloads directly, which is new-feature scope well beyond a
   "decide the fate of a branch" chore-tier ticket. Given `LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD`'s
   finding that XP gain (and therefore `unspent_ap`) is itself empirically near-zero in real corpus
   runs, urgency to wire a real producer right now is low. **Recommendation for Plan: dormant**,
   with the intentional_divergences.md entry explicitly cross-referencing DEV-003 and
   `TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION` as the real future unblock path, rather than
   inventing a new one.
2. **`resolver.py`'s cosmetic branch — genuinely open, not this investigation's call.** The
   ticket's own Assumptions section flags this explicitly: "Whether resolver.py's cosmetic branch
   remaining live (if dormant is chosen) is acceptable is an open call the decision doc must make
   explicit." Two real options exist: (a) leave it as a deliberate, documented "AP allocation via
   the conversion pipeline currently only decrements, does not grant" divergence (cheap, but leaves
   a genuinely misleading no-op-looking branch live whenever the flag is eventually flipped ON), or
   (b) fix it to actually set an `attributes=` delta (cheap in isolation, but raises the question of
   *which* implementation's logic to port in — flat delta like `core_actions.py`, or aptitude-scaled
   like `AllocateAttributeAction`— which in turn re-opens the AllocateAttributeAction disposition
   question). This investigation does not resolve which is better; Plan must decide.
3. **AllocateAttributeAction disposition — genuinely open between two defensible options.**
   (a) **Delete it**: it's dead code, and per repo convention (see `RolloutProfileManager`'s
   deletion in `TCK-20260824-ROLLOUT-FLAG-DECISIONS`) confirmed-dead-with-zero-callers code that
   duplicates a wired path is removed, not kept. Its 5 tests
   (`tests/unit/progression/test_attribute_growth.py`) would need deleting or repointing at
   whichever live implementation survives. (b) **Port its aptitude-multiplier logic into
   `core_actions.execute_allocate_ap`** (the wired path) and then delete the standalone file — this
   would also fix PROG-068/069's parity-ledger accuracy gap by making the live path actually satisfy
   those P0 claims, and fix `execute_allocate_ap`'s own silent-no-op-for-7-attributes bug identified
   above. This looks like the more defensible option on inspection (it fixes two real correctness
   bugs the investigation found, for modest effort — porting ~15 lines), but it is out of this
   ticket's stated Out-of-Scope ("Reconciling all three competing AP-allocation implementations
   beyond picking one canonical path and stating what happens to the other two") only if Plan judges
   it as "more than picking one path" — a judgment call for Plan, not settled here.
4. **PROG-015/PROG-067/PROG-068/PROG-069's parity-ledger accuracy** is a real gap surfaced by this
   investigation but is P0 — any status correction requires a real `test_path`. Plan must decide
   whether fixing this ledger accuracy gap is in this ticket's scope (it's arguably required by AC4's
   "not left as a third silent implementation" framing) or deferred to a follow-up, given the ticket's
   explicit Out-of-Scope carve-out for "full consolidation work."

## Anti-Drift Hazards

- **Do not conflate "wire the action-router `ALLOCATE_AP` branch" with "flip
  `ENABLE_PROGRESSION_EVOLUTION` ON."** They are different systems reaching different code paths
  (action-router/`core_actions.py` vs. conversion-phase/`resolver.py`) that currently never call
  each other. A fix that only flips the flag does not make `execute_allocate_ap` reachable; a fix
  that only wires a new AI producer for `ALLOCATE_AP` does not touch the flag-gated conversion
  phase at all.
- **Do not silently "fix" `resolver.py`'s cosmetic branch as a drive-by** without an explicit
  Plan-phase decision on which attribute-delta logic to port in (flat vs. aptitude-scaled) — this
  is exactly the "not left as a third silent implementation" trap the ticket is trying to avoid, one
  level down.
- **Do not delete `AllocateAttributeAction` without checking whether Plan wants to port its
  aptitude-multiplier logic elsewhere first** — deleting it before deciding is scope-correct-order
  risk: once deleted, the only correct-per-Mechanics-Bible implementation of PROG-015/069 is gone
  and would need to be re-derived from the mechanics doc instead of copied from working code.
- **Do not treat `TCK-20260824-ROLLOUT-FLAG-DECISIONS`'s "Kept OFF, deferred" verdict as fully
  answering this ticket** — it only resolves the flag/conversion-phase piece, not the
  action-router/`core_actions.py` piece or the `AllocateAttributeAction` piece. Citing it as blanket
  cover for a "no action needed" close would understate this ticket's actual required ACs (the
  intentional_divergences.md entry and the AllocateAttributeAction disposition are still genuinely
  this ticket's own work, not already done by that prior ticket).
- **The `min(100, ...)` vs. documented "cap of 99" mismatch in `AttributePatch.apply` /
  `attribute_progression_contract.md`** is a real, adjacent doc/code inconsistency — do not fix it
  as part of this ticket (out of scope, per the ticket's own "Any change to the aptitude-multiplier
  gap resolution pipeline beyond what's needed for the wire-vs-dormant call" exclusion), but do not
  let it get silently absorbed into this ticket's diff either if a future implementer touches
  `patches.py` while porting attribute-delta logic.
