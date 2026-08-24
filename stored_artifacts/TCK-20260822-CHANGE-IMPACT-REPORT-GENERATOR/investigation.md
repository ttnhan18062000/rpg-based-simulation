---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR
artifact_type: investigation
tags: [architecture, testing]
---

# Investigation — TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR

## Search-tooling note (read first)

`mcp__knowledge-search__search_docs` and `tools/knowledge_search.py` were both already confirmed
down for this worktree (known persistent "index not found" outage) before this investigation
started, and `graphify` is unusable here (`graphify-out/` is gitignored and was never built in
this fresh worktree — a `graph file not found` condition, not a transient failure). Both required
Context-Scan tools were unavailable for the documented reason, so this investigation went straight
to direct Read/Bash/grep, per CLAUDE.md's exception for genuine unavailability of both tools. This
mirrors the identical, already-logged exception the immediately-preceding sibling ticket
(`TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD`) recorded for the same worktree.

## Current Behavior

### 1. `tools/code_health_impact.py::build_impact_report()` — the function this ticket renders

Read in full (547 lines). Real signature:

```python
def build_impact_report(
    repo_root: Path,
    target_path: str,
    depth: int = DEFAULT_AFFECTED_DEPTH,
    graph: dict | None = None,
    graph_path: Path = DEFAULT_GRAPH_PATH,
    registry_entries: list | None = None,
    affected_runner=run_graphify_affected,
) -> dict:
```

Real return dict, **13 keys, confirmed by reading the literal `return {...}` block** (lines
468–482) — not the ticket's own paraphrase:

| Real key | Type | Ticket's Scope-bullet paraphrase |
|---|---|---|
| `target_path` | `str` | not named in the ticket's list |
| `subsystem` | `str` | "subsystem" ✓ |
| `dependents` | `list[str]` (already sorted via `sort_dependents_src_first`) | "direct dependents" (close, not literal) |
| `dependents_degraded` | `bool` | part of "degradation caveat" |
| `dependents_degradation_reason` | `str \| None` | part of "degradation caveat" |
| `resolved_symbols` | `list[str]` | not named in the ticket's list |
| `unresolved_symbols` | `list[str]` | part of "degradation caveat" (also separately named in Scope bullet 3) |
| `required_tests` | `list[str]` | "required tests" ✓ |
| `required_tests_registry_hit_count` | `int` | not named in the ticket's list |
| `architecture_rules` | `list[str]` | maps to **both** "relevant invariants" *and* "architecture rules" in the ticket's list — see below |
| `churn_lines_changed` | `int` | folded into "criticality tier" |
| `edge_degree` | `int` | folded into "criticality tier" |
| `criticality_tier` | `str` (`"high"`/`"medium"`/`"low"`) | "criticality tier" ✓ |

