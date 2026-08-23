---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD
artifact_type: investigation
tags: [agent-monitoring]
---

# Investigation — TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD

## Search-tooling note (read first)

`mcp__knowledge-search__search_docs` was confirmed unavailable before this investigation started
(index not found). `graphify query` was confirmed unavailable (`graphify-out/` is gitignored and
absent in this fresh worktree — "graph file not found"). Both required tools were tried and failed
before falling back to direct Read/Grep/Bash, per CLAUDE.md's documented exception for when both
Context-Scan tools are genuinely unavailable. `docs/REGISTRY.yaml` (a committed file, not
gitignored) is present in this worktree and was used as the prior-work index in its place.

## Current Behavior

### 1. `tools/codebase_health_baseline.py` — `build_report()` (lines 233-253), the de facto snapshot payload contract

Read in full. `build_report(repo_root: Path) -> dict` returns exactly 13 keys, computed fresh from
`git ls-files`/`git log`/the live filesystem on every call — no caching, no persistence:

| Key | Type | Meaning |
|---|---|---|
| `source_loc` | `int` | Total lines across git-tracked `src/*.py` files |
| `source_files` | `int` | Count of git-tracked `src/*.py` files |
| `test_loc` | `int` | Total lines across git-tracked `tests/*.py` files |
| `test_files` | `int` | Count of git-tracked `tests/*.py` files |
| `test_source_ratio` | `float` | `test_loc / source_loc` (unrounded; `0.0` if `source_loc == 0`) |
| `top_level_src_packages` | `int` | Count of unique top-level `src/<name>/` package directories |
| `test_subdirectories` | `int` | Count of unique parent dirs of git-tracked `tests/**/*.py` (excludes `tests/` root; filesystem-stale empty dirs excluded since it's git-tracked-content-based) |
| `commit_count` | `int` | `git log --oneline` line count (full history) |
| `doc_count` | `int` | Count of git-tracked `docs/*.md` (non-recursive: only direct children of `docs/`, per `_git_ls_files(repo_root, "docs/*.md")` — confirmed by reading `count_docs()`, not `docs/**/*.md`) |
| `registry_size_bytes` | `int` | `docs/REGISTRY.yaml` file size in bytes (`0` if absent) |
| `registry_size_lines` | `int` | `docs/REGISTRY.yaml` line count (`0` if absent) |
| `dead_bytecode_files` | `int` | Count of `.pyc` files anywhere in the live tree with no corresponding live `.py` source |
| `unused_core_dependencies` | `list[str]` | Import names from `pyproject.toml`'s `[project.dependencies]` never `import`ed/`from`ed anywhere in any git-tracked `.py` file, repo-wide |
| `churn_lines_changed_excl_bookkeeping` | `int` | Total insertions+deletions across full history, excluding `agent-monitoring/*.jsonl`, `tickets/working_log.csv`, `docs/REGISTRY.yaml` via a real git pathspec exclusion |

All fields are JSON-serializable as-is (no `datetime`, `Path`, or `set` objects — `list[str]` for
the one non-scalar field). This is directly relevant to Scope item 3 (schema freeze/versioning):
the dict is already flat and `json.dumps()`-safe with zero transformation needed.

`format_report(report: dict) -> str` (lines 256-277) is a pure presentation function over the same
dict — builds a fixed-width text table plus a trailing exclusion-note paragraph. It does not add,
rename, or drop any field; it is a strict formatter, confirming AC #4's "no parsing of
`format_report()`'s printed text" requirement is straightforward to satisfy — the new module never
needs to touch `format_report()` at all, only `build_report()`.

`main()` (lines 280-294): `argparse` with one optional `--repo-root` (default: the real repo root,
computed via `_TOOLS_DIR.parent`), calls `build_report()` then `print(format_report(report))`,
returns `0`. No stdlib-only constraint: this module's own imports are `argparse, re, subprocess,
sys, tomllib, pathlib` — all stdlib — but that is incidental to this particular module, not a
project-wide `tools/` rule (see "Anti-Drift Hazards" below).

### 2. `tools/personality_audit.py` — the Δ/↑↓→ pattern to mirror (lines 277-286)

Read in full. The cited pattern lives in `_print_summary()`:

```python
q1 = quartiles["Q1 (low)"]["avg_diversity"]
q4 = quartiles["Q4 (high)"]["avg_diversity"]
trend = ""
if q1 is not None and q4 is not None:
    diff = q4 - q1
    trend = f"  Δ={diff:+.4f} ({'↑' if diff > 0 else '↓' if diff < 0 else '→'})"
print(f"    {trait:15s}: Q1={q1}  Q4={q4}{trend}")
```

Two things to extract precisely, since the ticket cites this as the pattern to reuse:

- **The comparison itself is not cross-run** — `q1`/`q4` are two quartile buckets computed
  *within a single run's* analysis, not two different historical snapshots. What this ticket
  actually needs to mirror is the **rendering convention**, not the underlying quantity: `diff =
  later_value - earlier_value`; arrow = `↑` if `diff > 0`, `↓` if `diff < 0`, `→` if `diff == 0`;
  `Δ` shown with an explicit `+`/`-` sign and fixed precision.
- **No-prior-data handling**: when either side is `None`, `trend` stays the empty string `""` —
  the surrounding `print` still executes (`Q1=None  Q4=0.5`), it just omits the Δ/arrow suffix
  entirely rather than crashing or fabricating a comparison. This is the direct analog for this
  ticket's AC #3 (single-snapshot degradation): when only one historical snapshot exists, each
  metric should render with an explicit "no trend data yet" label instead of a Δ/arrow, using the
  same "degrade the annotation, not the whole render" shape.

Note for the scorecard's new numeric dimensions: several of `build_report()`'s fields are
monotonically-increasing counters by construction (`commit_count`, `source_loc`, `doc_count`,
`registry_size_*`) where a `→` (flat) reading is realistically rare between two real runs unless
they're taken back-to-back — this is expected, not a bug to special-case.

### 3. Append-only writer convention — `tools/agent-monitoring/writer.py`

Read in full, plus `record_run.py` (its real caller) and `docs/agent-monitoring/schema.md`'s
"Historical Corrections" section (the doc-level statement of the same contract).

**Important correction to the ticket's own Assumptions**: item 3 states "No existing generic
JSONL-append utility exists in tools/ (each JSONL writer inlines its own append logic)." This is
factually incorrect. `tools/agent-monitoring/writer.py` **is** exactly that: a generic, reusable,
already-shared append-only writer, currently used by 3 independent callers
(`record_run.py`, `record_events.py`, `post_tool_hook.py`). Its public surface:

```python
def write_line(target_path: Path, line: str) -> bool   # one pre-serialized JSON line
def write_lines(target_path: Path, lines: list[str]) -> bool  # batch, one lock acquisition
```

Real convention, not `open(path, "a")` alone:

1. Acquire an advisory lock via `os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)`
   (bounded retry: 200 attempts × 5ms sleep ≈ 1s ceiling; stale-lock recovery after 5s).
2. `target_path.parent.mkdir(parents=True, exist_ok=True)`, then `open(target_path, "a")` +
   `f.write(line + "\n")`.
3. Release the lock in a `finally` block.
4. **Never raises to the caller** — any failure (lock timeout, write error) is caught, logged to a
   lock-free best-effort diagnostic sidecar (`.writer_health.jsonl`, written via raw `os.write` on
   an `O_APPEND` fd for true single-line atomicity), and reported back as `bool`.

`record_run.py`'s real call site: `sys.path.insert(0, str(Path(__file__).resolve().parent))` then
`from writer import write_line`; call as `write_line(RUNS_FILE, json.dumps(record,
separators=(",", ":")))`; on `False`, print a `WARNING` to stderr but do not hard-fail the process.

**Import mechanics for a caller outside `tools/agent-monitoring/`**: the directory name has a
hyphen, so `import tools.agent_monitoring.writer` is not possible as a normal dotted import (no
`__init__.py`-based package name can contain a hyphen). Every existing caller of `writer.py` lives
*inside* `tools/agent-monitoring/` and reaches it via `sys.path.insert(0, <this file's own
parent>)`. A new module living directly in `tools/` (per the ticket's `expected:
tools/codebase_health_snapshot.py`) would need the equivalent of:

```python
sys.path.insert(0, str(_REPO_ROOT / "tools" / "agent-monitoring"))
from writer import write_line
```

This is the same cross-directory sys.path pattern `code_health_impact.py` already uses to import
`codebase_health_baseline` (both live in plain `tools/`, so that case doesn't cross the hyphenated
boundary — this ticket's case is one level harder, but the pattern is directly transferable).

`docs/agent-monitoring/schema.md`'s "Historical Corrections" section (lines 106-115) documents the
append-only contract at the doc level: "`runs.jsonl` is append-only for all *new* writes... every
writer... only ever `open(RUNS_FILE, "a")`s, never rewrites an existing line," with exactly one
documented historical exception (a one-time, audited, line-scoped correction, not a rewrite
precedent). This is the doc-level pattern this ticket's own new history file's schema
documentation should mirror (see "Docs Requiring Update" below).

### 4. `tools/code_health_impact.py` — sibling CLI/Makefile conventions to follow

Read in full (547 lines). Concrete conventions this ticket's own new module should match:

- **Structure**: `build_<x>_report(...) -> dict` (pure, testable, no I/O side effects beyond
  reads) separated from `format_<x>_report(report: dict, ...) -> str` (pure presentation) and a
  thin `main(argv=None) -> int` that composes the two and calls `print()`. `codebase_health_
  baseline.py` follows the identical shape. The new scorecard module should follow the same
  triad: a `build_scorecard(...)` (reads N snapshots, computes per-dimension trend) /
  `format_scorecard(...)` (renders it) / `main()` split.
- **`_TOOLS_DIR`/`_REPO_ROOT` module-level constants** computed via `Path(__file__).resolve()
  .parent[.parent]`, with a `sys.path.insert(0, str(_TOOLS_DIR))` guard before importing a
  sibling `tools/` module (`from codebase_health_baseline import compute_churn_lines_changed`).
  The new snapshot-writer module should import `build_report` from `codebase_health_baseline`
  the same way — direct Python import, not a subprocess/CLI shell-out, matching AC #4's "no
  re-implementation" requirement exactly.
- **`argparse`** with a required positional argument where the command needs one target (`
  target_path` for impact), or none where it's a whole-repo command (`codebase_health_baseline.py`
  has none besides `--repo-root`). The new snapshot-append command needs no positional argument;
  the new scorecard-read command likely wants an optional `--last N` (or similar) to bound how
  many historical snapshots to render — no existing sibling has this exact shape since neither
  baseline nor impact reads a history file, so this is a genuinely new but small design point.
- **Docstring-as-provenance**: both sibling files open with a substantial module docstring citing
  the ticket ID that built them, the epic, and the specific design rationale/D24 section behind
  each non-obvious decision. The new module(s) should do the same, citing this ticket ID and
  D24 §J/§M.
- **Makefile wiring** (confirmed directly):
  ```
  codebase-health-baseline: ## Print a live LoC/churn/dependency baseline snapshot (on-demand only — not CI)
  	python3 tools/codebase_health_baseline.py

  codebase-health-impact: ## Print a change-impact report for a source path (pass ARGS="src/engine/pipeline.py") (on-demand only — not CI)
  	python3 tools/code_health_impact.py $(ARGS)
  ```
  Both use the `## <description> (on-demand only — not CI)` comment convention that
  `make help`-style tooling in this repo relies on for self-documentation.
