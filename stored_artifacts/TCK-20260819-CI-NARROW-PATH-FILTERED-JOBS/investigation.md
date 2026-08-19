---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS
artifact_type: investigation
tags: [testing, workflows]
---

# Investigation — TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS

## Current Behavior

### `.github/workflows/test.yml` triggers (top-level, lines 1-16)
```yaml
on:
  pull_request:
  push:
    branches: [main]
  schedule:
    - cron: "0 3 * * *"
  workflow_dispatch: {}
```
No `paths:`/`paths-ignore:` filter exists at the workflow level. All 11 fast-lane jobs plus
`typecheck` run unconditionally on every trigger; only `slow` (lines 246-286) has a job-level
`if:`.

### `perf-cert-arena` (lines 200-214) — current, no `if:`
```yaml
perf-cert-arena:
  name: "Perf / cert / arena"
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with: { python-version: "3.13", cache: pip }
    - run: pip install -r requirements.txt
    - name: Run
      run: |
        pytest tests/perf \
               tests/certification \
               tests/arena \
               -m "not slow and not extra_slow" --tb=short -q
```
No `if:`, no `needs:` (nothing depends on it running before it, but `slow` job at line 265
lists it in `needs:` — see Risks section, this is load-bearing for the mechanism design).

### `migration-lanes` (lines 216-228) — current, no `if:`
```yaml
migration-lanes:
  name: "Migration lanes"
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with: { python-version: "3.13", cache: pip }
    - run: pip install -r requirements.txt
    - name: Fast lanes
      run: make lane-all-fast
    - name: Expansion gate
      run: make gate-expansion
```
`make lane-all-fast` (`Makefile:210-211`): `pytest tests/ -m "(catalog or content_graph or
worldassembly or registry_projection or scenario_setup or architecture) and not strict_matrix and
not slow" -v --tb=short`. `make gate-expansion` (`Makefile:213-214`):
`pytest tests/integration/content/test_expansion_gate.py -v --tb=short`. Verified live via
`.venv/bin/python3 -m pytest ... --collect-only`: 324/9223 tests collected for the
`lane-all-fast` marker expression — confirms the Makefile target text matches actual collection.

### Precedent — `slow` job's gating pattern (lines 246-266, added by
TCK-20260818-STANDARD-SLOW-REGRESSION-OFF-PR-PATH)
```yaml
slow:
  name: "Slow regression"
  runs-on: ubuntu-latest
  if: github.ref == 'refs/heads/main' || github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
  needs:
    - unit-core-world
    - unit-gameplay
    - unit-infra
    - integration
    - api-tools
    - agent-orchestration
    - simulation-quality
    - arch-docs
    - perf-cert-arena
    - migration-lanes
  steps: ...
```
This `if:` is a plain boolean expression with **no status-check function** (`success()`,
`always()`, etc.). Per GitHub Actions semantics, a job `if:` expression that omits a status-check
function is implicitly ANDed with `success()` against everything in `needs:` — i.e. GitHub
requires every job in `needs` to have concluded with `success` (not `skipped`, not `failure`)
before it even evaluates the custom boolean. This is the load-bearing precedent detail this
ticket's mechanism must not break — see Risks below.

## Mechanics / Engine Constraints
None. This ticket touches only `.github/workflows/test.yml` (CI plumbing), not any simulation
mechanic. No `docs/mechanics/` chapter or `docs/engine/` contract constrains a CI trigger
condition.

## Docs Requiring Update
- `docs/testing/migration_ci_lanes.md`: this is the living reference doc for the
  `migration-lanes` job's lane definitions and CI pipeline order; it must gain a section
  documenting the new path-based skip condition and the exact trigger path set, or the doc goes
  stale the moment this ticket ships (the doc's own "Last updated: 2026-06-09" header must also
  be bumped).

`docs/audits/D18_ci_release_pipeline.md` lines 169 and 187 reference `migration-lanes` but only
as **historical "RESOLVED (2026-06-25)" notes** recording when the job was first added — they
describe what the job runs, not its trigger conditions, so they do not need updating for a
trigger-gating change. No dedicated doc exists for `perf-cert-arena` (grepped `docs/` for both
job-name variants — zero hits) — none needed since none currently describes it.

