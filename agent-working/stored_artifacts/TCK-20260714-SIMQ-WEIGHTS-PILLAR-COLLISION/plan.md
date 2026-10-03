---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION
artifact_type: plan
tags: [simulation-quality, bug, calibration]
---

# Implementation Plan — TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION

**Plan Amendment (post first Review round):** architecture-reviewer found two fixable gaps,
both corrected in place below rather than as a separate addendum: (1) Step 3's
`test_missing_key_raises_validation_error` assumed `pydantic.ValidationError`, but
`ScoringWeights.load()` actually raises a bare `KeyError` for a missing `detection_params` key —
Step 3 now extends the same "verify actual exception type first" hedge already applied to the
malformed-value test to this test too. (2) Step 6's illustrative new parity-ledger ID
(`INFRA-235`) was already taken (confirmed via full-file scan: INFRA-235 through INFRA-270
exist) — corrected to the actual next-free ID, `INFRA-271`.

## Summary

`ScoringWeights` already stores every pillar's rule weights correctly, pillar-scoped, in
`self.pillar_rules: dict[str, dict[str, float]]` (keyed by `PillarId.value`, e.g.
`"COGNITION"`). The bug is entirely in `_build_flat_index()` collapsing that structure into
one shared `_flat_rules: dict[str, float]` that `__getitem__` reads from — no new storage is
needed, only a pillar-aware read path. This plan adds a `ScoringWeights.for_pillar(pillar_id)`
accessor returning a lightweight `PillarWeightsView` that reads only from that pillar's own
`pillar_rules` section (bare `view["key"]` syntax preserved) and forwards `int_param()`/
`pillar_weight()` unchanged. `PillarScorer.__init__` (base.py) is changed once to resolve
`self.weights = weights.for_pillar(self.PILLAR_ID)`, and each of the 10 scorer subclasses gets
one new class attribute (`PILLAR_ID = PillarId.XXX`, matching the `PillarId` it already
hardcodes inside its own `_rec()` closure) — so no scorer's `.score()` method body changes at
all. Top-level `ScoringWeights.__getitem__` keeps its old bare-string signature but now raises
a clear error for any key declared in more than one pillar section (instead of silently
returning whichever pillar was declared last), closing the landmine without requiring any of
the 9 non-colliding-key test files to change. The two INFRA-234-cited missing validation tests
are written in this ticket. The investigation's correction is treated as settled, not
reopened: the 7 keys' *differing values* across pillars are intentional (§6/§7.3 primary/
secondary design) — the bug was purely the mechanism collapsing two intentionally-distinct
values into one, and this plan fixes only that mechanism, never the values. Anchor
recalibration is scoped narrowly: this ticket runs the real `test_grade_regression.py` scan
post-fix (replacing the "up to 53" estimate with the actual diffed set), mechanically
re-anchors every anchor whose new score is fully explained by the corrected weight arithmetic,
and carves out anything unexplained (plus the one anchor with no calibration report) to a
named follow-up ticket rather than hand-investigating it here.

## Steps

### Step 1 — Add pillar-scoped read path to `ScoringWeights`
**Files:** `src/simulation_quality/weights.py`
**Change:**
- Add a new class `PillarWeightsView` in this file:
  ```python
  class PillarWeightsView:
      def __init__(self, pillar_id: str, rules: dict[str, float], parent: "ScoringWeights") -> None:
          self._pillar_id = pillar_id
          self._rules = rules
          self._parent = parent

      def __getitem__(self, key: str) -> float:
          try:
              return self._rules[key]
          except KeyError:
              raise KeyError(
                  f"ScoringWeights: rule key '{key}' not found in pillar '{self._pillar_id}'. "
                  f"Available keys for this pillar: {sorted(self._rules.keys())}"
              )

      def int_param(self, key: str) -> int:
          return self._parent.int_param(key)

      def pillar_weight(self, pillar_id: str) -> float:
          return self._parent.pillar_weight(pillar_id)
  ```
  (`int_param`/`pillar_weight` passthrough exists so scorer code that currently calls
  `self.weights.int_param(...)` — e.g. `cognition.py:53`, `economy.py:64-66` — needs zero
  changes once `self.weights` becomes a `PillarWeightsView`.)
- Add `ScoringWeights.for_pillar(self, pillar_id: str) -> PillarWeightsView`:
  ```python
  def for_pillar(self, pillar_id: str) -> "PillarWeightsView":
      key = str(pillar_id)
      rules = self.pillar_rules.get(key)
      if rules is None:
          raise KeyError(f"ScoringWeights.for_pillar: unknown pillar '{key}'. "
                          f"Available pillars: {sorted(self.pillar_rules.keys())}")
      return PillarWeightsView(key, rules, self)
  ```