- **`.PHONY` — a real, confirmed inconsistency, not a rule to blindly replicate**: neither
  `codebase-health-baseline` nor `codebase-health-impact` appears in the `.PHONY:` line, even
  though `agent-monitoring-index` and `parity-index` — two other targets independently marked
  `## ... (on-demand only — not CI)` — **are** both present in `.PHONY`. This is a real,
  confirmed omission in the two sibling tickets, not an established "on-demand targets skip
  .PHONY" convention (2 of 4 comparable on-demand targets already do declare `.PHONY`). This
  ticket's own new Makefile target(s) should be added to `.PHONY`, following the
  `agent-monitoring-index`/`parity-index` precedent rather than repeating the sibling gap — a
  small, explicitly-flagged decision for plan.md rather than a silent copy of whichever pattern
  happened to be typed most recently.
- **No CI wiring**: confirmed via `grep -rl "codebase-health\|code-health" .github/workflows/` —
  zero matches. Neither sibling target is referenced anywhere in CI. This ticket's Scope
  explicitly says the same for its own new command(s).

### 5. Test-fixture conventions — `tests/tools/test_codebase_health_baseline.py` and `tests/tools/test_code_health_impact.py`

Both read in full. Shared conventions:

- **`sys.path.insert(0, str(_TOOLS_DIR))` then `import <module> as <alias>`** at module level
  (`chb`, `chi`) — no package-relative import, matching the source modules' own sibling-import
  style.