## Parity Ledger Overlap
None. Grepped all `docs/parity_ledger/*.yaml` for `test.yml`/`github/workflows`/CI references —
no entry describes CI trigger/gating behavior (the parity ledger tracks simulation-mechanic
parity between legacy and V2 source, not CI plumbing). No P0 entries touched.

## Prior Work
- `stored_artifacts/TCK-20260818-STANDARD-SLOW-REGRESSION-OFF-PR-PATH/investigation.md` — the
  direct precedent for gating a job off the default PR path via job-level `if:`. Its own
  investigation confirms the `needs:` list (including `perf-cert-arena` and `migration-lanes`)
  pre-existed and was **not** touched by that ticket; the `slow` job's `if:` there only ever
  evaluated against `github.ref`/`github.event_name`, never against any upstream job's
  `result` — meaning the skip-propagation risk this ticket surfaces (see Risks) did not exist
  before now, because neither `perf-cert-arena` nor `migration-lanes` could previously report
  anything other than `success`/`failure`.
- `stored_artifacts/TCK-20260609-MIGRATION-CI-LANES/investigation.md` and
  `docs/testing/migration_ci_lanes.md` — establish the marker→lane Makefile mapping this ticket
  reuses to determine `migration-lanes`' real dependency set (see below); confirms
  `lane-all-fast`'s marker expression has been stable since 2026-06-09.
- `tests/static/test_corpus_diversity_ci_isolation.py` — direct precedent for a pytest-based
  static architecture guard that `yaml.safe_load`s `.github/workflows/test.yml` and asserts on
  job/step structure (job dict → `steps` list → dict lookups). This is the pattern `test_plan.md`
  reuses for the new verification tests, since GitHub Actions workflow YAML has no other test
  coverage mechanism in this repo (no `actionlint`/`yamllint`/`act` present — verified via
  `which actionlint yamllint act` returning nothing).

## Real Dependency Set — `perf-cert-arena`
Ran `grep -rhoE "^from src\." tests/perf tests/certification tests/arena | sort -u` (67 test
files). Distinct top-level `src/` directories actually imported:

```
ai  api  certification  cognition  config  core  domains  engine  observability
perf  platform  replay  world  worldbuilding
```

14 of the repo's 34 top-level `src/` directories (`src/*/`, excluding `__pycache__`) — **not** a
narrow slice. `src/core` and `src/engine` are both imported directly (`src.core.state`,
`src.core.builder`, `src.core.strategic`, `src.core.updates`, `src.core.enums`, `src.core.quests`,
`src.core.work`, `src.core.dirty`; `src.engine.apply`, `.checkpoint`, `.compactor`, `.executor`,
`.kernel`, `.lod`, `.pipeline_phases`, `.policy`, `.scheduler`, `.worker_logic`,
`.worker_manager`) — this directly triggers the ticket's own flag condition: **both
`src/core/state.py`-family and `src/engine/kernel.py`-family modules are imported by
`perf-cert-arena`'s tests, so `src/core/` and `src/engine/` must be IN the trigger path set, not
excluded.**

Directories **not** imported (safe to exclude from the trigger set): `actions`, `cli`, `content`,
`content_semantics`, `economy`, `entities`, `lab`, `logging`, `progression`, `quests`, `runtime`,
`scenarios`, `simulation_quality`, `strategy`, `systems`, `testing`, `town`, `views`,
`worldassembly`, `worldgeneration`, `worldmodules`.

Recommended trigger path set for `perf-cert-arena`:
```
tests/perf/**
tests/certification/**
tests/arena/**
src/ai/**
src/api/**
src/certification/**
src/cognition/**
src/config/**
src/core/**
src/domains/**
src/engine/**
src/observability/**
src/perf/**
src/platform/**
src/replay/**
src/world/**
src/worldbuilding/**
Makefile
requirements.txt
.github/workflows/test.yml
```
(`Makefile`/`requirements.txt`/the workflow file itself included as a general safety margin — a
change to any of them can affect what/whether these tests run or install correctly.)

## Real Dependency Set — `migration-lanes`
`migration-lanes`' selection is marker-based, not directory-based (`lane-all-fast`'s marker
expression `(catalog or content_graph or worldassembly or registry_projection or scenario_setup
or architecture) and not strict_matrix and not slow`, plus `gate-expansion`'s single hardcoded
test file). Found the 28 test files actually carrying these 6 markers via
`grep -rlE "pytest\.mark\.(catalog|content_graph|worldassembly|registry_projection|scenario_setup|architecture)\b" tests/`
(also checked for dynamic `pytest_collection_modifyitems`-based marker injection —
`tests/conftest.py:113`'s hook only enforces taxonomy markers under `tests/parity/`, unrelated to
these 6 markers, so the static grep is a complete and accurate picture, not an undercount).