- In `_build_flat_index()` (lines 26-33), in addition to building `_flat_rules` as today,
  track which keys appear in more than one pillar section: add
  `_ambiguous_keys: dict[str, float] = {}` (a new frozen-model private attribute, same pattern
  as `_flat_rules`/`_pillar_weights`) populated with a `set[str]` of keys seen in >1 section
  during the same iteration (use a `seen_in: dict[str, int]` counter or `set` scratch var
  local to the validator; store the final `set[str]` via `object.__setattr__`).
- Change `__getitem__` (lines 91-98): if `key in self._ambiguous_keys`, raise
  `KeyError(f"ScoringWeights: rule key '{key}' is declared in multiple pillars "
  f"({sorted(...)}) — use ScoringWeights.for_pillar(pillar_id)['{key}'] instead of a bare "
  f"top-level lookup for this key.")`. Otherwise, behavior is byte-identical to today
  (`_flat_rules.get(key)`, same not-found message).
**Do NOT touch:** `int_param()` (lines 100-107) and `pillar_weight()` (lines 109-110) on
`ScoringWeights` itself — leave both untouched; `PillarWeightsView` delegates to them, it does
not reimplement them. Do not touch `ScoringWeights.load()`'s YAML-parsing body (lines 36-78)
in this step — that is Step 3's concern (a different validation path).
**Verify:** New unit tests from Step 4 (`test_pillar_scoped_lookup_resolves_independently_of_declaration_order`,
`test_real_config_seven_known_collisions_resolve_per_pillar`); existing
`test_getitem_known_key` (`harvest_active` == 12.0, non-colliding, must still pass unchanged)
and `test_getitem_raises_on_missing_key` (unknown key, must still raise `KeyError` with the
old not-found message, not the new ambiguous-key message) both still pass unmodified.

### Step 2 — Wire scorers to their own pillar's view
**Files:** `src/simulation_quality/scorers/base.py`, and one class-attribute line each in
`agency.py`, `cognition.py`, `combat.py`, `economy.py`, `faction.py`, `information.py`,
`narrative.py`, `progression.py`, `social.py`, `world_dynamics.py`
**Change:**
- In `base.py`, add an abstract/required class attribute `PILLAR_ID: PillarId` to
  `PillarScorer` (import `PillarId` from `src.simulation_quality.pillars`), and change
  `__init__` (lines 15-16) from `self.weights = weights` to
  `self.weights = weights.for_pillar(self.PILLAR_ID)`.
- In each of the 10 scorer subclasses, add one line near the top of the class body:
  `PILLAR_ID = PillarId.COGNITION` (for `cognition.py`), `PillarId.ECONOMY` (`economy.py`),
  `PillarId.INFORMATION` (`information.py`), `PillarId.WORLD` (`world_dynamics.py`), and the
  matching `PillarId` for the remaining 6 files — each value must exactly match the
  `PillarId` that file's own `_rec()` closure already hardcodes (e.g. `cognition.py:41`
  already uses `PillarId.COGNITION`, so `PILLAR_ID = PillarId.COGNITION` is consistent, not a
  new decision). Do not remove the hardcoded `PillarId.XXX` inside each `_rec()` closure —
  leave it as-is; `PILLAR_ID` is a new, separate declaration used only for weights
  resolution, not a refactor of `ScoreRecord` construction.
- Subclasses with a custom `__init__` (`CognitionScorer`, `EconomyScorer` — both call
  `super().__init__(weights)` before setting their own instance flags) need no change to
  their `__init__` bodies: the class attribute is available at `super().__init__()` call time
  because Python resolves class attributes before instance `__init__` runs.
**Do NOT touch:** Any `.score()` method body in any of the 10 scorer files — `self.weights["key"]`
call sites keep identical syntax and now resolve correctly through `PillarWeightsView`. Do not
add a `self.pillar_id` instance attribute distinct from `PILLAR_ID` — one class attribute is
sufficient; do not create parallel bookkeeping.
**Verify:** Step 5's new `test_scorer_pillar_binding.py` (or folded test) confirming each
scorer's `PILLAR_ID` matches its own `_rec()`-hardcoded `PillarId`; existing
`test_agency_scorer.py`, `test_combat_scorer.py`, `test_faction_scorer.py`,
`test_progression_scorer.py`, `test_social_scorer.py`, `test_narrative_scorer.py`,
`test_timegate_penalties.py` (non-colliding scorers) all pass with zero value changes.

