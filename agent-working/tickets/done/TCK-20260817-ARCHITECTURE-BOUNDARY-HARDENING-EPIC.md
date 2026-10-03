---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC
phase: done
date: 2026-08-17
tags: [testing, architecture]
---

# TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC

## Title
Upgrade weak substring-based import-boundary tests to AST; add missing domains/systems boundaries

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
Two architecture boundary tests (`test_api_read_model_guard.py`, `test_phase_domain_permissions.py`)
are genuinely strong, AST-based checks. Two more
(`test_phase18_import_boundaries.py`, `test_phase19_observability_boundaries.py`) are plain
substring-grep checks, defeatable via `importlib`, aliasing, or an indirect import chain. No
boundary test exists at all for `domains ↛ observability` or `systems ↛ engine` internals. The
fix reuses a pattern already proven in this repo — no new technique to introduce.

## Scope
Full findings are in `docs/plans/architecture_boundary_hardening_epic.md`. Concrete scope, all
reusing the AST-visitor pattern `test_api_read_model_guard.py`/`test_phase_domain_permissions.py`
already establish:
- Rewrite `test_phase18_import_boundaries.py` and `test_phase19_observability_boundaries.py` from
  substring-grep to AST inspection.
- Add the two missing boundary tests: `domains ↛ observability` internals, `systems ↛ engine`
  internals.
