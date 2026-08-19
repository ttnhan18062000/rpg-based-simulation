---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC
artifact_type: test_plan
tags: [testing, architecture]
---

# Test Plan — TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC

## Regression Surface

All existing tests below currently pass under the project venv
(`.venv/bin/python3 -m pytest tests/architecture/ -q -m "not slow"` → 64 passed; system Python 3
lacks `pydantic` and cannot run this repo's tests at all — always invoke via `.venv/bin/python3`).

**Architecture (must stay green through the rewrite — these are the direct blast radius):**
- `tests/architecture/test_phase18_import_boundaries.py` — all 3 tests (being rewritten to AST;
  the underlying rule each test enforces today must still hold after rewrite, only the mechanism
  changes)
- `tests/architecture/test_phase19_observability_boundaries.py` — both tests (only
  `test_hot_path_does_not_import_heavy_analyzers` is being rewritten; `test_observability_
  boundaries_doc_exists` is untouched and must keep passing unmodified)
- `tests/architecture/test_api_read_model_guard.py` — the AST-visitor pattern being mirrored; not
  modified, but re-run to confirm the mirrored technique wasn't accidentally coupled to something
  API-specific
- `tests/architecture/test_phase_domain_permissions.py` — same, reference pattern only
- Everything else under `tests/architecture/` (`test_docker_compose_dependency_hygiene.py`,
  `test_phase18_cognition_migration_linter.py`, `test_legacy_enum_usage_boundaries.py`, etc.) —
  full-directory sweep to catch any accidental collateral damage from editing shared test-file
  scaffolding

**Unit — only if Plan chooses the facade-routing or import-refactor option for the currently-real
`systems ↛ engine` / `domains ↛ observability` violations found during Investigate (see
investigation.md Risks — otherwise these are unaffected and only need a smoke pass):**
- `tests/unit/campaigns/test_narrative_ledger.py`, `test_campaign_orchestrator.py`,
  `test_orchestrator_plan_wiring.py` — cover `narrative_ledger.py`/`orchestrator.py`, the 2 real
  `domains → observability` call sites
- `tests/unit/strategic/test_strategic_cognition_regression.py`,
  `test_detour_suggestion.py`, `test_strategic_detour_ph6.py`, `test_routine_biasing.py`,
  `test_anti_thrashing.py` — cover `intelligence.py`/`detour.py`/`redirection.py`, the bulk of the
  real `systems → engine` call sites
- `tests/unit/world/test_economy_contract.py`, `tests/unit/resource/test_economy_hardening.py` —
  cover `market.py`'s engine coupling
- No dedicated test file was found by name for `src/systems/world_systems/routine.py`'s specific
  `LegalityServiceV2` call site — if that file's import is touched, confirm coverage indirectly via
  whichever integration/kernel suite exercises `RoutineService` before relying on unit tests alone.

## New Tests Required

Per AC1 ("weak tests use AST inspection, not substring matching") and AC2 ("`domains ↛
observability` and `systems ↛ engine` each have an enforced boundary test") — exact enforcement
semantics (zero-tolerance vs. pinned-allowlist vs. facade-routing) are a Plan-phase decision per
investigation.md's flagged open question; the test shapes below assume whichever choice is made,
built on the `test_api_read_model_guard.py` AST-visitor technique (parse tree, collect
`TYPE_CHECKING`-guarded line ranges, walk `Import`/`ImportFrom` nodes, skip lines inside those
ranges, flag/allowlist-check the rest).

1. **AST rewrite of `test_entity_models_do_not_import_domain_services`** (`core ↛ domains`)
   - Category: architecture guard
   - Verifies: no file under `src/core/` has a real (non-`TYPE_CHECKING`) `Import`/`ImportFrom`
     node targeting `src.domains` or any submodule — same rule as today, AST-enforced instead of
     substring-matched
   - Location: `tests/architecture/test_phase18_import_boundaries.py` (in place, or split to a new
     file if Plan decides the AST rewrite warrants separating the 3 unrelated rules currently
     co-located in one file — not required by the AC, a Plan-phase call)

2. **AST rewrite of `test_observability_engine_imports_go_through_kernel_facade`**
   - Category: architecture guard
   - Verifies: every real `src.engine` import under `src/observability/` is exactly `from
     src.engine.kernel import Kernel` (AST node comparison instead of per-line string equality)
   - Location: same file, in place

3. **AST rewrite of `test_observability_domains_systems_import_allowlist`**
   - Category: architecture guard
   - Verifies: every real `src.domains`/`src.systems` import under `src/observability/` is both
     in an allowlisted file and matches the pinned allowlist of import statements, via AST instead
     of per-line string matching
   - Location: same file, in place

4. **AST rewrite of `test_hot_path_does_not_import_heavy_analyzers`**
   - Category: architecture guard
   - Verifies: no real import under the hot-path file set imports
     `observability.anomaly`/`observability.cognition`/`observability.reporting`, via AST
     `ImportFrom.module`/alias inspection instead of `f"import {forbidden}" in content` substring
     matching (which today can false-positive on a matching comment/docstring/string literal, and
     false-negative on an aliased or indirect import)
   - Location: `tests/architecture/test_phase19_observability_boundaries.py`, in place

5. **New: `domains ↛ observability` boundary test**
   - Category: architecture guard
   - Verifies: no file under `src/domains/` has a real `Import`/`ImportFrom` node targeting
     `src.observability` outside `TYPE_CHECKING`, except whatever Plan decides for the 2 confirmed
     real call sites (`narrative_ledger.py:71`, `orchestrator.py:319`, both importing
     `SimulationEvent`) — either a pinned allowlist entry for exactly those, or a facade
     abstraction if Plan chooses that route
   - Location: `tests/architecture/test_phase18_import_boundaries.py` (co-locate with the other
     import-direction tests) or a new `tests/architecture/test_domains_observability_boundary.py`
     if Plan prefers a dedicated file — either satisfies AC2, which only requires the test exist
     and be enforced

6. **New: `systems ↛ engine` boundary test**
   - Category: architecture guard
   - Verifies: no file under `src/systems/` has a real `Import`/`ImportFrom` node targeting
     `src.engine` outside `TYPE_CHECKING`, except whatever Plan decides for the confirmed real
     call sites in `intelligence.py`, `detour.py`, `redirection.py`, `market.py`, `routine.py`
     (13+ real import statements across 5 files — see investigation.md) — this is the test most
     likely to need a pinned-allowlist or facade design given the current violation count, not a
     small tweak
   - Location: same as #5

7. **Negative-case tests confirming AC3** ("confirmed to actually fail against a
   deliberately-introduced violation, not just pass trivially")
   - Category: architecture guard (meta-test / self-test of the guard tests)
   - Verifies: temporarily writing a disallowed import into a scratch fixture file (or monkeypatching
     the scanned-file list to include a small fixture module with a deliberate violation) causes
     the relevant AST test's assertion to fail — this should be run manually during Implement (per
     AC3's own wording) rather than committed as a permanent pytest test, unless Plan chooses to
     keep it as a permanent fixture-based regression test. If kept permanent: a small
     `tests/architecture/fixtures/` violation fixture per boundary, with the test asserting the
     scanner correctly flags it. Confirm this was actually run against the pre-fix (substring)
     versions too where applicable, matching how `TCK-20260813` verified its own new tests failed
     pre-fix and passed post-fix (see that ticket's Test Summary).

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest tests/architecture/ -q -m "not slow"
```

If Plan's chosen resolution for the open question touches any of the 7 production files found
during Investigate (`src/domains/campaigns/narrative_ledger.py`, `orchestrator.py`,
`src/systems/strategic_systems/intelligence.py`, `detour.py`, `redirection.py`,
`src/systems/economy_systems/market.py`, `src/systems/world_systems/routine.py`), add:

```
.venv/bin/python3 -m pytest tests/unit/campaigns/ tests/unit/strategic/ tests/unit/world/ tests/unit/resource/ -q -m "not slow"
```

Never `pytest tests/` unscoped. System Python 3 (no venv prefix) fails at collection
(`ModuleNotFoundError: No module named 'pydantic'`) — always invoke via `.venv/bin/python3 -m
pytest`.

## Anti-Drift Test Guards

- A guard asserting `test_phase19_observability_boundaries.py::test_observability_boundaries_doc_exists`
  is unmodified in behavior (still doc-existence + term-presence, not folded into the import-AST
  rewrite) — catches scope creep of "upgrade to AST" accidentally touching the one test in that
  file that isn't an import check at all.
- A guard confirming the rewritten tests still recognize the exact same `TYPE_CHECKING`-guarded
  import lines as legitimate that the substring versions implicitly tolerated (`intelligence.py:62`,
  `redirection.py:5`, `market.py:4`, `consequence_events.py:38`, `narrative_ledger.py:23`,
  `orchestrator.py:26`) — catches an AST rewrite that's stricter than intended and produces false
  positives on legitimate type-only imports.
- If a pinned-allowlist is chosen for either new test, a guard that the allowlist is an *exact*
  import-string/AST-node match, not a prefix or substring match — catches silent allowlist
  loosening, consistent with `TCK-20260813`'s explicit "not a silent addition" requirement for the
  existing `test_observability_domains_systems_import_allowlist` allowlist it's modeled on.
- A guard that no *new* file outside the 5 already-identified `systems → engine` files or the 2
  already-identified `domains → observability` files appears in whatever allowlist/exception
  mechanism is chosen — catches scope creep where the boundary test is loosened to paper over an
  unrelated future violation instead of being extended deliberately.
- Full `tests/architecture/` sweep (not just the 2 touched files) after any change, since these
  tests are cheap, fast (64 tests in ~4s), and any accidental collateral edit to shared test
  scaffolding (imports, fixtures) in the same file would otherwise go unnoticed.
