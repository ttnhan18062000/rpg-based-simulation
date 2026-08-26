---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260824-ALLOCATE-AP-BRANCH-DECISION
artifact_type: plan
tags: [progression]
---

# Implementation Plan — TCK-20260824-ALLOCATE-AP-BRANCH-DECISION

## Summary

The Plan-phase call is **dormant**: `core_actions.py::execute_allocate_ap` stays wired into
`ActionRouter` but gets no new producer. This is a documentation/cleanup ticket, not a
new-feature ticket — the evidence (zero producers anywhere in `src/`, the one real
gap-resolution pipeline that could drive it routed through a different, non-router code path
that is itself behind `ENABLE_PROGRESSION_EVOLUTION` = `FeatureMode.OFF` per the already-ratified
DEV-003 decision with a named, not-yet-run follow-up ticket
`TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION`) makes "wire a new producer" out of proportion
to a P2 chore. Concretely this plan: (1) records the dormant decision as a new `DEV-004` entry in
`docs/guidelines/intentional_divergences.md`, citing SUB-376/ENTITY-008/DEV-003; (2) documents
(does not fix) `resolver.py`'s cosmetic AP-decrement-with-zero-gain branch, because fixing it would
itself be "a change to the aptitude-multiplier gap resolution pipeline" that the ticket's own
Out-of-Scope excludes, and the branch is unreachable in every real run today regardless of whether
it's cosmetic or correct; (3) resolves `AllocateAttributeAction`'s disposition as **deleted** (dead
code, zero `src/` callers, per the repo's confirmed-dead-zero-caller-code convention) rather than
ported, naming `core_actions.py::execute_allocate_ap` as the one canonical (if currently unreached)
path and explicitly recommending — not creating — a follow-up ticket to port its aptitude-multiplier
logic and close the resulting parity gap; (4) corrects the `PROG-068`/`PROG-069` parity-ledger
entries (P0, currently `verified` with no `test_path`) to `divergent`, backed by a new test that
proves the live path's actual (buggy) behavior; (5) corrects
`docs/mechanics/attribute_progression_contract.md`'s false "enforced in the apply path" claim; (6)
adds a real, non-mocked `Kernel.tick_once()` regression test proving the dormancy claim is true
today, not just asserted.

## Steps

### Step 1 — Record the wire-vs-dormant decision as DEV-004

**Files:** `docs/guidelines/intentional_divergences.md`

**Change:** Add a new entry `### DEV-004 — ALLOCATE_AP Action-Router Branch Kept Dormant
(TCK-20260824-ALLOCATE-AP-BRANCH-DECISION)` immediately after the existing `### DEV-003 — ...`
entry (currently ending at line 1420, followed by the `---` / `*Last updated*` footer at
lines 1422-1423 — verified by reading `docs/guidelines/intentional_divergences.md:1397-1423`).
Follow the exact DEV-003 field shape (`**Subsystem**`, `**Situation**`, `**Decision**`,
`**Rationale**`, `**Verification**`, `**Status**`). Content to state, backed by citations already
gathered in `investigation.md`:
- **Subsystem**: Engine / Progression.
- **Situation**: `CoreActions.execute_allocate_ap` (`src/engine/domain/core_actions.py:146-176`) is
  dispatched from `ActionRouter.execute_action` (`src/engine/domain/action_router.py:49-50`, both
  hits verified by direct read) and reachable via two live call chains, but no code anywhere in
  `src/` ever constructs an `{"action": "ALLOCATE_AP", ...}` payload — the only such payload
  constructor in the repo is `tests/unit/quest/test_progression_regression.py:47` (verified: `grep
  -rn "ALLOCATE_AP" src/` returns 4 hits, none a payload constructor). The one real
  gap-resolution pipeline that could drive AP spending (`gaps.py` → `generator.py` →
  `ConversionIntentResolver.resolve`'s `ConversionKind.ALLOCATE_AP` branch,
  `src/domains/progression/resolver.py:82-89`, verified by direct read) never calls `ActionRouter`
  at all — it returns an `EntityUpdate` directly (`src/domains/progression/phase.py:73`) — and that
  whole `ProgressionConversionPhase` is gated behind `ENABLE_PROGRESSION_EVOLUTION`, which defaults
  to `FeatureMode.OFF` (`src/domains/optimization/feature_flags.py:42`, verified by direct read,
  comment there already names the follow-up ticket
  `TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION`).
- **Decision**: Keep `execute_allocate_ap` wired but dormant. No new producer is built in this
  ticket.
- **Rationale**: **Bounded** — building a real producer requires either flipping
  `ENABLE_PROGRESSION_EVOLUTION` ON (which duplicates the scope/evidence-gathering job of the
  already-filed `TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION`, per DEV-003's own standing
  "defer, don't wire yet, wait for real evidence" policy) or building an entirely new AI/goal
  producer (new-feature scope beyond a decide-the-fate chore ticket). Cite `SUB-376`
  (`docs/parity_ledger/substrate.yaml:4285`) and `ENTITY-008` (`docs/event_ledger/entity.yaml:62`)
  as the prior investigation that first established this exact reachability finding — this entry
  ratifies, not re-derives, their conclusion.
- Also record, in this same entry, the two other AC-required dispositions so DEV-004 is the single
  decision doc satisfying AC1+AC2+AC4:
  - `resolver.py`'s `ConversionKind.ALLOCATE_AP` branch (`src/domains/progression/resolver.py:82-89`)
    stays a decrement-only, zero-attribute-gain no-op. This is **documented, not fixed**, because
    (a) fixing it is "a change to the aptitude-multiplier gap resolution pipeline" the ticket's own
    Out-of-Scope excludes, and (b) it is unreachable today regardless of correctness, since the
    whole phase is behind the `FeatureMode.OFF` flag from DEV-003.
  - `AllocateAttributeAction` (`src/actions/attributes.py`) is **deleted** as dead code (zero `src/`
    callers outside its own file and its own test file, verified via `grep -rln
    "AllocateAttributeAction\|from src.actions.attributes" --include="*.py" .`, which returns only
    `src/actions/attributes.py` and `tests/unit/progression/test_attribute_growth.py`). Record that
    it held the only correct PROG-015/PROG-069 aptitude-multiplier logic
    (`src/actions/attributes.py:39-43`) and that a follow-up ticket is **recommended** (name it
    descriptively, e.g. "port `AllocateAttributeAction`'s aptitude-multiplier logic into
    `core_actions.execute_allocate_ap` and correct the resulting PROG-068/069/015 parity gap") but
    explicitly **not created** by this plan — ticket creation is a separate workflow action, out of
    this plan's step scope.
- **Verification**: cite the new test added in Step 4 (`tests/unit/quest/test_progression_regression.py`)
  and the new dormancy-proof integration test added in Step 6
  (`tests/integration/progression/test_allocate_ap_dormancy.py`) — fill in exact test names once
  written (Steps 4 and 6 run before this field is finalized, but the entry text itself can be
  drafted in this step and the Verification line completed last).
- **Status**: ACTIVE.
- Add a corresponding summary-table row near the top of the file (after the existing
  `Knowledge Gateway MCP / Packet Cache` row, matching the `| Subsystem | Feature | Rationale
  Class | Status |` shape already used by every other row) and update the trailing `*Last updated:
  ...*` line (currently `docs/guidelines/intentional_divergences.md:1423`) to reference DEV-004 and
  this ticket ID.

**Do NOT touch:** DEV-001/DEV-002/DEV-003's own text, the summary-table rows above them, or any
other subsystem's entry.

**Verify:** No automated test directly covers prose content; this step is verified by the `plan
→ implement → done-checker` frontmatter/structure check and by Steps 2-6 citing DEV-004 correctly
(a broken cross-reference would be caught in review).

---

### Step 2 — Document (do not fix) resolver.py's cosmetic ALLOCATE_AP branch

**Files:** `src/domains/progression/resolver.py`

**Change:** At the `elif kind == ConversionKind.ALLOCATE_AP:` branch
(`src/domains/progression/resolver.py:82-89`, verified by direct read — current body is exactly
`update = EntityUpdate(entity_id=entity.id, identity=IdentityUpdate(unspent_ap_delta=-1))`, no
`attributes=` field), replace the existing one-line comment (`# Map ALLOCATE_AP to IdentityUpdate
unspent_ap delta decrease`) with a comment that explicitly names this as a known, intentional,
currently-inert divergence: state that this branch decrements `unspent_ap` but grants zero
attribute delta, that this is tracked as `DEV-004`
(`docs/guidelines/intentional_divergences.md`), and that the branch is unreachable in any live run
today because the whole `ProgressionConversionPhase` is gated by `ENABLE_PROGRESSION_EVOLUTION`
(`FeatureMode.OFF`, DEV-003). **No behavioral change** — the `update = EntityUpdate(...)` line
itself is untouched, byte-for-byte.

**Other writers to this resource:** `resolver.py`'s `ConversionIntentResolver.resolve` is the only
writer of this specific branch's `EntityUpdate` — no other code path constructs an `EntityUpdate`
for `ConversionKind.ALLOCATE_AP` specifically (confirmed: this `kind` is only matched inside this
one `resolve` method, verified by reading the full method body at
`src/domains/progression/resolver.py:24-100`+; the sibling branches for `EQUIP_ITEM`,
`REPAIR_GEAR`, `CRAFT_ITEM`, `SELL_LOOT`, `ASK_ITEM_USE` in the same `if/elif` chain are untouched
by this step). The `EntityUpdate` this branch returns is merged into the tick's `StateUpdate` at
`src/domains/progression/phase.py:76` (per investigation.md) — that merge call site is unaffected
since the returned value's shape does not change.

**Do NOT touch:** the `if kind == ConversionKind.EQUIP_ITEM:` / `REPAIR_GEAR` / `CRAFT_ITEM` /
`SELL_LOOT` / `ASK_ITEM_USE` branches in the same file, `gaps.py`, `generator.py`, or `selector.py`
(`ConversionDecisionService`) — none of these are touched by this ticket's scope.

**Depends on:** Step 1 (needs the `DEV-004` ID to reference in the comment).

**Verify:**
`tests/unit/domains/progression/test_phase6_conversion_intent_bridge.py::test_allocate_ap_conversion_maps_to_allocate_ap_intent`
(verified by direct read at `tests/unit/domains/progression/test_phase6_conversion_intent_bridge.py:35-51`
— asserts only `upd.identity.unspent_ap_delta == -1`, no `attributes` assertion) must stay green
**unmodified** — this proves the comment-only change did not alter behavior. Also verify
`test_craft_conversion_maps_to_blacksmith_craft_intent` and the sibling Phase 6 suite
(`test_phase6_progression_boundary.py`, `test_phase6_conversion_decision_service.py`,
`test_phase6_progression_events.py`) stay green as the anti-drift guard that `gaps.py`/
`generator.py`/`selector.py` are untouched.

---

### Step 3 — Delete AllocateAttributeAction and its dedicated test file

**Files:** `src/actions/attributes.py` (delete), `tests/unit/progression/test_attribute_growth.py`
(delete)

**Change:** Remove both files entirely. Verified zero other referrers repo-wide:
`grep -rln "AllocateAttributeAction\|from src.actions.attributes" --include="*.py" .` returns
exactly these two files (self-definition and its own test); there is no `src/actions/__init__.py`
exporting it (`find src/actions -maxdepth 1 -type f` returns `harvest.py`, `loot.py`,
`attributes.py` only — no `__init__.py`), so no import-path breakage is possible elsewhere.

**Other writers to this resource:** N/A — this file has no other producers/consumers to
coordinate with (confirmed above); this is a pure deletion of dead code with a single, self-
contained test file.

**Do NOT touch:** `src/actions/harvest.py`, `src/actions/loot.py` — sibling files in the same
directory, unrelated to this ticket, must remain byte-for-byte unchanged.

**Depends on:** Step 1 (the DEV-004 entry must already state "deleted" as AllocateAttributeAction's
disposition before this step executes it — do not delete before the decision doc records why).

**Verify:** `pytest tests/unit/progression/ -v` after deletion should report the directory/file no
longer collected (no orphaned references); `pytest tests/unit/quest/test_progression_regression.py
tests/unit/domains/progression/ tests/unit/engine/test_sort_tiebreaker.py -v` (the rest of the
Regression Surface) must stay fully green, proving nothing else depended on the deleted module.

---

### Step 4 — Add a test documenting the live path's PROG-068 gap (unmodified behavior)

**Files:** `tests/unit/quest/test_progression_regression.py`

**Change:** Add a new test, e.g. `test_execute_allocate_ap_silently_no_ops_for_unhandled_attribute`,
co-located with the existing `test_attribute_allocation` (verified exact function name via `grep -n
"^def test_" tests/unit/quest/test_progression_regression.py` → only two functions exist in this
file today: `test_evolution_trigger_and_stat_boost` (line 25) and `test_attribute_allocation`
(line 41) — **note for the record: `test_plan.md`'s Regression Surface section names this test
`test_attribute_allocation_and_recalc`, which does not exist in the file; the correct existing name
is `test_attribute_allocation`. Treat all references in this plan and in Step 5/6 to "the existing
ALLOCATE_AP regression test" as meaning `test_attribute_allocation`, not the test_plan.md name.**
The new test should: build a hero entity with `unspent_ap >= amount` (same `create_mock_entity`
helper as the existing test, `tests/unit/quest/test_progression_regression.py:11-22`), call
`SimulationDomainLogic.execute_action(hero, payload={"action": "ALLOCATE_AP", "attribute":
"agility", "amount": 3}, current_tick=1)`, and assert the current live (buggy but now-decided-to-
stay, per DEV-004) behavior explicitly: `hero_up.identity.unspent_ap_delta == -3` **and**
`hero_up.attributes.is_noop() is True` (using `AttributeUpdate.is_noop()`, defined at
`src/core/updates.py:401-404`, verified by direct read — confirms `agility_delta` and all 7
non-strength/vitality fields default to `0` and stay `0`). This turns the previously-undocumented
silent gap into an explicit, named regression test per `test_plan.md`'s
`test_execute_allocate_ap_rejects_unknown_attribute_name` spec (branch: "If Plan's disposition
leaves `execute_allocate_ap` unmodified, this test should assert-and-document the current (buggy)
behavior explicitly").

**Other writers to this resource:** `core_actions.py::execute_allocate_ap`
(`src/engine/domain/core_actions.py:146-176`) is the sole implementation under test; no other code
writes to `AttributeUpdate`/`IdentityUpdate` via this exact call path. This step does **not**
modify `core_actions.py` — it only adds a test asserting current behavior.

**Do NOT touch:** `core_actions.py::execute_allocate_ap`'s logic itself (lines 146-176) — no fix,
no new attribute branches. Fixing the 7-attribute gap is exactly the deferred follow-up work named
in Step 1's DEV-004 entry, out of this ticket's scope.

**Depends on:** none (independent of Steps 1-3; can be written in parallel).

**Verify:** the new test itself, run via `pytest tests/unit/quest/test_progression_regression.py -v`.

---

### Step 5 — Correct PROG-068/PROG-069 parity-ledger status

**Files:** `docs/parity_ledger/progression.yaml`

**Change:** For `PROG-068` (`text: "Attribute allocation checks valid attribute name."`,
currently `status: verified`, `priority: P0`, `test_path: null` — verified by direct read at
`docs/parity_ledger/progression.yaml` around the `PROG-067`/`PROG-068`/`PROG-069`/`PROG-070` block)
and `PROG-069` (`text: "Attribute allocation applies aptitude multiplier or explicit
divergence."`, same current shape): change `status` from `verified` to `divergent`, keep
`priority: P0`, set `v2_evidence` to state that the live/wired path
(`core_actions.py::execute_allocate_ap`) only handles `strength`/`vitality` and applies no
aptitude multiplier at all — the only implementation that honored both gates
(`AllocateAttributeAction`) was deleted as dead code per `DEV-004`
(`docs/guidelines/intentional_divergences.md`) — and set `test_path` to
`tests/unit/quest/test_progression_regression.py::test_execute_allocate_ap_silently_no_ops_for_unhandled_attribute`
(the test added in Step 4), satisfying the project's "P0 entries require a passing `test_path`"
rule. Set `divergence_note` to a short pointer to `DEV-004`. **Do not touch `PROG-067` or
`PROG-070`** — investigation confirmed both remain true of the live path (`PROG-067`'s AP-
sufficiency check is honored at `core_actions.py:154-158`; `PROG-070`'s cap is enforced, if at 100
not the documented 99, in `AttributePatch.apply`, `src/engine/patches.py:570-585` — that
100-vs-99 mismatch is a separate, tangential issue explicitly out of this ticket's scope, see Scope
Guards). **Do not touch `PROG-015`** (`docs/parity_ledger/progression.yaml:150-160`) — same class
of aptitude-multiplier accuracy gap, but investigation explicitly flags it as "not asserted as
independently in-scope to fix" for this ticket; leave its `status: verified` as-is.

**Other writers to this resource:** `docs/parity_ledger/progression.yaml` is also written by the
`parity-updater` agent role during other tickets' Parity phase, and read (not written) by
`tools/parity_index_baseline`-style tests (e.g. `tests/tools/test_parity_index_baseline.py`,
referenced in project CLAUDE.md's CI-triage guidance as a baseline-drift-prone test). This step's
edit changes exactly 2 of the file's many `status`/`v2_evidence`/`test_path` fields
(`PROG-068`, `PROG-069`) and does not add/remove any `id:` entries or change the file's total
entry count, so it should not perturb any "missing `test_path` count"-style baseline test — but
Step 6's implementer must run whatever parity-index baseline test exists in scope
(`pytest tests/tools/ -k parity` or equivalent) to confirm no baseline count assertion needs an
accompanying update, since this edit does change one such count (two P0 entries move from
`test_path: null` to a real path).

**Do NOT touch:** any other `id:` entry in the file (`PROG-067`, `PROG-070`, `PROG-015`, `PROG-016`,
`PROG-071`, etc.) — this step is a two-entry, surgical status correction.

**Depends on:** Step 4 (the `test_path` this step writes must already exist and pass before the
ledger cites it).

**Verify:** the new/updated `test_path` test from Step 4 passes; `python3
tools/validate_frontmatter.py` (or the project's parity-schema validator, if separate) accepts the
edited YAML; whatever parity-index baseline test exists under `tests/tools/` stays green or is
updated in the same step if it hardcodes a `missing_test_path_count`-style number that this edit
changes.

---

### Step 6 — Correct the mechanics doc's false "enforced in the apply path" claim

**Files:** `docs/mechanics/attribute_progression_contract.md`

**Change:** The "Attribute Point Allocation Gates" section (verified by direct read — the text "AP
spend is validated in the apply path with four gates:" followed by a 4-item list for `PROG-067`
through `PROG-070`, immediately after the Level-Up pseudocode block) currently claims all four
gates are enforced "in the apply path." Per this investigation's confirmed finding
(`AttributePatch.apply`, `src/engine/patches.py:570-585`, and `RewardPatch.apply`,
`src/engine/patches.py:601-611`, are the only two apply-path sites touching
`attributes`/`unspent_ap`, and neither contains an AP-sufficiency check, an attribute-name check,
or an aptitude-multiplier lookup), rewrite the section to state each gate's actual current
enforcement location: `PROG-067` (sufficient AP) — enforced in the domain-handler layer,
`core_actions.py::execute_allocate_ap` (`src/engine/domain/core_actions.py:154-158`), not the apply
path; `PROG-068` (valid attribute name) — **not enforced on the live path** (see corrected
`PROG-068` parity entry from Step 5); `PROG-069` (aptitude multiplier) — **not enforced on the live
path** (see corrected `PROG-069` parity entry from Step 5); `PROG-070` (cap) — enforced in the
apply path, `AttributePatch.apply` (`src/engine/patches.py:570-585`), at a cap of 100 not the
99 this doc currently states. Add a one-line cross-reference to `DEV-004`.

**Other writers to this resource:** No other automated writer touches this file — mechanics-doc
edits are hand-authored/agent-authored prose, not machine-generated. The `mechanics-auditor` agent
role reads (does not write) this file when comparing it against source in future tickets; this
step's correction reduces, not introduces, a parity-auditor finding.

**Do NOT touch:** the `min(100, ...)` cap value itself in `AttributePatch.apply`
(`src/engine/patches.py:570-585`) — the 99-vs-100 mismatch is corrected in the **doc** only (state
the true current value, 100), not in code; changing the code's cap value is out of this ticket's
scope per its own "any change to the aptitude-multiplier gap resolution pipeline beyond what's
needed for the wire-vs-dormant call" exclusion, and per the investigation's explicit anti-drift
hazard on this exact point. Do not touch the "Derived Stat Recalculation Order" section immediately
below, or the Level-Up pseudocode block immediately above.

**Depends on:** Step 5 (the corrected `PROG-068`/`PROG-069` status this step references must exist
first, so the two documents stay consistent).

**Verify:** no automated test directly asserts this doc's prose; verified by review consistency
with the corrected `docs/parity_ledger/progression.yaml` entries from Step 5. If `docs/` files are
modified, run `make knowledge-index-update` per project convention (Finalize-phase requirement, not
this step's own test).

---

### Step 7 — Add a real, non-mocked dormancy-proof regression test

**Files:** `tests/integration/progression/test_allocate_ap_dormancy.py` (new file)

**Change:** Add `test_allocate_ap_unreachable_via_real_kernel_tick`: run a real (non-mocked)
`Kernel.tick_once()` loop over a bounded number of ticks (favor a small, fast bound — e.g. 100-200
ticks on a minimal or existing sandbox-style fixture/profile, not a full corpus run, to keep this
test fast per the project's `-m "not slow"` default scoping convention; mark `@pytest.mark.slow`
only if a larger tick count proves necessary to get a meaningful sample) and assert that zero
`attribute_changed` events (per the extractor at `src/observability/event_extractor.py`, the same
extractor `SUB-376`/`ENTITY-008` already verify) are attributable to either
`execute_allocate_ap` or the `ConversionKind.ALLOCATE_AP` resolver branch. This is the "prove the
negative" counterpart to the ticket's own conditional AC ("If wire: a real ... `Kernel.tick_once()`
run demonstrates a live path") and directly backs the dormancy claim recorded in `DEV-004` (Step 1)
— cite this test's path in `DEV-004`'s `**Verification**` field once written.

**Other writers to this resource:** This is a new test file with no existing writers to coordinate
with. It reads from (does not write to) the same `AuthoritativeState`/`Kernel` machinery every
other integration test uses — no shared mutable resource beyond the standard test-isolated
`Kernel`/`AuthoritativeState` instance this test constructs for itself.

**Do NOT touch:** any existing file under `tests/integration/` — this is a new, standalone file, not
an edit to an existing suite.

**Depends on:** Step 1 (references `DEV-004`'s ID in its docstring/comment) and Step 2 (asserts the
`resolver.py` branch specifically, so should exist after that branch's comment is in place, though
the assertion itself is behavioral, not comment-dependent).

**Verify:** the new test itself, run via `pytest tests/integration/progression/ -v -m "not slow"`
(per `test_plan.md`'s Scoped Pytest Commands).

## Scope Guards

- Do not flip `ENABLE_PROGRESSION_EVOLUTION` from `FeatureMode.OFF` — that decision belongs to the
  separate, already-filed `TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION`, not this ticket.
  Guarded by `tests/integration/test_scenario_feature_flag_defaults.py` and
  `tests/unit/config/test_phase10_feature_flags.py` staying green.
- Do not change `resolver.py`'s actual `ALLOCATE_AP` branch behavior (the `EntityUpdate(...)`
  construction itself) — Step 2 is comment-only. Guarded by
  `test_allocate_ap_conversion_maps_to_allocate_ap_intent` staying green **unmodified**.
- Do not touch `gaps.py` (`GrowthGapEvaluator`), `generator.py` (`ConversionOptionGenerator`), or
  `selector.py` (`ConversionDecisionService`) — listed in the ticket's Related Code Areas as context
  only. Guarded by the sibling Phase 6 test suite staying green.
- Do not change `ConversionKind`'s enum member set or values. Guarded by
  `tests/unit/engine/test_sort_tiebreaker.py` staying green.
- Do not modify `core_actions.py::execute_allocate_ap`'s logic (the strength/vitality-only branches,
  lines 164-169, or the unconditional AP decrement, line 173) — porting a fix is explicitly deferred
  to the follow-up ticket named (not created) in `DEV-004`.
- Do not touch `PROG-015`, `PROG-067`, or `PROG-070` in `docs/parity_ledger/progression.yaml` —
  only `PROG-068`/`PROG-069` are corrected in this ticket.
- Do not change the `min(100, ...)` cap value in `AttributePatch.apply`
  (`src/engine/patches.py:570-585`) — the 99-vs-100 doc/code mismatch is corrected in prose only
  (Step 6), not in code.
- Do not create the recommended follow-up ticket file (`tickets/todos/...`) for porting
  `AllocateAttributeAction`'s aptitude logic — `DEV-004` names and recommends it; actually filing it
  is a separate workflow action outside this plan's steps.
- Do not touch `src/actions/harvest.py` or `src/actions/loot.py` while deleting `attributes.py`.
- Do not touch DEV-001/DEV-002/DEV-003's own entries in `intentional_divergences.md`.

## Dependency Map

- Step 1 (DEV-004 entry) → no dependencies; run first.
- Step 2 (resolver.py comment) → depends on Step 1 (needs DEV-004 ID).
- Step 3 (delete AllocateAttributeAction) → depends on Step 1 (decision must be recorded before
  executed).
- Step 4 (new gap-documenting test) → independent; can run any time, but logically precedes Step 5.
- Step 5 (correct PROG-068/069 ledger) → depends on Step 4 (needs the test_path to exist and pass).
- Step 6 (correct mechanics doc) → depends on Step 5 (must stay consistent with corrected ledger).
- Step 7 (dormancy-proof integration test) → depends on Step 1 and Step 2 (references DEV-004 and
  the now-documented resolver.py branch); can run in parallel with Steps 3-6 otherwise.

Steps 2 and 3 are independent of each other (both only depend on Step 1). Step 4 is independent of
everything except being a prerequisite for Step 5.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| A decision doc states wire-vs-dormant with rationale citing SUB-376/ENTITY-008 | Step 1 | Manual/review (no direct test; cross-checked by Steps 2-7 citing DEV-004 correctly) |
| If dormant: an intentional_divergences.md entry is added, and resolver.py's cosmetic branch is corrected or documented as intended | Step 1 (entry), Step 2 (documented, not corrected) | `test_allocate_ap_conversion_maps_to_allocate_ap_intent` (unmodified, stays green) |
| The disposition of AllocateAttributeAction is explicitly resolved (wired, deleted, or documented) | Step 1 (records "deleted"), Step 3 (executes deletion) | `pytest tests/unit/progression/` reports no orphaned collection; full Regression Surface stays green |
| (Implicit, surfaced by investigation) Parity-ledger accuracy for the disposition made | Step 4 (new test), Step 5 (ledger correction) | `test_execute_allocate_ap_silently_no_ops_for_unhandled_attribute` |
| (Implicit) Mechanics doc must not contradict the corrected ledger | Step 6 | Review consistency with Step 5's ledger entries |
| (Implicit, test_plan.md's negative-proof requirement) Dormancy claim is actually true today | Step 7 | `test_allocate_ap_unreachable_via_real_kernel_tick` |

## Anti-Drift Notes

- **Do not conflate "wire the action-router `ALLOCATE_AP` branch" with "flip
  `ENABLE_PROGRESSION_EVOLUTION` ON."** They are different systems reaching different code paths
  that currently never call each other (investigation's own Anti-Drift Hazard #1). This plan
  touches neither the flag nor `core_actions.py`'s logic.
- **`test_plan.md` cites a test named `test_attribute_allocation_and_recalc` in
  `tests/unit/quest/test_progression_regression.py` — this test does not exist.** Verified via
  direct read: the file contains exactly `test_evolution_trigger_and_stat_boost` and
  `test_attribute_allocation`. Use `test_attribute_allocation` as the correct name for the existing
  ALLOCATE_AP regression test throughout implementation; do not search for or attempt to modify a
  test named `test_attribute_allocation_and_recalc`.
- **`AllocateAttributeAction` must not be deleted before Step 1's DEV-004 entry records the
  decision** — per investigation's Anti-Drift Hazard #3, deleting it first would destroy the only
  working copy of the PROG-015/069 aptitude-multiplier logic before the decision to defer (not
  port) that logic is durably recorded.
- **The `min(100, ...)` vs. documented "cap of 99" mismatch is real but explicitly out of scope for
  code changes** — Step 6 corrects the doc's stated value only; do not let a future implementer
  "fix" `patches.py`'s cap logic as a drive-by while touching this ticket's files.
- **PROG-015 is a known sibling accuracy gap, intentionally left uncorrected in this ticket** — do
  not expand Step 5 to also touch `PROG-015`; investigation explicitly frames it as adjacent, not
  in-scope.
- **Step 3's deletion has zero other referrers, verified by direct grep, not inferred from the
  investigation's earlier grep** — re-run `grep -rln "AllocateAttributeAction\|from
  src.actions.attributes" --include="*.py" .` immediately before deleting, in case another
  concurrent session's work has added a new caller since this plan was written (multiple sessions
  can share this working directory per project CLAUDE.md).

## Deviations

- **Step 5 touched one additional file the plan did not explicitly name as a "Files" target:
  `tests/tools/test_parity_index_baseline.py`.** Not a scope deviation — Step 5's own "Other
  writers to this resource" paragraph explicitly anticipated this and instructed running the
  parity-index baseline test to check for a `missing_test_path_count`-style hardcoded assertion
  needing an update. Moving `PROG-068`/`PROG-069` from `test_path: null` to a real `test_path`
  did change that count (1334 -> 1332, confirmed via `pytest
  tests/tools/test_parity_index_baseline.py`), so the assertion and its drift-history comment
  were updated in the same step, per the same documented-drift pattern CLAUDE.md's CI-triage
  section names for this exact test.
- No other deviations. All 7 steps executed as written, in the plan's stated dependency order.
