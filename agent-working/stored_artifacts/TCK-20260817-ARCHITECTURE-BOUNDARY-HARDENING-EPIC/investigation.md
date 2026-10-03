---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC
artifact_type: investigation
tags: [testing, architecture]
---

# Investigation — TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC

## Current Behavior

**The two "strong" AST-based reference patterns to mirror:**

- `tests/architecture/test_api_read_model_guard.py:19-79` — `ast.parse()` on each `src/api/routes`,
  `src/api/ws`, `src/api/server.py` file; walks the tree to find `if TYPE_CHECKING:` blocks and
  records every line number inside them; then walks all `Import`/`ImportFrom` nodes, skips any
  whose `lineno` fell inside a `TYPE_CHECKING` block, and flags any remaining import of
  `AuthoritativeState`/`EntityState`. This is the exact "collect TYPE_CHECKING line ranges, then
  filter AST import nodes against them" technique the ticket's scope says to reuse.
- `tests/architecture/test_phase_domain_permissions.py:1-61` — a different shape: it doesn't parse
  source at all, it imports `src.engine.phase_domain_permissions`'s `PHASE_READ_DOMAINS` /
  `PHASE_WRITE_DOMAINS` / `PHASE_EMIT_DOMAINS` dict constants directly and asserts structural
  properties (frozenset type, RESOLUTION is the sole entity/world writer, etc.). This is a
  "validate a declared permissions table," not an import-scanner, pattern — useful context but not
  the AST-visitor technique itself.

**The two "weak" tests to upgrade (both plain substring/line-grep, confirmed by direct read):**

- `tests/architecture/test_phase18_import_boundaries.py` — 3 tests, all `os.walk` + raw string
  matching:
  - `test_entity_models_do_not_import_domain_services` (line 5): `assert "import src.domains" not
    in content` over every file under `src/core/`. No AST, no comment/string-literal exclusion,
    one directional pair (`core ↛ domains`).
  - `test_observability_engine_imports_go_through_kernel_facade` (line 18): per-line
    `.startswith("from src.engine")` check against `src/observability/`, requiring the line equal
    exactly `from src.engine.kernel import Kernel`.
  - `test_observability_domains_systems_import_allowlist` (line 44): per-line
    `.startswith("from src.domains")`/`"from src.systems"` check against `src/observability/`, with
    a pinned allowlist of 4 exact import strings across 3 files.
  - These last two were added by `TCK-20260813-OBSERVABILITY-IMPORT-BOUNDARY-STALE-OR-VIOLATED`
    (2026-08-13) — already line-substring-based, not the AST pattern this ticket's scope calls for,
    despite being newer than the `core ↛ domains` test.
- `tests/architecture/test_phase19_observability_boundaries.py` — 2 tests:
  - `test_observability_boundaries_doc_exists` (line 5): file-existence + lowercase substring check
    against `docs/architecture/observability_behavior_profiling_boundary.md`. Not an import check
    at all — out of scope for the AST rewrite (nothing in the ticket's AC or scope calls for
    touching this test).
  - `test_hot_path_does_not_import_heavy_analyzers` (line 28): `os.walk` over
    `src/engine/`, `src/observability/config.py`, `event_extractor.py`, `event_recorder.py`;
    `assert f"import {forbidden}" not in content` for 3 forbidden substrings
    (`observability.anomaly`/`.cognition`/`.reporting`). This is the actual "hot path ↛ heavy
    observability analyzers" test the ticket's scope means to upgrade.

