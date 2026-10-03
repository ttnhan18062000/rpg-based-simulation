---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260824-WOUND-HEALING-DECISION
artifact_type: plan
tags: [combat]
---

# Implementation Plan — TCK-20260824-WOUND-HEALING-DECISION

## Summary
The ticket owner already decided Option (b): wounds are permanent, and scars will form via a
separate, later mechanic. This plan records that decision in both Mechanics Bible sections,
removes the two dead-by-design producer functions (`WoundService.heal_wound()` and
`MedicalService.get_diagnosis_quality()`) rather than annotating them dormant — following this
project's own DEV-004 precedent (deletion for `AllocateAttributeAction`, a structurally identical
"decide the fate of dead code" case) — with the 4 dependent unit tests rewritten (not deleted) to
hand-construct their fixtures directly instead of calling the removed function, adds one new
non-mocked `Kernel.tick_once()` integration test that proves `wound_sustained` fires while
`wound_healed`/`scar_gained` never do, and corrects `COMB-296`/`ENTITY-018` and
`intentional_divergences.md` (new `DEV-005` entry) to reflect that zero-producer state precisely
and independent of `ENABLE_COMBAT_ENGAGEMENT`'s gate state.

## Steps

### Step 1 — Record permanence decision in `02_combat_laws.md` Section 5
**Files:** `docs/mechanics/02_combat_laws.md`

**Change:** Replace line 85 (the last bullet of "## 5. Wound Infliction"):
```
- Permanent Scars: when a wound heals, it has a 30% chance to leave a scar (`scar_penalty = wound_penalty * 0.3`).
```
with an explicit permanence statement, e.g.:
```
- Wound Permanence: Wounds are permanent. No code path currently heals a wound — verified: the
  only production constructor of `WoundUpdate` is `CombatResolutionSystem._get_wound_infliction()`
  (`src/engine/combat.py:605-617`), which always builds `WoundUpdate(wounds_add=[wound])` and never
  populates `wounds_heal` or `scars_add`; `WoundUpdate.wounds_heal`/`scars_add` both default to `[]`
  (`src/core/updates.py:604-609`). A wound's penalty applies for as long as the wound exists on the
  entity. Permanent Scars — a lesser, persistent penalty replacing a healed wound — are planned to
  form via a separate mechanic, tracked by `TCK-20260824-TACTICAL-WOUND-SCAR-WIRING` (not yet
  implemented); until that lands, `scars_add` also has zero production producers.
```
Do not alter any other bullet in Section 5 (severity/type/penalty formula text, lines 71-84, is
owned by the already-completed `TCK-20260824-WOUND-PENALTY-FORMULA-WIRING` and is correct as-is).

**Do NOT touch:** Section 5's wound-infliction threshold text (`is_wound = damage > ...`, lines
71-74) — owned by the separate, still-open `TCK-20260824-WOUND-THRESHOLD-DECISION`. Section 6
("Area of Effect") below it.

**Verify:** No automated test covers doc prose directly; verification is a manual re-read
confirming the "when a wound heals" phrasing no longer appears and the new text matches the
decision in `investigation.md`. Confirmed consistent by the code citations above, both read
directly during planning.

---

### Step 2 — Record permanence decision in `01_entity_anatomy.md` Section 6
**Files:** `docs/mechanics/01_entity_anatomy.md`

**Change:** Replace the "### Permanent Scars" subsection (lines 169-173):
```
### Permanent Scars
When a wound is healed, it has a chance to leave a **Permanent Scar**, which carries **30%** of the original wound's stat penalties indefinitely.
```python
scar_penalty = wound_penalty * 0.3
```
```
with:
```
### Permanent Scars
Wounds are permanent under the current implementation — no code path heals a wound.
`WoundState.healed` never transitions `False → True` in production: the only `WoundUpdate`
constructor (`CombatResolutionSystem._get_wound_infliction()`, `src/engine/combat.py:605-617`)
never populates `wounds_heal`, and `WoundUpdate.wounds_heal`/`scars_add` both default to an empty
list (`src/core/updates.py:604-609`). A wound's penalty applies indefinitely unless a future
Scar-formation mechanic — tracked by `TCK-20260824-TACTICAL-WOUND-SCAR-WIRING`, not yet built —
converts it into a **Permanent Scar**, a lesser, persistent penalty:
```python
scar_penalty = wound_penalty * 0.3
```
This formula describes the intended future scar mechanic, not currently active behavior.
```
The `scar_penalty = wound_penalty * 0.3` code block itself is preserved verbatim — do not change
the 0.3 multiplier or its framing as a formula; only the surrounding prose changes from
presupposing healing happens to stating it does not (yet).

