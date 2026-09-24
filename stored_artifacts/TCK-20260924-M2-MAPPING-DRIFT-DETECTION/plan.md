---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260924-M2-MAPPING-DRIFT-DETECTION
artifact_type: plan
tags: [architecture, schema, registry]
---

# Implementation Plan — TCK-20260924-M2-MAPPING-DRIFT-DETECTION

## Summary

Build a new, report-only module `tools/semantic_control_plane/mapping_drift_check.py` that mirrors
`tools/mechanism_registry/mechanism_registry_changed_code_check.py`'s three-entry-point shape (pure
core / git wrapper / CLI), implementing two of `roadmap.md` M2's three named drift classes —
class 1 (cited `implemented_by` code changed since a row's own `date`) and class 3 (a mapped
mechanism's `verified.verdict` changed since the row's own `review_date`, recovered from
`registries/mechanisms.yaml` git history pinned to the specific commit that last touched the citing
row rather than an independent, same-day-ambiguous date search) — and consciously descopes class 2
(split/merge with a resolvable ID) with the written reason investigation.md already established: no
lineage field exists anywhere in the schema, and the one real precedent case is undetectable without
duplicating `mechanism_registry_changed_code_check.py`'s own whole-entry-diff approach on a new axis,
for a scenario that has not occurred once among M1's five mapped mechanisms. A `make
semantic-control-plane-drift-check` target wires it up; a new test module
`tests/unit/tools/test_semantic_control_plane_drift_detector.py` proves each implemented class fires
on a deliberately-planted fixture (never just clean-data), proves the report-only/exit-0 contract,
proves the detector never mutates the committed registries, and proves every echoed status word
resolves to `docs/plans/status_axis_model.md`'s vocabulary. The plan closes by running the detector
against M1's live Territory mapping, recording the real result in the ticket's Completion Summary,
and updating `roadmap.md`'s M2 section plus the epic ticket's milestone-disposition table to reflect
shipped state.

## Steps

### Step 1 — Drift class 1: cited-code-changed-since-review, pure core + tests

**Files:** `tools/semantic_control_plane/mapping_drift_check.py` (new),
`tests/unit/tools/test_semantic_control_plane_drift_detector.py` (new)

**Change:** Create the new module. Add a frozen dataclass `CitedCodeDriftFinding(rule_id: str,
mechanism_id: str, edge_type: str, row_date: str, changed_paths: List[str])`. Add the pure-core
function:

```python
def check_cited_code_drift(
    edge_rows: List[dict], file_last_commit_dates: Dict[str, str],
) -> List[CitedCodeDriftFinding]:
```

`edge_rows` is `rule_mechanism_edges.yaml`'s own `edges:` list, already loaded (confirmed shape —
`rule_id, mechanism_id, edge_type, evidence, date`, `registries/rule_mechanism_edges.yaml:31-38` for
one real row). For each row, resolve its mapped mechanism's `implemented_by` citations by loading
`registries/mechanisms.yaml` (via `tools.mechanism_registry.registry.MechanismRegistry`, confirmed
`get_verification`/entry access pattern at `tools/mechanism_registry/registry.py:157-171,200-205`)
and calling `tools.mechanism_registry.registry.parse_implemented_by_entry` (confirmed signature
`(entry: str) -> Tuple[str, Optional[str]]`, `tools/mechanism_registry/registry.py:101-108`) on each
`implemented_by` string to get the bare path — **reuse this function, do not re-parse the `::`
suffix**, per the ticket's own Scope instruction. `file_last_commit_dates` is a pre-resolved
`{path: "YYYY-MM-DD"}` map the git wrapper (Step 4) builds — **the core function takes no git
dependency and does no file I/O**, mirroring `check_drift(old_data, new_data, changed_files)`'s own
purity contract (`tools/mechanism_registry/mechanism_registry_changed_code_check.py:14-18,87-102`).
A row is a finding when any cited path's resolved last-commit date is strictly after the row's own
`date` string (conservative same-day reading, per the ticket's own "Open (not blocking)" instruction:
a same-day code change counts as changed-since-review, i.e. only `changed_paths` where
`file_last_commit_dates[path] > row["date"]`, not `>=`).

Add tests in the new test module (mirrors
`tests/unit/tools/test_mechanism_registry_changed_code_check.py:35-97`'s positive/negative-control
shape):
- `test_pure_core_takes_no_git_dependency` — asserts `check_cited_code_drift` and (after Step 2)
  `check_verdict_drift` import cleanly and run against plain dicts/strings with no `subprocess` or
  `git` call reachable from their own code path (inspect via `inspect.getsource` grep for
  `subprocess`/`git` tokens, or a monkeypatched-away `subprocess.run` that must never be invoked).
- `test_drift_class_1_fires_on_planted_stale_citation` — a synthetic edge row with a resolved
  `file_last_commit_dates` entry after the row's own `date` produces a finding.
- `test_drift_class_1_silent_when_cited_file_unchanged_since_review` — same row, but the resolved
  date is on/before the row's own `date`, produces no finding.

**Do NOT touch:** `tools/semantic_control_plane/registry.py`, `rule_catalog.py`, or
`generate_territory_control_view.py` — read from them (import), never edit them. Do not add a
`--base`/`--head` two-ref parameter anywhere in this function's signature — that is the
`mechanism_registry_changed_code_check.py` axis this ticket's own Scope explicitly says not to copy
(confirmed distinct question, `tools/mechanism_registry/mechanism_registry_changed_code_check.py:19-21,133-135`).

**Verify:** `test_plan.md` items 1–3 (`test_pure_core_takes_no_git_dependency`,
`test_drift_class_1_fires_on_planted_stale_citation`,
`test_drift_class_1_silent_when_cited_file_unchanged_since_review`).

---

### Step 2 — Drift class 3: verdict-changed-since-review, pure core + git-history recovery + tests

**Files:** `tools/semantic_control_plane/mapping_drift_check.py`,
`tests/unit/tools/test_semantic_control_plane_drift_detector.py`

**Change:** Add `VerdictDriftFinding(rule_id: str, mechanism_id: str, row_date: str, old_verdict:
Optional[str], new_verdict: Optional[str])` and the pure-core function:

```python
def check_verdict_drift(
    edge_rows: List[dict],
    review_time_verdicts: Dict[str, Optional[str]],
    current_verdicts: Dict[str, Optional[str]],
) -> List[VerdictDriftFinding]:
```

Iterate `edge_rows` (same `rule_mechanism_edges.yaml` rows as Step 1 — `rule_classifications.yaml`
rows carry no `mechanism_id` and cannot feed this check, confirmed shape
`registries/rule_classifications.yaml:24,31-33`). A row is a finding when
`review_time_verdicts[mechanism_id] != current_verdicts[mechanism_id]` for its `mechanism_id`.
`review_time_verdicts`/`current_verdicts` are pre-resolved maps the git wrapper builds — no git call
inside this function.

**Git-history recovery design (the wrapper side, still this step's scope since the test in Step 2
exercises the resolved values, not the git call itself):** do **not** independently date-search
`registries/mechanisms.yaml`'s own commit history by the row's `date`/`review_date` string — that is
the exact same-day ambiguity investigation.md flags (today, every M1 row and `mechanisms.yaml`'s own
last commit share `"2026-09-24"`; a bare `--before=<date> 23:59:59` lookup against
`mechanisms.yaml` directly is correct only by accident once a second same-day commit becomes
possible). Instead: resolve the **anchor commit** by finding the last commit on/before the row's own
`date` that touched `registries/rule_mechanism_edges.yaml` itself (`git log --before="<date>
23:59:59" --format=%H -- registries/rule_mechanism_edges.yaml`, taking the first/most-recent
result) — for M1's real data this resolves unambiguously to `741b117de` (confirmed: this is the
file's *only* commit, `investigation.md`'s "Git history check" finding, independently re-derivable
via `git log --format='%H %ad %s' --date=short -- registries/rule_mechanism_edges.yaml`). Then read
`registries/mechanisms.yaml` **at that same pinned SHA** (`git show <sha>:registries/mechanisms.yaml`)
and extract the mapped mechanism's `verified.verdict` via
`MechanismRegistry.get_verification(mechanism_id)`'s own dict-access shape
(`tools/mechanism_registry/registry.py:200-205`, `verified.get("verdict")`). This sidesteps the
ambiguous axis entirely: the anchor commit is resolved from the row's *own* file's history (which is
unambiguous for M1 — one commit total), never from an independent search against
`mechanisms.yaml`'s own history.

