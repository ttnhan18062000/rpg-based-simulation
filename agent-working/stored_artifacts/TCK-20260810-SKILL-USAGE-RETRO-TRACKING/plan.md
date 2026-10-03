---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260810-SKILL-USAGE-RETRO-TRACKING
artifact_type: plan
tags: [skills, agent-monitoring, observability, process-improvement]
---

# Implementation Plan — TCK-20260810-SKILL-USAGE-RETRO-TRACKING

## Summary

Wire `skill_usage_metric.py`'s `build_skill_usage_section` into `generate_retro.py`'s recurring
report by **relocating** the function into `generate_retro.py` (mirroring the exact,
twice-already-used house pattern for this exact class of circular-import constraint — see Design
Decision 1), with `skill_usage_metric.py` re-importing it back so its CLI stays byte-identical.
Add a new `## Skill Usage` section to `generate()`'s render with two subsections of genuinely
different scope: a **period-scoped** per-skill invocation count (trended report-over-report via a
new `index.md` column, mirroring Search Calls/Read Calls) and an **all-time** zero-invocation flag
(a new `compute_zero_invocation_skill_flags` function, also placed in `generate_retro.py`, never
in `skill_usage_metric.py`, so both the existing and new skill-domain logic live in one place). The
all-time subsection — and the `compute_zero_invocation_skill_flags` call feeding it — is computed
and rendered **only when the caller explicitly passes `all_tools` to `generate()`**; when
`all_tools` is not supplied (the vast majority of the 121+ pre-existing `test_generate_retro.py`
calls), the subsection is omitted entirely and the function is never invoked, so no call that
hasn't opted in can trigger a real, unmocked scan of `.claude/skills/*/SKILL.md` on disk (fix for a
confirmed architecture-review violation — see Step 4's revised Change text and Design Decision 3's
resolution).
The flag applies a resolved fail-open policy for skills with no `date_added` — see Design Decision
2 — split into two distinct, non-conflated buckets (`flagged_stale` for skills with a real
`date_added` older than the grace period, `flagged_unknown_age` for skills whose creation date
cannot be established) so the report never implies false certainty about a skill's real age. Tests
mirror the sibling ticket's established patterns (AST reuse guards, derivation checks, live-corpus
integration tests, synthetic-fixture regression tests) and re-derive all real-corpus expectations
live rather than hardcoding the ticket's now-stale 6-skills-all-zero snapshot. Docs (README.md,
`docs/guides/agent_monitoring.md`, `schema.md`) and a new `INFRA-333` parity ledger entry close out
the change.

## Design Decisions

### Design Decision 1 — import-direction / placement

**Resolved: relocate, mirror the sibling ticket's precedent exactly, apply it to both the existing
`build_skill_usage_section` and the new flag function.**

Evidence:
- `skill_usage_metric.py:19` — `from generate_retro import DEFAULT_TOOLS_FILE, load_jsonl`. This is
  the real, current one-directional import. Any top-level `from skill_usage_metric import
  build_skill_usage_section` added to `generate_retro.py` recreates the exact two-file cycle this
  repo has already hit once.
- `generate_retro.py:325-334` is the real, already-landed fix for the identical shape of problem:
  `SEARCH_TOOL_NAMES`, `build_search_count_section`, `build_raw_investigation_count_section` were
  relocated from `retrieval_baseline_metrics.py` into `generate_retro.py`
  (`TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING`), with the comment's own words: "semantics
  and membership unchanged, only the file of definition moved." `retrieval_baseline_metrics.py:30-35`
  shows the exact re-import-back shape (`from generate_retro import ..., SEARCH_TOOL_NAMES,
  build_search_count_section, build_raw_investigation_count_section`).
- Grepped this whole tree for any precedent of the alternative (a local/deferred import inside a
  function body used to dodge a circular import): zero matches anywhere in
  `tools/agent-monitoring/*.py`. Relocation is the only pattern this codebase has ever used for
  this exact problem, used twice already, with committed reasoning already in the file.
- Out of Scope forbids modifying `skill_usage_metric.py`'s "existing counting logic, regex, or
  output shape" — relocation changes none of those three; `build_skill_usage_section`'s body moves
  verbatim, byte-for-byte, and `skill_usage_metric.py`'s CLI (`main()`) keeps calling the same
  module-level name, now reached via re-import instead of local definition. All 12 existing tests
  in `tests/tools/test_skill_usage_metric.py` were read directly (lines 45-171) — none of them
  assert `build_skill_usage_section` is *defined* in `skill_usage_metric.py` via AST; they only
  import and call it (`from skill_usage_metric import build_skill_usage_section`, line 24) or shell
  out to its CLI. None require modification.

The new zero-invocation flag function is placed directly in `generate_retro.py` from the start (no
relocation needed — it never existed in `skill_usage_metric.py`), for the same reasoning: it's new
skill-domain logic, and putting it anywhere else would create a second, inconsistent resolution
pattern for what is structurally the identical cycle shape.

### Design Decision 2 — missing-`date_added` policy (AC2 sanity check)