### Step 3 — Close the INFRA-234 test gap (missing-key / malformed-value validation)
**Files:** `tests/simulation_quality/test_weights.py`
**Change:** Add two new tests, named exactly as INFRA-234 and this ticket's AC #3 already
cite:
- `test_missing_key_raises_validation_error` — construct a temp YAML/dict missing a required
  top-level key `ScoringWeights.load()` depends on (e.g. omit `detection_params.yaml`'s
  `loop_threshold`). **Architecture-review correction:** `load()`'s current code
  (`raw_detection["loop_threshold"]`) raises a bare `KeyError` here, not
  `pydantic.ValidationError` — the ticket's AC #3 and INFRA-234's existing text both assert
  `ValidationError`, which this path cannot produce as written today. Apply the same resolution
  as the malformed-value test below: read `load()`'s actual behavior for this exact missing-key
  path first; if it raises `KeyError` (confirmed), either (a) wrap the dict access so it
  surfaces as `pydantic.ValidationError` consistent with the rest of `load()`'s validation
  surface, or (b) assert the real exception type (`KeyError`) and correct AC #3/INFRA-234/§4.8's
  wording to match reality instead of silently asserting the wrong exception type. Use `tmp_path`
  fixtures written with `yaml.safe_dump`, following the existing `test_missing_file_raises`
  pattern (lines 109-115) for temp-file construction style.
- `test_malformed_value_raises_validation_error` — construct a temp `scoring_weights.yaml`
  where a rule value is a non-numeric string (e.g. `harvest_active: "not_a_number"`) and
  assert `ValidationError` (or the `ValueError` that `load()`'s `float(v)` conversion at line
  58 raises today — read `load()`'s current exception type for this exact malformed-value
  path before writing the assertion, since line 58's `float(v)` on a non-numeric string raises
  `ValueError` at the point the ticket's AC/INFRA-234 both say `ValidationError` is expected;
  if the current code raises `ValueError` not `ValidationError` for this specific malformed
  case, either wrap the conversion so it surfaces as `pydantic.ValidationError` consistent
  with the missing-key case, or adjust the test to the actually-correct exception type and
  flag the mismatch in Test Summary — do not silently assert the wrong exception type to make
  the test pass).
**Do NOT touch:** `ScoringWeights.load()`'s control flow beyond what's needed to make the
missing-key and malformed-value paths raise a consistent, documented exception type, if a
mismatch is found for either. Do not change `_build_flat_index()` in this step — unrelated to Step 1.
**Verify:** Both new tests pass; `INFRA-234`'s `test_path` in
`docs/parity_ledger/infrastructure.yaml` becomes accurate (closed in Step 6, using whichever
real exception types Step 3 confirms for both paths — not assumed as `ValidationError` for
either without verification).

### Step 4 — New pillar-scoping regression tests (AC #1, AC #2)
**Files:** `tests/simulation_quality/test_weights.py`
**Change:**
- `test_pillar_scoped_lookup_resolves_independently_of_declaration_order` — build two small
  synthetic `ScoringWeights` instances directly via the constructor (not `load()`, to avoid
  needing temp files): one with `pillar_rules={"PILLAR_A": {"shared_key": 1.0, ...}, "PILLAR_B": {"shared_key": 2.0, ...}}`
  and a second with the two pillar keys' dict-insertion order reversed. For both, assert
  `weights.for_pillar("PILLAR_A")["shared_key"] == 1.0` and
  `weights.for_pillar("PILLAR_B")["shared_key"] == 2.0` regardless of declaration order —
  proving the fix isn't order-dependent luck.