Add tests:
- `test_drift_class_3_fires_on_planted_verdict_change` — planted temp-git-repo fixture (mirror
  `_init_temp_repo`/`_commit`/`_in_temp_repo`,
  `tests/unit/tools/test_mechanism_registry_changed_code_check.py:182-210`) with two commits: one
  seeding `rule_mechanism_edges.yaml` + a `mechanisms.yaml` entry with `verified.verdict:
  observed`, a later commit changing only `mechanisms.yaml`'s `verified.verdict` to
  `contradicted` (both values drawn from `VALID_VERDICTS`,
  `tools/mechanism_registry/registry.py:153`) — asserts the detector reports drift naming both old
  and new verdict.
- `test_drift_class_3_silent_when_verdict_unchanged_since_review` — same shape, verdict unchanged —
  no finding.
- `test_drift_class_3_review_time_recovery_uses_commit_not_bare_date_string` — plants two commits on
  the exact same calendar date touching `rule_mechanism_edges.yaml` (distinct wall-clock timestamps,
  same `--date=short` value) and asserts the anchor-commit resolution picks the correct
  (most-recent-on/before-date) one deterministically, documenting the tie-break rule explicitly
  rather than leaving it implicit — this is the ticket's own "not blocking" open question, now
  answered and tested per its own "state it in a test" instruction.