- Lower priority within this ticket: a Tier-3→Tier-0 `docker-compose.yml` startup-dependency
  linter (motivated by Epic A's RabbitMQ finding) — a compose-file concern needing a different
  mechanism than an architecture test.

## Out of Scope
- Building a general machine-readable subsystem-ownership manifest for all 38 `src/` packages —
  a larger initiative than hardening 4 existing/missing boundary tests.
- The Tier-3→Tier-0 `docker-compose.yml` startup-dependency linter — a compose-file concern
  motivated by a different epic's finding (Epic A), needs a different mechanism, lower priority
  within this epic.

## Acceptance Criteria
- [x] The two weak boundary tests use AST inspection, not substring matching.
- [x] `domains ↛ observability` and `systems ↛ engine` each have an enforced boundary test.
- [x] Each new/upgraded test is confirmed to actually fail against a deliberately-introduced
      violation (not just pass trivially because nothing violates it yet).

## Related Tickets
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic)
- TCK-20260817-DEAD-INFRA-REMOVAL-EPIC (motivates this epic's lower-priority compose-linter item)

## Related Docs
- docs/plans/architecture_boundary_hardening_epic.md
- docs/plans/architecture_resilience_remediation_roadmap.md
- docs/audits/D24_codebase_health_observatory.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- tests/architecture/test_api_read_model_guard.py
- tests/architecture/test_phase_domain_permissions.py
- tests/architecture/test_phase18_import_boundaries.py
- tests/architecture/test_phase19_observability_boundaries.py

## Assumptions / Open Questions
- Whether `domains ↛ observability` or `systems ↛ engine` violations currently exist wasn't
  checked in either source audit — this affects whether the new tests start red or green, and
  needs confirming before implementation.
- **Downgraded from epic to standard tier (2026-08-18):** one of 10 sub-epics under
  `TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC`; four items mechanically reusing one already-
  proven in-repo pattern against a handful of test files — cohesive, one standard ticket.
  `staging_artifacts/TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC/` not yet created.

## Implementation Notes
Followed `staging_artifacts/TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC/plan.md`'s 8 steps
in order.

- **Steps 1-3** (`tests/architecture/test_phase18_import_boundaries.py`): added a module-level
  `_type_checking_lines(tree) -> set[int]` helper (mirrors
  `test_api_read_model_guard.py:40-51`'s technique) and rewrote
  `test_entity_models_do_not_import_domain_services`,
  `test_observability_engine_imports_go_through_kernel_facade`, and
  `test_observability_domains_systems_import_allowlist` from raw-text substring matching to
  `ast.parse` + `ast.walk` over `Import`/`ImportFrom` nodes, skipping any node whose `lineno` falls
  inside a `TYPE_CHECKING` block. The Kernel-facade test now asserts on `node.module`/`node.names`
  identity (module `== "src.engine.kernel"`, single unaliased `Kernel` name) instead of exact-line
  string equality. The domains/systems allowlist test keeps its existing 4-entry pinned set
  unchanged, matched via `(module, sorted names-as-written)` tuples instead of exact import
  strings.
- **Step 4**: added `test_domains_do_not_import_observability_outside_pinned_exceptions`. Re-read
  both pinned sites directly against current source before pinning (per instruction) —
  `src/domains/campaigns/narrative_ledger.py:71` and `orchestrator.py:319` — both unchanged from
  investigation.md/plan.md, both still `from src.observability.events import SimulationEvent`.
  Neither production file was touched.
- **Step 5**: added `test_systems_do_not_import_engine_outside_pinned_exceptions`, 13 pinned
  `(file, lineno) -> (module, names-as-written)` entries across `intelligence.py` (9 sites),
  `detour.py`, `redirection.py`, `market.py`, `routine.py`. Re-confirmed all 13 by direct
  `grep -rn "src\.engine" src/systems/` plus targeted reads — every line number matched plan.md
  exactly, including the aliased `SystemCadence as DefaultCadence` on lines 833/905, and
  `intelligence.py:62`'s `SystemCadence` import correctly excluded by `_type_checking_lines`
  before the pinned-dict check runs (verified: it never reaches the assertion). No production
  file touched.
- **Step 6** (`tests/architecture/test_phase19_observability_boundaries.py`): added a duplicated,
  file-local `_type_checking_lines` helper (per Scope Guards — no shared cross-file utility
  module) and rewrote `test_hot_path_does_not_import_heavy_analyzers` to AST inspection.
  `test_observability_boundaries_doc_exists` untouched. **Deviation found and resolved here — see
  plan.md's Deviations section and below.**
- **Step 7**: manually verified all 6 upgraded/new tests actually fail against a
  deliberately-introduced violation, then reverted with `git checkout -- <file>` (fixtures never
  committed): (a) `import src.domains.campaigns.state` in `src/core/actions.py`; (b)
  `from src.engine.spatial_query import SpatialQueryService` in
  `src/observability/entity_timeline.py`; (c) `from src.domains.campaigns.state import
  CampaignState` in `src/observability/config.py`; (d) `from src.observability.events import
  SimulationEvent` in `src/domains/campaigns/behavior_change.py`; (e) `from src.engine.legality
  import LegalityServiceV2` in `src/systems/economy_systems/chests.py`; (f) `import
  observability.anomaly` in `src/engine/apply_plan.py`. All 6 reproduced a failure, all 6 fixture
  edits reverted cleanly (`git status --short` empty on each file afterward). Full sweep:
  `.venv/bin/python3 -m pytest tests/architecture/ -q -m "not slow"` → 66 passed, 0 failed
  (64 existing + 2 new, matching plan.md's expectation exactly).
- **Step 8**: updated `docs/audits/D14_coupling_depth.md` (added a `systems` row to the Layer
  Architecture diagram, worded per architecture review's caveat as "13 sites grandfathered as
  pinned exceptions, no new violations permitted" rather than a clean-boundary claim; added two
  new Coupling Inventory subsections for `domains → observability` and `systems → engine` mirroring
  the existing `core` upward-dependency table's format), `docs/plans/architecture_boundary_hardening_epic.md`
  (added `## Status` section recording resolution, matching sibling epics' pattern in
  `docs/plans/dead_infra_removal_epic.md`), and `docs/audits/D24_codebase_health_observatory.md`
  (§K: moved the two upgraded tests out of "substring-based (weak — upgrade candidates)" and the
  two new boundaries out of "Proposed, not yet enforced," into "Already enforced, hard invariant,
  AST-based (strong)"). Ran `make knowledge-index-update` (3 files re-embedded) and `graphify
  update .` (no topology changes) per project convention since `docs/` files changed.

**Deviation (documented in full in plan.md's Deviations section):** Step 6's literal AST rewrite
(matching each import's resolved module string, e.g. `src.observability.reporting...`, against the
3 forbidden substrings) surfaced that the *old* substring-grep test was silently vacuous — its
`f"from {forbidden}"` check required the bare, un-prefixed form `"observability.anomaly"` with no
`src.` prefix, which never matches this codebase's real `from src.observability.anomaly...` import
style. A `src.`-aware match correctly catches 5 real, currently-shipping violations in
`src/engine/kernel.py` (lines 129, 277, 278, 289, 1111 — lazy imports of
`observability.reporting`/`.cognition` submodules), none of which are named in this ticket's Scope
Guards, pinned-exception lists, or Related Code Areas. Per instruction not to silently work around
a discovered conflict, and not authorized to either invent a new unreviewed pinned-exception list
for `kernel.py` or refactor production code outside this ticket's test-tooling-only scope, the
implementation preserves the *old* test's literal real-world matching behavior (bare-prefix
`startswith`, not `src.`-aware) so the rewritten test stays semantically equivalent to what it
already enforced (AC1's "not a change in which imports are forbidden"). The 5 real `kernel.py`
violations remain live and undetected by any test after this ticket — flagged here and in plan.md
as a recommended follow-up ticket, not fixed or hidden.

## Test Summary
`.venv/bin/python3 -m pytest tests/architecture/ -q -m "not slow"` → **66 passed, 0 failed**
(baseline was 64; +2 for the new `domains ↛ observability` / `systems ↛ engine` tests). All 6
upgraded/new tests individually verified to fail against a deliberately-introduced, then-reverted
violation (AC3) — see Implementation Notes Step 7 for the exact 6 fixture edits and results. No
other test suite scoped or run — this ticket touches only `tests/architecture/` and `docs/`.

## Files Changed
- `tests/architecture/test_phase18_import_boundaries.py` — rewrote 3 existing tests to AST, added
  2 new pinned-exception boundary tests, added shared `_type_checking_lines`/`_iter_py_files`/
  `_parse`/`_names_as_written` helpers.
- `tests/architecture/test_phase19_observability_boundaries.py` — rewrote
  `test_hot_path_does_not_import_heavy_analyzers` to AST, added a file-local
  `_type_checking_lines` helper; `test_observability_boundaries_doc_exists` unmodified.
- `docs/audits/D14_coupling_depth.md` — added `systems` row to Layer Architecture diagram; added
  "Layer: `src/domains/` — upward dependency into `src/observability/`" and "Layer:
  `src/systems/` — upward dependency into `src/engine/`" subsections to Coupling Inventory.
- `docs/plans/architecture_boundary_hardening_epic.md` — added `## Status` section recording
  resolution.
- `docs/audits/D24_codebase_health_observatory.md` — §K: moved upgraded/new tests from
  "weak"/"proposed" into "Already enforced ... AST-based (strong)"; also annotated the
  pre-existing §A/§E/§H passages that described the pre-fix substring-grep state as point-in-time
  history, and added a §K "Proposed, not yet enforced" bullet recording the `kernel.py` finding.
- `docs/plans/architecture_resilience_remediation_roadmap.md` — added a "Status: Resolved" block
  to Epic G, matching the precedent already set for Epics A/B/E in the same file.
- `tickets/inprogress/TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC.md` — this file (Status,
  Acceptance Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary).
- `staging_artifacts/TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC/plan.md` — added
  Deviations section documenting the Step 6 `kernel.py` finding.
- `staging_artifacts/TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC/investigation.md` —
  written during the Investigate phase (pre-existing part of this run, not a later edit).
- `staging_artifacts/TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC/test_plan.md` — written
  during the Investigate phase (pre-existing part of this run, not a later edit).

No `src/domains/`, `src/systems/`, or `src/engine/` production file was modified — all 6 negative
verification-case edits (Step 7) were temporary, run-and-reverted, and confirmed clean via
`git status --short` on each touched file.

## Completion Summary
Rewrote the two substring-grep import-boundary test files
(`test_phase18_import_boundaries.py`, `test_phase19_observability_boundaries.py`) to AST-based
inspection using the `if TYPE_CHECKING:` line-range-exclusion technique already proven in
`test_api_read_model_guard.py`, and added two new AST-based boundary tests
(`domains ↛ observability`, `systems ↛ engine`) that pin the 2 and 13 currently-real violation
sites respectively as exact `(file, lineno, module, names)` grandfathered exceptions — a
freeze-at-baseline, not a claim that either boundary is now cleanly honored. No production
`src/domains/`, `src/systems/`, or other file was refactored; this ticket is test-tooling only.
All 6 upgraded/new tests were manually confirmed to fail against a deliberately-introduced,
reverted violation (AC3), and the full `tests/architecture/` sweep is 66 passed / 0 failed. Docs
(`D14_coupling_depth.md`, the epic tracking doc, `D24_codebase_health_observatory.md`) were
updated to record the resolution. One out-of-scope discovery was made and is documented rather
than silently fixed or hidden: the literal AST-correct version of Step 6's rewrite would also
catch 5 real, previously-undetected `src/engine/kernel.py` imports of heavy observability
analyzers, which the old (buggy) substring test never caught due to a missing `src.` prefix in
its own forbidden-string pattern; this implementation preserves the old test's literal matching
behavior to stay within this ticket's approved scope and flags the finding for a follow-up
ticket.
