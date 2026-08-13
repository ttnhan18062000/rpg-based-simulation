---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260813-OBSERVABILITY-IMPORT-BOUNDARY-STALE-OR-VIOLATED
phase: done
date: 2026-08-13
tags: [observability, documentation]
---

# TCK-20260813-OBSERVABILITY-IMPORT-BOUNDARY-STALE-OR-VIOLATED

## Title
`docs/guides/observability.md`'s stated import boundary ("`src/observability/` must never import
from `src/engine/`, `src/domains/`, `src/systems/`") is contradicted by `event_shapers.py`'s real
imports, and no existing architecture test enforces the doc's stated rule

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found incidentally during `TCK-20260812-EVENT-TYPE-COVERAGE-SOURCE-COLUMN-STALENESS`'s
Document-Update phase, while correcting `docs/guides/observability.md`'s stale description of
`event_extractor.py` vs. `event_shapers.py` as the live event-derivation path.

`docs/guides/observability.md:185` states: **"Architecture boundary: `src/observability/` must
never import from `src/engine/`, `src/domains/`, or `src/systems/`."**

Direct read of `src/observability/event_shapers.py`'s import block confirms 3 real, unconditional,
top-level imports that appear to violate this stated rule:
- `src/observability/event_shapers.py:25` — `from src.domains.world_emergence.schema import
  WorldEventCategory`
- `src/observability/event_shapers.py:34` — `from src.domains.commitment.abandonment import
  AbandonmentEvaluator, AbandonmentCategory`
- `src/observability/event_shapers.py:35` — `from src.systems.strategic_systems.intelligence
  import _MAX_CONSECUTIVE_REJECTIONS`

Confirmed the existing architecture-boundary tests do **not** catch this: ran
`tests/architecture/test_phase19_observability_boundaries.py` and
`tests/architecture/test_phase18_import_boundaries.py` — both pass (3/3), but neither test asserts
the specific rule the doc states. `test_phase19_observability_boundaries.py`'s
`test_hot_path_does_not_import_heavy_analyzers` checks a narrower, different rule (hot-path modules
must not import heavy analyzer submodules like `observability.anomaly`/`observability.cognition`/
`observability.reporting`) — it says nothing about `src/engine/`, `src/domains/`, or
`src/systems/`. No other test found (via the same sweep) enforces the doc's stated blanket rule.

This means one of two things is true, and this ticket's job is to determine which:
1. The doc is stale/wrong — the real, intentional rule is narrower than stated (e.g. only certain
   `src/observability/` submodules are hot-path-restricted, and `event_shapers.py` was always meant
   to import from `src/domains/`/`src/systems/` for its push-shaper derivation logic) — in which
   case the doc needs correcting, not the code.
2. The doc is correct and `event_shapers.py`'s imports are a genuine, real architecture-boundary
   violation introduced at some point during the push-shaper migration epic (`TCK-20260806-PUSH-
   CUTOVER-COMBAT-ECONOMY-FACTION` and its siblings) — in which case either the imports need to be
   refactored out (e.g. via dependency injection / a narrower shared module) or the doc's rule
   needs an explicit, documented exception with rationale.

