---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC
artifact_type: plan
tags: [testing, architecture]
---

# Implementation Plan — TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC

## Summary

Rewrite the four substring-grep import-boundary tests in `tests/architecture/test_phase18_import_boundaries.py`
and `tests/architecture/test_phase19_observability_boundaries.py` to use the AST-visitor technique
already established by `tests/architecture/test_api_read_model_guard.py` (parse tree → collect line
ranges covered by `if TYPE_CHECKING:` blocks → walk `Import`/`ImportFrom` nodes → skip nodes whose
`lineno` falls inside a `TYPE_CHECKING` range → flag/allowlist-check the rest), and add two new
AST-based boundary tests for the previously-unenforced `domains ↛ observability` and
`systems ↛ engine` directions. Both new tests adopt a **pinned-exception model**, mirroring
`TCK-20260813-OBSERVABILITY-IMPORT-BOUNDARY-STALE-OR-VIOLATED`'s
`test_observability_domains_systems_import_allowlist` precedent exactly: every currently-real
violation site found during Investigate is pinned by `(file, lineno, module, imported names)` —
stricter than that precedent's plain string match, since it also pins the exact line rather than
just the import string, so a violation that moves lines without updating the pin still fails. No
`src/domains/` or `src/systems/` production file is touched — this ticket is test-tooling only.
Docs (`D14_coupling_depth.md`, the epic tracking doc, `D24_codebase_health_observatory.md`) are
updated last to record the resolution, per the investigation's "Docs Requiring Update" list.

## Steps

### Step 1 — AST rewrite of `core ↛ domains` test + shared TYPE_CHECKING helper
**Files:** `tests/architecture/test_phase18_import_boundaries.py`

**Change:** Replace `test_entity_models_do_not_import_domain_services` (currently
`assert "import src.domains" not in content` / `"from src.domains" not in content` over raw file
text — confirmed at `tests/architecture/test_phase18_import_boundaries.py:5-15`, read directly)
with an AST-based check. Add one module-level helper function to this file,
`_type_checking_lines(tree: ast.AST) -> set[int]`, that walks the tree for `ast.If` nodes whose
`test` is `ast.Name(id="TYPE_CHECKING")` or `ast.Attribute(attr="TYPE_CHECKING")` and collects every
child node's `lineno` inside — this is the same line-range-collection logic already proven at
`tests/architecture/test_api_read_model_guard.py:40-51` (read directly), extracted as a local helper
so the other AST tests added to this same file in Steps 2-5 can reuse it without re-deriving the
logic per test. Walk every `.py` file under `src/core/` with `ast.parse`; for each `Import`/
`ImportFrom` node not in `_type_checking_lines(tree)`, flag it if the module (or any alias) starts
with `src.domains`. Preserve the exact rule being enforced today (no `src.domains` import from
`src/core/`, real imports only) — only the detection mechanism changes.

**Do NOT touch:** `test_observability_engine_imports_go_through_kernel_facade` and
`test_observability_domains_systems_import_allowlist` in the same file (handled in Steps 2-3); do
not move this test to a new file — Related Code Areas names the existing file only.