- **Real git repos in `tmp_path`**, not mocked git calls — a small `_init_repo(tmp_path)` /
  `_commit(tmp_path, message)` helper pair, duplicated verbatim in both test files (not factored
  into a shared conftest fixture). `build_report()`/its constituent functions are called for
  real, never mocked — "every check the tool claims to compute has at least one fixture proving
  it computes correctly, not just that it runs without error" (explicit docstring convention in
  both files, worth repeating verbatim in the new test file's own docstring).
- **One `test_make_target_runs_successfully_with_plausible_values()`**-shaped test per module:
  shells out to the real `make <target>` against the real repo (`cwd=_REPO_ROOT`), asserts
  `returncode == 0` and that key output strings/plausible value bounds appear. This is the
  pattern to reuse for verifying the new Makefile target(s) actually work end-to-end, not just
  that the underlying Python functions do.
- **`code_health_impact.py`'s tests never invoke the real `graphify` CLI or a real `graph.json`**
  except in 4 tests explicitly gated behind `@pytest.mark.skipif` on `graphify`/`graph.json`
  availability (`_requires_graphify`) — everything else uses hand-built fixture dicts
  (`_make_graph(nodes, links)`) and dependency-injected fake `affected_runner` callables. Since
  the new module has no `graphify` dependency at all, this pattern doesn't directly transfer, but
  the underlying idea — dependency-inject the one genuinely environment-dependent piece (here:
  nothing, since `build_report()` only needs a real git repo, which `tmp_path` already provides
  cheaply) — confirms no skip-gating is needed for this ticket's own new tests.