**Important correction to the ticket's own field list**: there is no separate "relevant
invariants" field anywhere in `build_impact_report()`'s return dict or in `code_health_impact.py`
at all. `match_architecture_rules()` (lines 254–260) returns one list, `architecture_rules`,
matched by subsystem-path-prefix against `tests/architecture/`'s 17 boundary-test filenames (the
`ARCHITECTURE_RULE_PATH_PREFIXES` dict, lines 86–128). D24 §L's worked example prints "Relevant
invariants" and "Architecture rules" as two separate human-readable *rows* (`single-writer
mutation, per-tick atomicity` vs. `test_phase_domain_permissions.py`), but that distinction was
never implemented as two separate fields — both are rendered from the same one `architecture_rules`
list in the real code. The ticket's Scope bullet 2 phrase "relevant invariants, architecture
rules" should be read as one real field, `architecture_rules`, not two. Plan should decide
explicitly whether the report generator renders all 13 real keys or only a curated subset
resembling the ticket's paraphrase — see Risks below.

**Module docstring's framing, quoted verbatim** (lines 6–9), which Scope bullet 4 requires this
ticket's own report to preserve:

> This is a **discovery/ triage aid, not a certified coverage oracle** — every signal below is a
> best-effort heuristic and is presented as such; false positives/negatives are acceptable,
> silently presenting them as certain is not.

`format_impact_report()` (lines 485–529) already restates this per-report, at the end of every
printed report (line 524–527):

> Note:                 discovery/triage aid, not a certified coverage
>                       oracle — verify before treating any of the above as complete.

The new report generator's own Markdown/JSON rendering must carry an equivalent line — not
paraphrase it away — since it is the one framing statement AC's "preserve... framing" language is
anchored to.

**Degradation signals, exact source**: `dependents_degraded`/`dependents_degradation_reason` come
from `find_dependents()` (lines 201–251) — two independent degradation modes, both documented in
the module docstring (zero resolvable symbols; "No unique node match" for every resolved symbol).
`unresolved_symbols` is populated even in the *non*-degraded case (only some symbols ambiguous) —
`format_impact_report()` renders this as a separate "note:" line (lines 503–507) only when
`dependents_degraded` is `False`, since the degraded branch already explains itself via
`dependents_degradation_reason`. The new report generator must reproduce this same conditional
(do not print both a degradation-reason line and a stale/empty unresolved-symbols note for the
same field state).

**No aggregate score exists anywhere in this module** — `criticality_tier` is the closest thing to
a rollup and it is explicitly a 3-value qualitative tier (`compute_criticality_tier()`, lines
393–398), not a number. AC #3 ("never renders a single aggregate numeric 'health score'") is
already satisfied by construction as long as the report generator only ever surfaces existing
fields verbatim — a real risk only if the new code invents its own summary computation.

### 2. `tests/tools/test_code_health_impact.py` — test conventions to mirror

Read in full (451 lines). Established conventions this ticket's new test file
(`tests/tools/test_pr_impact_report.py`) must mirror:

- `_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"` + `sys.path.insert(0, str(_TOOLS_DIR))`
  guard before `import code_health_impact as chi` — real-module import, not mocked.
- `_GRAPHIFY_AVAILABLE` / `_requires_graphify` skip-marker pattern (lines 26–41): real `graphify
  affected` subprocess + real `graphify-out/graph.json` are dev-only, absent from CI and from this
  fresh worktree — this ticket's new tests must use the **same** `_requires_graphify` skip guard
  (or import it directly from `code_health_impact`-adjacent test module) for any test that calls
  `chi.build_impact_report()` against the real graph rather than a synthetic fixture graph/injected
  `affected_runner`.
- Fixture-graph helper pattern (`_make_graph`, `_fake_graph_two_symbols`) + a fake
  `affected_runner` callable injected via `build_impact_report(..., affected_runner=...)` — the
  existing tests never invoke the real `graphify` subprocess except in the 4
  `@_requires_graphify`-marked tests. Since `build_impact_report()` already fully supports
  dependency injection (`graph=`, `registry_entries=`, `affected_runner=`), the new report
  generator's own tests should build a `report: dict` directly (either via a hand-constructed dict
  matching the real 13-key shape, or via a real `chi.build_impact_report()` call against a fixture
  graph) rather than re-deriving impact data — the same "coverage-honesty" convention stated in
  this test file's own module docstring (every check the tool claims to compute has at least one
  fixture proving it, not just that it runs).
- `test_make_target_runs_successfully_against_real_repo` (lines 404–415) — the Makefile-target
  shell-out pattern (`_requires_graphify`-marked, `subprocess.run(["make", "codebase-health-impact",
  "ARGS=..."])`) this ticket's own new Makefile target's test should mirror.

### 3. `tools/codebase_health_snapshot.py` — the C1 module this ticket's open question is about