## Scope
- Determine, with git-blame/history evidence, when and why `event_shapers.py` first imported from
  `src/domains/`/`src/systems/` — was this a deliberate, reviewed decision (check the relevant
  push-shaper migration tickets' own Architecture-Verify passes) or an unnoticed drift?
- Determine the doc's own original intent — check `docs/architecture/
  observability_behavior_profiling_boundary.md` (the doc `test_phase19_observability_boundaries.py`
  actually validates) for whether it states the same or a different boundary rule than
  `docs/guides/observability.md:185`.
- Resolve the discrepancy: either correct `docs/guides/observability.md`'s stated rule to match
  reality (if the imports are legitimate), or file/implement a real architecture fix (if they're
  not) — do not silently leave the doc and the code disagreeing.
- If a real code fix is warranted, that likely exceeds hotfix tier — reassess tier at Investigate
  time and escalate to standard if a genuine refactor is needed.

## Out of Scope
- Any other claim in `docs/guides/observability.md` beyond this one import-boundary line — the rest
  of the doc was already reviewed and corrected by `TCK-20260812-EVENT-TYPE-COVERAGE-SOURCE-COLUMN-
  STALENESS`'s Document-Update phase.
- Re-auditing every other `src/observability/` file for the same potential violation — this ticket
  is scoped to the one concrete finding (`event_shapers.py`'s 3 imports); if Investigate finds more,
  handle within this ticket's own scope since it's the same root question, but don't proactively
  expand before that.

## Acceptance Criteria
- [x] Root cause determined: is `docs/guides/observability.md:185`'s stated rule stale/wrong, or is
      `event_shapers.py`'s import genuinely a violation — with real evidence (git history, other
      docs, existing test intent), not assumed. **Both, in different ways** — see Implementation
      Notes: the `src/domains/`/`src/systems/` half of the rule was stale from inception (same
      commit `6e25d4f2` introduced both the doc line and the contradicting imports); the
      `src/engine/` half was a real, genuine violation of an already-established precedent
      (`TCK-20260627-P2G-KERNEL-FACADE`), found in 3 call sites once the guard test surfaced them.
- [x] Resolved consistently: either the doc is corrected to state the real rule, or the code is
      fixed to comply with a real rule, or an explicit documented exception is added — not left
      contradicting itself. Doc corrected (`docs/guides/observability.md:185`) to state the real,
      evidence-based rule; code fixed (3 `src/engine/` internal imports rerouted through 2 new
      `Kernel` facade methods, mirroring the existing `get_world_indexes()` precedent exactly).
- [x] If a real architecture test gap exists (no test enforces whatever the true rule turns out to
      be), a decision is made and recorded on whether to add one (may be out of this ticket's own
      scope if it requires new test infrastructure — file a further follow-up if so, don't leave it
      silently unstated). Two new tests added to
      `tests/architecture/test_phase18_import_boundaries.py` — no new test infrastructure was
      needed (same file-content-grep style as the existing `test_entity_models_do_not_import_
      domain_services`), so no follow-up ticket required.

## Related Tickets
- TCK-20260812-EVENT-TYPE-COVERAGE-SOURCE-COLUMN-STALENESS (the ticket whose Document-Update phase
  found this while correcting an unrelated staleness in the same doc)

## Related Docs
- docs/guides/observability.md (line 185, the stated rule)
- docs/architecture/observability_behavior_profiling_boundary.md (the doc the existing test
  actually validates — check whether it states a matching or different rule)

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/observability/event_shapers.py (lines 25, 34, 35 — the 3 originally-flagged imports;
  plus a 4th Kernel-facade violation found during Implement, line 1256)
- src/observability/event_extractor.py (Kernel-facade violation found during Implement, line 1403)
- src/observability/hard_law_monitor.py (Kernel-facade violation found during Implement, line 151)
- src/engine/kernel.py (2 new facade methods added: get_building_region, verify_occupancy_legal)
- tests/architecture/test_phase19_observability_boundaries.py
- tests/architecture/test_phase18_import_boundaries.py (2 new tests added)

## Assumptions / Open Questions
- Whether this is a doc-staleness issue (hotfix-appropriate) or a real architecture violation
  requiring a code refactor (likely standard-tier) is not yet known — Investigate must determine
  this before Plan/Implement proceeds, and the tier should be reassessed accordingly rather than
  forced into hotfix if a real refactor turns out to be needed.

## Implementation Notes

**Root cause (git-history evidence):** `docs/guides/observability.md:185`'s "Architecture
boundary" line and `src/observability/event_extractor.py`'s imports from
`src.domains.commitment.abandonment`, `src.domains.world_emergence.schema`, and
`src.systems.strategic_systems.intelligence` were introduced in the **same commit** (`6e25d4f2`,
2026-07-02). The doc's "must never import from `src/domains/`/`src/systems/`" claim was false
from the moment it was written — not later drift introduced by the push-shaper migration epic as
the ticket's own Request Summary speculated. `event_shapers.py` (created later, batch commit
`11b83f37`) simply continued the same established pattern. All 4 domains/systems symbols involved
are pure/read-only, confirmed by direct read of each definition: `WorldEventCategory` (plain
`str, Enum`, no logic); `AbandonmentEvaluator`/`AbandonmentCategory` (a `@staticmethod`
classifying primitive inputs into a frozen dataclass, no state access — its own docstring makes
no explicit non-mutation claim, but none is needed given the pure-function shape);
`_MAX_CONSECUTIVE_REJECTIONS` (plain `int` constant); `CognitionGraphExporter` (the only one of
the 4 whose docstring explicitly says "Does NOT mutate any state. Does NOT serve as source of
truth" — all 4 are pure by construction on inspection, but only this one carries that literal
phrasing; corrected here after Architecture-Verify flagged the earlier overstated citation).

The `src/engine/` half of the doc's rule is different: `TCK-20260627-P2G-KERNEL-FACADE`
(also closed in the same `6e25d4f2` commit) established a real, reviewed precedent — route
`src/engine/` dependencies through the `Kernel` facade (`Kernel.get_world_indexes()`), never
import a lower-level engine internal (e.g. `WorldIndexService`) directly. Building the guard
test this ticket's own AC3 required surfaced 3 genuine, later violations of that exact
precedent that a manual `grep -rn "^from src\.engine"` pass had missed (they're indented/lazy
imports inside function bodies, not top-of-file):
- `src/observability/event_extractor.py:1403` — `SpatialQueryService` (added `caf8aa90`,
  2026-07-08, 6 days after the Kernel-facade precedent was established)
- `src/observability/event_shapers.py:1256` — same `SpatialQueryService` pattern
- `src/observability/hard_law_monitor.py:151` — `LegalityServiceV2` (added `46c5ae59`,
  2026-07-16) — in the same file `TCK-20260627-P2G-KERNEL-FACADE` had already fixed for a
  different internal (`WorldIndexService`)

Per this ticket's Out-of-Scope clause ("if Investigate finds more, handle within this ticket's
own scope since it's the same root question, but don't proactively expand before that") — these
were found as a direct byproduct of testing the exact rule this ticket investigates, not from
proactively re-auditing unrelated files, so fixed in-scope rather than deferred. All three fixes
are small and mechanical (add one `Kernel` static delegation method + swap one call-site import),
identical in shape and risk to the already-hotfix-tier `TCK-20260627-P2G-KERNEL-FACADE` precedent
— no tier escalation warranted.

**Fix:**
1. Added `Kernel.get_building_region(state, building_id)` and
   `Kernel.verify_occupancy_legal(pos, state, ignore_entity_id=None)` to `src/engine/kernel.py`,
   both static methods mirroring `get_world_indexes()`'s exact shape (lazy internal import,
   one-line delegation, docstring explaining the facade rationale).
2. Rerouted all 3 call sites (`event_extractor.py:1403`, `event_shapers.py:1256`,
   `hard_law_monitor.py:151`) to call the new `Kernel` methods instead of importing
   `SpatialQueryService`/`LegalityServiceV2` directly. `hard_law_monitor.py` already had a
   module-level `Kernel` import, so its local (now-redundant) import was removed rather than
   duplicated. No behavior change — pure import-boundary refactor, confirmed by full test suite
   pass.
3. Corrected `docs/guides/observability.md:185`'s Architecture boundary note to state the real,
   evidence-based rule: `src/engine/` must route through `Kernel`; `src/domains/`/`src/systems/`
   may use a small pinned allowlist of pure/stateless symbols for read-only classification;
   hot-path heavy-analyzer restrictions are separately enforced by the existing
   `test_phase19_observability_boundaries.py` test.
4. Added 2 new tests to `tests/architecture/test_phase18_import_boundaries.py`:
   `test_observability_engine_imports_go_through_kernel_facade` (asserts every `src/observability/`
   `src.engine` import is exactly `from src.engine.kernel import Kernel`) and
   `test_observability_domains_systems_import_allowlist` (pins the exact 4-symbol,
   3-file allowlist; any new import outside it fails the test, forcing a deliberate doc+test
   update rather than silent expansion).

No new architecture-test infrastructure was needed — both tests follow the exact file-content-grep
style already established by `test_entity_models_do_not_import_domain_services` in the same file,
so AC3's "may be out of scope, file a follow-up if so" branch did not apply.

## Test Summary

- `pytest tests/architecture/test_phase18_import_boundaries.py tests/architecture/
  test_phase19_observability_boundaries.py -v -m "not slow"` → 5 passed (both new guard tests
  included; confirmed they fail against the pre-fix state — verified during Implement before the
  code fix landed — and pass after)
- `pytest tests/architecture/ tests/unit/observability/ tests/engine/ -q -m "not slow"` → 1082
  passed, 6 skipped (pre-existing, unrelated), 0 failed — full regression sweep across every test
  file touching the 4 changed production files
- `pytest tests/engine/test_hard_law_monitor.py -q -m "not slow"` → 12 passed
- `pytest tests/unit/observability/test_event_shapers_world_dynamics.py tests/simulation_quality/
  test_world_dynamics_scorer.py -q -m "not slow" -k "sabotag"` → 4 passed (the specific
  `building_sabotaged` event path both rerouted call sites feed)
- Direct import smoke test: `Kernel.get_building_region`/`Kernel.verify_occupancy_legal`/
  `Kernel.get_world_indexes` all present and importable post-change

## Files Changed

- `docs/guides/observability.md` — corrected the Architecture boundary note (line 185 area) to
  state the real, evidence-based import rule
- `src/engine/kernel.py` — added `Kernel.get_building_region()` and
  `Kernel.verify_occupancy_legal()` static facade methods
- `src/observability/event_extractor.py` — rerouted `SpatialQueryService` import through `Kernel`
- `src/observability/event_shapers.py` — rerouted `SpatialQueryService` import through `Kernel`;
  updated one docstring reference to match
- `src/observability/hard_law_monitor.py` — rerouted `LegalityServiceV2` import through the
  already-present module-level `Kernel` import (removed now-redundant local import)
- `tests/architecture/test_phase18_import_boundaries.py` — added
  `test_observability_engine_imports_go_through_kernel_facade` and
  `test_observability_domains_systems_import_allowlist`

## Completion Summary

Root-caused the doc/code disagreement to two distinct mechanisms: the `src/domains/`/`src/systems/`
half of the doc's stated rule was false from the moment it was written (same commit introduced
both), so corrected the doc to describe the real, always-practiced pattern (a small pinned
allowlist of pure/stateless symbols). The `src/engine/` half was a real violation of an
already-established, reviewed facade precedent (`TCK-20260627-P2G-KERNEL-FACADE`) — found 3
genuine instances via the guard test this ticket's own AC3 required, fixed all 3 with the same
mechanical Kernel-facade-delegation pattern the precedent already established, no behavior change.
Added 2 new architecture tests pinning both halves of the corrected rule so this can't silently
drift again. No tier escalation needed — all fixes were small, mechanical, low-risk, matching the
precedent ticket's own hotfix-tier shape.