### 6. Dimension set — decided from `build_report()`'s real 13 fields (Scope item, this ticket's own call)

Per the ticket's own Assumption ("this ticket decides the scorecard's dimension set... nothing
else will make this decision"), and drawing only from fields `build_report()` actually returns
(never inventing new ones): the natural per-dimension scorecard rows are the **11 direct numeric/
list-derived fields**, i.e. every key except the two purely-structural ones that don't carry a
meaningful up/down health direction on their own:

**Recommended as trend dimensions** (11): `source_loc`, `source_files`, `test_loc`, `test_files`,
`test_source_ratio`, `top_level_src_packages`, `test_subdirectories`, `commit_count`, `doc_count`,
`dead_bytecode_files`, `churn_lines_changed_excl_bookkeeping`.

**Recommended folded together or shown as one row, not two**: `registry_size_bytes` +
`registry_size_lines` measure the same underlying quantity (`docs/REGISTRY.yaml`'s size) at two
units — showing both as independently-trending "dimensions" double-counts one real signal. plan.md
should decide explicitly whether to show one (e.g. `registry_size_lines`, the more human-legible
unit) or both under one combined row label — either is defensible, but it must be a stated
decision, not an accidental doubling.

**Recommended as a non-trended, present/absent-only row, not a numeric trend**:
`unused_core_dependencies` is a `list[str]`, not a scalar — it has no natural up/down/flat
direction the same way a count does (a 2-item list changing to a *different* 2-item list is not
correctly described by any arrow). Render its raw value (or count-of-list, clearly labeled as
"count of unique names," if a numeric trend is wanted alongside the raw list) rather than forcing
it through the same Δ/arrow machinery as the 11 scalar dimensions above. This distinction is worth
stating explicitly in plan.md since it's the one field that doesn't fit the general shape.

**Direction-of-good is intentionally not encoded**: nothing in `build_report()` or this ticket's
scope assigns "more is better"/"less is better" per field (e.g. more `test_loc` is usually good,
more `dead_bytecode_files` is usually bad, more `commit_count` is neutral/expected). The ticket's
own scope says trend arrows only, no aggregate score — adding good/bad coloring per dimension
would be a step toward exactly the single-aggregate-judgment shape the epic explicitly rules out
of scope. Recommendation: render the raw directional arrow only, uncolored/unjudged, consistent
with "no aggregate/combined score field anywhere in the output."

### 7. Schema-freeze/versioning mechanism — concrete proposal

`build_report()`'s dict has no explicit schema declaration anywhere today — its shape is
implicit in the function body. Three real options, evaluated against this ticket's own
requirement ("a future change to `build_report()` is a visible breaking change, not silent
drift"):

- **(a) Explicit expected-keys allowlist checked at snapshot-write time.** A frozen
  `EXPECTED_SNAPSHOT_KEYS = frozenset({...})` (13 names, hand-copied once from the current
  `build_report()` return) in the new snapshot module. At write time, assert
  `set(report.keys()) == EXPECTED_SNAPSHOT_KEYS` (or a superset/subset check, deliberately
  chosen) before appending; raise loudly (not silently drop/pad) on mismatch. Cheap, requires no
  change to `codebase_health_baseline.py` itself (respects AC #4's "no re-derivation" — this
  reads and validates the dict, never modifies `build_report()`), and directly satisfies "visible
  breaking change, not silent drift": a future added/removed/renamed field in `build_report()`
  makes every subsequent snapshot-write call fail loudly until the allowlist is deliberately
  updated in the same change.
- **(b) A `snapshot_schema_version` integer field, stamped into every written record,
  manually bumped whenever the allowlist in (a) changes.** Complements rather than replaces (a) —
  version alone doesn't stop drift, it only labels it after the fact for a reader parsing old vs.
  new records. Cheap addition on top of (a).
- **(c) Import `build_report`'s dict directly with no allowlist at all** (the ticket's own
  parenthetical alternative — "or import the dict directly"). This satisfies AC #4 but not the
  "visible breaking change, not silent drift" half of the same Scope bullet on its own: a field
  rename in `build_report()` would silently produce differently-shaped rows in the history file
  going forward with no error anywhere, and the scorecard reader would either KeyError deep in
  rendering (unfriendly) or silently show fewer dimensions (actual silent drift, the exact
  failure mode this ticket exists to prevent).

**Recommendation**: (a) + (b) together — a small, frozen, explicit allowlist constant plus a
version field stamped into every record. This is the smallest mechanism that satisfies both
halves of the Scope bullet as written, reuses `build_report()`'s dict directly (no re-derivation),
and requires zero changes to `codebase_health_baseline.py`. plan.md should make the final call;
this is presented as a concrete, evidence-grounded default, not an open question left for the
implementer to invent from scratch.

## Mechanics / Engine Constraints

None. This ticket lives entirely in `tools/` — a developer/agent-facing tooling script, not
simulation logic. No `docs/mechanics/` chapter or `docs/engine/` contract governs codebase-health
tooling; the Mechanics Bible and Engine Contracts constrain `src/` simulation behavior, which this
ticket never touches (confirmed: Scope explicitly forbids any change to
`build_report()`'s metric computation itself).

## Docs Requiring Update

The `docs/agent-monitoring/schema.md` doc (path: `docs/agent-monitoring/schema.md`, under
`docs/`) is not required to change for this ticket: it documents `agent-monitoring/*.jsonl`, a
separate file family from this ticket's new history file, and this ticket does not modify it. It
is mentioned here only as a cross-reference source — its "Historical Corrections"
append-only-contract section (lines 106-115) is the established doc pattern this ticket's own new
history file needs an equivalent of, addressed by the new doc bullet below.
- `docs/plans/codebase_health_observatory_tooling_epic.md`: its "Scope for the eventual
  `create-tickets` pass" bullet for "Historical metric snapshots... plus a multi-dimension
  scorecard" needs the same `~~struck-through~~` + "**Resolved** (`TCK-20260822-CODEBASE-HEALTH-
  SNAPSHOT-SCORECARD`, ...)" treatment already applied to the two sibling bullets immediately
  above it in the same file, once this ticket ships — matching the file's own established
  extraction-tracking convention.
- A new doc describing the snapshot file's schema and the scorecard command's output shape is
  required — this is net-new persistent, durable, machine-read state (a new JSONL history file)
  with no existing doc coverage anywhere. Per CLAUDE.md's Durable State Rule ("If something
  survives beyond the current tick or current function call, it must have a typed model... a
  defined lifecycle, inspection/debug visibility, and tests" — durable here in the ticket-history
  sense, not simulation-tick sense) and per this repo's own established precedent
  (`docs/agent-monitoring/schema.md` exists specifically to document `runs.jsonl`'s shape), a new
  file — recommend `docs/agent-monitoring/codebase_health_history_schema.md` or a new top-level
  section appended to a `docs/observability/` doc if one is judged a better fit by plan.md — must
  document: the history file's path, its JSONL append-only contract (mirroring schema.md's
  "Historical Corrections" language), the frozen key allowlist from Investigation item 7, and the
  `snapshot_schema_version` field's meaning and bump discipline. This is not optional per this
  repo's own precedent: every other durable JSONL history file in this repo
  (`agent-monitoring/{runs,events,tools}.jsonl`) has exactly this kind of doc; a fourth JSONL
  history file with none would itself be a documentation-drift gap on day one.

No `docs/parity_ledger/` entry applies (see below) and no `docs/mechanics/`/`docs/engine/` doc
applies (see above) — both correctly absent from this list, not omitted by oversight.

## Parity Ledger Overlap

None. Grepped every `docs/parity_ledger/*.yaml` for `codebase_health`/`code_health_impact`/
`codebase-health`/`snapshot` (in the specific sense relevant here) — zero entries exist for either
sibling ticket's shipped modules (`tools/codebase_health_baseline.py`,
`tools/code_health_impact.py` have no `v2_evidence` reference anywhere in
`docs/parity_ledger/infrastructure.yaml` or any other subsystem file). This is consistent, not a
gap: the parity ledger tracks Mechanics-Bible-to-`src/`-implementation parity; this ticket (like
both its siblings) lives entirely in `tools/` and never touches `src/` simulation logic, so no
parity ledger entry is expected or required for it either.