**Resolved: fail-open, split into two distinct, non-conflated status buckets — `flagged_stale` and
`flagged_unknown_age`. Do not merge them into one undifferentiated "flagged" list.**

Corpus evidence, verified directly this session (not inferred from the investigation's prose):

- Direct `grep -m1 "^date_added:"` / `"^source:"` across all 22 `.claude/skills/*/SKILL.md` files
  found **9** skills with `date_added` (`api-design-principles`, `architecture` — both
  `2026-02-27`, `source: community`; `backend-testing`, `cognition-strategy`, `combat-mechanics`,
  `observability`, `progression-entities`, `simq-dev`, `systems-economy` — all `2026-08-05`,
  `source: project`), and **13** with neither field (`agent-monitoring-retro`, `brainstorming`,
  `create-tickets`, `debugging-strategies`, `doc-coauthoring`, `frontend-design`, `implement-epic`,
  `implement-ticket`, `prompt-builder`, `python-performance-optimization`,
  `python-testing-patterns`, `simq-audit`, `test-driven-development`). **This corrects
  investigation.md's "8 of 22" / "14 of 22" claim by one in each direction** — the real split is
  9/13, not 8/14. (Minor, non-blocking factual correction; flagging it here per the plan's
  fact-verification duty rather than silently propagating the off-by-one.)
- Ran `python3 tools/agent-monitoring/skill_usage_metric.py` directly against the real corpus this
  session: 233 total `Skill` invocations, 0 unparseable, 15 distinct skill names with >=1
  invocation. Cross-referencing that `per_skill` output against the 22-entry catalog: **15 of the
  22 project-level skills currently show zero invocations** (`api-design-principles`,
  `architecture`, `backend-testing`, `combat-mechanics`, `debugging-strategies`, `doc-coauthoring`,
  `frontend-design`, `observability`, `progression-entities`, `prompt-builder`,
  `python-performance-optimization`, `python-testing-patterns`, `simq-dev`, `systems-economy`,
  `test-driven-development`).
- Of those 15 zero-invocation skills, **7 have no `date_added`** (`debugging-strategies`,
  `doc-coauthoring`, `frontend-design`, `prompt-builder`, `python-performance-optimization`,
  `python-testing-patterns`, `test-driven-development`). **This directly falsifies the
  investigation's candidate "practical false-positive risk is low" resolution** — over half
  (7/13) of the no-`date_added` skills are zero-invocation *today*, so a naive fail-open design
  that dumps everything into one flagged list would immediately, and permanently (no age signal
  ever arrives for these skills), surface 7 skills at once with no way to distinguish "genuinely
  stale" from "we simply never recorded when this was authored."
- 3 of those 7 (`doc-coauthoring`, `python-testing-patterns`, `test-driven-development`) are also
  named in `TCK-20260705-SIX-SKILLS-INVESTIGATION`'s prior "correctly redundant" verdict set. Per
  this ticket's own Out of Scope and investigation.md's Prior Work section, the new flag firing on
  them again is explicitly expected and not a re-litigation — but conflating them with a
  *confirmed*-age flag (as if the flag "proved" they're N days idle, which is unknowable for them)
  would read as a stronger, more alarming claim than the data supports.

Resolution: `compute_zero_invocation_skill_flags` returns two separate lists instead of one:
- `flagged_stale` — skill has a real, parseable `date_added` older than the grace period AND zero
  invocations. A confirmed-age signal.
- `flagged_unknown_age` — skill has no `date_added` (missing or unparseable) AND zero invocations.
  An honest "cannot prove this is genuinely stale, but it has zero invocations and no recorded
  authorship date" signal — this is the fail-open bucket that makes `backend-testing`'s real
  pre-`TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED` state (no `date_added`, no `source`, zero
  invocations — confirmed via `TCK-20260705-SIX-SKILLS-INVESTIGATION`'s independently-verified
  `backend-testing` 0/41 finding) correctly appear in the flag output, satisfying AC2's literal
  "correctly would have flagged `backend-testing`" requirement, without collapsing it into the same
  certainty class as a skill with a real, old `date_added`.

This resolution is not left as an "Unresolved Question" — it is a defensible, corpus-evidenced
design captured here and in Step 3's Change text.

### Design Decision 3 — period-scoped vs. all-time (new, load-bearing, not flagged by investigation)

Investigation did not surface this, but it is required for AC2 to be correct on every report type
`generate_retro.py` produces (`--week`, `--days N`, `--all`), not just `--all`.

- `generate()`'s existing `tools` argument (`generate_retro.py:1027`) is **period-scoped** —
  `main()` (`:1514-1546`) slices `all_tools` down to the reporting window before calling `generate(
  ..., tools=tools)`. This is correct for every existing additive section (Search & Investigation
  Effort, Tool Safety Audit, Parity Index Read-Path Usage) because those are legitimately
  per-period counts.
- The zero-invocation flag is fundamentally **not** a per-period question — "has this skill ever
  been invoked" must be answered against the whole corpus regardless of which week's report is
  being rendered, or a skill invoked heavily in a prior week (but not in this week's slice) would
  incorrectly read as zero-invocation in a `--week` report. AC2's own phrasing ("correctly excludes
  the 6 domain skills *today*") implies exactly this cumulative, point-in-time semantics.
- Resolution: `generate()` gains a new optional parameter, `all_tools=None`. **Revised per
  architecture-review NEEDS_CHANGES (2026-08-15): there is no `tools`-fallback for `all_tools`.**
  The original draft of this decision had `all_tools` default to `tools or []` when not supplied,
  which the architecture-reviewer confirmed reaches `compute_zero_invocation_skill_flags` — whose
  own `skills_dir` parameter itself defaults to the real, on-disk `_DEFAULT_SKILLS_DIR`
  (`.claude/skills`) — for every one of the 121+ pre-existing `test_generate_retro.py` calls that
  pass only `tools=`/no arguments at all, silently coupling those synthetic-fixture tests' output to
  the live state of the real skills catalog on Day 1. The fix (architecture-reviewer's option 1):
  `compute_zero_invocation_skill_flags` is called, and the Zero-Invocation Flags subsection is
  rendered, **only when `all_tools is not None` as the caller's own literal argument** — never
  substituted from `tools`. When `all_tools` is not supplied, the whole subsection (and the function
  call feeding it) is omitted, not degraded. `main()` (`:1514-1522`, where `all_tools =
  load_jsonl(DEFAULT_TOOLS_FILE)` is already computed) passes it through explicitly:
  `generate(runs, events, label, week_str, tools=tools, all_tools=all_tools)` — `main()`'s real call
  path is completely unaffected by this stricter gate, since it already supplies a real, explicit,
  non-None `all_tools` on every invocation. The period-scoped per-skill count section (AC1) stays on
  `tools`, unchanged from every other section's convention. See Step 4 for the exact gating logic
  and the new isolation-guard test this fix requires.
- `index.md`'s new trend column (Step 2) reports the *period*-scoped `total_skill_invocations` per
  report row (a real week-over-week trend, mirroring Search Calls/Read Calls) — the flag buckets
  are deliberately **not** added as an index.md column, since an all-time value would render
  identically in every row and wouldn't be a real trend; this is called out explicitly so no future
  reader "fixes" this as a missing column.

## Steps

### Step 1 — Relocate `build_skill_usage_section` into `generate_retro.py`

**Files:** `tools/agent-monitoring/generate_retro.py`, `tools/agent-monitoring/skill_usage_metric.py`

**Change:** Move `build_skill_usage_section`'s full body (`skill_usage_metric.py:28-66`, including
the module-level `_SKILL_NAME_RE` regex at `:24` it depends on) into `generate_retro.py`, placed
near the other `build_*`/`compute_*` section functions (alongside `build_search_count_section` at
`:342`, matching that function's own placement precedent after its relocation). Copy verbatim — no
change to the regex, the `unattributed`/`unparseable` bucketing, or the returned dict shape (Out of
Scope). In `skill_usage_metric.py`, replace the local function definition and `_SKILL_NAME_RE` with
a re-import: `from generate_retro import DEFAULT_TOOLS_FILE, load_jsonl, build_skill_usage_section`
(extending the existing import at `:19`), matching `retrieval_baseline_metrics.py:30-35`'s exact
re-import shape. `skill_usage_metric.py`'s `main()` (`:69-86`) requires zero further edits — it
already calls the module-level name `build_skill_usage_section`, which now resolves via re-import
instead of local definition.

**Do NOT touch:** `_SKILL_NAME_RE`'s pattern, the `unattributed`/`unparseable` bucketing logic, the
`derivation` string's wording, `skill_usage_metric.py`'s `main()`/CLI argument parsing, or
`manifest._assert_safe_output_path` usage.

**Verify:** All 12 existing tests in `tests/tools/test_skill_usage_metric.py` pass unmodified
(`test_reuses_generate_retro_loader_not_a_second_loader`, `test_never_calls_json_loads_on_input_summary`,
`test_causes_zero_diff_on_real_corpus`, `test_cli_runs_against_real_corpus_and_prints_json`, and the
remaining 8). New: `test_generate_retro_imports_build_skill_usage_section_not_a_reimplementation`
(AST guard confirming `generate_retro.py` now defines, not duplicates, the function).

---

### Step 2 — Wire the period-scoped `## Skill Usage` count subsection into `generate()` and `index.md`

**Files:** `tools/agent-monitoring/generate_retro.py`

**Change:** In `generate()` (`:1027-1038`), add `su = build_skill_usage_section(tools or [])`
alongside the existing `pircc = compute_parity_index_readpath_call_count(tools or [])` line. Render
a new `## Skill Usage` heading with a `### Per-Skill Invocation Counts (This Period)` subsection,
placed after `## Parity Index Read-Path Usage` (`:1495-1503`) and before `## Notes`
(`:1508`) — a table of skill name -> count from `su["per_skill"]`, the `su["total_skill_invocations"]`
total, and `su["derivation"]` rendered via `lines.append(f"_{su['derivation']}_")`, matching the
Parity Index Read-Path Usage section's exact rendering convention (`:1503`). Gate this subsection
conditionally — omitted when `su["total_skill_invocations"] == 0` for the period — mirroring
Search & Investigation Effort's own gate (`:1417`, `if sc["total"] + ric["total"] > 0`), not the
Parity Index Read-Path Usage always-render exception (that exception is specific to a reviewed-GO,
zero-call-site read path — a different situation from ordinary per-period skill usage, which
legitimately has empty periods). In `_update_index()` (`:1561-1601`), add a new `Skill Invocations`
column to the trend table (`:1567`'s header, `:1596`'s row-append), computed the same way Search
Calls/Read Calls already are (`:1592-1594`): `build_skill_usage_section(week_tools)["total_skill_invocations"]`,
reusing the same `week_tools` slice already built there.

**Do NOT touch:** the Zero-Invocation Flags subsection (Step 4) — that is all-time-scoped and lives
in a separate subsection under the same `## Skill Usage` heading, added by Step 4, not this step.
Do not add a flags-count column to `index.md` (Design Decision 3).

**Verify:** `test_skill_usage_section_present_in_generated_report`,
`test_skill_usage_section_matches_real_corpus_counts`, `test_skill_usage_trend_column_in_retro_index`,
`test_skill_usage_section_has_derivation`.

---

### Step 3 — Add `compute_zero_invocation_skill_flags` (pure function, no rendering)

**Files:** `tools/agent-monitoring/generate_retro.py`

**Change:** Add a new module-level constant, `SKILL_ZERO_INVOCATION_GRACE_PERIOD_DAYS = 14`, placed
near `SEARCH_TOOL_NAMES` (`:325-334`)'s constant block, with a comment citing the corroborating
evidence from investigation.md's Risk 3 (6 domain skills are 10 days old today, still inside a
14-day window; `SIX-SKILLS-INVESTIGATION`'s pre-existing skills stayed zero past 30+ days
regardless of grace length, so grace-period length mainly protects genuinely-new skills). Add
`_DEFAULT_SKILLS_DIR = _DEFAULT_TICKETS_ROOT / ".claude" / "skills"` next to `_DEFAULT_TICKETS_ROOT`
(`:58`, confirmed to already resolve to the real repo root — `generate_retro.py` lives at
`tools/agent-monitoring/generate_retro.py`, and `.parent.parent.parent` from that file is the repo
root, matching the existing comment at `:57`).

Add `compute_zero_invocation_skill_flags(tools: list, skills_dir: Path | None = None, today: date | None
= None) -> dict`:
- `skills_dir = skills_dir or _DEFAULT_SKILLS_DIR`; `today = today or datetime.now(timezone.utc).date()`
  (accepting both as parameters, not reading wall-clock/filesystem-default internally by default,
  keeps the function's own unit tests deterministic — CLAUDE.md's "do not break determinism"). This
  function's own real-filesystem `skills_dir` default is intentional and stays as-is — it is what
  makes `main()`'s real call path correct without any extra wiring. It is only safe because, per
  Step 4's revised gating (architecture-review fix), `generate()` never reaches this function unless
  the caller explicitly supplied `all_tools`; unit tests that exercise this function's own
  zero-invocation logic (this step's Verify list) call it directly with an explicit `skills_dir`
  (a `tmp_path` fixture), never relying on the real-filesystem default themselves.
- Call `build_skill_usage_section(tools)` (the Step 1 relocated function — reuse, not
  reimplementation) once, and read its `per_skill` dict.
- Iterate `sorted(skills_dir.iterdir())`, skip anything without a `SKILL.md` file. For each real
  skill directory: if `per_skill.get(name, 0) > 0`, never flag it (regardless of age) — matches
  test plan's `test_zero_invocation_flag_excludes_skill_with_nonzero_invocations_regardless_of_age`.
  Otherwise, call `extract_frontmatter(skill_md.read_text())` — **already imported into
  `generate_retro.py` at `:29-32`** (`from validate_frontmatter import ..., extract_frontmatter`,
  confirmed by direct read; zero new import needed, strongest possible reuse). Wrap in
  `try/except ValueError` (this function raises `ValueError` on malformed frontmatter, confirmed at
  `tools/validate_frontmatter.py:82`/`:89` — `"Unparseable frontmatter line"`/`"Empty key"`); on
  exception, record the skill name in a `catalog_parse_errors` list and treat it as unknown-age
  (fall through to the missing-`date_added` branch below — a parse failure is not a reason to
  silently exclude a skill from the flag, per Design Decision 2's fail-open reasoning applied
  consistently).
  - If `fm` is `None` (no frontmatter block at all) or `fm.get("date_added")` is falsy: append to
    `flagged_unknown_age`.
  - Else, parse `date_added` via `datetime.strptime(date_added, "%Y-%m-%d").date()`; on
    `ValueError` (malformed date string), also append to `flagged_unknown_age` (cannot establish
    age). Otherwise compute `(today - added_date).days`; if `>= SKILL_ZERO_INVOCATION_GRACE_PERIOD_DAYS`,
    append to `flagged_stale`; otherwise (still within grace period) do not flag at all.
- Return `{"grace_period_days": SKILL_ZERO_INVOCATION_GRACE_PERIOD_DAYS, "flagged_stale":
  sorted(...), "flagged_unknown_age": sorted(...), "catalog_parse_errors": sorted(...), "derivation":
  <see below>}`.
- `derivation` string must explicitly state the fail-open policy per Design Decision 2 (required by
  `test_grace_period_missing_date_added_policy_is_explicit_not_accidental`): state that
  `flagged_stale` requires a real, parseable `date_added` older than the grace period, that
  `flagged_unknown_age` covers skills with no (or unparseable) `date_added` and zero invocations —
  explicitly named as a lower-certainty signal, not proof of staleness — and that this fail-open
  choice is what makes `backend-testing`'s real pre-`TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED`
  state (no `date_added` at all) correctly flaggable, per this ticket's AC2.
- Never write to `.claude/skills/` or anywhere else — read-only (`skill_md.read_text()`,
  `skills_dir.iterdir()` only; no `Path.write_text`/`open(..., "w")` anywhere in the function body).

**Other writers to `.claude/skills/*/SKILL.md`:** grepped for any other code path that writes to
`.claude/skills/`; none found in `tools/` or `src/` — SKILL.md files are hand-authored/edited by
agents via `Edit`/`Write` tool calls during skill-authoring tickets, never by an automated script.
This function is the first automated *reader* of the catalog as a whole; there is no concurrent
writer to race against within a single `generate_retro.py` invocation, and the function's own
read-only guarantee (verified by the architecture-guard tests below) means it cannot corrupt
anything even if a SKILL.md is mid-edit by a human/agent in a separate process — worst case is a
transient `ValueError` on a half-written frontmatter block, already handled by the
`catalog_parse_errors` path.

**Do NOT touch:** `build_skill_usage_section`'s own logic (call it, don't inline a second
extraction pass). Do not add any deprecation/removal/auto-invocation side effect keyed off
`flagged_stale`/`flagged_unknown_age` (Out of Scope).

**Verify:** `test_zero_invocation_flag_excludes_skill_within_grace_period`,
`test_zero_invocation_flag_includes_skill_past_grace_period_with_zero_invocations`,
`test_zero_invocation_flag_excludes_skill_with_nonzero_invocations_regardless_of_age`,
`test_backend_testing_pre_fix_state_would_have_been_flagged`,
`test_zero_invocation_flag_function_never_crashes_on_malformed_skill_md`,
`test_zero_invocation_flag_catalog_scan_is_pure_no_file_mutation`,
`test_grace_period_missing_date_added_policy_is_explicit_not_accidental`.

---

### Step 4 — Wire zero-invocation flags into `generate()`'s render, thread `all_tools`

**Files:** `tools/agent-monitoring/generate_retro.py`

**Change:** Add `all_tools=None` parameter to `generate()`'s signature (`:1027`) — **no `tools`
fallback of any kind.** This step was returned `NEEDS_CHANGES` by architecture-review on
2026-08-15; the fix below replaces the originally-planned `all_tools if all_tools is not None else
(tools or [])` substitution, which the reviewer confirmed causes every one of the 121+ pre-existing
`test_generate_retro.py` calls that pass only `tools=` (or no tools argument at all) to silently
invoke `compute_zero_invocation_skill_flags` against the real, unmocked `.claude/skills/*/SKILL.md`
catalog on disk (`compute_zero_invocation_skill_flags`'s own `skills_dir` parameter defaults to the
real `_DEFAULT_SKILLS_DIR` — Step 3), injecting live `flagged_stale`/`flagged_unknown_age` skill
names into dozens of tests whose fixtures never asked for this feature.

Inside `generate()`'s body:
- `zif = compute_zero_invocation_skill_flags(all_tools) if all_tools is not None else None` — the
  function is called **only** when the caller's own literal argument is non-`None`. `tools` is
  never read or substituted for this purpose anywhere in this branch.
- Render the `### Zero-Invocation Flags (All-Time, {grace_period_days}-Day Grace Period)`
  subsection under the same `## Skill Usage` heading added in Step 2 (after the per-period counts
  subsection) only when `zif is not None and (zif["flagged_stale"] or zif["flagged_unknown_age"])`
  — list `flagged_stale` and `flagged_unknown_age` under clearly separate labels (never merged into
  one undifferentiated list — Design Decision 2), and render `zif["derivation"]` via the same
  `_{...}_` convention as every other section.
- Gate the whole `## Skill Usage` heading (not just this subsection) as: render if
  `su["total_skill_invocations"] > 0 or (zif is not None and (zif["flagged_stale"] or
  zif["flagged_unknown_age"]))`. The `zif is not None` short-circuit is load-bearing — it must be
  evaluated before either flag list is dereferenced, so a caller that never supplied `all_tools`
  can never hit a `NoneType` access, and (more importantly) never triggers the real-filesystem scan
  as a side effect of merely checking whether there's something to render.
- In `main()` (`:1514-1522`, `:1546`), pass the already-computed `all_tools` through explicitly:
  `report = generate(runs, events, label, week_str, tools=tools, all_tools=all_tools)`. `main()`'s
  real call path already computes `all_tools` unconditionally and passes it as a real, non-`None`
  value, so it is completely unaffected by this stricter gate — the Zero-Invocation Flags
  subsection continues to render for the production report exactly as originally intended.

**New test (required by this fix, isolation guard):**
`test_generate_without_all_tools_never_computes_zero_invocation_flags` — monkeypatches
`generate_retro.compute_zero_invocation_skill_flags` to a stub that raises `AssertionError` if
called at all, then calls `generate(runs, events, "test-label", tools=<synthetic tools fixture
with >=1 Skill invocation>)` with no `all_tools` argument supplied — mirroring the calling
convention of the vast majority of the 121+ pre-existing tests. Asserts no exception is raised
(proving the function is never invoked, not merely that its result goes unrendered) and that the
returned Markdown contains no `### Zero-Invocation Flags` heading text. This is the direct
regression guard for the confirmed architecture-review violation: it fails loudly if any future
edit reintroduces a `tools`-based fallback or any other path that reaches
`compute_zero_invocation_skill_flags` without an explicit `all_tools` argument.

**Do NOT touch:** `_update_index()` — the flag buckets are explicitly not added as an index.md
column (Design Decision 3). Do not change `main()`'s existing per-period `tools` slicing logic
(`:1523-1545`) — `all_tools` is threaded through as an additional argument, not a replacement. Do
not reintroduce any `tools`-derived default, substitution, or "best effort" value for `all_tools`
inside `generate()` — `compute_zero_invocation_skill_flags` must only ever be reached when the
caller's own `all_tools` argument is explicitly non-`None`.

**Verify:** `test_zero_invocation_flag_current_domain_skills_all_excluded_on_real_corpus`,
`test_backend_testing_post_fix_state_not_currently_flagged`, `test_zero_invocation_flag_has_derivation`,
`test_all_new_sections_have_derivation_key` (extended), `test_new_sections_never_write_any_file`
(extended), `test_flagged_skills_list_never_auto_triggers_downstream_action`,
`test_six_domain_skills_verdict_not_reopened`,
`test_generate_without_all_tools_never_computes_zero_invocation_flags` (new).

---

### Step 5 — Tests

**Files:** `tests/tools/test_generate_retro.py`, `tests/tools/test_skill_usage_metric.py` (verify-only,
no edits expected per Step 1's analysis)

**Change:** Add every new test named across Steps 1-4's Verify lines to `test_generate_retro.py`,
following the file's existing structural convention (a `# --- ## Skill Usage (ACx) ---` comment
banner, matching the `## Parity Index Read-Path Usage (AC3)` banner at `:2058`). Extend the two
existing cross-cutting tests rather than duplicating them:
`test_all_new_sections_have_derivation_key` (`:2106-2115`) gets
`compute_zero_invocation_skill_flags([])` and `build_skill_usage_section([])` added to its
assertion list; `test_new_sections_never_write_any_file` (`:2118-2133`) gets both new functions
added to its `inspect.getsource` string-absence loop. Run
`tests/tools/test_skill_usage_metric.py`'s existing 12 tests unmodified as a regression check
(Step 1's relocation must not require touching this file). Include
`test_generate_without_all_tools_never_computes_zero_invocation_flags` (Step 4) — this is the
direct regression guard for the architecture-review fix and must not be dropped or weakened.

**Do NOT touch:** any assertion inside the 121+ pre-existing tests in `test_generate_retro.py` for
sections this ticket doesn't change (Tag Breakdown, Outliers, Retrieval Quality, Shadow vs.
Baseline, Search & Investigation Effort, Tool Safety Audit). Do not hardcode the ticket's
2026-08-10 snapshot ("6 domain skills all zero") anywhere — `cognition-strategy` already drifted to
1 real invocation as of this session; `test_zero_invocation_flag_current_domain_skills_all_excluded_on_real_corpus`
must assert "not flagged" (true either via grace period or nonzero count), never "exactly 6 skills
show zero."

**Verify:**
```
pytest tests/tools/test_generate_retro.py tests/tools/test_skill_usage_metric.py -v
```

---

### Step 6 — Docs updates

**Files:** `docs/agent-monitoring/README.md`, `docs/guides/agent_monitoring.md`,
`docs/agent-monitoring/schema.md`

**Change:**
- `docs/agent-monitoring/README.md`: append a dated addendum paragraph under the existing "##
  Skill Usage Metric" section (ends after its "Built by `TCK-20260805-SKILL-USAGE-METRIC`..."
  sentence), mirroring the exact "**2026-08-14 — `search_count`/`raw_investigation_count` now also
  feed the recurring cadence**" addendum already in this file (immediately below the Baseline
  Metrics Snapshot section). State: `build_skill_usage_section` was relocated into
  `generate_retro.py` (this module now re-imports it) to resolve the same circular-import
  constraint as the `search_count`/`raw_investigation_count` precedent; `generate()` now renders a
  `## Skill Usage` section with a period-scoped per-skill count subsection (trended via
  `index.md`'s new Skill Invocations column) and an all-time, two-bucket zero-invocation flag
  subsection (`flagged_stale` / `flagged_unknown_age`, `{N}`-day grace period, fail-open on missing
  `date_added` — cite `TCK-20260810-SKILL-USAGE-RETRO-TRACKING`).
- `docs/guides/agent_monitoring.md`: add a new `**Skill Usage**` row to the Report Sections table
  (`:55-72`), styled like the existing `**Tool Safety Audit**`/`**Search & Investigation Effort**`
  rows — describe both subsections' distinct scoping (period vs. all-time) explicitly, since that
  distinction (Design Decision 3) is exactly the kind of thing a future reader would otherwise
  misread as a bug.
- `docs/agent-monitoring/schema.md`: the `input_summary` row in the Fields table (`:365`) currently
  lists per-tool shapes for `Read`/`Edit`/`Write`/`MultiEdit`/`Bash`/`Agent` but has **no `Skill`
  case** (confirmed by direct read — this is a real, pre-existing documentation gap, not a
  "minimal cross-reference," contrary to investigation.md's hedge). Add a `Skill` case to that
  row's prose: `input_summary` is a Python dict-repr string containing a `'skill'` key (e.g.
  `"{'skill': 'graphify', ...}"`), not JSON — extracted via regex (never `json.loads()`) by
  `build_skill_usage_section` (`generate_retro.py`, relocated from `skill_usage_metric.py` by
  `TCK-20260810-SKILL-USAGE-RETRO-TRACKING`).

**Do NOT touch:** `docs/ai/skills.md` — not named in the ticket's AC5, not flagged in
investigation.md's Docs Requiring Update list; out of this plan's scope even though it's listed
under the ticket's Related Docs (that list is "related," not "requires an edit").

**Verify:** No pytest test enforces doc prose directly (matches existing convention — confirmed no
test file greps README.md's prose). Verified via `tools/doc_staleness_check.py` at Finalize and
manual done-checker review against this step's bullets.

---

### Step 7 — Parity ledger entry

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Add a new entry, `id: INFRA-333` (confirmed next-available — `INFRA-332` is the latest
existing entry in this file, at line 8439), following the `INFRA-281`-`INFRA-332` continuous-run
"agent-tooling-infrastructure" shape exactly (same fields as `INFRA-332`'s own entry: `status:
verified`, `priority: P2`, `legacy_evidence: null`, `v2_evidence` citing real `file:line` for
`build_skill_usage_section`'s new location, `compute_zero_invocation_skill_flags`, and the two new
`generate()` render subsections, `proof_type: regression`, `test_path:
tests/tools/test_generate_retro.py`, `divergence_note: null`, `support_boundary`: agent-monitoring
tooling only, no `src/` touched, no simulation behavior). This follows the actually-followed
precedent (`TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING`'s own entry was "added
independently during the Parity phase" overriding its own investigation's "no entry needed"
conclusion) rather than `TCK-20260805-SKILL-USAGE-METRIC`'s older, since-superseded "no `src/`
touched -> no entry needed" reasoning. This step is expected to be finalized by the Parity phase
(parity-updater agent) against the actual landed `v2_evidence` line numbers, per that same
precedent — this plan supplies the draft shape and citations so that phase has what it needs
without re-deriving them from scratch.

**Do NOT touch:** any existing `INFRA-*` entry's text, status, or evidence.

**Verify:** `python3 tools/parity_index.py health` (or equivalent parity-ledger validation already
run at Finalize) passes with the new entry present and schema-valid.

## Scope Guards

- Do not modify `build_skill_usage_section`'s regex (`_SKILL_NAME_RE`), counting logic, or output
  dict shape — Step 1 is a verbatim relocation only.
- Do not modify any of the 12 existing tests in `tests/tools/test_skill_usage_metric.py`.
- Do not auto-invoke, auto-deprecate, or otherwise act on any skill in `flagged_stale` or
  `flagged_unknown_age` — this ticket is visibility-only. No step writes to `.claude/skills/`.
- Do not re-litigate or reference `TCK-20260705-SIX-SKILLS-INVESTIGATION`'s six prior verdicts as
  confirmed, overturned, or re-scored in any new test, doc, or derivation string — the flag is a
  forward-looking signal only.
- Do not add a zero-invocation-flag column to `agent-monitoring/retro/index.md` (Design Decision
  3) — only the period-scoped `Skill Invocations` count is trended there.
- Do not touch `docs/ai/skills.md`.
- Do not change `main()`'s existing per-period `tools`/`events`/`run_ids` slicing logic
  (`generate_retro.py:1523-1545`) beyond adding the `all_tools=` passthrough.
- Do not hardcode the ticket's 2026-08-10 "6 domain skills, all zero" snapshot in any test —
  `cognition-strategy` has already drifted to a real nonzero count.
- Do not let `generate()` substitute `tools` (or any other implicit default) for a missing
  `all_tools` argument to compute or render the Zero-Invocation Flags subsection —
  `compute_zero_invocation_skill_flags` must only be called when the caller explicitly passes a
  non-`None` `all_tools`; when it isn't supplied, the subsection (and the underlying call) must be
  omitted entirely, never degraded into a real-filesystem `.claude/skills/` scan (architecture-review
  fix, 2026-08-15 — see Step 4).

## Dependency Map

- Step 1 has no dependencies (pure relocation).
- Step 2 depends on Step 1 (`build_skill_usage_section` must live in `generate_retro.py` first).
- Step 3 depends on Step 1 (reuses the relocated function) but is otherwise independent of Step 2.
- Step 4 depends on Step 3 (renders its output) and touches the same `generate()`/`main()` region
  as Step 2 — implement Step 2 before Step 4 to avoid rebasing the same `lines.append` block twice.
- Step 5 depends on Steps 1-4 (tests the landed functions/signatures).
- Step 6 depends on Steps 1-4 (docs describe landed behavior) but has no code dependency and could
  be done in parallel with Step 5.
- Step 7 depends on Steps 1-4 (needs real `file:line` evidence from the landed diff) and is
  expected to be finalized at the Parity phase, not necessarily by the implementer.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — real `## Skill Usage` section, real per-skill counts, reuses `build_skill_usage_section` | Steps 1, 2 | `test_generate_retro_imports_build_skill_usage_section_not_a_reimplementation`, `test_skill_usage_section_present_in_generated_report`, `test_skill_usage_section_matches_real_corpus_counts` |
| AC2 — zero-invocation-after-grace-period flag excludes 6 domain skills today, correctly would have flagged `backend-testing` pre-fix | Steps 3, 4 | `test_zero_invocation_flag_current_domain_skills_all_excluded_on_real_corpus`, `test_backend_testing_pre_fix_state_would_have_been_flagged`, `test_backend_testing_post_fix_state_not_currently_flagged`, `test_zero_invocation_flag_excludes_skill_within_grace_period`, `test_zero_invocation_flag_includes_skill_past_grace_period_with_zero_invocations` |
| AC3 — every new section has a `derivation` string | Steps 2, 3, 4 | `test_skill_usage_section_has_derivation`, `test_zero_invocation_flag_has_derivation`, `test_all_new_sections_have_derivation_key` |
| AC4 — new tests mirror existing patterns (never-silent, derivation-matches-fields, real-corpus, reuse-not-reimplement AST guards) | Step 5 | `test_new_sections_never_write_any_file`, `test_zero_invocation_flag_function_never_crashes_on_malformed_skill_md`, `test_zero_invocation_flag_catalog_scan_is_pure_no_file_mutation`, `test_grace_period_missing_date_added_policy_is_explicit_not_accidental`, `test_flagged_skills_list_never_auto_triggers_downstream_action`, `test_six_domain_skills_verdict_not_reopened`, `test_generate_without_all_tools_never_computes_zero_invocation_flags` |
| AC5 — `docs/agent-monitoring/README.md`/`schema.md` updated | Step 6 | `tools/doc_staleness_check.py` (no pytest coverage of doc prose, matches convention) |

## Anti-Drift Notes

- The relocation in Step 1 must be verbatim — if any test asserts specific counting behavior
  differs after the move, that is a real bug introduced by the move, not an acceptable side
  effect; stop and fix rather than adjusting the test.
- Design Decision 3 (period vs. all-time scoping) is easy to silently regress if a future edit
  simplifies `generate()`'s two `su`/`zif` computations down to a single `tools`-scoped call — the
  zero-invocation flag would then silently become wrong for every `--week`/`--days` report while
  still looking correct for `--all`. The `all_tools` parameter and its distinct usage must survive
  any later refactor.
- `flagged_stale` and `flagged_unknown_age` must never be merged into one list or rendered under
  one undifferentiated heading — that would recreate exactly the false-certainty problem Design
  Decision 2 exists to avoid, and would make it look like the flag "proved" an unknown-age skill is
  stale.
- `SKILL.md` frontmatter parsing must go through `extract_frontmatter` (already imported at
  `generate_retro.py:29-32`) — do not add a second hand-rolled YAML/regex frontmatter parser for
  this purpose; that would violate the same reuse-not-reimplement discipline this codebase already
  enforces for `build_skill_usage_section` and `load_jsonl`.
- The corrected 9/13 `date_added` split (Design Decision 2) should be reflected if `investigation.md`
  is revisited later, but is not itself an in-scope edit for this plan/implementation pass.
- Step 4's `zif = compute_zero_invocation_skill_flags(all_tools) if all_tools is not None else
  None` gate must never be weakened back into a `tools`-fallback substitution (e.g. `all_tools or
  tools`) — that reintroduces the confirmed architecture-review violation: a silent, real
  `.claude/skills/` filesystem scan on every one of the 121+ pre-existing calls that don't supply
  `all_tools`. `test_generate_without_all_tools_never_computes_zero_invocation_flags` (Step 4) exists
  specifically to catch this regression and must not be removed or loosened in a future edit.