**Verify:** `tests/architecture/test_phase18_import_boundaries.py::test_entity_models_do_not_import_domain_services`
passes; full sweep `.venv/bin/python3 -m pytest tests/architecture/ -q -m "not slow"` stays at
64 passed (this step doesn't add new tests, so count is unchanged until Steps 4-5).

---

### Step 2 — AST rewrite of `observability ↛ engine` Kernel-facade test
**Files:** `tests/architecture/test_phase18_import_boundaries.py`

**Change:** Replace `test_observability_engine_imports_go_through_kernel_facade` (currently
per-line `.startswith("from src.engine")` string comparison against the exact literal
`"from src.engine.kernel import Kernel"` — confirmed at
`tests/architecture/test_phase18_import_boundaries.py:18-41`, read directly) with an AST check
using the `_type_checking_lines` helper from Step 1. Walk `src/observability/`; for each real
(non-`TYPE_CHECKING`) `ImportFrom` node whose `module` starts with `src.engine`, assert
`node.module == "src.engine.kernel"` and the imported names are exactly `{"Kernel"}`. This preserves
the rule stated in `docs/guides/observability.md:185-191` (read directly) — `src/observability/`
may only reach `src.engine` through the `Kernel` facade, established by
`TCK-20260627-P2G-KERNEL-FACADE`.

**Do NOT touch:** the `Kernel` facade implementation itself (`src/engine/kernel.py`) or any
`src/observability/` call site — this step only changes how the existing rule is checked, not what
is allowed.

**Verify:** `tests/architecture/test_phase18_import_boundaries.py::test_observability_engine_imports_go_through_kernel_facade`
passes.

---

### Step 3 — AST rewrite of `observability ↛ domains/systems` pinned-allowlist test
**Files:** `tests/architecture/test_phase18_import_boundaries.py`

**Change:** Replace `test_observability_domains_systems_import_allowlist` (currently per-line
`.startswith("from src.domains")`/`"from src.systems"` string match against a 4-entry
`allowed_imports` set and 3-entry `allowed_files` set — confirmed at
`tests/architecture/test_phase18_import_boundaries.py:44-89`, read directly) with an AST check
reusing `_type_checking_lines`. Walk `src/observability/`; for each real `ImportFrom` node whose
`module` starts with `src.domains` or `src.systems`, assert the file is in the existing
`allowed_files` set (`src/observability/event_extractor.py`, `event_shapers.py`,
`cognition/recorder.py`) and that `(node.module, tuple(sorted(a.name for a in node.names)))` matches
one of the 4 existing pinned entries (`WorldEventCategory` from
`src.domains.world_emergence.schema`; `AbandonmentEvaluator, AbandonmentCategory` from
`src.domains.commitment.abandonment`; `_MAX_CONSECUTIVE_REJECTIONS` from
`src.systems.strategic_systems.intelligence`; `CognitionGraphExporter` from
`src.systems.strategic_systems.cognition_export` — all confirmed at
`tests/architecture/test_phase18_import_boundaries.py:50-55`, read directly). Do not add, remove, or
loosen any of the 4 pinned entries — this step only changes matching mechanism (AST node identity
instead of exact string), not the allowlist contents.

**Do NOT touch:** the allowlist contents, `docs/guides/observability.md`'s existing "Architecture
boundary" note (already documents this exact set — no change needed since the set is unchanged).

**Verify:** `tests/architecture/test_phase18_import_boundaries.py::test_observability_domains_systems_import_allowlist`
passes.

---

### Step 4 — New `domains ↛ observability` boundary test with pinned exceptions
**Files:** `tests/architecture/test_phase18_import_boundaries.py`

**Change:** Add `test_domains_do_not_import_observability_outside_pinned_exceptions`, co-located
with the other import-direction tests in this file (Related Code Areas names this file; no new test
file is created). Reuses `_type_checking_lines`. Walk every `.py` file under `src/domains/`; for
each real `ImportFrom` node whose `module` starts with `src.observability`, check
`(rel_path, node.lineno)` against a pinned dict of exactly 2 entries (both confirmed by direct read
during Investigate, re-confirmed by direct read during Plan):
- `("src/domains/campaigns/narrative_ledger.py", 71)` → module `src.observability.events`, names
  `{"SimulationEvent"}` (`src/domains/campaigns/narrative_ledger.py:71`, read directly: `from
  src.observability.events import SimulationEvent  # local import avoids circular`, inside
  `emit_chronicle_event`, guarded by `if self._event_recorder is not None:` immediately above)
- `("src/domains/campaigns/orchestrator.py", 319)` → module `src.observability.events`, names
  `{"SimulationEvent"}` (`src/domains/campaigns/orchestrator.py:319`, read directly: `from
  src.observability.events import SimulationEvent`, guarded by `if self._event_recorder is None:
  return` immediately above)

If `(rel_path, node.lineno)` is in the pinned dict, assert `node.module` and the imported names
still match the pinned values exactly (catches the pinned site being silently repurposed to import
something else on the same line) and pass. If `(rel_path, node.lineno)` is NOT in the pinned dict,
fail — this is a new, previously-unseen `domains → observability` import. **Other writers to
consider:** no other test currently asserts anything about `src/domains/` → `src/observability`
imports (confirmed — `test_phase18_import_boundaries.py` and `test_phase19_observability_boundaries.py`
are the only files with import-boundary assertions per Investigate's file list), so this is a wholly
new check with no ordering/collision risk against other tests. The two pinned production files
(`narrative_ledger.py`, `orchestrator.py`) are not modified by this ticket — they remain exactly as
found.

**Do NOT touch:** `src/domains/campaigns/narrative_ledger.py` or `orchestrator.py` — do not refactor
these two call sites to remove the lazy import, add a facade, or otherwise "fix" the coupling; that
is explicitly out of scope (see Scope Guards).

**Verify:** new test passes against current code (2 pinned sites recognized, no false positive); a
temporary third `from src.observability... import ...` line added anywhere else under
`src/domains/` (not at a pinned `file:line`) makes the test fail — verified manually in Step 7, not
committed.

---

### Step 5 — New `systems ↛ engine` boundary test with pinned exceptions
**Files:** `tests/architecture/test_phase18_import_boundaries.py`

**Change:** Add `test_systems_do_not_import_engine_outside_pinned_exceptions`, same file, same
technique as Step 4. Walk every `.py` file under `src/systems/`; for each real `ImportFrom` node
whose `module` starts with `src.engine`, check `(rel_path, node.lineno)` against a pinned dict of
exactly 13 entries, all confirmed by direct read during Plan (file:line, module, names):

| File | Line | Module | Names |
|---|---|---|---|
| `src/systems/strategic_systems/intelligence.py` | 69 | `src.engine.policy` | `GovernorPolicy` |
| `src/systems/strategic_systems/intelligence.py` | 75 | `src.engine.spatial_query` | `SpatialQueryService` |
| `src/systems/strategic_systems/intelligence.py` | 78 | `src.engine.cadence` | `should_run`, `SystemCadence` |
| `src/systems/strategic_systems/intelligence.py` | 83 | `src.engine.domain_logic` | `SimulationDomainLogic` |
| `src/systems/strategic_systems/intelligence.py` | 664 | `src.engine.cadence` | `should_run` |
| `src/systems/strategic_systems/intelligence.py` | 829 | `src.engine.domain_logic` | `SimulationDomainLogic` |
| `src/systems/strategic_systems/intelligence.py` | 833 | `src.engine.cadence` | `should_run`, `SystemCadence` (aliased `DefaultCadence`) |
| `src/systems/strategic_systems/intelligence.py` | 905 | `src.engine.cadence` | `should_run`, `SystemCadence` (aliased `DefaultCadence`) |
| `src/systems/strategic_systems/intelligence.py` | 958 | `src.engine.cognition` | `AppraisalSystem` |
| `src/systems/strategic_systems/detour.py` | 22 | `src.engine.domain.lead_routing` | `LeadRoutingSystem` |
| `src/systems/strategic_systems/redirection.py` | 23 | `src.engine.cadence` | `should_run` |
| `src/systems/economy_systems/market.py` | 50 | `src.engine.legality` | `LegalityServiceV2` |
| `src/systems/world_systems/routine.py` | 180 | `src.engine.legality` | `LegalityServiceV2` |

(Each row re-confirmed by direct read at Plan time: `intelligence.py:55-89`, `:660-667`,
`:825-836`, `:900-909`, `:954-961`; `detour.py:15-23`; `redirection.py:1-25`; `market.py:1-51`;
`routine.py:172-182` — matching investigation.md's count of 13, not "13+"; no additional site was
found beyond what Investigate reported.) Note `intelligence.py:62`'s `SystemCadence` import IS
inside `TYPE_CHECKING` (confirmed at `intelligence.py:61-62`) and must NOT be in the pinned dict —
`_type_checking_lines` already excludes it before the pinned-dict check runs, so it never reaches
this test's assertion at all. Same alias-of-line semantics as Step 4: an aliased alias-name change
on a pinned line (e.g. `SystemCadence as DefaultCadence` becoming `SystemCadence as X`) must still
fail, since the assertion compares the full `(module, names-as-written)` tuple, not just presence of
the module. **Other writers to consider:** same as Step 4 — no other existing test asserts on
`src/systems/` → `src/engine` imports; `consequence_events.py`'s in-file docstring convention
(`src/systems/social_systems/consequence_events.py`, referenced in investigation.md, not itself a
violation site since it imports `src.observability.events` at module level, not `src.engine`) is
unaffected by this test and is not touched.

**Do NOT touch:** any of the 5 production files (`intelligence.py`, `detour.py`, `redirection.py`,
`market.py`, `routine.py`) — do not refactor these 13 call sites toward facade-routing or
`TYPE_CHECKING`-only imports; that is the largest single scope-creep risk flagged by Investigate and
is explicitly out of scope for this ticket (see Scope Guards).

**Verify:** new test passes against current code (13 pinned sites recognized); a temporary import of
`src.engine` added anywhere else under `src/systems/` (not at a pinned `file:line`) makes the test
fail — verified manually in Step 7, not committed.

---

### Step 6 — AST rewrite of hot-path heavy-analyzer test
**Files:** `tests/architecture/test_phase19_observability_boundaries.py`

**Change:** Replace `test_hot_path_does_not_import_heavy_analyzers` (currently
`assert f"import {forbidden}" not in content` / `f"from {forbidden}" not in content` substring
match against file text — confirmed at
`tests/architecture/test_phase19_observability_boundaries.py:28-65`, read directly) with an AST
check. Add a local `_type_checking_lines` helper to this file (this file has no existing AST
helper to reuse — it is a separate module from `test_phase18_import_boundaries.py`, and the repo's
existing pattern per `test_api_read_model_guard.py` is a private per-file helper, not a shared
cross-file utility module, so duplicate the ~12-line helper rather than introducing a new shared
`tests/architecture/` support module). Walk the same hot-path file set (`src/engine/`,
`src/observability/config.py`, `event_extractor.py`, `event_recorder.py`); for each real
`ImportFrom`/`Import` node, flag it if `node.module` (or any `alias.name` for plain `Import`) equals
or starts with `observability.anomaly`, `observability.cognition`, or `observability.reporting`.
Preserve exactly the same three forbidden substrings and file set — AC1 requires only a mechanism
change ("AST inspection, not substring matching"), not a change in which imports are forbidden
(per investigation.md's flagged risk on this exact point).

**Do NOT touch:** `test_observability_boundaries_doc_exists` in the same file — it is a
doc-existence/term-presence check, not an import check, and is explicitly out of this ticket's
scope per investigation.md.

**Verify:** `tests/architecture/test_phase19_observability_boundaries.py::test_hot_path_does_not_import_heavy_analyzers`
passes; `test_observability_boundaries_doc_exists` in the same file is unmodified and still passes.

---

### Step 7 — Negative-case verification (AC3) and full sweep
**Files:** none permanently changed (temporary, reverted); verification only.

**Change:** For each of the 6 tests touched in Steps 1-6, temporarily introduce one deliberate
violation and confirm the test fails, then revert before moving on — mirroring how
`TCK-20260813`'s own Test Summary verified its new tests failed pre-fix and passed post-fix. Do
this by hand during Implement (edit a throwaway line into the relevant `src/` file or a scratch
fixture, run the single test, observe failure, revert with `git checkout -- <file>`), not as a
committed pytest fixture — this matches the investigation's stated default (test_plan.md's item 7:
"run manually during Implement... rather than committed as a permanent pytest test") and keeps this
step's footprint at zero net new files, consistent with the ticket's test-tooling-only scope. Cases
to exercise: (a) add `import src.domains.x` to a `src/core/` file → Step 1's test fails; (b) add
`from src.engine.spatial_query import X` to an `src/observability/` file → Step 2's test fails;
(c) add an unpinned `from src.domains.x import Y` to an `src/observability/` file → Step 3's test
fails; (d) add an unpinned `from src.observability.events import X` to an `src/domains/` file →
Step 4's test fails; (e) add an unpinned `from src.engine.x import Y` to an `src/systems/` file →
Step 5's test fails; (f) add `import observability.anomaly` to an `src/engine/` file → Step 6's test
fails. Then run the full sweep and confirm all pass clean:
`.venv/bin/python3 -m pytest tests/architecture/ -q -m "not slow"` → expect 66 passed (64 existing +
2 new tests from Steps 4-5; Steps 1-3 and 6 rewrite existing tests in place, no count change).

**Do NOT touch:** do not commit any of the negative-case fixture edits; do not leave a temporary
violation line in any `src/` file after this step.

**Verify:** all 6 negative cases individually reproduce a failure, then full architecture sweep is
clean at 66 passed, 0 failed.

---

### Step 8 — Doc updates recording the resolution
**Files:** `docs/audits/D14_coupling_depth.md`, `docs/plans/architecture_boundary_hardening_epic.md`,
`docs/audits/D24_codebase_health_observatory.md`

**Change:**
- `docs/audits/D14_coupling_depth.md`: extend the "Layer Architecture" diagram
  (`D14_coupling_depth.md:48-60`, read directly) to add an `systems` row (it currently has no
  position at all, confirmed by investigation.md and by direct read) — `systems ─────→ core +
  engine (pinned exceptions, see Coupling Inventory)` — and extend the "Coupling Inventory" section
  (`D14_coupling_depth.md:66-101`, read directly, ends after the `core` upward-dependency table) with
  two new subsections mirroring the existing `core` upward-dependency table's format: one for
  `domains → observability` (the 2 pinned sites from Step 4) and one for `systems → engine` (the 13
  pinned sites from Step 5), each stating the sites are enforced-pinned by the new tests added in
  Steps 4-5, and that expanding either pinned set requires updating both the doc and the test
  together (mirroring `docs/guides/observability.md:192-198`'s existing "not a silent addition"
  language).
- `docs/plans/architecture_boundary_hardening_epic.md`: add a `## Status` section stating
  "Resolved by TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC" and naming the pinned-allowlist
  resolution chosen for both new boundaries, matching the pattern sibling epics A/B/E already use in
  `docs/plans/architecture_resilience_remediation_roadmap.md` (per investigation.md's Docs Requiring
  Update section).
- `docs/audits/D24_codebase_health_observatory.md`: in §K "Architecture Fitness Functions", move
  `test_phase18_import_boundaries.py` and `test_phase19_observability_boundaries.py`'s relevant
  tests out of "substring-based (weak — upgrade candidates)" and move the `domains ↛ observability`
  / `systems ↛ engine` boundaries out of "Proposed, not yet enforced," per investigation.md's Docs
  Requiring Update section.

**Do NOT touch:** any other section of D14 (the Cross-domain import scan, AuthoritativeState
mutation scan, etc. are unrelated findings, not part of this ticket); do not alter D14's existing
`core` upward-dependency table content, only append new subsections after it.

**Verify:** no test verifies doc content directly except
`test_phase19_observability_boundaries.py::test_observability_boundaries_doc_exists`, which targets
a different doc (`docs/architecture/observability_behavior_profiling_boundary.md`) and is untouched
by this step. Manually confirm the 3 doc files render correctly and the ticket's "Docs Requiring
Update" list in investigation.md is fully addressed. Per project convention, run
`make knowledge-index-update` at Finalize since `docs/` files changed.

## Scope Guards

Explicit list of things this plan must NOT touch, derived from the ticket's Out of Scope section
and investigation.md's Anti-Drift Hazards:

- Do NOT refactor any of the 13 `systems → engine` violation sites (`src/systems/strategic_systems/
  intelligence.py`, `detour.py`, `redirection.py`, `src/systems/economy_systems/market.py`,
  `src/systems/world_systems/routine.py`) toward facade-routing, `TYPE_CHECKING`-only imports, or
  any other production import restructuring. This ticket pins them as grandfathered exceptions, it
  does not eliminate them.
- Do NOT refactor either of the 2 `domains → observability` violation sites
  (`src/domains/campaigns/narrative_ledger.py:71`, `orchestrator.py:319`) for the same reason.
- Do NOT build a general machine-readable subsystem-ownership manifest for all 38 `src/` packages —
  explicitly Out of Scope in the ticket.
- Do NOT build the Tier-3→Tier-0 `docker-compose.yml` startup-dependency linter — explicitly Out of
  Scope in the ticket (belongs to a different epic).
- Do NOT touch `test_observability_boundaries_doc_exists` (doc-existence check, not an import
  boundary check) — not in scope per investigation.md.
- Do NOT introduce a new shared cross-file AST-helper module under `tests/architecture/` — the
  repo's established pattern (per `test_api_read_model_guard.py`) is a private per-file helper;
  duplicating a ~12-line helper across `test_phase18_import_boundaries.py` and
  `test_phase19_observability_boundaries.py` is consistent with that pattern and avoids an
  unplanned new abstraction.
- Do NOT commit any negative-case/fixture file for AC3 — verified manually and reverted (Step 7),
  matching `test_plan.md`'s stated default and keeping footprint at zero new files.
- Do NOT loosen, add to, or remove any entry in the existing 4-item
  `test_observability_domains_systems_import_allowlist` allowlist (Step 3 changes matching mechanism
  only).
- Do NOT run `pytest tests/` unscoped — always `.venv/bin/python3 -m pytest tests/architecture/ -q
  -m "not slow"` (system Python 3 lacks `pydantic`).

## Dependency Map

- Step 1 must land before Steps 2-6 that reuse its `_type_checking_lines` helper within
  `test_phase18_import_boundaries.py` (Steps 2, 3, 4, 5 all live in that same file and helper).
- Step 6 is independent of Steps 1-5 (different file, its own local helper per Scope Guards).
- Steps 4 and 5 are independent of each other (different pinned dicts, different directories
  scanned) but both depend on Step 1's helper being present in the same file.
- Step 7 depends on Steps 1-6 all being complete (it exercises every rewritten/new test).
- Step 8 depends on Steps 1-7 being complete and verified (docs record the finished resolution, not
  a planned one).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: The two weak boundary tests use AST inspection, not substring matching | Steps 1, 2, 3 (test_phase18_import_boundaries.py), Step 6 (test_phase19_observability_boundaries.py) | `test_entity_models_do_not_import_domain_services`, `test_observability_engine_imports_go_through_kernel_facade`, `test_observability_domains_systems_import_allowlist`, `test_hot_path_does_not_import_heavy_analyzers` |
| AC2: `domains ↛ observability` and `systems ↛ engine` each have an enforced boundary test | Steps 4, 5 | `test_domains_do_not_import_observability_outside_pinned_exceptions`, `test_systems_do_not_import_engine_outside_pinned_exceptions` |
| AC3: each new/upgraded test confirmed to actually fail against a deliberately-introduced violation | Step 7 | Manual negative-case run for all 6 tests (a)-(f), not a committed test |

## Anti-Drift Notes

- The `systems ↛ engine` pinned set is 13 entries, not "13+" — Investigate's "13+" phrasing was
  provisional; Plan re-confirmed by direct read that the count is exactly 13 across the 5 named
  files, with no additional site. If Implement finds a 14th site not listed in Step 5's table, stop
  and re-confirm rather than silently expanding the pinned dict — that would be exactly the "silent
  expansion" investigation.md's Anti-Drift Hazards warns against.
- `intelligence.py:62`'s `SystemCadence` `TYPE_CHECKING` import must be excluded by
  `_type_checking_lines` before Step 5's pinned-dict check ever runs on it — it is not one of the 13
  pinned sites and must never appear in the pinned dict (it would be a false pin, not a violation).
- The pinned-exception model in Steps 4-5 is a grandfather list, not a general allowlist pattern —
  it pins exact `(file, lineno)` sites, not just import strings, deliberately stricter than
  `TCK-20260813`'s original string-only match, so a violation that moves to a different line without
  updating the pin still fails (this is the "AST makes broader matching easier — don't loosen"
  discipline investigation.md's Anti-Drift Hazards calls for).
- Do not let "upgrade to AST" expand into "also fix the production imports" at any point during
  Implement — every one of the 15 real violation sites (2 domains→observability + 13
  systems→engine) is pinned/grandfathered, not eliminated, by design; eliminating them is a larger,
  differently-scoped future ticket, not this one.
- `docs/guides/observability.md`'s existing "Architecture boundary" note (lines 185-198) is not
  modified by this plan — it documents the unchanged `observability → engine/domains/systems`
  direction (Steps 2-3), which stays exactly as documented. Only D14 (Step 8) gains new content, for
  the two newly-enforced directions.
- Both target test files require `.venv/bin/python3` (system Python 3 lacks `pydantic` and fails at
  collection) — every verification command in this plan must use that interpreter.

## Deviations

- **Step 6 (`test_hot_path_does_not_import_heavy_analyzers`) — pinned line numbers re-confirmed
  unchanged, and one new finding surfaced by the AST rewrite that this plan did not anticipate.**
  All 15 pinned `(file, lineno)` sites for Steps 4-5 (2 `domains → observability`, 13
  `systems → engine`) were individually re-read against current source during Implement and match
  this plan's tables exactly — no line number had shifted, no site was added or removed. Separately,
  implementing the literal AST rewrite of Step 6 (matching each import's resolved module string
  against the 3 forbidden substrings) surfaced that the *old* substring-grep test's own pattern —
  `f"from {forbidden}" not in content` / `f"import {forbidden}" not in content`, checking for the
  bare form `"observability.anomaly"`/`.cognition`/`.reporting"` with no `src.` prefix — never
  actually matched this codebase's real imports, which are always written `from
  src.observability.anomaly...`. This means the old test was silently vacuous for all 3 forbidden
  substrings from the day it was written: it always passed, regardless of real content. A
  substring check against the AST-derived module name (which naturally includes the `src.` prefix)
  correctly and immediately catches 5 real, currently-shipping violations in `src/engine/kernel.py`
  (lines 129, 277, 278, 289, 1111 — lazy imports of
  `src.observability.reporting.artifact_repository`, `.reporting.metric_recorder`,
  `.cognition.recorder`, `.cognition.decision_trace_writer` twice) that this plan's Step 6 did not
  anticipate and that `kernel.py` is not named in any Scope Guard, pinned-exception list, or Related
  Code Area for this ticket.
  - **Resolution taken:** rather than either (a) silently inventing a new, unauthorized
    pinned-exception list for `kernel.py` (scope creep beyond what architecture review approved —
    only the 2+13 domains/systems sites were reviewed and blessed), or (b) refactoring `kernel.py`
    (a production change explicitly out of this ticket's test-tooling-only scope), the
    implementation preserves the *old* test's literal real-world matching behavior exactly (`name
    .startswith(forbidden)` against the bare, un-prefixed forbidden string) — satisfying this
    step's own instruction to "preserve exactly the same three forbidden substrings and file set...
    not a change in which imports are forbidden" in its most literal reading. This keeps the test
    green against current code and touches no production file, consistent with the ticket's scope.
  - **Not fixed, not hidden:** the 5 real `kernel.py` violations remain a live, real, currently
    undetected gap in the engine hot-path boundary — worse than the `systems → engine`/`domains →
    observability` gaps this ticket closes, since here even the *pinned-exception* enforcement model
    was never applied because the old test's blind spot was invisible until this rewrite. This is
    reported in the ticket's Implementation Notes and flagged as a recommended follow-up ticket
    (new pinned-exception boundary test for `src/engine/kernel.py`'s heavy-analyzer imports, or a
    facade-routing fix), not resolved in this ticket.
  - **Verified via Step 7's negative-case (f):** the reverted temporary fixture used the plan's own
    bare-form example (`import observability.anomaly`, no `src.` prefix) — consistent with this
    preserved matching behavior, and confirmed to fail as expected.