## Prior Work

- `tickets/done/TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET.md` +
  `stored_artifacts/TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET/{investigation,plan,
  test_plan}.md` — built `build_report()`/`format_report()` itself; this ticket's own snapshot
  payload contract (Investigation item 1) traces directly back to that work.
- `tickets/done/TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND.md` +
  `stored_artifacts/TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND/{investigation,plan,
  test_plan}.md` — the CLI/Makefile/test-fixture conventions this ticket's own new module should
  match (Investigation items 4-5) are drawn directly from this ticket's shipped code.
- `tools/agent-monitoring/writer.py` + its own consumers (`record_run.py`, `record_events.py`,
  `post_tool_hook.py`) — the hardened append-only convention (Investigation item 3) this ticket's
  new history-file writer should reuse rather than reinvent, correcting the ticket's own
  Assumption that no such utility exists.
- `docs/audits/D24_codebase_health_observatory.md` §J/§L/§M and
  `docs/plans/codebase_health_observatory_tooling_epic.md` — both read in full; confirm this
  ticket is exactly "Phase 4, item 10" of the epic's own sequencing, explicitly deferred until
  last because it has no dependency of its own beyond the two now-shipped sibling tickets.

## Risks and Open Questions

- **Open, blocks nothing but needs a plan.md decision**: should the new snapshot-writer module
  reuse `tools/agent-monitoring/writer.py::write_line` (hardened, lock-protected, matches this
  ticket's own explicit "following the same pattern agent-monitoring/runs.jsonl already uses"
  Scope language literally) or a simpler unlocked `open(path, "a")` (matches the ticket's Scope
  language less literally, but avoids importing across the hyphenated-directory boundary
  described in Investigation item 3, and this history file has no realistic concurrent-writer
  scenario the way `runs.jsonl`/`tools.jsonl` do from parallel agent sessions). Recommend reusing
  `write_line` — it's a two-line import once the `sys.path.insert` boundary is crossed, it is the
  literal established pattern the Scope text names, and it costs nothing at this file's expected
  write frequency (on-demand, human-triggered, not per-tick or per-hook).