**Do NOT touch:** Section 1's Wisdom attribute-table row ("Healing quality and tactical
decision-making") — informational flavor text for WIS's intended future role, not in this
ticket's Scope or Related Docs per `investigation.md`. Section 6's "Wound Infliction" and "Wound
Penalty" subsections above (lines 147-167) — owned by `WOUND-THRESHOLD-DECISION` and the
already-completed `WOUND-PENALTY-FORMULA-WIRING` respectively. Do not resolve the pre-existing
"30% chance" vs. "carries 30% of penalties" phrasing contradiction (investigation.md Finding 4) —
that belongs to `TCK-20260824-TACTICAL-WOUND-SCAR-WIRING`'s real formula, out of scope here.

**Verify:** Manual re-read; same code citations as Step 1 (verified directly, both files read
during planning: `src/engine/combat.py:605-617`, `src/core/updates.py:604-609`).

---

### Step 3 — Remove `heal_wound()` and `get_diagnosis_quality()`; update their 4 dependent tests
**Files:** `src/engine/rpg_depth.py`, `tests/unit/core/test_rpg_depth.py`

**Change:**
1. Delete `WoundService.heal_wound()` (`src/engine/rpg_depth.py:186-200`, read directly — a
   `@staticmethod` that unconditionally builds `healed = replace(wound, healed=True,
   scar_created=True)` and a `ScarState` with `atk_penalty/def_penalty/speed_penalty` each `wound.*
   * 0.3`, returning `(healed, scar)`). Confirmed zero `src/` callers other than its own
   definition (grep during investigation, re-confirmed no new callers introduced by this ticket
   since only docs/tests change elsewhere).
2. Delete `MedicalService.get_diagnosis_quality()` (`src/engine/rpg_depth.py:272-282`, read
   directly) and, since removing it leaves `MedicalService` (`src/engine/rpg_depth.py:272-273`) an
   empty stub class with no other members, delete the empty `MedicalService` class declaration
   too. Do **not** touch `DiscoveryService` (`src/engine/rpg_depth.py:261-270`) or the shared
   section comment `# ─── Discovery and Medical Services ──── (Task 10.1, 10.2)`
   (`src/engine/rpg_depth.py:259`) — `DiscoveryService` is live and stays under that header.
3. In `tests/unit/core/test_rpg_depth.py`, rewrite (not delete) all 3 tests in
   `TestScarPermanence` (lines 234-258) and `TestSkillScaling::test_effective_stats_with_scars`
   (lines 475-489, specifically line 482) to hand-construct the `WoundState`→`ScarState`
   transition inline instead of calling the removed `heal_wound()` — i.e. reproduce exactly what
   `heal_wound()` did, as local test-fixture code:
   ```python
   healed_wound = replace(wound, healed=True, scar_created=True)
   scar = ScarState(
       id=f"scar_{wound.id}", wound_kind=wound.kind, tick_created=wound.tick_inflicted,
       atk_penalty=wound.atk_penalty * 0.3, def_penalty=wound.def_penalty * 0.3,
       speed_penalty=wound.speed_penalty * 0.3,
   )
   ```
   `replace`, `WoundState`, and `ScarState` are already imported at the top of this test file
   (`tests/unit/core/test_rpg_depth.py:23-25`, read directly) — no new imports needed.
   `ScarState`'s fields (`id`, `wound_kind`, `tick_created`, `atk_penalty=0.0`, `def_penalty=0.0`,
   `speed_penalty=0.0`) were confirmed directly at `src/core/state.py:105-112`. This preserves
   `test_scar_permanence`'s assertions on the `healed`/`scar_created` flags and `scar.id`/
   `scar.wound_kind`, `test_scar_lesser_penalty`'s 30%-multiplier assertions, and
   `test_scar_cumulative_penalties`'s coverage of the still-live `WoundService.get_scar_stat_penalties()`
   (`src/engine/rpg_depth.py:171`, read directly, unaffected by this deletion) — none of that
   coverage is lost, matching `test_plan.md`'s explicit "New Tests Required" directive to update
   rather than delete these 4 tests.