**Do NOT touch:** `registries/mechanisms.yaml`, `registries/rule_mechanism_edges.yaml`,
`registries/rule_classifications.yaml` — read-only via `git show`/`yaml.safe_load`, never written.
Do not add a `reviewed_mechanism_verdict` field to either edges/classifications schema — the ticket's
own Scope and investigation.md both confirm the git-history path is viable, so the schema-migration
fallback is not reached.

**Verify:** `test_plan.md` items 4–6.

---

### Step 3 — Record drift class 2's descope decision in the ticket

**Files:** `tickets/inprogress/TCK-20260924-M2-MAPPING-DRIFT-DETECTION.md`

**Change:** This step writes no code. Per this plan's own directive (see prompt's "Key decisions
already settled by investigation"), drift class 2 (split/merge with a resolvable ID) is descoped as
its own detector code, per `investigation.md`'s "Risks and Open Questions" finding: no lineage field
exists anywhere in `registries/mechanisms.yaml` (confirmed by grep, zero hits for
`split_from|merged_into|successor|predecessor|lineage|renamed_from`), and the one real precedent
(`action_pacing_readiness`) is only detectable via a full-entry snapshot diff against a stored
review-time baseline — which would duplicate `mechanism_registry_changed_code_check.py`'s own
`old_mechs.get(mid) == mech` whole-entry-equality check
(`tools/mechanism_registry/mechanism_registry_changed_code_check.py:100`) on a different axis, for a
scenario that has not occurred among M1's 5 mapped mechanisms. Update the ticket's own "Open
(implementer's call, record it)" bullet under **Assumptions / Open Questions** to state this
resolution explicitly (descoped, reason as above, pointer to `investigation.md`), and add one
sentence under **Implementation Notes** recording the same. This satisfies AC #2's "or any one
consciously descoped with a written reason in investigation.md and a note in this ticket" — the
investigation.md side is already written; this step supplies the ticket-side note.

**Do NOT touch:** Any other ticket section (Scope, Acceptance Criteria checkboxes themselves stay
as written — do not delete or reword AC #2, only satisfy it). Do not write any code toward a class-2
detector.

**Verify:** No test — this is a documentation-only AC per its own wording ("a written reason...and a
note in this ticket," not a runtime check). `test_plan.md`'s own item 7 is explicit that if
descoped, "this is not a runtime test but a documentation check."

**Dependency:** None — independent of Steps 1/2/4–9, but should land before Step 8 so the
Completion Summary can reference the resolved AC #2 state.

---

### Step 4 — Git-backed wrapper + report-only CLI entry point

**Files:** `tools/semantic_control_plane/mapping_drift_check.py`,
`tests/unit/tools/test_semantic_control_plane_drift_detector.py`

**Change:** Add the wrapper function `check_drift_from_git(base_ref: str = "origin/main") ->
Tuple[List[CitedCodeDriftFinding], List[VerdictDriftFinding]]` (or an equivalent single dataclass
report) that: (a) loads the real `edges:` list from `registries/rule_mechanism_edges.yaml` off disk
(or `WORKTREE`, matching `load_registry_at_ref`'s own `"WORKTREE"` sentinel pattern,
`tools/mechanism_registry/mechanism_registry_changed_code_check.py:138-145`); (b) for each cited path
in step 1's set, resolves `file_last_commit_dates[path]` via `git log -1 --format=%ad --date=short --
<path>`; (c) for each row's mechanism, resolves the anchor commit + review-time verdict per Step 2's
design, and the current verdict via a live `MechanismRegistry().get_verification(mechanism_id)`; (d)
calls `check_cited_code_drift` and `check_verdict_drift` with the assembled inputs. Add
`main(argv=None) -> int` that runs `check_drift_from_git()`, prints a human-readable report (finding
counts + one line per finding, mirroring
`tools/mechanism_registry/mechanism_registry_changed_code_check.py:240-250`'s own print shape), and
**always returns 0** — report-only, never fails the build, per `main()`'s own precedent at
`tools/mechanism_registry/mechanism_registry_changed_code_check.py:251` ("Always 0 -- this check
never fails the build") and this ticket's own explicit Out of Scope ("Report-only, exit 0 regardless
of findings, same as every other detector in this corpus. Do not add a ratchet.").

**Other writers to `registries/rule_mechanism_edges.yaml` / `rule_classifications.yaml` /
`mechanisms.yaml` this step must account for:** this wrapper is read-only against all three files
(via `git show`/`yaml.safe_load` off disk), so it does not race any writer for correctness — but
name them for completeness, since the wrapper's own git-log calls resolve against whatever the
current HEAD/worktree state is at invocation time: `tools/semantic_control_plane/registry.py`'s
`validate_all()` is the only other reader-not-writer of these same three files in this package;
`tools/mechanism_registry/registry.py`'s own `main()` (invoked by `make mechanism-registry-view`
etc.) reads but never writes `mechanisms.yaml`; the files are otherwise hand-edited only by a human
or an implementer during a future M3/M4 ticket, never by any automated writer today (confirmed:
`registries/rule_mechanism_edges.yaml` and `registries/rule_classifications.yaml` each have exactly
one commit in their own `git log`, `741b117de`, per investigation.md). No ordering/race/collision
risk exists for a read-only detector against hand-edited YAML.

Add `test_report_only_exits_zero_with_findings_present` (mirrors
`test_main_always_exits_zero`/`test_ticket_id_cli_path_never_fails_even_with_findings`,
`tests/unit/tools/test_mechanism_registry_changed_code_check.py:144-159,291-...`): run `main()`
against a planted-drift temp repo (reuse Step 1/2's fixtures) and assert the return value is `0` even
though findings are non-empty.

**Do NOT touch:** Do not add an `argparse` flag that changes the exit code based on findings (e.g.
no `--strict`/`--fail-on-drift`) — out of scope per the ticket.

**Verify:** `test_plan.md` item 8.

**Dependency:** Requires Steps 1 and 2 (core functions it calls).

---

### Step 5 — `make` target

**Files:** `Makefile`

**Change:** Add a new target immediately after the existing `mechanism-registry-changed-code-check`
target block (`Makefile:382-383`, confirmed exact two-line shape: a `##`-commented target line
followed by one `$(PYTHON3) ...` recipe line), following the same naming/help-comment convention
every sibling target in this family uses (`territory-control-view`, `Makefile:361-362`;
`mechanism-registry-changed-code-check`, `Makefile:382-383`):

```makefile
semantic-control-plane-drift-check: ## Report-only: flag M1 mapping rows whose cited code or mapped mechanism's verdict changed since the row's own review date
	$(PYTHON3) tools/semantic_control_plane/mapping_drift_check.py
```

**Other writers to `Makefile` this step must account for:** the `Makefile` is a single shared file
that many other tickets across this repo append targets to over time (every `mechanism-*`/
`territory-control-view` target visible in the grep above was added by a separate, already-merged
ticket). This step is a pure, isolated append — one new target block inserted after an existing one,
touching no other target's lines — so it carries the same low collision risk as every prior addition
to this family; if a concurrent ticket also appends near the same line, git's line-based merge
resolves it as two independent insertions unless they land on the exact same line, which this
placement (immediately after a specific, already-existing target's recipe line) makes unlikely.

**Do NOT touch:** Any existing target's recipe or help text. Do not reorder targets.

**Verify:** `test_plan.md` item 9 (`test_make_target_runs_clean`, subprocess `make
semantic-control-plane-drift-check`, exit 0).

**Dependency:** Requires Step 4 (the module `main()` this target invokes).

---

### Step 6 — Read-only guard: registries unchanged after a run

**Files:** `tests/unit/tools/test_semantic_control_plane_drift_detector.py`

**Change:** Add `test_registries_still_validate_clean_after_running_detector`: snapshot the three
real committed registry files' bytes (or their `validate_all()` error list,
`tools/semantic_control_plane/registry.py:255-287`) before running `check_drift_from_git()` /
`main()` against them, run the detector, then re-run `validate_all()` (or the documented CLI
invocation via `subprocess`, mirroring `test_documented_cli_invocation_actually_runs` in
`tests/unit/tools/test_semantic_control_plane_schema.py`) and assert it is still `[]`/exit 0 — proves
the detector is read-only in practice, not just by code inspection. No production code change in
this step; it is a regression guard over Steps 1–4's already-written read-only behavior.

**Do NOT touch:** Any registry file. This test must run against the real, unmodified committed
files, not a temp-repo fixture, to prove the *real* files stay clean (the temp-repo tests in Steps
1/2/4 already cover the synthetic-fixture path).

**Verify:** `test_plan.md` item 10. Maps directly to AC #7 ("`python3
tools/semantic_control_plane/registry.py` still validates clean... M2 must not alter the committed
mapping files").

**Dependency:** Requires Step 4.

---

### Step 7 — Status-vocabulary guard

**Files:** `tools/semantic_control_plane/mapping_drift_check.py` (if any output-shaping change is
needed to satisfy the test), `tests/unit/tools/test_semantic_control_plane_drift_detector.py`

**Change:** Add `test_detector_status_words_resolve_to_status_axis_model_vocabulary`: for every
`old_verdict`/`new_verdict` value the detector's report ever echoes (from
`VerdictDriftFinding`), assert membership in `tools.mechanism_registry.registry.VALID_VERDICTS`
(confirmed `frozenset({"observed", "contradicted", "inconclusive"})`,
`tools/mechanism_registry/registry.py:153`) — never a minted term. Report-level prose the detector
itself invents (e.g. "DRIFT FOUND", "CLEAN") is explicitly out of this test's scope, per
`docs/plans/status_axis_model.md`'s own axis table (`status_axis_model.md:20-26`) only binding
values the detector *echoes back* from a registry, not its own report language. If Steps 1/2/4's
existing implementation already only ever echoes real `verified.verdict` values (which it should,
since `VerdictDriftFinding.old_verdict`/`new_verdict` come straight from
`MechanismRegistry.get_verification()`), this step may require no production code change — write the
test first and confirm.

**Do NOT touch:** Do not invent a new "drift status" enum distinct from `VALID_VERDICTS`/
`VALID_STATES`/`VALID_RULE_CLASSIFICATIONS` for the report — reuse the existing three axis
vocabularies exactly as `status_axis_model.md` documents them.

**Verify:** `test_plan.md` item 11. Maps to AC #8.

**Dependency:** Requires Step 4.

---

### Step 8 — Run against M1's live Territory mapping; record the result

**Files:** `tests/unit/tools/test_semantic_control_plane_drift_detector.py`,
`tickets/inprogress/TCK-20260924-M2-MAPPING-DRIFT-DETECTION.md` (Completion Summary section)

**Change:** Add `test_live_run_against_territory_mapping_reports_or_records_finding`: call
`check_drift_from_git()` (Step 4's real, non-mocked wrapper) against the actual committed
`registries/{rule_mechanism_edges,rule_classifications,mechanisms}.yaml` and assert it completes
without raising, returning a finding count (including possibly zero). Then — separately from the
test — actually run `make semantic-control-plane-drift-check` once by hand and read its real output.
Per the ticket's own AC #4 and Out of Scope ("do not silently re-review the row to make the report
clean"): if the run is clean, record that in the ticket's Completion Summary; if it reports a real
finding (plausible candidate: the `TERR-02` row's `+-50`/`+-100` threshold evidence, already flagged
in `registries/rule_mechanism_edges.yaml`'s own TERR-02 evidence prose as a live disagreement,
though not itself dated differently from `mechanisms.yaml`'s single commit so may not trigger class
1/3 today), record every finding verbatim in Completion Summary with a disposition — either "real
drift, follow-up ticket filed: `<new ticket id>`" or "false positive, detector fixed: `<what
changed>`" — never edit the underlying registry rows to force a clean report.

**Do NOT touch:** `registries/rule_mechanism_edges.yaml`, `registries/rule_classifications.yaml`, or
`TERR-02`'s classification, even if the detector reports something about it — explicitly named in
the ticket's Out of Scope (the `TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT` ticket
owns that decision, not this one).

**Verify:** `test_plan.md` item 12. Maps to AC #4.

**Dependency:** Requires Steps 1, 2, 3, 4 (needs both drift classes and the wrapper working, and
class 2's descope already recorded so the Completion Summary can state all three classes' final
disposition together).

---

### Step 9 — Update `roadmap.md` M2 section and the epic's milestone-disposition table

**Files:** `docs/plans/simulation_semantic_control_plane/roadmap.md` (M2 section, lines 109–125),
`tickets/inprogress/TCK-20260923-SEMANTIC-CONTROL-PLANE-EPIC.md` (milestone-disposition table, M2
row, currently line 81)

**Change:** In `roadmap.md`, rewrite the M2 section's **Deliverables** and **Exit criteria** to
reflect shipped state instead of an unstarted milestone description: name the real module
(`tools/semantic_control_plane/mapping_drift_check.py`), the real `make` target
(`semantic-control-plane-drift-check`), state that drift classes 1 and 3 shipped as code and class 2
was consciously descoped with a one-line pointer to `investigation.md`'s reasoning (do not repeat the
full reasoning in `roadmap.md` — one sentence + a pointer, matching this doc's own terse milestone
style elsewhere), and report the real Step 8 outcome against the "clean today" exit criterion
(`roadmap.md:123-124`, "Running the detector against Territory's live mapping reports 'clean' today")
— if not clean, state that plainly rather than rewording the exit criterion to match a partial
result. In the epic ticket, update the M2 row (`tickets/inprogress/TCK-20260923-SEMANTIC-CONTROL-PLANE-EPIC.md:81`,
currently `"**SCOPED** 2026-09-24, dispatched to \`rpg-implementer\`. Standard tier, P1. Checks M1's
live Territory mapping for the three \`roadmap.md\` M2 drift classes; report-only, \`make\` target, no
CI wiring at this milestone."`) to a `DONE`-shaped disposition matching this ticket's real final
state (2 of 3 classes implemented, 1 descoped, real `make` target name, Step 8's real finding
outcome).

**Other writers to these two files this step must account for:** `roadmap.md` is co-owned across all
of M0–M4's own tickets, each responsible only for its own milestone's section — M0's ticket already
updated the M0 section, M1's the M1 section; do not touch M1 (`roadmap.md:1-108`), M3
(`roadmap.md:128-156`), or M4 (`roadmap.md:158+`) sections, only M2's own block. The epic ticket's
milestone-disposition table has one row per milestone, each written only by that milestone's own
ticket at close time (M0's and M1's rows already exist and are not touched here) — edit only the M2
row (currently line 81); do not touch the M0/M1/M3/M4 rows around it.

**Verify:** No automated test (this is a docs/ticket-prose update); the `check_docs_to_update_coverage`
static check (referenced in `investigation.md`'s "Docs Requiring Update" section) is the closest
automated proxy for the `roadmap.md` half — confirm the ticket's own "Related Docs"/doc-update bullet
format is present so that check passes at Verify/Finalize time. Maps to AC #9.

**Dependency:** Should run last, after Step 8, so the real shipped/descoped/finding state is known
before it is written into either document.

## Scope Guards

- No new mapping entries in `rule_mechanism_edges.yaml`, `rule_classifications.yaml`, or
  `mechanism_causal_edges.yaml` — M2 checks M1's data, never extends it (ticket Out of Scope).
- No CI wiring, no blocking gate, no ratchet — every entry point must return/exit 0 unconditionally
  regardless of findings (ticket Out of Scope; Step 4's `main()`).
- No fix to any real drift the detector finds — record and file a follow-up, never silently
  re-review a row to force a clean report (ticket Out of Scope; Step 8).
- No change to `registries/mechanisms.yaml` content, including `tactical_decision`'s `contradicted`
  verdict — that is M4's scope, not this ticket's (ticket Out of Scope).
- No resolution of the `TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT` `+-50`/`+-100`
  contradiction, and no edit to `TERR-02`'s classification even if the detector reports on it (ticket
  Out of Scope; Step 8).
- No M3 finding-ingestion work, no M4 second-slice/cross-domain-view work (ticket Out of Scope).
- No test files written to `tests/tools/` — the real, established home is `tests/unit/tools/`
  (investigation.md's directory correction; every step above).
- No `reviewed_mechanism_verdict` (or similarly named) field added to `rule_mechanism_edges.yaml` or
  `rule_classifications.yaml` — the git-history recovery path is confirmed viable (Step 2).
- No classification-deriving helper — the detector reports staleness, it never computes or suggests
  a new `rule_classifications.yaml` value (investigation.md's Anti-Drift Hazards; applies to Steps
  1, 2, 4).
- No edits to `tools/semantic_control_plane/registry.py`, `rule_catalog.py`, or
  `generate_territory_control_view.py` beyond importing from them (Step 1).
- No edits to any `roadmap.md` section other than M2's own block, and no edits to any epic-ticket
  milestone row other than M2's own (Step 9).

## Dependency Map

```
Step 1 (class 1 core)  ─┐
Step 2 (class 3 core)  ─┼─> Step 4 (git wrapper + CLI) ─┬─> Step 5 (make target)
Step 3 (class 2 descope, independent) ─────────────────┘    ├─> Step 6 (read-only guard)
                                                              ├─> Step 7 (vocab guard)
                                                              └─> Step 8 (live run + record)
                                                                    └─> Step 9 (docs/epic update)
```

Steps 1 and 2 are independent of each other (different drift classes, no shared state) and can be
implemented in either order. Step 3 is fully independent and can happen at any point before Step 8.
Steps 5, 6, and 7 all depend only on Step 4 and are independent of each other. Step 8 needs Steps 1,
2, 3, and 4 all complete (it reports the combined, final state of all three drift classes). Step 9
must be last.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — detector module with pure core + git wrapper, mirrors 3-entry-point separation | Steps 1, 2, 4 | `test_pure_core_takes_no_git_dependency` |
| AC2 — all 3 drift classes implemented or 1 descoped with written reason (class 2 expected) | Steps 1, 2, 3 | Class 1/3: fixture tests in Steps 1/2. Class 2: no test, documentation check per `test_plan.md` item 7 |
| AC3 — `make` target exists, documented in Makefile help text | Step 5 | `test_make_target_runs_clean` |
| AC4 — live run against Territory mapping produces a report; findings recorded w/ disposition if not clean | Step 8 | `test_live_run_against_territory_mapping_reports_or_records_finding` |
| AC5 — each implemented drift class has a fixture test that fires, not just clean-data pass | Steps 1, 2 | `test_drift_class_1_fires_on_planted_stale_citation`, `test_drift_class_3_fires_on_planted_verdict_change` |
| AC6 — report-only: exits 0 with findings present, test asserts | Step 4 | `test_report_only_exits_zero_with_findings_present` |
| AC7 — `registry.py` still validates clean after a run; M2 must not alter committed files | Step 6 | `test_registries_still_validate_clean_after_running_detector` |
| AC8 — every status word resolves to `status_axis_model.md` vocabulary | Step 7 | `test_detector_status_words_resolve_to_status_axis_model_vocabulary` |
| AC9 — `roadmap.md` M2 section + epic milestone-disposition table updated | Step 9 | Manual/doc-coverage check, no pytest |

## Anti-Drift Notes

- **Do not copy `mechanism_registry_changed_code_check.py`'s `--base`/`--head` two-ref-diff shape**
  into either `check_cited_code_drift` or `check_verdict_drift`. Both answer "has X changed since
  this row's own recorded date," a per-row date comparison, not "did this diff change X" — confirmed
  as a distinct axis in both the ticket's own Scope and investigation.md's Current Behavior section.
  `test_pure_core_takes_no_git_dependency` (Step 1) is the direct guard.
- **Same-day git-history ambiguity is real, not hypothetical, as of today's date (2026-09-24).**
  Every M1 row and `registries/mechanisms.yaml`'s own last commit share the same calendar date. Step
  2's anchor-commit-via-the-edges-file design sidesteps this for M1's actual data, but the design
  must generalize — `test_drift_class_3_review_time_recovery_uses_commit_not_bare_date_string`
  (Step 2) exists specifically to catch a future regression where someone "simplifies" the lookup
  back into an independent date search against `mechanisms.yaml`.
- **Class 2 stays descoped — do not add split/merge detection code speculatively.** If Implement
  finds a mechanical signal investigation.md missed, that is new evidence requiring the plan itself
  to be revisited (a new step, a new test per `test_plan.md` item 7's "otherwise substitute"
  language), not a silent scope expansion inside Step 1/2/4's existing steps.
- **The detector must never write a `rule_classifications.yaml` value.** Investigation.md's
  Anti-Drift Hazards section already ties this to `test_no_function_derives_classification_from_edges`
  (`tests/unit/tools/test_semantic_control_plane_schema.py:387-400`) — that existing test's own
  scanning approach does not currently cover the new module by name; if it is regex/path-scoped
  rather than corpus-wide, confirm during Step 7 that it (or an equivalent new assertion) actually
  reaches `mapping_drift_check.py`, don't assume coverage silently extends.
- **`UNKNOWN` / absent mappings are not errors.** Neither `check_cited_code_drift` nor
  `check_verdict_drift` should ever iterate over Rules or mechanisms with no mapping row — both only
  walk `rule_mechanism_edges.yaml`'s existing `edges:` list, so an absent mapping never enters either
  function's input in the first place (architecture.md §7 compliance is structural here, not a
  runtime check to add).

## Deviations

- **Step 1's `check_cited_code_drift` signature gained a third parameter,
  `mechanism_cited_paths: Dict[str, List[str]]`**, beyond the plan's literal
  `(edge_rows, file_last_commit_dates)`. Reason: the plan's own prose for this step states the pure
  core "takes no git dependency and does no file I/O," but its worked description also has the core
  function resolve `implemented_by` citations via a live `MechanismRegistry()` (which reads
  `registries/mechanisms.yaml` off disk) — those two statements are in tension. Implementing it with
  `MechanismRegistry()` called *inside* `check_cited_code_drift` broke the very test the plan itself
  specifies (`test_drift_class_1_fires_on_planted_stale_citation`, using a synthetic, non-real
  `mechanism_id` like `"fake_mechanism"`): a synthetic id can't resolve against the real committed
  registry, so no cited paths would ever be found and the fixture could never fire. Resolved by
  moving mechanism-id -> cited-paths resolution into the git wrapper (`check_drift_from_git`, Step
  4), so `check_cited_code_drift` itself is fully pure (zero `MechanismRegistry`/git/file-I-O
  dependency, verified by `test_pure_core_takes_no_git_dependency` via bytecode `co_names`
  inspection) — this is the literal reading of the plan's own purity contract, and mirrors
  `check_drift(old_data, new_data, changed_files)`'s true shape (pre-loaded data in, no I/O inside)
  more closely than the plan's own worked description did. `check_verdict_drift`'s signature is
  unchanged from the plan (already fully pure as specified).
- **Step 1's purity test** (`test_pure_core_takes_no_git_dependency`) uses `fn.__code__.co_names`
  (bytecode-level name references) rather than a raw `inspect.getsource(fn)` substring scan for
  `"git"`. Reason: a raw substring scan false-positives on the word "git" appearing harmlessly
  inside each function's own docstring prose (e.g. "no git dependency, no file i/o" in
  `check_cited_code_drift`'s own docstring) — `co_names` only reflects names the function's
  bytecode actually references as globals/attributes, so a docstring mention can never trip it.
  Same intent as the plan's own step text, just a more precise check.
- Everything else (Steps 2–9) implemented as planned, including the anchor-commit-via-
  `rule_mechanism_edges.yaml`'s-own-history design (Step 2), the `check_drift_from_git`/`main()`
  shape (Step 4), the `make` target placement (Step 5), the read-only and status-vocabulary guards
  (Steps 6–7), the live run against M1's Territory mapping — clean, 0 findings (Step 8), and the
  `roadmap.md`/epic-ticket updates (Step 9).