Read in full (345 lines). `EXPECTED_SNAPSHOT_KEYS` (lines 73–78) is a frozen, hand-copied allowlist
of exactly 14 keys, **all repo-wide aggregates**: `source_loc`, `source_files`, `test_loc`,
`test_files`, `test_source_ratio`, `top_level_src_packages`, `test_subdirectories`,
`commit_count`, `doc_count`, `registry_size_bytes`, `registry_size_lines`, `dead_bytecode_files`,
`unused_core_dependencies`, `churn_lines_changed_excl_bookkeeping`. Every one of these is computed
once, globally, over the entire repository (`build_report()` in `codebase_health_baseline.py`) —
**none of them is parameterized by, or resolvable to, a single target path.** `read_snapshots()`
(lines 159–174) returns the full list of historical repo-wide records; `build_scorecard()` (lines
215–239) always compares the two most recent repo-wide snapshots and produces per-dimension trend
rows for those same 14 repo-wide dimensions — there is no per-file/per-path key, index, or lookup
anywhere in this module.

## Mechanics / Engine Constraints

None apply. This ticket is tools/-only (a report generator over an existing developer-tooling
output shape); it touches no `src/` simulation logic, no Mechanics Bible chapter, and no engine
contract. Same conclusion the two immediately-preceding sibling tickets in this epic
(`TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND`, `TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD`)
reached for the identical reason.

## Docs Requiring Update

- `docs/plans/codebase_health_observatory_tooling_epic.md`: its "Scope for the eventual
  `create-tickets` pass" bullet ("PR/AI change-impact report generator, built on top of the
  impact-model command above — the last item in sequence...") needs the same
  `~~struck-through~~` + "**Resolved** (`TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR`, ...)"
  treatment already applied to the three sibling bullets above it in the same file, once this
  ticket ships — and the resolution note should state explicitly that no snapshot-history
  dependency was required (see "Risks and Open Questions" below), correcting the epic doc's
  standing "built on top of" phrasing rather than leaving it ambiguous about what "on top of"
  turned out to mean.

`docs/audits/D24_codebase_health_observatory.md` is mentioned here only as background — it is the
originating audit and its §M Phase 4 item 11 language ("PR/AI change-impact report generator,
built on top of Phase 3's impact model") is directly relevant context for the open question below,
but per the confirmed precedent of both sibling tickets (`git log` shows this file has not been
edited by any child ticket since its own creation commit), the audit itself is treated as a
historical, frozen document and is not edited by child tickets. No bullet for it above.

No `docs/parity_ledger/*.yaml` entry needs to change — see below.

## Parity Ledger Overlap

None. Grepped every `docs/parity_ledger/*.yaml` for `code_health_impact`/`codebase_health`/
`pr_impact_report`/`change.impact`/`graphify` in the specific sense relevant here — the only hits
are 30+ unrelated lines in `infrastructure.yaml` belonging to the separate KGMCP
(`search_mcp.py`/context-search) epic, not to this tool family. Zero `v2_evidence` reference to
either `tools/code_health_impact.py` or `tools/codebase_health_snapshot.py` exists anywhere in
`docs/parity_ledger/`. Consistent with both sibling tickets' own conclusion for the same reason:
this is developer-facing tooling, not simulation behavior.

## Prior Work

- `stored_artifacts/TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND/` (investigation.md, plan.md,
  test_plan.md) — the direct predecessor. Its investigation.md's "Related" section describes this
  epic's build order as "impact command → historical snapshots → PR report generator" (a *ticket
  sequencing* note, written before either successor ticket existed) — see "Risks and Open
  Questions" for why this phrase should not be read as a claimed functional data dependency.
- `stored_artifacts/TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD/` (investigation.md, plan.md,
  test_plan.md) — the immediately-preceding sibling, shipped 2026-08-23 (`tickets/done/
  TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD.md`). Direct structural precedent for this
  investigation/test_plan's own frontmatter, section shape, and the `build_<x>`/`format_<x>`/
  `main()` triad convention. Confirms the `docs/plans/codebase_health_observatory_tooling_epic.md`
  bullet-resolution pattern this ticket must also follow.