- **Open, needs a plan.md decision, not a blocker**: how many historical points constitute "a
  trend" — the epic's own acceptance signal only requires "at least two runs." AC #2 says "two or
  more historical snapshots" render a directional indicator; AC #3 says exactly one snapshot
  degrades gracefully. Nothing in the ticket or its epic specifies whether a *third+* snapshot
  should compare only the latest two, or something richer (e.g., a short sparkline/first-vs-last
  comparison across all N). Simplest AC-satisfying choice: always compare the two most recent
  snapshots only, regardless of how many exist. This satisfies both ACs literally; anything richer
  is a valid enhancement but not required by any AC text read here.
- **Not open, but worth flagging so it isn't second-guessed during implementation**: this ticket's
  own Scope explicitly forbids a combined/aggregate score "at any layer of the output" — this
  includes not just the top-level render but also things like an implicit "N up / M down" summary
  count line, which itself starts to function as a single aggregate signal in practice. plan.md
  should decide explicitly whether even a plain up/down/flat *count* (not a score) crosses this
  line — the safer reading, given how explicit and repeated this constraint is across the ticket,
  the epic doc, and D24 §J/§M, is to avoid any single derived summary number, arrow-count included.

## Anti-Drift Hazards

- **Do not let AC #4's "no re-derivation" become "no reuse either."** The ticket forbids
  reimplementing `build_report()`'s metric computation; it does not forbid importing and reusing
  `codebase_health_baseline.py`'s own helper functions (e.g. `compute_churn_lines_changed` already
  has precedent for cross-module reuse via `code_health_impact.py`). The new snapshot module
  should import `build_report` directly, never subprocess/shell out to
  `python3 tools/codebase_health_baseline.py` and parse stdout — that would silently violate AC #4
  by coupling to `format_report()`'s text shape instead of the dict.