Marker-carrying files span 3 top-level `tests/` dirs and these subdirs:
```
tests/architecture/                              (3 files — static guards)
tests/integration/content/                        (2 files)
tests/integration/scenarios/                      (2 files)
tests/integration/worldassembly/                  (6 files)
tests/unit/certification/                         (1 file)
tests/unit/content/                                (2 files)
tests/unit/runtime/                                (2 files)
tests/unit/scenarios/                              (2 files)
tests/unit/worldassembly/                          (8 files)
```
`grep`ing those 28 files' own `from src.` imports (plus `tests/integration/content/
test_expansion_gate.py`, the `gate-expansion` target) gives the real `src/` dependency set:
```
src.certification.models        src.core.modes            src.core.registries
src.core.state                  src.content.matrix         src.content.pack_manifest
src.content.reference_graph     src.content.repository     src.content.resolver
src.runtime.bootstrap           src.scenarios.*             src.worldassembly.*
src.worldbuilding.*             src.worldmodules.*
```
This confirms the ticket's own prediction: **this needs a coarser (broader) trigger set than
`perf-cert-arena`'s**, spanning 8 `src/` top-level dirs (`core`, `content`, `runtime`,
`scenarios`, `worldassembly`, `worldbuilding`, `worldmodules`, `certification`) rather than a
single clean directory tree. `src/core` is real (via `src.core.registries`, which is imported by
`tests/conftest.py` itself at collection time — every single test in the repo transitively
depends on `src/core/registries.py` loading cleanly, but a **behavior** change specific to
`src/core/state.py`/`src/core/modes.py` etc. is what these 28 tests actually exercise, matching
`perf-cert-arena`'s independent finding that `src/core/` must be included).

Recommended trigger path set for `migration-lanes`:
```
tests/architecture/**
tests/integration/content/**
tests/integration/scenarios/**
tests/integration/worldassembly/**
tests/unit/certification/**
tests/unit/content/**
tests/unit/runtime/**
tests/unit/scenarios/**
tests/unit/worldassembly/**
tests/conftest.py
src/core/**
src/content/**
src/runtime/**
src/scenarios/**
src/worldassembly/**
src/worldbuilding/**
src/worldmodules/**
src/certification/**
Makefile
requirements.txt
.github/workflows/test.yml
```

## Recommended Mechanism
A top-level `paths:`/`paths-ignore:` trigger filter is **wrong** — it applies to the entire
workflow (all 11+1 jobs), and 9 of those jobs are explicitly out of scope for path-filtering per
this ticket's Request Summary. Per-job `if:` is required, mirroring the `slow` job's existing
pattern.

`dorny/paths-filter` (or any other third-party changed-files action) is **not currently used
anywhere** in this repo's workflows — grepped every `uses:` line in both
`.github/workflows/*.yml` files; only `actions/checkout`, `actions/setup-python`,
`actions/configure-pages`, `actions/upload-pages-artifact`, `actions/deploy-pages`, and
`actions/upload-artifact` appear, all first-party GitHub actions. **Recommendation: hand-roll the
`git diff` check** rather than introduce a new third-party action for exactly 2 call sites — this
keeps the skip logic auditable in-repo (consistent with the project's "no hidden/implicit durable
behavior" rule) with no new external trust boundary, and a plain `git diff --name-only` +
`grep -E` against the path list above is well within the complexity this needs.

**Architecture: a new upstream `changed-files` job**, because a job-level `if:` is evaluated
*before* the job (including its `checkout` step) starts — the diff cannot be computed as a step
inside `perf-cert-arena`/`migration-lanes` itself and still skip the whole job (checkout + pip
install + pytest) that way; it must be computed by a separate job whose `outputs` the two target
jobs' `if:` conditions reference via `needs.changed-files.outputs.*`. This new job is plumbing,
not a third skippable job: it must always run (no `if:` on it) since skipping *it* would
cascade-skip everything downstream via the same `needs`-success mechanism documented below.

Sketch (illustrative — exact step contents are Implement's call):
```yaml
changed-files:
  name: "Changed files (path-filter gate)"
  runs-on: ubuntu-latest
  outputs:
    run_perf_cert_arena: ${{ steps.diff.outputs.run_perf_cert_arena }}
    run_migration_lanes: ${{ steps.diff.outputs.run_migration_lanes }}
  steps:
    - uses: actions/checkout@v4
      with: { fetch-depth: 0 }   # need full history to diff against an arbitrary base sha
    - id: diff
      run: |
        # Non-PR events (push to main, schedule, workflow_dispatch) always run both jobs —
        # fail-safe-to-run applies at the event-type level too, and this also means
        # perf-cert-arena/migration-lanes NEVER report "skipped" on the event types where the
        # `slow` job's own `if:` can be true (see Risks — this sidesteps the needs-skip-
        # propagation problem entirely instead of requiring a `slow`-job edit).
        if [ "${{ github.event_name }}" != "pull_request" ]; then
          echo "run_perf_cert_arena=true" >> "$GITHUB_OUTPUT"
          echo "run_migration_lanes=true" >> "$GITHUB_OUTPUT"
          exit 0
        fi
        BASE="${{ github.event.pull_request.base.sha }}"
        HEAD="${{ github.event.pull_request.head.sha }}"
        if ! CHANGED=$(git diff --name-only "$BASE" "$HEAD" 2>&1); then
          echo "::warning::changed-files diff failed ($CHANGED) — failing open, both jobs will run"
          echo "run_perf_cert_arena=true" >> "$GITHUB_OUTPUT"
          echo "run_migration_lanes=true" >> "$GITHUB_OUTPUT"
          exit 0
        fi
        echo "$CHANGED"
        PERF_RE='^(tests/(perf|certification|arena)/|src/(ai|api|certification|cognition|config|core|domains|engine|observability|perf|platform|replay|world|worldbuilding)/|Makefile$|requirements\.txt$|\.github/workflows/test\.yml$)'
        MIG_RE='^(tests/architecture/|tests/(integration|unit)/(content|scenarios|worldassembly|certification|runtime)/|tests/conftest\.py$|src/(core|content|runtime|scenarios|worldassembly|worldbuilding|worldmodules|certification)/|Makefile$|requirements\.txt$|\.github/workflows/test\.yml$)'
        echo "run_perf_cert_arena=$(echo "$CHANGED" | grep -qE "$PERF_RE" && echo true || echo false)" >> "$GITHUB_OUTPUT"
        echo "run_migration_lanes=$(echo "$CHANGED" | grep -qE "$MIG_RE" && echo true || echo false)" >> "$GITHUB_OUTPUT"

perf-cert-arena:
  needs: [changed-files]
  if: needs.changed-files.outputs.run_perf_cert_arena == 'true'
  ...

migration-lanes:
  needs: [changed-files]
  if: needs.changed-files.outputs.run_migration_lanes == 'true'
  ...
```
`fetch-depth: 0` on the `changed-files` job's checkout is required: default `actions/checkout@v4`
fetch-depth is 1, and `github.event.pull_request.base.sha` is very unlikely to be present in a
depth-1 clone, so an unqualified `git diff` would fail with "unknown revision" on essentially
every PR. Using `github.event.pull_request.head.sha` (the PR branch's actual last commit) rather
than `github.sha` (which for `pull_request` events is the synthetic merge commit) is a small
precision improvement worth keeping.

## Fail-Safe-to-Run Verification
Both required safeguards are present in the sketch above and must be preserved by Implement:
1. **Wrong event type** (not `pull_request`) → unconditional `true` output, no diff attempted at
   all.
2. **`git diff` command failure** (any non-zero exit — e.g. base sha genuinely unreachable even
   with `fetch-depth: 0`, transient network issue) is caught via `if ! CHANGED=$(...)`, which
   distinguishes "command failed" from "command succeeded with empty output" (a real "no files
   changed" case must still be possible to represent) — on failure, both outputs are forced to
   `true` and the step exits 0 (so the *job* doesn't fail; it just conservatively decides to run
   the gated jobs). This is the load-bearing distinction the ticket's acceptance criteria demand:
   ambiguity in the check itself must never quietly resolve to "skip," and should also not
   surface as an unrelated CI failure on the `changed-files` job itself.

## Risks and Open Questions

**RESOLVED during this investigation (not left open):** the `slow` job's `needs:` list (line
265-266) includes both `perf-cert-arena` and `migration-lanes`, and its `if:` (line 255) is a
plain expression with no status-check function — per GitHub Actions semantics this means GitHub
implicitly requires every job in `needs` to have concluded `success` before evaluating `slow`'s
own boolean. If `perf-cert-arena`/`migration-lanes` could report `skipped` on a `push` to `main`
or on `schedule`/`workflow_dispatch` (the only events where `slow`'s own `if:` can be true), `slow`
would silently cascade-skip too — a real change to another job's trigger behavior, which
Acceptance Criteria #3 ("No other job's trigger behavior changes") and Out of Scope ("The `slow`
job's own trigger gating — already handled by a prior ticket [and not touched by this one]")
would otherwise put in direct tension with each other. **The recommended mechanism above resolves
this cleanly by scoping the skip logic to `github.event_name == 'pull_request'` only** — on push
to main, schedule, and workflow_dispatch (the only events under which `slow`'s `if:` can
evaluate true), both gated jobs always run to completion and can only conclude `success` or
`failure`, never `skipped`. This means `slow`'s `if:` line does not need to be touched at all,
honoring the Out-of-Scope boundary. Flagging this prominently rather than assuming the planner
will independently derive it — get this wrong and the `slow` regression job (a real safety net,
per TCK-20260818-STANDARD-SLOW-REGRESSION-OFF-PR-PATH) silently stops running on `main` pushes.

**Open for Plan phase, not blocking:** whether the "changed-files" gate job's diff-and-match logic
lives inline in the workflow YAML (as sketched) or is extracted to a small `tools/` script
invoked from the workflow step. Repo precedent (`test_corpus_diversity_ci_isolation.py`) parses
`test.yml`'s `run:` step text directly via `yaml.safe_load`, which favors keeping the logic inline
in the YAML `run:` block (so the static test can assert on its exact text) rather than delegating
to an opaque external script call — recommend inline, but this is a Plan-phase call, not
predetermined here.

**Not a risk, confirmed clean:** `test-scoper`'s local per-ticket scoping (an agent-side tool that
maps changed files to relevant tests for a *local* pre-push run) is architecturally unrelated to
this CI-side job-trigger mechanism — no shared state, no shared code path, nothing to keep in
sync. Grepped `tools/` for any coupling; found none.

## Anti-Drift Hazards
- **Do not widen scope to the other 9 fast-lane jobs.** Explicitly out of scope; the Request
  Summary's own reasoning (widely-imported modules create false-negative risk) applies to them
  even more strongly than to the 2 in-scope jobs.
- **Do not let the trigger path sets silently drift narrower than the real dependency set found
  above.** If a future PR adds a new `tests/perf/`/`tests/certification/`/`tests/arena/` test
  file that imports a `src/` directory not already in the trigger list (e.g. a new import of
  `src/systems/`), the path filter becomes a false negative for that specific new test until the
  filter list is updated — there is no automatic mechanism to detect this drift as of this
  investigation. Consider (Plan/Implement's call, not decided here) whether a lightweight guard
  test asserting "every `src/` top-level dir imported anywhere under tests/perf,
  tests/certification, tests/arena is present in the workflow's `PERF_RE`" is worth adding; the
  Test Plan below proposes this as a **New Test**.
- **Do not touch the `slow` job's `if:` line** unless the event-scoped design above is abandoned
  for some other reason discovered at Plan/Implement time — if it is abandoned, the
  skip-propagation risk documented above must be re-solved explicitly, not left implicit.
- **Do not let the `changed-files` gate job itself become conditionally skippable.** It must have
  no `if:` of its own; skipping it would cascade-skip both target jobs via the same
  needs-success mechanism, silently reintroducing the exact failure mode this ticket exists to
  prevent (never fail open to skip).
- **`gate-expansion` (`test_expansion_gate.py`) and `lane-all-fast` are two separate `run:` steps
  inside the same `migration-lanes` job** — a single job-level `if:`/skip covers both, which is
  correct (they share the same job and the same broad dependency set), but do not split them into
  two jobs with independent filters as part of this ticket; that would be scope expansion beyond
  "exactly 2 jobs."