- `docs/plans/codebase_health_observatory_tooling_epic.md` — the epic tracking doc; each of the 3
  prior items records its own "Resolved (`TCK-...`)" note directly in this file's Scope section,
  the established convention this ticket's own Document-Update step must continue.

## Risks and Open Questions

### The central open question (ticket Scope bullet 5 / AC #4 / Assumptions) — RESOLVED, with evidence

**Question**: does the report generator have a real, concrete dependency on
`tools/codebase_health_snapshot.py`'s snapshot/scorecard output?

**Conclusion: no.** There is no real per-path dependency, and none is buildable without adding new
impact-computation logic that the ticket's own Out-of-Scope section explicitly forbids ("Any new
impact-computation logic — this ticket only renders `build_impact_report()`'s existing output").
Evidence, in order of directness:

1. **Structural mismatch, confirmed by reading both modules' real code.**
   `codebase_health_snapshot.py`'s `EXPECTED_SNAPSHOT_KEYS` is a frozen set of 14 **repo-wide
   aggregate** metrics (source_loc, test_loc, commit_count, etc. — see "Current Behavior" §3
   above). None of them is keyed, filterable, or resolvable by a target path.
   `build_impact_report()` is a **per-path** function — its one caller-supplied identity is
   `target_path: str`. There is no join key between "this one path's impact" and "the whole
   repo's aggregate LoC/churn/dependency-count history" that would produce a meaningful per-path
   trend. A per-path "trend" derived from a repo-wide aggregate would either (a) be the same
   number for every target path in a given PR (not a real per-path signal, just the ambient
   repo-wide number re-printed N times), or (b) require genuinely new logic to decompose the
   aggregate by path — which does not exist today and squarely is "new impact-computation logic,"
   the one thing this ticket's Out-of-Scope section rules out.
2. **The originating design doc (D24 §L) never proposed this dependency.** §L's own "Change-Impact
   Model" section lists exactly 4 composable data sources for the impact command:
   graphify edge data, `tests/architecture/` boundary tests, `docs/REGISTRY.yaml`'s
   `related_code_areas`, and churn × centrality for criticality tier. Historical snapshot data is
   not among them — §L was written before the snapshot mechanism (§J's separate bullet, §M item
   10) was designed at all.
3. **§M's own sequencing plan, read precisely, does not claim a data dependency either.** Phase 4
   lists item 10 (historical snapshots) and item 11 (PR/AI report generator) as *build-order*
   items, and item 11's text says "built on top of **Phase 3's impact model**" — Phase 3 is item 8
   (`code-health impact <path>` command / `build_impact_report()`), not item 10. The phrase "built
   on top of" refers to the impact command, which this ticket already fully satisfies by rendering
   `build_impact_report()`'s output. No sentence in §L, §M, or the epic Problem statement asserts
   that the report generator needs snapshot *trend data* specifically.
4. **The sibling ticket's own citation, checked directly, does not establish a stronger claim.**
   The ticket's Assumptions section cites `stored_artifacts/TCK-20260819-.../investigation.md`
   "lines 14-15, 61-64" for the phrase "impact command → historical snapshots → PR report
   generator." That file is 67 lines total (confirmed via `wc -l`); lines 61–64 exist (they're the
   "Related" section's list of related tickets) but do not contain that phrase — the phrase itself
   is at lines 14–15 only, inside the "Origin" section, worded as a parenthetical describing *this
   epic's own extraction order* ("the next item in that epic's own dependency chain"), not as a
   functional-data-consumption claim. It is a ticket-sequencing note (this item comes third,
   because it wasn't independently scopable until the first two landed), not a design requirement
   that item 3 consume item 2's output data.

**Resulting scope determination**: per the ticket's own conditional Scope bullet 5 ("If design
does not require it, state explicitly that this iteration renders from `build_impact_report()`
output alone"), this iteration should render **from `build_impact_report()` output alone**. AC #4
is satisfied trivially and by design, not by building a graceful-degradation path against a real
dependency — there is no snapshot integration in this ticket's scope. This should be stated
explicitly in the new module's own docstring (mirroring how `codebase_health_snapshot.py`'s
docstring explicitly documents its own design decisions) so a future reader doesn't reintroduce a
false per-path/aggregate join.