- `test_real_config_seven_known_collisions_resolve_per_pillar` — load the real
  `config/simulation_quality/scoring_weights.yaml` via the `scoring_weights` fixture, and
  parametrize over the 7 keys × their 2 owning pillars (`belief_active`, `subjective_divergence`,
  `knowledge_rot`, `omniscience_collapse` via COGNITION vs INFORMATION;
  `ecology_cycling`, `ecology_broken` via ECONOMY vs WORLD; `knowledge_economy_active` via
  ECONOMY vs INFORMATION), asserting `weights.for_pillar("COGNITION")["belief_active"] == 2.0`
  and `weights.for_pillar("INFORMATION")["belief_active"] == 10.0` (and so on for all 7×2
  combinations, using the exact values tabulated in investigation.md's collision table).
  Also assert that a bare `weights["belief_active"]` (top-level, ambiguous) now raises
  `KeyError` (proves Step 1's ambiguous-key guard is live for all 7 keys, not just resolved
  silently).
**Do NOT touch:** Do not assert anything about `CognitionScorer`/`EconomyScorer` behavior in
this step — that is Step 5, exercised through the real scorer `.score()` path, not direct
`ScoringWeights` queries.
**Verify:** Both new tests pass. Satisfies ticket AC #1 and AC #2 exactly as worded.

### Step 5 — Update the 4 known scorer-test value oracles + add pillar-binding guard test
**Files:** `tests/simulation_quality/test_cognition_scorer.py` (lines ~40, ~68, ~102),
`tests/simulation_quality/test_economy_scorer.py` (line ~126), new file
`tests/simulation_quality/test_scorer_pillar_binding.py`
**Change:**
- In `test_cognition_scorer.py`, the 3 assertions currently reading
  `scoring_weights["belief_active"]` / `scoring_weights["knowledge_rot"]` /
  `scoring_weights["subjective_divergence"]` as their expected-value oracle must be rewritten
  — after Step 1, these bare top-level lookups raise `KeyError` (ambiguous key), so the tests
  would fail outright, not silently pass with a wrong value. Rewrite each to assert against
  either a literal (`2.0`, `-3.0`, `5.0` — COGNITION's own declared values) or
  `scoring_weights.for_pillar("COGNITION")["belief_active"]` etc. Prefer the explicit
  pillar-scoped call over a bare literal so the test still fails loudly if
  `scoring_weights.yaml` is ever re-tuned (keeps the test's original intent — asserting
  against the config, not a hardcoded magic number — while being the pillar-correct config
  value instead of the collapsed one).
- In `test_economy_scorer.py`, the `knowledge_economy_active` assertion (~line 126) is
  rewritten the same way: `scoring_weights.for_pillar("ECONOMY")["knowledge_economy_active"]`
  (== `8.0`), not the bare top-level (now-ambiguous, now-raising) form.
- New `test_scorer_pillar_binding.py`: for all 10 `PillarScorer` subclasses, instantiate each
  with the real `scoring_weights` fixture and assert `scorer.PILLAR_ID` equals the `PillarId`
  literal that file's own `_rec()` closure constructs `ScoreRecord(pillar=...)` with. Since
  there's no programmatic way to introspect a closure's hardcoded literal, implement this as
  10 explicit assertions (e.g. `assert CognitionScorer.PILLAR_ID == PillarId.COGNITION`) with
  a one-line comment next to each citing the `_rec()` line number it must match — this is a
  manual-but-explicit correctness lock, not a dynamic check, since the alternative (parsing
  source) is fragile.
**Do NOT touch:** `test_information_scorer.py` and `test_world_dynamics_scorer.py`'s existing
value assertions — per investigation, INFORMATION and WORLD were always the flat-dict
"winner" for all 7 keys, so their scorer behavior is provably invariant to this fix; these
files must keep passing with the exact same numeric outcomes, unmodified. If either file's
values change, the fix has been implemented backwards.
**Verify:** `pytest tests/simulation_quality/test_cognition_scorer.py
tests/simulation_quality/test_economy_scorer.py tests/simulation_quality/test_information_scorer.py
tests/simulation_quality/test_world_dynamics_scorer.py tests/simulation_quality/test_scorer_pillar_binding.py -v`
all green. Document each of the 4 rewritten assertions in the ticket's Test Summary per AC #4.

### Step 6 — Update docs and parity ledger
**Files:** `docs/simulation_quality/quality_scoring_contract.md`,
`docs/parity_ledger/infrastructure.yaml`
**Change:**
- §4.8 "Data-Driven Scoring Weights": add a paragraph documenting that weight lookup is
  pillar-scoped (`ScoringWeights.for_pillar(pillar_id)["key"]`, or `self.weights["key"]` from
  inside a `PillarScorer` subclass, which now resolves through that scorer's own
  `PILLAR_ID`-bound view) — no rule key collapses across pillars anymore, and a key declared
  in more than one pillar section will raise `KeyError` on the ambiguous top-level
  `ScoringWeights.__getitem__` if ever queried without going through `for_pillar()`.
- §7.2 "Adding a Scoring Rule to an Existing Pillar": confirm/update the example code — it
  already teaches `self.weights["rule_key"]` inside a scorer, which is unchanged syntax; add a
  note that this now resolves to the *calling scorer's own pillar*, not a shared namespace.
- §7.3 "Conflict Detection Rules": add a cross-reference confirming that the primary/secondary
  dual-pillar design documented there (SQ-15, SQ-16, SQ-08/18) is what the pillar-scoped fix
  makes actually work as intended — cite this ticket ID as the fix that closed the gap between
  the documented design and the previously-buggy shared-namespace implementation.
- `docs/parity_ledger/infrastructure.yaml` INFRA-234: update `test_path` to the corrected,
  now-existing test names (`tests/simulation_quality/test_weights.py::test_missing_key_raises_validation_error,
  test_malformed_value_raises_validation_error`), update `v2_evidence`/`status` to reflect the
  now-passing state, and add a new entry — **`INFRA-271`** (architecture-review confirmed via a
  full-file ID scan that INFRA-235 through INFRA-270 already exist; INFRA-271 is the actual next
  free ID, re-confirm at implementation time in case another ticket lands first) — documenting
  the pillar-scoped lookup guarantee itself, with `test_path` pointing at Step 4's
  `test_real_config_seven_known_collisions_resolve_per_pillar`.
**Do NOT touch:** Any other `docs/parity_ledger/infrastructure.yaml` entry unrelated to
`ScoringWeights`/INFRA-234. Do not touch `docs/guidelines/intentional_divergences.md` in this
step — the `EconomyScorer` "documentary only" divergence (§7.3) is explicitly out of scope for
this ticket (see Scope Guards); if the implementer wants to flag it, do so as a note in the
ticket's own Implementation Notes recommending a follow-up ticket, not as a new divergence
entry attributed to this ticket's diff.
**Verify:** `make knowledge-index-update` after these doc edits (required by project workflow
whenever `docs/` changes); manual read-through confirming §4.8/§7.2/§7.3 and the ledger entries
accurately describe Steps 1-2's actual mechanism (not a paraphrase of this plan).

### Step 7 — Run the grade-regression scan, enumerate diffs, re-anchor mechanical ones
**Files:** `tests/simulation_quality/fixtures/grade_anchors.json`, plus whatever calibration
re-run tooling `test_grade_regression.py` / `make calibrate` already provides — no new test
code in this step, just running existing tooling and editing fixture data.
**Change:**
- With Steps 1-2 landed, run `pytest tests/simulation_quality/test_grade_regression.py -v`
  (and the `-m slow` variant if time allows) to get the actual (not estimated) full diff
  across all 76 anchors — this replaces investigation's "up to 53, only 10 confirmed" estimate
  with ground truth.
- For every anchor whose new `{grade, score}` differs from the committed fixture: verify the
  new value is explained by the corrected weight substitution (e.g., a COGNITION anchor whose
  `subjective_divergence`-tagged events now score at COGNITION's own `5.0` per event instead
  of INFORMATION's previously-collapsed `30.0` — the arithmetic must reconcile against
  `event_count` and the known per-key delta, same style of reconstruction investigation
  already did for `urban_political_seed42_200t`). If it reconciles, update that anchor's
  `{grade, score}` in `grade_anchors.json` directly — never add, remove, or duplicate a
  top-level scenario key (the count must stay pinned at 76;
  `test_grade_anchors_entry_count_unchanged` is the tripwire).
- If any anchor's diff does NOT reconcile against the expected arithmetic (unexplained
  magnitude, unexpected sign, or any other surprise), do not re-anchor it and do not
  investigate further in this ticket — list it explicitly in Implementation Notes/Completion
  Summary and recommend a named follow-up ticket (created via the `create-tickets` skill, per
  the investigation's own anti-drift guidance) to investigate that specific anchor.
- The one anchor with no calibration report on disk
  (`urban_political_selfmodel_execution_probe_seed42_200t`) cannot be evaluated by this scan at
  all — note it explicitly as a pre-existing, out-of-scope gap (already confirmed by
  investigation, unrelated to this ticket) rather than silently omitting it from the
  enumeration.
**Do NOT touch:** Do not re-tune any weight value in `scoring_weights.yaml` to make an anchor
"look better" — only the fixture's recorded `{grade, score}` may change, and only when the new
value is the direct, reconciled output of the corrected lookup. Do not touch anchors whose
`COGNITION.event_count == 0` and `ECONOMY.event_count == 0` (the 22 provably-unaffected
anchors) — leave them untouched as a confirmation the fix has zero blast radius there.
**Verify:** `pytest tests/simulation_quality/test_grade_regression.py -v` fully green after
re-anchoring the reconciled diffs; `test_grade_anchors_entry_count_unchanged` still asserts 76;
every reconciled diff and every carved-out (unreconciled or unevaluable) anchor listed
verbatim in the ticket's Test Summary, per AC #5.

## Scope Guards

- Do not change any weight *value* in `config/simulation_quality/scoring_weights.yaml` — only
  the lookup mechanism changes. `test_getitem_known_key`'s `harvest_active == 12.0` assertion
  is the tripwire; it must never change.
- Do not touch `EconomyScorer`'s `paid_info_transaction` handling (`economy.py:130-135`)
  beyond the mechanical effect of it now correctly reading ECONOMY's own `8.0` instead of
  INFORMATION's `15.0`. Whether `EconomyScorer` should stop scoring this event entirely (to
  match §7.3's "documentary only" secondary-pillar rule) is a separate, pre-existing
  divergence — flag it, do not fix it here.
- Do not touch `int_param()` or `pillar_weight()` on `ScoringWeights` (lines 100-110) —
  `PillarWeightsView` delegates to them unchanged; they are not part of the collision bug.
- Do not touch `src/engine/kernel.py`'s tick-budget watchdog/throttle — unrelated.
- Do not touch `TCK-20260713-SIMQ-SCORE-CEILING-FIX`'s rescale values or methodology for
  WORLD, PROGRESSION, or ECONOMY.
- Do not investigate or fix `TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM`'s
  `event_count` nondeterminism — this ticket only fixes the weight-collapse mechanism.
- Do not add a `self.pillar_id` instance attribute distinct from the `PILLAR_ID` class
  attribute introduced in Step 2 — one mechanism, not two.
- Do not hand-verify all 53 possibly-affected anchors' arithmetic manually — Step 7 uses the
  actual regression-test diff output as ground truth, not manual reconstruction (except to
  spot-check reconciliation of specific surprising diffs).
- Do not fold `docs/guidelines/intentional_divergences.md` changes into this ticket for the
  `EconomyScorer` "documentary only" question — note it, do not resolve it here.

## Dependency Map

- Step 1 is the foundation; Steps 2, 4 depend on it.
- Step 2 depends on Step 1 (`for_pillar()`/`PillarWeightsView` must exist first).
- Step 3 is independent of Steps 1-2 (different code path — `load()`'s YAML validation, not
  `__getitem__`/`for_pillar()`); can be done in parallel with Step 1.
- Step 4 depends on Step 1 (`for_pillar()`) and, for the "through scorer path" framing implied
  by AC #2's wording, benefits from Step 2 being done first so the parametrized test can
  optionally also assert through `CognitionScorer`/`EconomyScorer`/`InformationScorer`/
  `WorldDynamicsScorer` instances if desired — but the core AC #2 test can be written against
  `ScoringWeights.for_pillar()` directly without waiting on Step 2.
- Step 5 depends on Step 2 (scorer behavior must be wired to pillar-scoped views before their
  test oracles can be correctly rewritten).
- Step 6 depends on Steps 1-2 being finalized (docs must describe the actual shipped
  mechanism, not a draft of it) and benefits from Step 3 (INFRA-234 test names must exist to
  cite correctly).
- Step 7 depends on Steps 1-2 being complete and merged into the working tree (the fix must be
  live before its effect on anchors can be measured) — it should run last.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — pillar-scoped resolution proven via synthetic two-pillar fixture, order-independent | Step 1, Step 4 | `test_pillar_scoped_lookup_resolves_independently_of_declaration_order` |
| AC #2 — real-config regression for all 7 colliding keys resolves per-pillar | Step 1, Step 4 (Step 2 for scorer-path framing) | `test_real_config_seven_known_collisions_resolve_per_pillar` |
| AC #3 — `ScoringWeights.load()` validation behavior preserved (INFRA-234) | Step 3 | `test_missing_key_raises_validation_error`, `test_malformed_value_raises_validation_error` (newly written, per Design Decision #1) |
| AC #4 — all scorer call sites updated consistently, existing scorer tests pass | Step 2, Step 5 | `test_cognition_scorer.py`, `test_economy_scorer.py` (4 rewritten assertions), `test_information_scorer.py`, `test_world_dynamics_scorer.py` (unchanged), `test_scorer_pillar_binding.py`, plus all 6 non-colliding scorer test files (unchanged) |
| AC #5 — grade regression diffs enumerated, fixed or explicitly deferred | Step 7 | `test_grade_regression.py` full run, `test_grade_anchors_entry_count_unchanged` |
| AC #6 — `quality_scoring_contract.md` §4.8/§7.2 (and §7.3, per this plan's addition) updated | Step 6 | Doc read-through; `make knowledge-index-update` |
| AC #7 — `infrastructure.yaml` INFRA-234 (and new entry) updated | Step 6 | Ledger read-through; new entry's `test_path` resolves to a real, passing test |

## Design Decisions

**1. INFRA-234's two missing tests — write now, in this ticket.**
They are small, self-contained additions to `test_weights.py`, the exact file this ticket is
already modifying in Steps 1 and 4. The ticket's own AC #3 already names them, and the parity
ledger already cites them as if they exist — deferring would leave AC #3 permanently
unsatisfiable without a follow-up ticket that would just re-open this same file for a few
lines of test code. Bounded, zero-risk, in scope. See Step 3.

**2. Pillar-scoping mechanism — `for_pillar()` view wrapper, not a signature change to
`__getitem__`.**
`ScoringWeights.pillar_rules` already stores every pillar's weights correctly-scoped; the bug
is purely that `_build_flat_index()`/`__getitem__` throw that structure away. The fix adds
`ScoringWeights.for_pillar(pillar_id) -> PillarWeightsView`, a thin wrapper with a
bare-string `__getitem__` (so scorer `.score()` method bodies need zero syntax changes) that
also forwards `int_param()`/`pillar_weight()` unchanged. `PillarScorer.__init__` resolves
`self.weights = weights.for_pillar(self.PILLAR_ID)` once at construction, using a new
`PILLAR_ID` class attribute added to each of the 10 scorer subclasses (matching the `PillarId`
each already hardcodes in its own `_rec()` closure — not a new decision, just making an
implicit fact explicit). Top-level `ScoringWeights.__getitem__` keeps working exactly as
before for the many non-colliding keys, but now raises a clear `KeyError` for any of the 7
colliding keys if queried without going through `for_pillar()` — converting a silent
mis-resolution into a loud, immediate failure. This satisfies the investigation's own
recommendation (bare-string compatibility, minimal test churn: only the 2 files with real
value bugs need editing, the other 9 files' direct `scoring_weights["key"]` usages are for
non-colliding keys and are provably unaffected).

**3. Anchor recalibration — scan runs in this ticket; only mechanically-reconciled diffs get
re-anchored here; anything unexplained is carved out to a named follow-up ticket.**
Leaving anchors silently wrong (never running the scan) is not acceptable — the ticket's own
AC #5 requires enumeration at minimum, and the fix's whole point is correctness. But
hand-verifying up to 53 anchors' arithmetic one at a time (as investigation did for exactly
one, at real effort) is exactly the kind of open-ended, size-unknown-until-you-look work this
ticket's Out-of-Scope section already warns against ("a full recalibration pass across the
corpus is not assumed in-scope by default"). The resolution that keeps both correctness and
scope control: Step 7 runs the actual regression harness (which mechanically computes the
right-answer diff for every anchor in one pass — this is exactly what
`test_grade_regression.py` is for), producing precise numbers instead of the "up to 53"
estimate. Every diff that reconciles against the known corrected arithmetic (i.e., is fully
explained by the 7-key substitution — expected for the mechanical, deterministic cases like
`subjective_divergence`'s 6x-per-event correction) gets re-anchored in this ticket, because
that is a bounded, finite, fully-automated-diff-driven edit, not open-ended investigation. Any
anchor whose diff does NOT reconcile cleanly (a second bug, an unexpected magnitude, or
anything requiring actual investigation beyond "the corrected weight explains this") is
explicitly named and carved out to a follow-up ticket instead of being force-fit into this
diff or silently left uncommitted. The one anchor with no calibration report on disk is
likewise named and left to a separate, pre-existing-gap follow-up rather than blocking this
ticket. This bounds the ticket's actual size to "run one command, edit N fixture entries whose
new values are provably explained," while guaranteeing no anchor is left silently wrong
without at least being named.

## Anti-Drift Notes

- **Residual risk — `omniscience_collapse`'s "identical value today" is coincidence, not
  correctness.** Even after this fix, COGNITION and INFORMATION happen to both declare
  `-20.0` for this key today. Nothing in this plan changes either value (per Scope Guards);
  the fix only ensures that if either value is ever retuned independently in the future, each
  pillar will correctly read its own value instead of silently colliding again. No test
  assertion in Step 4/5 should assume these two values must always match — assert each
  pillar's own declared value independently (currently both `-20.0`, coincidentally).
- **Residual risk — the ecology pair's ECONOMY-side values (`ecology_cycling: 8.0`,
  `ecology_broken: -25.0`) remain genuinely dead config after this fix**, exactly as before —
  `EconomyScorer` never queries them (confirmed in investigation). The fix corrects the *data
  structure* (no future YAML-reorder landmine for `WorldDynamicsScorer`), but does not make
  this dead config live, and should not: reviving it is a scope decision this ticket does not
  make.
- **Residual risk — `EconomyScorer`'s `paid_info_transaction` divergence from §7.3's
  "documentary only" rule survives this fix unresolved**, just now reading the mechanically
  correct `8.0` instead of the accidentally-borrowed `15.0`. This is a real, live behavioral
  question (should ECONOMY score this event at all?) that this ticket deliberately does not
  answer — flag it in Implementation Notes as a candidate follow-up ticket, do not resolve it
  mid-implementation even if it looks like a one-line fix once `economy.py` is already open.
  Per CLAUDE.md's Uncertainty Rule, this stays vague/deferred, not collapsed into an ad hoc
  decision.
- **Residual risk — the grade-regression scan (Step 7) is the ticket's least bounded step in
  practice**, even with Design Decision #3's scope narrowing. If more than a handful of
  anchors fail to reconcile cleanly, that is itself a signal worth surfacing loudly (it would
  suggest either a second, undiscovered collision or an error in the fix itself) rather than
  quietly bulk-carving all of them into a follow-up ticket to preserve this ticket's velocity.
- **Residual risk — `PillarWeightsView`'s forwarding of `int_param()`/`pillar_weight()` must be
  verified byte-identical**, not just structurally present. A guard test (folded into Step 1's
  verification) asserting `scorer.weights.int_param("stasis_gate_ticks") == 5` (via a live
  scorer instance, not just direct `ScoringWeights`) closes this out concretely, per the
  investigation's explicit call-out that these two accessors must stay provably untouched.

## Unresolved Questions

None. All three open questions flagged by investigation.md are resolved above under Design
Decisions, with concrete implementation shape specified in Steps 1-7. If, during Step 7's
actual scan, the number of unreconciled anchor diffs turns out to be large (investigation's
own words: "very likely... non-trivial"), that is a signal for the main session to reassess
scope before closing the ticket — not a question this plan can pre-resolve without the scan's
real output.

## Deviations

**Step 7 — environment had zero local calibration data, not "up to 53 possibly-affected, 1
missing."** At resume time `data/calibration/` (fully gitignored) held only one stale report
(`urban_political_selfmodel_execution_probe_seed42_200t`); the other 75 anchors had none at all.
`pytest tests/simulation_quality/test_grade_regression.py` against that state would have only
skipped, producing no real diff. Before the scan could run for real, all 76 anchors' calibration
reports were regenerated via `tools/evaluate_simq.py` (no `--dry-run`), batched by tick count
(46×200t, 12×500t, 12×1000t, 6×2000t) to fit per-command timeouts — roughly 20 minutes of engine
time not anticipated as a Step 7 sub-task by the plan text, but a necessary precondition for the
scan the plan itself calls for.

**Step 7 — actual reconciled/unreconciled counts vs. the plan's estimates.** The real scan
surfaced 61 pillar-level score-tolerance diffs across 76 anchors (0 band-level regressions — all
within ±1 letter, only the separate score-tolerance check caught them). 41 of 61 (39 unique
anchors, all COGNITION) mechanically reconciled against the corrected weight substitution
(verified per-event via each anchor's `quality_scores.jsonl`, not just spot-checked) and were
re-anchored. This is below investigation's "up to 53 possibly at risk" ceiling (COGNITION+ECONOMY
event-exercised anchors), consistent with investigation's own caveat that not every possibly-at-risk
anchor actually drifts outside tolerance. 20 of 61 diffs (14 anchors) did not reconcile and were
carved out to a new follow-up ticket, `TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP` — this
matches the plan's own anti-drift note anticipating this as a real possible outcome ("if more than
a handful of anchors fail to reconcile cleanly, that is itself a signal worth surfacing loudly").
Investigation into *why* these 14 don't reconcile (cross-referencing the closed
`TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM` ticket's F6 root cause) went one step further
than the plan's literal instruction ("do not investigate further") purely to give the follow-up
ticket a well-founded working hypothesis to start from — no code or config change resulted from
that cross-reference, and no anchor was reconciled or re-anchored based on it.

**Step 7 — `pytest tests/simulation_quality/test_grade_regression.py -v` is not fully green at
ticket close**, contrary to the plan's literal Step 7 Verify clause. 67/81 tests pass; 14 fail,
corresponding exactly to the 14 carved-out anchors named above and in the ticket's Implementation
Notes. The plan's Verify clause was written before the scan's real output was known; per Design
Decision #3's own governing instruction ("any anchor whose diff does NOT reconcile cleanly ... is
explicitly named and carved out ... instead of being force-fit into this diff or silently left
uncommitted"), force-reconciling these 14 to make the suite green would have violated the
Scope Guards (no weight retuning, no silent investigation-and-fix beyond what reconciles). The
ticket's Test Summary states the true 67/14 result rather than a fabricated fully-green result.