- **Do not silently drop the `unused_core_dependencies` field from the frozen schema allowlist**
  just because it's the one non-scalar/non-trended field (Investigation item 6) — it is still part
  of `build_report()`'s real contract and must still be captured and versioned in every snapshot
  record, even though it renders differently in the scorecard than the 11 scalar dimensions.
- **Do not let the "no stdlib-only guard for `tools/`" finding (Investigation item, confirmed via
  `code_health_impact.py`'s real `import yaml`) become an invitation to add a new third-party
  dependency for this ticket specifically.** Nothing in this ticket's scope needs one — plain
  `json`/`pathlib`/`argparse` cover the read/write/render surface entirely — this finding only
  answers the "is there an architecture guard blocking third-party imports in tools/" question
  (no), not "should this ticket add one" (no reason to).
- **Do not let the new history file's path collide with or get confused for
  `agent-monitoring/runs.jsonl`.** The ticket's Scope says "following the same pattern," not
  "written to the same file" — the new file needs its own distinct path (plan.md's call; a
  natural candidate given the sibling naming convention is something like
  `agent-monitoring/codebase_health_history.jsonl`, keeping it inside the same directory family
  that already has the writer/lock/diagnostic-sidecar infrastructure this ticket is reusing, but
  this is plan.md's decision to make explicit, not something to leave implicit).
- **Do not compute "flat" (`→`) via floating-point equality on ratio-typed fields** (chiefly
  `test_source_ratio`) without considering that two live runs of `build_report()` on an unchanged
  repo could differ by float rounding noise in a way integer fields never do — a naive `diff == 0`
  check is fine for `commit_count`/`source_loc`/etc. (exact integers) but plan.md should confirm
  whether `test_source_ratio`'s `→` case needs any tolerance, or whether exact-zero is
  acceptable/expected in practice (two runs against the exact same commit would produce bit-
  identical floats, so exact-zero is likely fine — but this is worth a one-line explicit decision
  rather than an unstated assumption).
