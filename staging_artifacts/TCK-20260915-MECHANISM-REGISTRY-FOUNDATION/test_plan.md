---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260915-MECHANISM-REGISTRY-FOUNDATION
artifact_type: test_plan
tags: [architecture, documentation, schema]
---

# Test Plan — TCK-20260915-MECHANISM-REGISTRY-FOUNDATION

## Regression Surface

This ticket adds new files; it does not change any existing runtime behavior. The regression
surface is therefore narrow — mainly "did this new tool/target break anything already using the
same conventions it borrows from."

**Unit**
- `tests/unit/engine/test_capability_registry.py` — must keep passing unmodified. It's the pattern
  this ticket's own validator/reader imitates; a passing baseline proves the imitated pattern still
  works before layering a new, structurally similar registry on top of it.

**Tooling / generation precedent**
- `tools/generate_brainstorm_idea_index.py` invoked via `make brainstorm-idea-index` — not modified
  by this ticket, but if the two stale atlas badges (Breakthrough, Race-Keyed Evolution Chains — see
  investigation.md "Docs Requiring Update") are corrected as part of this ticket's work, re-running
  `make brainstorm-idea-index` afterward must still succeed with an unchanged idea count (68) and no
  `SystemExit` from its own `_atlas_idea_ids()`/`build_index()` assertions — a quick regression check
  that the badge-text edits didn't disturb the `id="card-sections-data"` JSON block's structure the
  generator parses.

**Integration**
- None. This ticket's registry is not read by anything yet (Out of Scope item 3) — nothing depends on
  it existing, so there is no integration surface it could break beyond the two items above.

## New Tests Required

Per Acceptance Criteria #1, #4, #5. AC #2 and #3 are schema-shape assertions folded into the fixture
tests below rather than separate standalone tests (they're properties the seed data and reader must
have, verified by the same reader-based checks that prove the other invariants).

1. **`test_registry_yaml_exists`**
   - Category: unit
   - Verifies: `docs/brainstorm/mechanisms.yaml` exists and parses as valid YAML via `yaml.safe_load`.
   - Location: `tests/unit/tools/test_mechanism_registry.py` (new file — no existing
     `tests/unit/tools/` precedent test targets a `docs/brainstorm/` YAML specifically; placed beside
     other `tools/`-adjacent registry tests rather than under `tests/unit/engine/`, since this
     registry is not an engine-runtime artifact the way `capability_registry.yaml` is).