### Other open items

- **The ticket's own Scope-bullet-2 field list is a paraphrase, not the literal field names** (see
  "Current Behavior" §1 table). Plan must decide explicitly which of the 13 real keys the rendered
  report surfaces — rendering all 13 (safest interpretation of "fully traceable... no impact
  logic duplicated... existing fields only") vs. a curated subset resembling the ticket's
  paraphrase (`target_path`, `resolved_symbols`, `required_tests_registry_hit_count`,
  `churn_lines_changed`, `edge_degree` are not named in the ticket's own list but are real fields
  of the object it must render "fully traceable" to). Recommend rendering all 13 — omitting real
  fields the underlying command computes would itself be a form of silently dropping data, which
  Scope bullet 3 explicitly forbids for the 3 degradation-signal fields and there is no principled
  reason to apply a different standard to the other 10.
- **Multi-path batching + partial-failure isolation (Scope bullet 6) has no existing precedent in
  this module family** — `build_impact_report()` itself is called once per path by its own `main()`
  today; nothing in `code_health_impact.py` batches multiple paths in one process. The new
  generator must call `build_impact_report()` once per target path independently and catch/report
  a per-path failure (e.g. a `find_file_node()` miss, or any other exception) without letting one
  bad path abort the whole batch — this is genuinely new orchestration logic (not
  impact-computation logic), squarely in scope.
- **No CLI convention exists yet for accepting *multiple* target paths** (`code_health_impact.py`'s
  `main()` takes exactly one positional `target_path`). Plan should decide `argparse` shape:
  `nargs="+"` on a single positional, repeated `--path` flags, or one path per line on stdin — no
  existing sibling precedent to copy verbatim, unlike the single-path case.

## Anti-Drift Hazards

- **Do not recompute or re-derive any of `build_impact_report()`'s 13 fields inside the new
  module.** The clearest anti-drift guard from the sibling ticket
  (`test_snapshot_payload_built_from_real_build_report_dict_not_reimplemented`) applies here with
  equal force — an equivalent test asserting the new module's rendered report is byte-traceable
  to a real `build_impact_report()` call's dict (not a re-implementation) should exist.
  `code_health_impact.py`'s own `format_impact_report()` is a **legitimate template to study**, not
  a function to import and wrap silently — the new module renders the *dict*, and may reuse
  formatting *conventions* (truncation, degradation phrasing) but should not just call the existing
  plain-text formatter and call it "the Markdown/JSON report," since AC #1 requires a rendered
  Markdown or JSON *artifact*, a different shape than `format_impact_report()`'s fixed-width plain
  text.
- **Do not add a snapshot/scorecard dependency "just in case."** Section above resolves this
  explicitly as out of scope for this iteration; re-litigating it mid-implementation (e.g. "while
  I'm here, let me wire in a trend line") would violate both the Out-of-Scope section and this
  investigation's own resolved conclusion.
- **Do not invent a single aggregate score.** AC #3 is explicit and mirrors the sibling ticket's own
  "no aggregate/combined score field, anywhere" guard almost verbatim — apply the same
  denylist-of-key-names test pattern (`score`/`overall`/`combined`/`summary`-shaped keys) to this
  ticket's own output shape.
- **Preserve the triage-aid framing text verbatim, not paraphrased away.** Multiple markdown
  renderers/summarizers have a natural pull toward trimming caveat language for brevity — the
  module docstring's own phrasing ("discovery/triage aid, not a certified coverage oracle") is the
  literal text AC language and Scope bullet 4 anchor to; test for its literal presence, not just
  "some caveat exists."