**Ground truth on whether `domains ↛ observability` / `systems ↛ engine` violations currently
exist (the ticket's own stated open question — checked directly, not assumed):**

`domains ↛ observability` — 2 real runtime violations, both narrow and deliberate:
- `src/domains/campaigns/narrative_ledger.py:71` — `from src.observability.events import
  SimulationEvent  # local import avoids circular` inside a method body (not `TYPE_CHECKING`).
- `src/domains/campaigns/orchestrator.py:319` — `from src.observability.events import
  SimulationEvent` inside a method body, same shape, no comment but same "no-op when recorder is
  None" guard pattern immediately above it.
- (`narrative_ledger.py:23` and `orchestrator.py:26` also import `EventRecorder` from
  `src.observability.event_recorder`, but both are inside `if TYPE_CHECKING:` blocks — not real
  runtime imports, would not trip an AST-based check that excludes `TYPE_CHECKING` the way
  `test_api_read_model_guard.py` does.)
- Both real violations import the same symbol (`SimulationEvent`, a plain event dataclass
  constructor) for the same purpose (emit-if-recorder-present), both as lazy/local imports with
  circular-import avoidance as the stated or implied reason.

`systems ↛ engine` — substantially more real violations, across 5 files, both module-level and
lazy:
- `src/systems/strategic_systems/intelligence.py` — **module-level, real (not TYPE_CHECKING)**:
  line 69 `from src.engine.policy import GovernorPolicy`, line 75 `from src.engine.spatial_query
  import SpatialQueryService`, line 78 `from src.engine.cadence import should_run, SystemCadence`,
  line 83 `from src.engine.domain_logic import SimulationDomainLogic`. (Line 62's `SystemCadence`
  import is the only one actually inside `TYPE_CHECKING`.) Plus lazy/function-local real imports at
  lines 664, 829, 833, 905, 958 (`cadence.should_run`, `domain_logic.SimulationDomainLogic`,
  `cognition.AppraisalSystem`).
- `src/systems/strategic_systems/detour.py:22` — module-level, real: `from
  src.engine.domain.lead_routing import LeadRoutingSystem`.
- `src/systems/strategic_systems/redirection.py:23` — lazy, real: `from src.engine.cadence import
  should_run`.
- `src/systems/economy_systems/market.py:50` — lazy, real: `from src.engine.legality import
  LegalityServiceV2`.
- `src/systems/world_systems/routine.py:180` — lazy, real: `from src.engine.legality import
  LegalityServiceV2`.
- Adjacent context (not one of the two required pairs, but informs the pattern):
  `src/systems/social_systems/consequence_events.py` has a documented in-file convention
  ("Design constraints... MUST NOT import from src.engine or src.core.state at module level")
  that explicitly restricts only *module-level* engine imports and explicitly *permits* a
  module-level import from `src.observability.events` for shared event-type constants — i.e. the
  codebase already organically practices "TYPE_CHECKING + lazy-import engine access from systems,"
  it just isn't test-enforced.

This directly contradicts the epic plan's framing of "an enforcement gap, not a confirmed
violation" for `systems ↛ engine` — it is a confirmed, current, and non-trivial violation if the
new test means "systems must never import `src.engine`." See Risks below — this is the ticket's
central open question and blocks Plan.

## Mechanics / Engine Constraints

Not a mechanics-formula ticket — no `docs/mechanics/` chapter constrains this work. Relevant
engine/architecture constraints:

- `docs/audits/D14_coupling_depth.md`'s "Layer Architecture" diagram (lines 51-61) is the only
  documented, established dependency-flow rule in the repo:
  ```
  content ─────────────────────────────┐
  core  ────────────────────────────── │ (base types — imports nothing)
  domains ──────── → core only         │
  engine ─────────→ core + domains     │
  observability ──→ engine             │
  api ────────────→ engine + core      │
  lab ────────────→ engine             │
  ```
  `domains → core only` already implies `domains ↛ observability` as a documented (if never
  test-enforced) rule. **`src/systems/` does not appear anywhere in this diagram** — D14's own
  audit (2026-06-18) never assigned `src/systems/` a layer position, so `systems ↛ engine` has no
  prior documented rule at all, only the epic's own new proposal.
- `docs/engine/authoritative_mutation_pipeline_contract.md` and `authoritative_pipeline.md`: not
  directly implicated — this ticket is import-boundary tooling, not a mutation-path change.
- Established precedent for the *shape* of the fix when observability's own outbound boundary
  needed hardening: `TCK-20260627-P2G-KERNEL-FACADE` (route engine-internal access through
  `Kernel` facade methods) and `TCK-20260813-OBSERVABILITY-IMPORT-BOUNDARY-STALE-OR-VIOLATED`
  (pin a small allowlist of pure/stateless symbols for domains/systems access that couldn't be
  eliminated). Both are directly relevant precedent for how to resolve the `systems ↛ engine` /
  `domains ↛ observability` open question below — see Risks.

## Docs Requiring Update

- `docs/audits/D24_codebase_health_observatory.md`: §K "Architecture Fitness Functions" lists the
  two weak tests under "substring-based (weak — upgrade candidates)" and the two new boundaries
  under "Proposed, not yet enforced" — both lists must move once this ticket lands, so the audit
  doesn't keep describing already-fixed findings as open.
- `docs/plans/architecture_boundary_hardening_epic.md`: needs a `## Status` section recording
  resolution, matching the pattern already used by sibling epics A/B/E in
  `docs/plans/architecture_resilience_remediation_roadmap.md` (each got a "Status: Resolved by
  TCK-..." paragraph once implemented).
- `docs/audits/D14_coupling_depth.md`: its "Layer Architecture" diagram (lines 51-61) is the
  closest existing home for a `domains ↛ observability` rule statement and currently omits
  `src/systems/` entirely — whichever resolution the open question below gets (ban vs. pinned
  allowlist vs. facade-routing), the diagram and Coupling Inventory section should be extended to
  state it, the same way `docs/guides/observability.md:185`'s "Architecture boundary" note states
  the analogous rule for observability's outbound engine/domains/systems imports. Exact wording
  depends on the Plan-phase decision on the open question below — flagging the path, not
  prescribing content.

## Parity Ledger Overlap

None directly. Searched `docs/parity_ledger/` for any entry whose `test_path` references
`test_phase18_import_boundaries.py`, `test_phase19_observability_boundaries.py`,
`test_api_read_model_guard.py`, or `test_phase_domain_permissions.py` — only the two *strong*,
untouched reference tests have entries (`docs/parity_ledger/infrastructure.yaml`: INFRA-206/207/208
→ `test_phase_domain_permissions.py`, status `verified`, priority `P1`; INFRA-210 →
`test_api_read_model_guard.py`, status `verified`, priority `P1`). Neither is `P0`, and neither is
touched by this ticket's scope (upgrading the two weak tests, adding two new ones) — confirmed
these entries stay green by running `pytest tests/architecture/ -q -m "not slow"` under
`.venv/bin/python3` → 64 passed, 0 failed (system Python 3 lacks `pydantic`; use the project venv).
No new parity ledger entry is required unless the Plan phase decides the new tests should carry
one (optional — they're tooling/test-architecture, not a mechanics/pipeline behavior claim, similar
to how the two existing weak tests never got their own parity entries either).

## Prior Work

- `TCK-20260813-OBSERVABILITY-IMPORT-BOUNDARY-STALE-OR-VIOLATED` (done, hotfix tier) — the most
  directly relevant precedent, found via `search_docs`. Fixed the *opposite* direction
  (`observability → engine/domains/systems`, i.e. what observability is allowed to import) using
  two techniques this ticket should consider for its own open question: (1) route unavoidable
  engine access through the `Kernel` facade (`Kernel.get_world_indexes()` /
  `get_building_region()` / `verify_occupancy_legal()`), added when real violations were found
  during that ticket's own test-writing pass; (2) pin a small, exact allowlist of pure/stateless
  symbols for the domains/systems imports that were legitimate and couldn't reasonably be removed,
  requiring the test and the doc note to be updated together for any future addition — not a
  silent expansion. Both techniques used simple `os.walk` + line-string matching (not AST) even
  though written after the two strong AST tests already existed in the repo — this ticket's own
  scope explicitly calls for upgrading to AST instead of repeating that shortcut.
- `TCK-20260627-P2G-KERNEL-FACADE` — established the `Kernel` facade precedent
  `TCK-20260813-...` built on. Not re-read in full (superseded detail already captured inside the
  `TCK-20260813` done ticket's Implementation Notes), but its existence and shape is load-bearing
  context for the Plan phase's decision.
- `TCK-20260618-AUDIT-D14-COUPLING` (done) — produced `docs/audits/D14_coupling_depth.md`, the only
  doc with a documented cross-layer dependency-flow diagram. Confirms (line 93, 97-98) that even
  `core → engine` lazy/TYPE_CHECKING imports were flagged as a coupling risk finding (F2, risk
  10/15) rather than a hard-enforced test failure — i.e. this codebase's established practice is to
  *document and score* some upward couplings as accepted risk rather than always eliminate them,
  relevant precedent for how strict the two new tests should be.
- `TCK-20260529-OBS-PHASE19` (done) — original ticket that created
  `test_phase19_observability_boundaries.py`. Not re-read in full; referenced for registry
  completeness only, superseded by the more recent `TCK-20260813` and this ticket's own scope.

## Risks and Open Questions

**Blocking open question (do not assume an answer — flag for Plan):** The ticket's own
"Assumptions / Open Questions" section states whether `domains ↛ observability` or
`systems ↛ engine` violations currently exist "wasn't checked in either source audit" and "affects
whether the new test starts red or green." This investigation now has ground truth: both exist,
and `systems ↛ engine` is not marginal — 13+ real, non-`TYPE_CHECKING` import statements across 5
production files (`intelligence.py`, `detour.py`, `redirection.py`, `market.py`, `routine.py`),
none of which are in this ticket's "Related Code Areas" or Scope. This has three real
consequences for Plan:
1. A **zero-tolerance ban** ("systems may never import `src.engine`") would make the new test fail
   immediately against current production code, not merely "against a deliberately-introduced
   violation" (AC3's framing) — forcing either an in-ticket refactor of 5 unrelated production
   files (contradicts the ticket's Scope, which lists only test files under Related Code Areas)
   or a tier escalation the ticket's own downgrade rationale ("mechanically reusing one
   already-proven pattern... cohesive, one standard ticket," 2026-08-18 note) did not anticipate.
2. A **pinned-allowlist model** (mirroring `TCK-20260813`'s `test_observability_domains_systems_
   import_allowlist`) would let the test go green immediately by encoding the current real
   imports as the allowlist, matching this ticket's actual stated scope (test-file work only) and
   the codebase's own established practice (D14's F2 finding: document/score upward coupling
   rather than always eliminate it). This is the option most consistent with the ticket's stated
   scope and tier.
3. A **facade-routing model** (mirroring the `Kernel`-facade fix for observability→engine) would
   require adding facade methods and refactoring 5 systems files' call sites — a real, if
   mechanical, production change of similar shape to `TCK-20260813`'s own in-scope fix, but larger
   in surface area (5 files/13 sites vs. that ticket's 3 sites).

For `domains ↛ observability`, the same three options apply but the blast radius is much smaller
(2 files, 2 real call sites, both importing the same pure `SimulationEvent` dataclass) — a pinned
allowlist or facade-routing fix here is low-risk regardless of which option Plan picks for
`systems ↛ engine`.

**Other risks:**
- `test_hot_path_does_not_import_heavy_analyzers`'s forbidden-substring list
  (`observability.anomaly`/`.cognition`/`.reporting`) checks the literal substring anywhere in
  file content, including inside comments/docstrings/lazy-import strings written for other
  purposes — an AST rewrite must decide whether to preserve or tighten this (the ticket's AC only
  requires "AST inspection, not substring matching," not a change in which imports are forbidden).
- The `core ↛ domains` test (`test_entity_models_do_not_import_domain_services`) is *not* named in
  the ticket's Related Code Areas as a target file beyond being in the same source file as the two
  tests being upgraded — confirm with Plan whether it's in scope to also convert to AST (the
  ticket's prose only names the observability-boundary tests in `test_phase18_...py` as upgrade
  targets, but AC1 says "The two weak boundary tests use AST inspection" referring to the two
  *files*, and this test lives in one of those two files).

## Anti-Drift Hazards

- Do not let "upgrade to AST" become "also fix the systems→engine production imports" without an
  explicit Plan-phase decision — that's a materially larger, differently-scoped change (see Risks
  above) than what the ticket's Scope/Related Code Areas describe.
- Do not silently choose zero-tolerance-ban semantics for either new test without surfacing that it
  will immediately fail against real, currently-shipping code — AC3's "confirmed to actually fail
  against a deliberately-introduced violation" reads as assuming a currently-clean baseline, which
  is false for `systems ↛ engine`.
- If a pinned-allowlist approach is chosen (as `TCK-20260813` precedent suggests), keep the
  allowlist *exact* (full import-string match, not prefix/substring) — that ticket's own text
  warns against "silent expansion," and an AST-based allowlist should preserve that same
  discipline rather than loosening it just because AST makes broader matching easier.
- `test_phase19_observability_boundaries.py::test_observability_boundaries_doc_exists` is not an
  import-boundary test at all (doc-content check) — do not accidentally fold it into the AST
  rewrite; it's out of this ticket's scope.
- Any new/rewritten test must still pass for the existing legitimate `TYPE_CHECKING`-guarded
  imports found in `intelligence.py:62`, `redirection.py:5`, `market.py:4`,
  `consequence_events.py:38`, `narrative_ledger.py:23`, `orchestrator.py:26` — an AST visitor that
  naively flags *any* `from src.engine`/`from src.observability` line without excluding
  `TYPE_CHECKING` blocks (the way `test_api_read_model_guard.py` already does) would produce false
  positives beyond what even a zero-tolerance policy intends.