2. **`test_registry_has_layers_and_mechanisms_blocks`**
   - Category: unit
   - Verifies: the top-level YAML has exactly the two documented keys, `layers` (a dict) and
     `mechanisms` (a list); each `layers` entry has `cadence` and `rank`; no mechanism entry carries
     a `cadence` key (AC #3 — frequency lives only on layers, never on a mechanism) and no top-level
     structure stores a computed dependent-count anywhere (AC #2 — `depends_on` is the only
     hand-authored edge data).
   - Location: same file.

3. **`test_registry_seed_meets_expected_scale`**
   - Category: unit
   - Verifies: `len(mechanisms) >= 30` as a sanity floor (not a hard count match to the ticket's own
     30–50 estimate, since investigation found the real corpus-backed count is ~73 — see
     investigation.md). Guards against an accidentally near-empty seed, not against exceeding the
     original estimate.
   - Location: same file.

4. **`test_validator_rejects_unresolved_depends_on`** (Acceptance Criteria #4, invariant 1)
   - Category: unit
   - **Fixture (deliberately broken):** a minimal 2-entry `mechanisms` list where one entry's
     `depends_on` names an id that is not declared anywhere else in the same fixture file
     (e.g. `mechanisms: [{id: foo, layer: entity, depends_on: [nonexistent_id], state: done}]`).
   - Verifies: the validator raises/returns a failure identifying both the offending mechanism id
     (`foo`) and the unresolved dependency id (`nonexistent_id`) — not just a generic failure.
   - Location: `tests/unit/tools/test_mechanism_registry.py`, fixture file under
     `tests/fixtures/mechanism_registry/invalid_depends_on.yaml` (or inline YAML string — match
     whatever `test_capability_registry.py` does for its own fixtures once the validator's actual
     module shape is chosen during implementation).

5. **`test_validator_rejects_dependency_cycle`** (invariant 2 — DAG acyclicity)
   - Category: unit
   - **Fixture (deliberately broken):** a direct 2-node cycle (`a depends_on: [b]`, `b depends_on:
     [a]`) *and* a second case covering a longer 3-node cycle (`a depends_on: [b]`, `b depends_on:
     [c]`, `c depends_on: [a]`) — the direct 2-cycle alone would not catch a validator that only
     checks immediate self-reference or pairwise symmetry instead of running a real cycle detection
     (e.g. Kahn's algorithm / DFS with a visiting-set).
   - Verifies: both fixtures fail; the failure message identifies at least one mechanism id in the
     cycle.
   - Location: same file, two fixture files or two inline fixtures within one test function pair.

6. **`test_validator_rejects_undeclared_layer`** (invariant 3)
   - Category: unit
   - **Fixture (deliberately broken):** a `mechanisms` entry with `layer: nonexistent_layer`, where
     the fixture's own `layers` block does not declare `nonexistent_layer`.
   - Verifies: failure identifies the offending mechanism id and the undeclared layer name.
   - Location: same file.

7. **`test_validator_rejects_invalid_state`** (invariant 4 — six-class enum)
   - Category: unit
   - **Fixture (deliberately broken):** a `mechanisms` entry with `state: broken` (a plausible-looking
     but not-one-of-the-six value — chosen deliberately because it's a real word someone might type
     by habit from the wiring map's own `bug`/`broken` vocabulary, which is exactly the kind of
     cross-document vocabulary bleed this test should catch).
   - Verifies: failure identifies the offending mechanism id and the invalid state value; a second
     assertion confirms all six valid values (`done`, `partial`, `gap`, `orphan`, `gated`,
     `skeleton`) are individually accepted (parametrized), proving the enum boundary is exact, not
     accidentally permissive on one side.
   - Location: same file.

8. **`test_validator_accepts_valid_fixture`** (happy path — required precisely because AC #4 warns a
   validator only ever run against good data is indistinguishable from one that does nothing; this
   test exists specifically so the six invalid-fixture tests above are proven to be testing a
   validator that *can* pass, not one that always fails)
   - Category: unit
   - **Fixture:** a small, internally consistent 4–5 node graph using real seeded ids from
     investigation.md (e.g. `combat_resolution depends_on [tactical_decision, combat_engagement]`,
     `tactical_decision depends_on [action_pacing_readiness]`, all declared under `layer: entity`,
     all `state` values from the six-class set).
   - Verifies: validator returns success/no-failure for this fixture.
   - Location: same file.

9. **`test_reader_class_basic_accessors`**
   - Category: unit
   - Verifies: a `MechanismRegistry`-shaped reader (mirroring `CapabilityRegistry`'s
     `all_capabilities()`/`get_status()`/`is_supported()` shape) correctly returns a mechanism's
     `state` by id, returns `None`/raises cleanly for an unknown id, and returns the full mechanism
     list. Mirrors `test_capability_reader_get_status`/`test_capability_reader_unknown_id` in
     `tests/unit/engine/test_capability_registry.py` directly.
   - Location: same file.

10. **`test_make_target_validates_registry`** (Acceptance Criteria #5)
    - Category: integration (subprocess)
    - Verifies: running the new `make` target (e.g. `make mechanism-registry-validate`, name TBD at
      implementation time, registered alongside `brainstorm-idea-index` per Scope item 4) against the
      real committed `docs/brainstorm/mechanisms.yaml` exits 0 with no manual steps; a second
      invocation against a copy with one of the fixture#4–7 defects injected exits non-zero. Uses
      `subprocess.run([...], capture_output=True)` the way any Makefile-target test in this repo
      would (no existing precedent test directly invokes `make brainstorm-idea-index` via subprocess,
      so this is a new pattern — kept minimal: exit code only, not stdout content matching).
    - Location: `tests/unit/tools/test_mechanism_registry.py` or `tests/integration/tools/` if the
      repo's convention reserves subprocess-invoking tests for `tests/integration/` — confirm against
      a real existing `make`-target test at implementation time rather than guessing further here.

11. **`test_graphify_crosscheck_never_fails_build`** (Scope item 5 — report-only)
    - Category: architecture guard
    - Verifies: whatever script implements the graphify cross-check (out of this Foundation ticket's
      full design per investigation.md's Graphify Cross-Check Feasibility section, but its
      report-only contract still needs a test once *some* version exists) always exits 0 / never
      raises, even when it finds and reports a suspicious `depends_on` edge with no supporting
      call/import path. Construct this by feeding it a registry fixture containing at least one
      `depends_on` edge between two real code symbols known to have no direct relationship (this
      investigation's own tested pair, `CampService`/`EquipmentService`, is a candidate — though
      recall from investigation.md that a bare "no path" check is unreliable at this codebase's
      scale, so whichever real detector ships must be tested against its own actual precision
      criteria, not just "some path was flagged").
    - Location: same file or a dedicated `tests/unit/tools/test_mechanism_registry_graphify_check.py`
      if the checker ends up substantial enough to warrant its own module (likely, per
      investigation.md's feasibility discussion — this is real script work, not a one-liner).

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest tests/unit/tools/test_mechanism_registry.py -v
.venv/bin/python3 -m pytest tests/unit/engine/test_capability_registry.py -v   # regression: imitated pattern still passes
```

Never `pytest tests/`. If the graphify cross-check lands as its own module (item 11 above), add it
explicitly:

```
.venv/bin/python3 -m pytest tests/unit/tools/test_mechanism_registry_graphify_check.py -v
```

## Anti-Drift Test Guards

- **`test_registry_seed_meets_expected_scale`'s floor (`>= 30`) must not be tightened into an exact
  count match.** The real seed is ~73 per investigation.md, not 30–50 — a test asserting an exact
  count would immediately start failing the moment anyone adds or corrects a mechanism, which is
  expected, healthy churn for a hand-authored file, not a regression to guard against.
- **The six invalid-fixture tests (4–7) must each use a fixture that is invalid for exactly one
  invariant at a time.** A fixture that is simultaneously missing a layer *and* has an unresolved
  `depends_on` would pass even if the validator only implements 1 of the 4 invariants, silently
  hiding a missing check — the same "validator that does nothing" failure mode AC #4 warns about,
  just one level deeper (a suite that looks like it covers all 4 invariants but doesn't, because its
  fixtures are entangled).
- **`test_validator_accepts_valid_fixture` must use real seeded ids from investigation.md, not
  synthetic placeholder ids like `a`/`b`/`c`.** Using real ids (`combat_resolution`,
  `tactical_decision`, etc.) means this test doubles as a canary: if the actual seed data in
  `docs/brainstorm/mechanisms.yaml` is later hand-edited to rename or remove one of these ids without
  updating this fixture, the fixture and the real file silently diverge — acceptable for a fixture,
  but worth a code comment noting the fixture is a frozen snapshot, not a live reference, so a future
  renamer doesn't assume editing the real YAML alone is sufficient.
- **The `make` target test (10) must run against a *copy* of the real YAML with an injected defect,
  never mutate `docs/brainstorm/mechanisms.yaml` in place.** Use `tmp_path`/`shutil.copy` — a test
  that corrupts the real committed file, even transiently, in a repo where CLAUDE.md's Worktree
  Isolation notes the working directory can be shared across concurrent sessions, is a real hazard,
  not just poor test hygiene.
- **The graphify cross-check test (11) must assert "never fails the build" using a fixture proven to
  trigger a suspicious-edge report, not a fixture that happens to pass silently.** A test that never
  actually exercises the "found something suspicious" branch would pass whether or not the
  never-fail contract is honored — mirrors AC #4's own warning, applied to Scope item 5's
  report-only requirement instead of the four hard invariants.