**Other writers to the touched resource:** `heal_wound()`/`get_diagnosis_quality()` have zero
other callers anywhere in `src/` or `tests/` beyond the 4 test call sites named above (confirmed
by investigation's full-repo grep, and no step in this plan adds a new caller) — there is no
concurrent writer or pipeline phase that also constructs these symbols, so deletion has no
ordering/race interaction to account for.

**Do NOT touch:** `WoundService.create_wound()` (`src/engine/rpg_depth.py`, live, wired by
`WOUND-PENALTY-FORMULA-WIRING`) and `WoundService.get_wound_stat_penalties()`/
`get_scar_stat_penalties()` — all three stay untouched. `should_inflict_wound()`/
`WOUND_THRESHOLD_RATIO` (owned by `WOUND-THRESHOLD-DECISION`). `TestWoundInfliction` in the same
test file (separate ticket's scope). `test_wound_heal_through_apply`
(`tests/unit/core/test_rpg_depth.py:590-603`, read directly — tests `ApplyPath._apply_entity_update`
consuming a hand-built `WoundUpdate(wounds_heal=["w1"])`, i.e. the apply-path consumer, not
`heal_wound()`) — it does not call `heal_wound()` and must keep passing completely unmodified.

**Verify:** `pytest tests/unit/core/test_rpg_depth.py -v` — all tests pass, including the 4
rewritten tests and `test_wound_heal_through_apply` unchanged. `grep -rn "heal_wound\|get_diagnosis_quality" src/ tests/` returns zero matches outside the rewritten test bodies (which no longer
reference either symbol) — confirms complete removal with no leftover dangling references.

---

### Step 4 — Add a real-tick integration test proving zero `wound_healed`/`scar_gained` producers
**Files:** `tests/integration/combat/test_relation_combat_integration.py` (add to this existing
file, which already covers combat integration scenarios) or a new file
`tests/integration/combat/test_wound_healing_permanence.py` if the existing file's fixtures don't
suit a multi-tick `Kernel` loop — implementer's call based on what's already there.

**Change:** Add one new integration test that drives a real, non-mocked `Kernel.tick_once()` loop
(the established repo pattern for proving/disproving reachability of a gated mechanic — see
`tests/integration/scenarios/test_entity_differentiation.py:137-146`, read directly: constructs
`Kernel(_test_profile(), initial_state, rng, flags={...})` with
`"ENABLE_COMBAT_ENGAGEMENT": "ON"` in the scenario config and calls `kernel.tick_once()` in a
loop) for enough ticks that at least one `wound_sustained` event fires (proving combat/wounding is
genuinely live in this test, not just theoretically gated on), and asserts:
- at least one `wound_sustained` event occurs across the run, and
- zero `wound_healed` events occur, and
- zero `scar_gained` events occur,
in the same run. Extract events the same way `EventExtractor`/existing combat integration tests
already do (check `test_relation_combat_integration.py`'s existing event-collection helper before
inventing a new one). This is the concrete evidence AC #4 requires — proving the distinction
between "gate-limited but real" (`wound_sustained`) and "zero producers regardless of gate"
(`wound_healed`/`scar_gained`) in one run, not asserting it from static analysis alone.

**Other writers to the touched resource:** This step only adds a new test; it does not modify
`Kernel`, `EventExtractor`, or any production pipeline phase. No other test in the suite currently
drives `wound_healed`/`scar_gained` through a real tick loop (the existing
`test_wound_healed_fires`/`test_scar_gained_fires` in
`tests/unit/observability/test_event_extractor_vitals.py` hand-construct a `healed=True`
`WoundState` directly, bypassing `Kernel` entirely — confirmed by investigation, unaffected by
this step) — no collision.

**Do NOT touch:** `test_information_intent_execution_fires_through_kernel_tick_once` or any other
existing gated-mechanic integration test — this is a new, additive test only.

**Verify:** `pytest tests/integration/combat/ -v -m "not slow"` — new test passes, proving
`wound_sustained` fires and `wound_healed`/`scar_gained` never do in a real tick loop.

---

### Step 5 — Correct `COMB-296` in `docs/parity_ledger/combat_movement.yaml`
**Files:** `docs/parity_ledger/combat_movement.yaml`

**Change:** Locate entry `id: COMB-296` (`docs/parity_ledger/combat_movement.yaml:3201-3244`, read
directly). Leave `text` unchanged (it neutrally describes what `ENTITY-VITALS-OBSERVABILITY-GAP`
added — three new event blocks — and does not itself make a misleading reachability claim). Edit
only:
- `v2_evidence` (currently states events were "Verified via real, non-mocked `WoundState`/
  `ScarState` objects constructed by hand ... not through a live `Kernel.tick_once()` loop" for
  all three events uniformly) — replace with text distinguishing `wound_sustained` (now verified
  through a real `Kernel.tick_once()` loop per Step 4, gated only by `ENABLE_COMBAT_ENGAGEMENT`)
  from `wound_healed`/`scar_gained` (verified via hand-constructed objects for the consumer logic,
  but with **zero production producers regardless of gate state** — `WoundUpdate.wounds_heal`/
  `scars_add` are never populated by any code in `src/`, per `TCK-20260824-WOUND-HEALING-DECISION`).
- `support_boundary` (currently: "Code path is real and tested but currently unreachable in any
  shipped calibration world since combat engagement is corpus-wide off; will begin firing
  naturally once a future ticket re-enables it") — this sentence is accurate only for
  `wound_sustained`. Correct it to state plainly that `wound_healed` and `scar_gained` will **not**
  begin firing once `ENABLE_COMBAT_ENGAGEMENT` is re-enabled, because no producer exists for
  either — only `wound_sustained` is gate-limited-but-real.
- `test_path` — append the new Step 4 integration test's node id alongside the existing 3
  (`test_wound_sustained_severity_mapping`, `test_wound_healed_fires`, `test_scar_gained_fires`,
  which all stay, per `investigation.md`'s Parity Ledger Overlap note that the existing
  `test_path` "remains valid as consumer-logic evidence").
Use `tools/parity_ledger_writer.py` (the sanctioned, schema-validating YAML writer for this file)
rather than a raw text edit, per this project's established parity-ledger-safety convention —
a raw/ad-hoc edit to this large generated-shape YAML file risks unintended full-file rewrites.

**Other writers to the touched resource:** `docs/parity_ledger/combat_movement.yaml` is a shared,
append-mostly ledger with many other entries (`COMB-072/073/102/103/104/290/297/314`, etc.)
written by other, separate tickets over time — this step touches only the `COMB-296` entry's
`v2_evidence`/`support_boundary`/`test_path` fields and must not alter any other entry's content
or ordering. `COMB-290` (wound-infliction threshold, owned by `WOUND-THRESHOLD-DECISION`) and
`COMB-072/073/102/103/104/314` (already corrected by `WOUND-PENALTY-FORMULA-WIRING`) are adjacent
entries in the same file and must not be touched by this step.

**Do NOT touch:** Any other `id:` entry in this file.

**Verify:** Whatever validation `tools/parity_ledger_writer.py` runs on write (schema check); a
manual re-read confirming `wound_sustained` vs. `wound_healed`/`scar_gained` are now described
with the correct, distinct reachability claims.

---

### Step 6 — Correct `ENTITY-018` in `docs/event_ledger/entity.yaml`
**Files:** `docs/event_ledger/entity.yaml`

**Change:** Locate entry `id: ENTITY-018` (`docs/event_ledger/entity.yaml:132-137`, read directly).
Its `notes` field currently reads: "Cannot fire in any current calibration world since
`ENABLE_COMBAT_ENGAGEMENT` is corpus-wide off ... the code path is real and tested, just
currently unreachable in practice" — applied uniformly to all three `event_types`
(`wound_sustained`, `wound_healed`, `scar_gained`). Correct `notes` to state the same distinction
as Step 5: `wound_sustained` has a real production producer
(`CombatResolutionSystem._get_wound_infliction`, `src/engine/combat.py:605-617`) gated only by
`ENABLE_COMBAT_ENGAGEMENT`; `wound_healed`/`scar_gained` have **zero production producers
independent of the gate** — `WoundUpdate.wounds_heal`/`scars_add` are never constructed anywhere
in `src/`. Also update `evidence` if it still reads "verified via real hand-constructed
WoundState/ScarState objects ... could not be exercised through a real tick loop this session" —
add that `wound_sustained` is now additionally verified through a real `Kernel.tick_once()` loop
(Step 4's new test), while `wound_healed`/`scar_gained` remain hand-constructed-object-only
because no real trigger exists to exercise.

**Other writers to the touched resource:** `docs/event_ledger/entity.yaml` has many other
`ENTITY-*` entries (e.g. `ENTITY-017`, `ENTITY-019`, `ENTITY-020` adjacent to this one, read
directly) maintained by separate tickets — this step touches only `ENTITY-018`'s `evidence`/
`notes` fields, not the file's structure, ordering, or any other entry.

**Do NOT touch:** `ENTITY-017`, `ENTITY-019`, `ENTITY-020`, or any other entry in this file.

**Verify:** Manual re-read confirming the corrected distinction; no automated schema test is
known to cover this file beyond whatever generic YAML-parses-cleanly check the repo already runs
(implementer should check for one before assuming none exists).

---

### Step 7 — Add `DEV-005` entry to `docs/guidelines/intentional_divergences.md`
**Files:** `docs/guidelines/intentional_divergences.md`

**Change:** This file's most recent entry is `DEV-004` (`docs/guidelines/intentional_divergences.md:1463-1502`,
read directly in full as the template — Subsystem / Situation / Decision / Rationale /
Verification / Status shape, used as precedent by `investigation.md`). Add, after `DEV-004` and
before the closing `---`/"Last updated" line (currently lines 1504-1506):

```
### DEV-005 — Wounds Are Permanent; heal_wound()/get_diagnosis_quality() Removed (TCK-20260824-WOUND-HEALING-DECISION)
- **Subsystem**: Engine / Combat
- **Situation**: `WoundService.heal_wound()` (`src/engine/rpg_depth.py:186-200`, deleted by this
  ticket) had zero `src/` callers — its only 5 references were 4 unit tests in
  `tests/unit/core/test_rpg_depth.py` that directly exercised the dead function itself.
  `MedicalService.get_diagnosis_quality()` (`src/engine/rpg_depth.py:272-282`, also deleted) had
  zero callers anywhere, including tests. The only production constructor of `WoundUpdate`
  (`CombatResolutionSystem._get_wound_infliction()`, `src/engine/combat.py:605-617`) never
  populates `wounds_heal` or `scars_add` — confirmed zero production producers for wound healing
  and scar formation, independent of `ENABLE_COMBAT_ENGAGEMENT`'s gate state.
  `MedicalService.get_diagnosis_quality()`'s only plausible consumer, by name/docstring
  ("diagnosis accuracy", "healing quality"), was a hypothetical WIS-gated heal-success roll
  feeding `heal_wound()` — it is an unfinished half of the same never-wired healing pipeline, not
  a separately-dead subsystem.
- **Decision**: Wounds are declared permanent. No healing trigger is built. Both
  `heal_wound()` and `get_diagnosis_quality()` (plus the now-empty `MedicalService` class) are
  **deleted**, not annotated dormant — following the `DEV-004` precedent of deletion for
  zero-caller dead code (`AllocateAttributeAction`). Their 4 dependent unit tests
  (`TestScarPermanence`'s 3 tests, `test_effective_stats_with_scars`) are rewritten to
  hand-construct the `WoundState`→`ScarState` transition inline, preserving their coverage of
  `WoundService.get_scar_stat_penalties()` and `SkillScalingService.get_effective_stats()` with
  scars. Scar formation is deferred to a separate, later mechanic tracked by
  `TCK-20260824-TACTICAL-WOUND-SCAR-WIRING` (not yet implemented as of this entry — that ticket's
  current scope only reads existing `ScarState` data, it does not itself build a scar-formation
  producer; flagged for the ticket owner, not a blocker for this decision).
- **Rationale**: **Bug Fix** / dead-code removal. `heal_wound()`'s and `get_diagnosis_quality()`'s
  zero-caller status (confirmed by full-repo search) matches the same evidentiary bar `DEV-004`
  used for `AllocateAttributeAction`'s deletion — no live or planned call site references either
  function today, and no test beyond the 4 rewritten fixture-builders exercised them.
- **Verification**: `tests/unit/core/test_rpg_depth.py::TestScarPermanence` (3 tests, rewritten),
  `::TestSkillScaling::test_effective_stats_with_scars` (rewritten),
  `::TestSkillScaling::test_wound_heal_through_apply` (unchanged — apply-path consumer regression
  guard, proves `WoundUpdate.wounds_heal` plumbing still works even though nothing produces it);
  [Step 4's new integration test path — fill in exact node id once Step 4 lands] (proves
  `wound_sustained` fires while `wound_healed`/`scar_gained` never do, in the same real
  `Kernel.tick_once()` run). See `docs/parity_ledger/combat_movement.yaml::COMB-296` and
  `docs/event_ledger/entity.yaml::ENTITY-018` for the corrected reachability record.
- **Status**: ACTIVE
```
Then update the closing footer line (currently `*Last updated: 2026-08-26 (DEV-004,
TCK-20260824-ALLOCATE-AP-BRANCH-DECISION).*`) to reference `DEV-005`/this ticket/today's date, and
add a new row to "## 1. Divergence Summary Table" (after the `ALLOCATE_AP` row) — e.g.
`| **Engine / Combat** | Wounds Permanent; heal_wound()/get_diagnosis_quality() Removed | **Bug Fix** | ACTIVE |`.

**Other writers to the touched resource:** `docs/guidelines/intentional_divergences.md` is a
long-lived, append-only log with 31+ prior entries from many separate tickets — this step must
only append a new `### DEV-005` section and one summary-table row, and update the trailing "Last
updated" line; it must not reorder, edit, or renumber any existing `DEV-001`-`DEV-004` entry or
any `§2.x` legacy-numbered entry.

**Do NOT touch:** Any existing entry (`DEV-001` through `DEV-004`, or any `§2.x` entry).

**Verify:** Manual re-read; cross-check the `[fill in exact node id]` placeholder is resolved
before this step is considered complete — it must not ship with a placeholder still in it.

## Scope Guards

- Do not touch `should_inflict_wound()` or `WOUND_THRESHOLD_RATIO` (`src/engine/rpg_depth.py`) —
  owned by the separate, still-open `TCK-20260824-WOUND-THRESHOLD-DECISION`.
- Do not touch `WoundService.create_wound()` (already live, wired by
  `WOUND-PENALTY-FORMULA-WIRING`).
- Do not remove or modify `test_wound_heal_through_apply`
  (`tests/unit/core/test_rpg_depth.py:590-603`) — it tests the apply-path consumer
  (`ApplyPath._apply_entity_update` / `WoundPatch.apply`), which is correct, tested plumbing that
  stays regardless of this ticket's decision.
- Do not conflate `ScarState` (entity combat trauma, `src/core/state.py:105`) with
  `LocalScarState` (world/regional trauma, `src/core/state.py:176`) — do not touch
  `LocalScarState`, `StateUpdate.scars_add_or_update`, or
  `tests/unit/world/test_consequences.py`.
- Do not silently change `wound_sustained`'s reachability status — it has a real production
  producer gated only by `ENABLE_COMBAT_ENGAGEMENT`; only `wound_healed`/`scar_gained` lack a
  producer regardless of gate state. `COMB-296`/`ENTITY-018` corrections must be precise about
  which of the three events is actually affected, not blanket-rewritten.
- Do not implement Option (a) (an active healing trigger) — already decided against by the ticket
  owner.
- Do not resolve the pre-existing "30% chance" vs. "carries 30% of penalties" phrasing
  contradiction in the scar formula text (investigation.md Finding 4) — owned by
  `TCK-20260824-TACTICAL-WOUND-SCAR-WIRING`.
- Do not touch `docs/mechanics/01_entity_anatomy.md` Section 1's Wisdom attribute-table row.
- Do not touch `COMB-290`, `COMB-072/073/102/103/104/314`, or any other parity ledger entry
  besides `COMB-296`. Do not touch `ENTITY-017`, `ENTITY-019`, `ENTITY-020`, or any other
  event-ledger entry besides `ENTITY-018`.
- Do not edit any existing entry in `docs/guidelines/intentional_divergences.md` — only append
  `DEV-005` and the footer/table updates.
- Never edit a gate/test to force it to pass instead of fixing substance (project Hard Rule) —
  applies to any test failure surfaced while running Step 3/4's verification commands.

## Dependency Map

- Steps 1 and 2 (Mechanics Bible doc updates) are independent of every other step and of each
  other's exact wording, though both should land together since they describe the same decision.
- Step 3 (code + unit test removal/rewrite) is independent of Steps 1/2, 5, 6.
- Step 4 (new integration test) is independent of Step 3 mechanically, but should be implemented
  after Step 3 lands in the same branch to avoid two agents editing test infrastructure
  concurrently; it does not depend on Step 3's changes functionally.
- Steps 5 and 6 (ledger corrections) should land **after** Step 4, since their `v2_evidence`/
  `evidence`/`test_path` fields cite Step 4's new test by name — write Step 4 first so the exact
  test node id is known.
- Step 7 (`DEV-005` entry) should land **last**, after Steps 3-6 are complete, since it summarizes
  the disposition decided in Step 3 and cites the verification evidence from Steps 3, 4, 5, and 6.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| An explicit decision is recorded in both Mechanics Bible sections, replacing the ambiguous "when a wound heals" phrasing | Steps 1, 2 | Manual doc re-read (no automated test covers doc prose) |
| If healing made active: real production code path + non-mocked `Kernel.tick_once()` verification | N/A — Option (a) not chosen; ticket owner already decided Option (b) | N/A |
| If wounds declared permanent: `heal_wound()`/`get_diagnosis_quality()` removed or annotated dead-by-design, with `intentional_divergences.md` entry added | Steps 3 (removal), 7 (DEV-005 entry) | `pytest tests/unit/core/test_rpg_depth.py -v`; manual re-read of DEV-005 entry |
| `COMB-296` and `ENTITY-018` corrected to reflect zero production producers regardless of gate state | Steps 5, 6 (evidenced by Step 4) | `pytest tests/integration/combat/ -v -m "not slow"` (Step 4's new test); manual re-read of both ledger entries |
| State explicitly whether `get_diagnosis_quality()` belongs to the healing pipeline or is separately dead | Step 7 (DEV-005 Situation section states it is the same never-wired pipeline, not separately dead) | Manual re-read |

## Anti-Drift Notes

- **`heal_wound()`/`WOUND_THRESHOLD_RATIO` are separate dead-code decisions in the same file, same
  week** — easy to conflate. This ticket owns only `heal_wound()`/`get_diagnosis_quality()`;
  `should_inflict_wound()`/`WOUND_THRESHOLD_RATIO` belong to `WOUND-THRESHOLD-DECISION`.
- **`ScarState` vs. `LocalScarState`** — both contain "scar" and both have `scars_add`-shaped
  fields on different `*Update` classes (`WoundUpdate.scars_add` vs.
  `StateUpdate.scars_add_or_update`), but are unrelated subsystems (entity combat trauma vs.
  world/regional trauma). Verified directly: `ScarState` at `src/core/state.py:105-112`;
  `LocalScarState` is a distinct, untouched type per investigation.md.
  `TCK-20260824-TACTICAL-WOUND-SCAR-WIRING`'s current scope does not itself build a
  scar-formation producer (it only makes `TacticalDecisionSystem` read existing
  `ScarState`/`.scars` data) — this means "wounds become Scars via a different path" remains a
  declared intent, not yet a real end-to-end path, even after that ticket lands as currently
  scoped. This is informational only, already resolved as non-blocking for this ticket by
  `investigation.md`, and is surfaced again here (in the DEV-005 entry's Decision section, Step 7)
  for the ticket owner's visibility — it does not require a plan decision or change to this
  ticket's scope.
- **`test_wound_heal_through_apply` must keep passing completely unmodified** — it does not call
  `heal_wound()` and tests separate, correct, staying plumbing (`WoundPatch.apply`). If it starts
  failing or needs modification during Step 3/4, that is a signal of drift into consumer-plumbing
  territory — stop and re-scope rather than editing it to pass.
- **`COMB-296`'s `text` field should NOT be edited** — only `v2_evidence`, `support_boundary`, and
  `test_path` make the misleading "will begin firing naturally once re-enabled" claim; `text` is
  a neutral description of what was added and is already accurate.

## Unresolved Questions

None.

## Deviations

**Step 3**: `TestSkillScaling::test_effective_stats_with_scars` (as named in this plan) does not
exist under that class name in the current test file — the actual class is `TestEffectiveStats`.
Same test (`test_effective_stats_with_scars`), rewritten as planned; only the class-name citation
in this plan was imprecise. Also removed the now-dead `from dataclasses import replace` import
from `src/engine/rpg_depth.py` after deleting `heal_wound()` (its only use) — not explicitly named
by this plan's Step 3 but required to avoid leaving an unused import per this project's code
quality rules.

**Steps 4-7: initially blocked by a newly-discovered architectural conflict, not by any mistake in
this plan's own reasoning; now RE-SCOPED and completed in a follow-up session.** While building
Step 4's real, non-mocked `Kernel.tick_once()` integration test, direct verification showed
`wound_sustained` does **not** fire through any real Kernel loop today — contradicting this plan's
premise (inherited from `investigation.md`, itself inherited from the pre-existing
`COMB-296`/`ENTITY-018` ledger text) that it is a real, working producer gated only by
`ENABLE_COMBAT_ENGAGEMENT`.

Root cause (verified directly, reproducibly): `WoundPatch.apply()`
(`src/engine/patches.py:639`) always commits `entity.combat.wounds`/`.scars` as **tuples**
(`tuple(new_wounds)`, `tuple(new_scars)`) via the real authoritative apply path.
`src/observability/event_extractor.py:280-281,302-303` gate the wound/scar diffing blocks with
`isinstance(x, list)` — not `(list, tuple)` — so any wound/scar that reached state through the
real apply path is silently treated as absent, and the diff loop that emits
`wound_sustained`/`wound_healed`/`scar_gained` never runs. The same file already uses the correct
`isinstance(x, (list, tuple))` pattern elsewhere (lines 1499, 1583), confirming this is a real,
unintentional bug, not a deliberate design choice. The existing `COMB-296`/`ENTITY-018` test
evidence (`test_wound_sustained_severity_mapping` etc. in
`tests/unit/observability/test_event_extractor_vitals.py`) all construct
`wounds=[wound]` as a literal Python `list`, bypassing the real apply path entirely — which is why
they pass despite this bug, and why neither this plan nor `investigation.md` caught it.

This was out of this ticket's approved scope (`event_extractor.py` is not named as a file to
change in any of this plan's 7 steps) and was not something a `heal_wound()`/
`get_diagnosis_quality()` dead-code decision could responsibly paper over — completing Steps 4-7
as originally written would have required either asserting a false claim (`wound_sustained` fires
through the event layer) or restating a real bug as an accepted gate-limitation in the
parity/event ledgers. Per this project's Hard Rules ("Never edit an artifact to make an automated
gate/check pass instead of fixing the underlying substance"), this was reported rather than worked
around, and a new hotfix ticket, `TCK-20260829-HOTFIX-WOUND-SCAR-EVENT-EXTRACTOR-TUPLE-BLIND`, was
filed to own the `event_extractor.py` fix separately.

**Re-scope (this session, after the hotfix ticket was filed):** the top-level session directed
that Step 4's proof be re-targeted at the state/producer level instead of the event layer, so this
ticket's own completion does not depend on the separate hotfix landing first. The event-extraction
bug affects **all three** wound/scar events uniformly (`wound_sustained`, `wound_healed`,
`scar_gained`) — it is not specific to healing — so building Step 4's evidence around it would
conflate this ticket's healing-permanence claim with an unrelated, independently-scoped
observability bug.

Step 4 is redefined as: **a real, non-mocked `Kernel.tick_once()` integration test that reads
`kernel.state.entities[...].combat.wounds`/`.scars` directly** (the real, frozen, authoritative
state — populated via the real `WoundPatch.apply()` apply path, confirmed tuple-shaped by an
in-test `isinstance(..., tuple)` assertion) rather than via `EventExtractor`-emitted events. This
is a producer-existence proof, not an event-observability proof, and does not require the
event_extractor bug to be fixed first. Implemented as
`tests/integration/combat/test_wound_healing_permanence.py::test_wound_healed_and_scar_gained_have_zero_production_producers`:
two hand-built hostile entities (`hero_guild` attacker, ATK 80; `goblin_warband` defender, HP 100),
`ENABLE_COMBAT_ENGAGEMENT` ON, run for 40 ticks at seed 42. A real wound is genuinely inflicted at
tick 9 (`damage > defender.combat.max_hp * 0.25` per `combat.py:607`, verified deterministic and
reproducible), proving combat/wounding is live in this test. Across the full 40-tick run: no wound
ever transitions `healed: False -> True`, and no `ScarState` is ever added to either entity's
`.scars` — proving zero production producers exist for `WoundUpdate.wounds_heal`/`scars_add`,
independent of `ENABLE_COMBAT_ENGAGEMENT`'s gate state, exactly matching this ticket's original AC
#4 requirement without depending on the separate event-extraction fix.

Steps 5-7 proceed as originally planned, with their `v2_evidence`/`notes`/`evidence` corrections
scoped precisely to `wound_healed`'s (and `scar_gained`'s) zero-producer status — **not** to
`wound_sustained`'s event-layer reachability, which is a distinct, still-broken claim owned by the
separate hotfix ticket and explicitly left uncorrected here (that ticket's own Scope names the
`wound_sustained`/`scar_gained` post-fix correction to `COMB-296`/`ENTITY-018` as its own
responsibility, coordinated with, not duplicated by, this ticket's edits).
