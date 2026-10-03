---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP
artifact_type: plan
tags: [testing, bug]
---

# Implementation Plan — TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP

## Summary

Nine independently-fixable stale-reference groups (the ticket's original 8 plus
`test_args_point_to_search_mcp`, found during Investigate as the same root cause as Group 7) are
fixed in ascending order of risk: pure data/constant corrections first (frozen-hash dict
narrowing, a path constant, an evidence-citation string), then generator/config/fixture changes
that touch more surface (the `content_usage_matrix.md` generator, the `gate_a` corpus
skip-with-disclosure, the `epic_staleness_check` synthetic fixture, the `.mcp.json`
command/wrapper-chain assertion rewrite), and finally the two `@pytest.mark.slow` marker
additions, closed out by two full-lane verification runs. Every fix is a correction to a
confirmed-stale reference — no assertion is loosened to force a pass; the `gate_a` corpus fix is
an honest, disclosed skip (not a fabricated reconstruction, which the ticket's Out of Scope
section explicitly forbids), and the `epic_staleness_check` fix moves a real, now-gone live-repo
fixture to a synthetic one that preserves the original test's exact assertions and pipeline
coverage. No `src/` engine/simulation behavior changes anywhere in this plan.

## Steps

### Step 1 — Narrow the 3 stale frozen-content-hash guards

**Files:** `tests/tools/test_context_kind_priority_decision.py`,
`tests/tools/test_exact_lookup_convention_decision.py`,
`tests/tools/test_stored_artifact_kind_decision.py`

**Change:** Each file's `_EXPECTED_TOOLS_HASHES` dict (confirmed by direct read this session:
`test_context_kind_priority_decision.py:24-37`, `test_exact_lookup_convention_decision.py:36-`,
`test_stored_artifact_kind_decision.py:26-39`) pins a SHA-256 snapshot of specific `tools/*.py`
files "as of that historical ticket's own Implementation start." Confirmed via direct pytest run
(investigation.md Group 3) which single entry per file is now stale because the named file
legitimately changed via unrelated later work (`git log` confirms neither
`TCK-20260802-CONTEXT-KIND-PRIORITY`, `TCK-20260802-EXACT-LOOKUP-CONVENTION`, nor
`TCK-20260802-STORED-ARTIFACT-KIND` itself touched the file):

- `test_context_kind_priority_decision.py:31-33` — remove the `"tools/parity_index.py": (...)`
  entry. Leave the other 3 entries (`context_packet_assembler.py`, `hybrid_retrieval.py`,
  `generate_registry.py`) untouched.
- `test_exact_lookup_convention_decision.py:37-39` — remove the `"tools/parity_index.py": (...)`
  entry. Leave the other 3 entries (`hybrid_retrieval.py`, `context_packet_assembler.py`, and the
  4th entry further down the dict — confirm its exact key by reading the full dict block before
  editing, since only lines 37-45 were read this session) untouched.
- `test_stored_artifact_kind_decision.py:27-29` — remove the `"tools/generate_registry.py": (...)`
  entry. Leave the other 3 entries (`validate_frontmatter.py`, `context_packet_assembler.py`,
  `hybrid_retrieval.py`) untouched.

Add one disclosure comment per file, directly above `_EXPECTED_TOOLS_HASHES`, immediately after
the existing "Recorded at the time this ticket authored..." comment block (do not delete that
existing block — append below it), mirroring the exact tone/format already established 3x this
session at `tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py:105-113` and
`tests/tools/test_kgmcp_phase4_direct_tool_comparison.py`'s own narrowing comments (both read this
session). Use this exact template, substituting the real filename and historical ticket per file:

```python
# tools/parity_index.py removed (TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP, 2026-08-17):
# this file has legitimately changed via unrelated later work since <HISTORICAL_TICKET_ID>'s own
# Implementation start (e.g. TCK-20260731-PARITY-READPATH-GATE, TCK-20260810-PARITY-LEDGER-
# WRITE-SAFETY-TOOL) — confirmed via `git log` that <HISTORICAL_TICKET_ID> itself never touched
# it. This hash snapshot only ever validly reflected that ticket's own committed state at
# authoring time, not a permanent repo-wide ban. The remaining entries below still correctly
# protect the files that ticket's own diff actually left untouched.
```

For `test_stored_artifact_kind_decision.py`, substitute `tools/generate_registry.py` for
`tools/parity_index.py` and `TCK-20260802-STORED-ARTIFACT-KIND` for the historical ticket ID.

**Do NOT touch:** any of the other (non-stale) entries in any of the 3 dicts — each remaining
entry still correctly protects a real Out-of-Scope file for that historical decision-only ticket.
Do not touch the section of each file below the dict (the `_contract_text()`/`_section()` helpers
and the actual decision-content assertions) — this step is a hash-dict edit only.

**Verify:** `pytest tests/tools/test_context_kind_priority_decision.py
tests/tools/test_exact_lookup_convention_decision.py
tests/tools/test_stored_artifact_kind_decision.py -v` — all 34 tests (11+12+11) pass, including
the 3 remaining-entries content-hash assertions per file (not just the previously-failing 3).

### Step 2 — Update the stale epic ticket path constant

**Files:** `tests/tools/test_exact_lookup_convention_decision.py`

**Change:** `_EPIC_TICKET_PATH` (`:28-30`, read this session) currently reads
`_REPO_ROOT / "tickets" / "inprogress" / "TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md"`.
Confirmed via investigation.md Group 6 (re-derived, not guessed) that the real file now lives at
`tickets/backlogs/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`. Change the `"inprogress"`
path segment to `"backlogs"`. Do not change any other part of the constant or the test body that
consumes it (`test_epic_ticket_decision_9_marked_resolved`) — the assertion itself (Open Decision
9 is marked resolved) is unaffected by where the file physically lives.

**Do NOT touch:** any other path constant in this file (`_CONTRACT_PATH` stays as-is).

**Verify:** `test_epic_ticket_decision_9_marked_resolved` (part of the same file covered by Step
1's verify command — no separate run needed, but confirm this specific test individually passes).

### Step 3 — Correct the `ENTITY-003` evidence citation's second bare mention

**Files:** `docs/event_ledger/entity.yaml`

**Change:** `ENTITY-003.evidence` (`:30`, read this session) already correctly leads with
`"src/observability/event_extractor.py (multiple sites); ..."`. The bug is a second, incidental
bare mention later in the same string's prose: `"...combat_hard_law_violation remains
event_extractor.py-only, not shaper-migrated."` — the test's regex extraction
(`re.findall(r"[\w./]+\.py", evidence)`, confirmed at `tests/tools/test_entity_event_ledger.py:37`
this session) captures this bare `event_extractor.py` substring as if it were its own path
citation, and `Path("event_extractor.py").exists()` correctly fails (no such file at repo root).
Change the substring `"combat_hard_law_violation remains event_extractor.py-only"` to
`"combat_hard_law_violation remains src/observability/event_extractor.py-only"` in the
`ENTITY-003.evidence` string. Do not touch the correct leading citation
(`"src/observability/event_extractor.py (multiple sites); ..."`) or any other entity in the file.

**Do NOT touch:** any other `ENTITY-*` entry in `docs/event_ledger/entity.yaml` — only
`ENTITY-003`'s evidence string is edited, and only its second mention within that string.

**Verify:** `pytest tests/tools/test_entity_event_ledger.py -v` — both
`test_entity_ledger_evidence_citations_are_real_files` and
`test_entity_ledger_covers_every_entity_update_field` pass; re-run the full evidence-citation test
(not filtered to `ENTITY-003`) to confirm the edit introduced no new bare-filename regex match
elsewhere in the same entry's prose (test_plan.md Anti-Drift Test Guards, Group 8).

### Step 4 — Prepend a frontmatter block to `generate_matrix_report()`'s output

**Files:** `src/content/matrix.py`

**Change:** `docs/mechanics/content_usage_matrix.md` is script-generated, not hand-maintained —
confirmed this session (investigation.md Group 2) that
`tests/unit/content/test_content_usage_matrix.py::test_generate_and_save_report` (`:111-120`)
unconditionally calls `generate_matrix_report()` and writes its return value to
`docs/mechanics/content_usage_matrix.md` on every test run (`output_path.write_text(report, ...)`,
`:118`), which also runs as part of the `unit-core-world` CI job. **Other writers to this file:**
confirmed via investigation — no `Makefile` target and no other `tools/` script writes to this
path; `src/content/repository.py:150` is a read-side comment reference only. `test_generate_and_
save_report` is the *only* writer, so this fix is safe from any concurrent-writer race or
double-write concern.

In `generate_matrix_report()` (`src/content/matrix.py:715-737`, read this session), change the
`lines` list's opening from:

```python
lines = [
    "# Content Usage Matrix Report",
    "",
```

to:

```python
lines = [
    "---",
    "status: active",
    "layer: mechanics",
    "authority: P1",
    "audience: developer",
    "---",
    "",
    "# Content Usage Matrix Report",
    "",
```

Field choice per investigation.md Group 2: `status: active` (not `authoritative`) because
`last_verified` is only required when `status: authoritative`
(`tools/validate_frontmatter.py:44-58`, read this session) and no human curates a
`last_verified` date on an automated regenerate — matching the precedent at
`docs/simulation_quality/eval_matrix_results.md:1-5`. `layer: mechanics` is confirmed registered
at `registries/layer_registry.jsonl:1`.

**Do NOT touch:** the table-building loop (`:731-735`) or any `CONTENT_USAGE_MATRIX` entry data —
this step only changes the static header lines the function prepends, never the per-entry content.
Do not hand-edit `docs/mechanics/content_usage_matrix.md` directly — any manual edit would be
silently overwritten by the next `test_generate_and_save_report` run.

**Verify:** `pytest tests/unit/content/test_content_usage_matrix.py
tests/tools/test_generate_registry.py tests/tools/test_validate_frontmatter.py -q` — all pass,
including `TestRealDocsTree` (2 tests) and `TestPreviouslyFrontmatterMissingDocs` (all 12
parametrized cases, not just this file's own case). Additionally re-validate directly:
`python3 tools/validate_frontmatter.py docs/mechanics/content_usage_matrix.md` (or the equivalent
scoped validator invocation) after a real regeneration cycle, per test_plan.md's Anti-Drift Test
Guards for Group 2 — proves the frontmatter survives being regenerated, not just a hand-edited
snapshot.

### Step 5 — Skip the `gate_a_corpus.json`-dependent tests with an honest, dated disclosure

**Files:** `tests/tools/test_gate_a_readpath_review.py`

**Change:** Confirmed exhaustively this session (investigation.md Group 4) that
`gate_a_corpus.json`/`gate_a_results.json` were never committed to the repository at any point —
`git log --all` searches by date range, by grep, and by `--diff-filter=A --name-only` against the
staging directory all return zero hits; no `find` match anywhere in the working tree. The 3
hand-authored `SYN-*` synthetic edge cases' exact field values are nowhere disclosed (only their
shape/adjudicated outcome, in the decision doc), so any reconstruction now would be a fabricated
after-the-fact "freeze" — explicitly forbidden by this ticket's Out of Scope section. The correct
fix is a disclosed skip, not deletion, reconstruction, or an assertion loosening.

Add near the top of the file (after the existing `_DECISION_DOC_PATH` constant at `:54`):

```python
_CORPUS_AVAILABLE = _CORPUS_PATH.exists()
_SKIP_REASON = (
    "gate_a_corpus.json and gate_a_results.json were never committed to this repository at any "
    "point in its history — confirmed via exhaustive `git log --all` search on 2026-08-17 "
    "(TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP): no date-ranged history search, no "
    "grep-by-name search, and no diff-filter=A search against staging_artifacts/"
    "TCK-20260731-PARITY-READPATH-GATE/ found any trace of either file. The raw corpus/results "
    "JSON is unrecoverable. This does NOT invalidate the Gate A GO decision itself — "
    "docs/ai/parity_readpath_gate_a_decision.md narrates its own real findings (including the "
    "WORLD-076 divergent-status case) independently of this raw JSON's presence in the repo. "
    "Reconstructing the corpus now, with hindsight knowledge of what the decision doc already "
    "says it proved, would be a fabricated after-the-fact 'freeze' of already-known results — "
    "explicitly forbidden by this ticket's own Out of Scope section. Skipping honestly rather "
    "than fabricating a corpus or leaving these tests erroring."
)
```

Apply `@pytest.mark.skipif(not _CORPUS_AVAILABLE, reason=_SKIP_REASON)` as a class decorator on
`TestCorpusIntegrity` (2 tests) and directly on
`TestAdjudication::test_gate_a_no_phase2_synthetic_fixture_relabeled_as_ticket_derived_corpus`
(`:520`, the one `TestAdjudication` test that calls `_load_corpus()` directly rather than through
the fixture). Add `if not _CORPUS_AVAILABLE: pytest.skip(_SKIP_REASON)` as the first line inside
the module-scoped `gate_a_full_run` fixture (`:229-231`), so every test that consumes it
(`TestLegacyCapture` — 1 test, `TestIndexCapture` — 2 tests, the other 2 `TestAdjudication` tests,
`TestMetrics` — 2 tests) reports as skipped, not errored. Leave `TestNoMutation` (1 test, reads
only `_protected_files()`) and `TestDecisionDocIntegrity` (5 tests, reads only
`_DECISION_DOC_PATH`) completely unedited — neither depends on the corpus.

**Do NOT touch:** `TestNoMutation` or `TestDecisionDocIntegrity` (must never be gated by
`_CORPUS_AVAILABLE`). Do not add any `SYN-*` synthetic fixture content anywhere to "restore" the
corpus — this is the one thing this ticket's Out of Scope explicitly forbids. Do not delete the
corpus-dependent test classes/methods — skip them, keep them as documentation of what would run if
the corpus existed.

**Verify:** `pytest tests/tools/test_gate_a_readpath_review.py -v` reports exactly **10 skipped,
6 passed, 0 failed, 0 errors** (2 `TestCorpusIntegrity` + 1 `TestLegacyCapture` + 2
`TestIndexCapture` + 3 `TestAdjudication` + 2 `TestMetrics` = 10 skipped; 1 `TestNoMutation` + 5
`TestDecisionDocIntegrity` = 6 passed). A different split means `_CORPUS_AVAILABLE` was applied to
the wrong test set (test_plan.md Anti-Drift Test Guards, Group 4 skip guard) — stop and re-check
before proceeding.

### Step 6 — Replace `test_epic_staleness_check.py`'s real, now-gone OBSISO fixture with a synthetic one

**Files:** `tests/tools/test_epic_staleness_check.py`

**Change:** `REAL_OBSISO_DIR = tickets/todos/obs-isolation` and
`TCK-20260702-OBSISO-EPIC` no longer exist at those paths — the folder completed and moved to
`tickets/done/obs-isolation/` (standard Finalize convention). Confirmed this session
(investigation.md Group 5) that no other live `tickets/todos/` folder is a valid substitute: the
only other folder, `codex-runtime-activation/`, has real, non-zero child activity as of 17 days
ago and would itself be flagged stale today — disqualified, not a "never-started" case.
`tickets/backlogs/` is never scanned by `discover_candidate_epics()` at all. Per the ticket's own
fallback instruction, move to a synthetic `tmp_path` fixture, mirroring this same file's own
existing hybrid-folder-shape construction pattern (`test_handles_hybrid_folder_shape`, `:125-149`)
and its own existing tmp_path-based `find_stale_epics`/`compute_stale_epics_report` integration
pattern (`test_dual_presence_not_double_reported_in_stale_list`, `:349-374`) — both read this
session and confirmed to construct: a `todos_dir` subfolder containing a `SEQUENCE.md` (listing
child ticket IDs) plus the epic-tier ticket file itself (`_write_ticket(..., tier="epic", ...)`),
and a real `working_log.csv`/`runs.jsonl` file pair passed as explicit paths (not the real repo's
files) to `find_stale_epics(...)`/`compute_stale_epics_report(...)` with an explicit `now=NOW`
argument.

Replace `test_does_not_flag_never_started_real_obsiso_epic` (`:60-66`) with
`test_does_not_flag_never_started_synthetic_folder_epic(tmp_path)`:

```python
def test_does_not_flag_never_started_synthetic_folder_epic(tmp_path):
    inprogress_dir = tmp_path / "inprogress"
    todos_dir = tmp_path / "todos"
    working_log_path = tmp_path / "working_log.csv"
    runs_jsonl_path = tmp_path / "runs.jsonl"
    inprogress_dir.mkdir()
    todos_dir.mkdir()

    folder = todos_dir / "synthetic-never-started-epic"
    folder.mkdir()
    (folder / "SEQUENCE.md").write_text(
        "Epic: `TCK-20260701-SYNTH-NEVER-STARTED-EPIC`.\n\n"
        "| Order | Ticket |\n|---|---|\n"
        "| 1 | TCK-20260701-SYNTH-NEVER-STARTED-CHILD |\n"
    )
    _write_ticket(
        folder / "TCK-20260701-SYNTH-NEVER-STARTED-EPIC.md",
        "TCK-20260701-SYNTH-NEVER-STARTED-EPIC", "epic", "2026-07-01",
    )
    # Zero rows for the child ID anywhere — real, zero activity ever.
    working_log_path.write_text("timestamp,ticket_id,title,status,summary,artifacts_path\n")
    runs_jsonl_path.write_text("")

    stale = find_stale_epics(inprogress_dir, todos_dir, working_log_path, runs_jsonl_path, now=NOW)
    assert "TCK-20260701-SYNTH-NEVER-STARTED-EPIC" not in [c.epic_id for c in stale]

    report = compute_stale_epics_report(
        inprogress_dir, todos_dir, working_log_path, runs_jsonl_path, now=NOW
    )
    assert "TCK-20260701-SYNTH-NEVER-STARTED-EPIC" not in report.split("Informational:")[0]
    assert "TCK-20260701-SYNTH-NEVER-STARTED-EPIC" in report.split("Informational:")[1]
```

Replace `test_advisory_only_no_file_mutation` (`:242-251`) with
`test_advisory_only_no_file_mutation_synthetic(tmp_path)`, reusing the same synthetic folder
construction (factor the folder-building lines above into a small local helper if the implementer
prefers, to avoid duplicating them across both new tests — implementer's call), then:

```python
def _hash_dir(directory):
    return {p.name: p.read_bytes() for p in sorted(directory.iterdir()) if p.is_file()}

before = _hash_dir(folder)
compute_stale_epics_report(inprogress_dir, todos_dir, working_log_path, runs_jsonl_path, now=NOW)
find_stale_epics(inprogress_dir, todos_dir, working_log_path, runs_jsonl_path, now=NOW)
after = _hash_dir(folder)

assert before == after
```

Sanity-check (test_plan.md Anti-Drift Test Guards, Group 5): the existing, unmodified
`test_epic_with_all_children_stale` (`:187-209`) already proves the opposite case (non-zero old
activity *does* get flagged) still works — leave it untouched as the differentiating control.

Remove the now-unused `REAL_INPROGRESS_DIR`, `REAL_TODOS_DIR`, `REAL_WORKING_LOG`,
`REAL_RUNS_JSONL`, `REAL_OBSISO_DIR` module-level constants (`:33-37`) — confirmed this session
that no other test in this 392-line file references them once these two tests are replaced;
implementer should re-grep the file for `REAL_` before deleting, in case a test outside the range
read this session references one. Update the module docstring (`:7-12`) to remove the now-false
claim that `TCK-20260702-OBSISO-EPIC` is "the repo's real live proof of the never-started case" —
state instead that the never-started case is proven via a synthetic `tmp_path` fixture, since the
real folder completed and moved to `tickets/done/`.

**Do NOT touch:** any of the other ~15 tests in this file (`test_does_not_flag_recently_active_
epic`, `test_identifies_epic_tickets_vs_regular_tickets`, `test_handles_hybrid_folder_shape`,
`test_handles_missing_or_malformed_sequence_md`, `test_epic_with_all_children_stale`,
`test_does_not_flag_never_started_epic`, `test_advisory_only_never_raises_on_missing_files`, the
`csv.DictReader`/dual-presence tests) — none of them depend on `REAL_OBSISO_DIR` or the real repo
state. Do not repurpose `codex-runtime-activation/` as a fixture target (confirmed disqualified,
investigation.md Group 5).

**Verify:** `pytest tests/tools/test_epic_staleness_check.py -v` — all ~17 tests pass (the 2 new
synthetic tests plus the ~15 unmodified ones).

### Step 7 — Rewrite the `.mcp.json` command/args assertions to the real, intentional contract

**Files:** `tests/tools/test_search_mcp.py`

**Change:** `.mcp.json`'s `knowledge-search` server intentionally uses `"command": "bash"` /
`"args": ["tools/start_search_mcp.sh"]` — the shipped `TCK-20260624-FIX-TOOLS-SERVER` portability
fix (`tickets/working_log.csv` row), not a stale artifact itself. `tools/start_search_mcp.sh`
(read in full this session) tries `.venv/bin/python3`, then a hardcoded `vboxuser` venv path, then
`command -v python3`, and `exec`s whichever is found running `search_mcp.py` — the wrapper script,
not `.mcp.json`'s own `command` field, is what invokes python3. Two tests in `TestMcpJson`
(`:55-64`) are the stale artifacts, asserting the pre-portability-fix literal:

1. `test_command_is_python3` (`:55-58`) — change the assertion from
   `assert entry["command"] == "python3"` to `assert entry["command"] == "bash"`.
2. `test_args_point_to_search_mcp` (`:60-64`) — change the assertion from
   `assert entry["args"][0].endswith("search_mcp.py")` to
   `assert entry["args"][0] == "tools/start_search_mcp.sh"`.

Both method names may stay as-is (test_plan.md specifies "extend in place," not a rename) even
though they now assert `bash`/the wrapper path rather than `python3`/`search_mcp.py` directly —
implementer discretion to rename either for clarity is fine but not required, since the docstring
comment above each assertion will carry the real explanation either way.

Add a new test on the same `TestMcpJson` class, proving the full chain end-to-end (not just the
first hop):

```python
def test_start_search_mcp_wrapper_invokes_python3(self):
    data = json.loads((_REPO_ROOT / ".mcp.json").read_text())
    entry = data["mcpServers"]["knowledge-search"]
    wrapper_path = _REPO_ROOT / entry["args"][0]
    assert wrapper_path.exists(), f"{wrapper_path} referenced by .mcp.json but does not exist"
    assert "python3" in wrapper_path.read_text()
```

This derives the wrapper path from `entry["args"][0]` (not a hardcoded string), so it stays
correct even if `.mcp.json`'s args value is ever legitimately re-pointed elsewhere.

**Do NOT touch:** `test_mcp_json_exists`, `test_has_knowledge_search_server`, or any class besides
`TestMcpJson` in this file (`TestDeriveTitle`, `TestRunSearch`, etc.) — none of those reference the
`command`/`args` contract.

**Verify:** `pytest tests/tools/test_search_mcp.py -v` — full file passes, including all 3
`TestMcpJson` tests (2 rewritten + 1 new) and every other class in the file unmodified.

### Step 8 — Mark the 2 real-gateway budget-busting tests `@pytest.mark.slow`

**Files:** `tests/tools/test_kgmcp_phase2_baseline_recomparison.py`,
`tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py`

**Change:** Measured directly this session (`--resource-budget off --durations=10`,
investigation.md Group 1): `test_zero_mutation_of_agent_monitoring_and_manifest_across_full_run`
takes 40.94s in `test_kgmcp_phase2_baseline_recomparison.py:375` and 60.98s in
`test_kgmcp_phase3_pilot_acceptance_measurement.py:667` — both at/over `tests/conftest.py:60-88`'s
default 60s "medium" budget, both real live-gateway calls, not code bugs. `pyproject.toml:67-69`
already registers the `slow` marker (no new registration needed). `.github/workflows/test.yml`'s
`slow` job (`:208-241`) already runs `pytest tests/ -m "slow or extra_slow" --resource-budget large
...` — `tests/` is the whole tree recursively, so `tests/tools/` is already covered; **no
`.github/workflows/test.yml` change is required.**

- `test_kgmcp_phase2_baseline_recomparison.py`: this file currently has no `import pytest`
  (confirmed by direct read this session — imports are `ast`, `json`, `subprocess`, `sys`,
  `pathlib.Path` only). Add `import pytest` to the import block. Add `@pytest.mark.slow` directly
  above `def test_zero_mutation_of_agent_monitoring_and_manifest_across_full_run():` (`:375`).
- `test_kgmcp_phase3_pilot_acceptance_measurement.py`: this file already imports `pytest` and
  already has `@pytest.mark.extra_slow` on this exact function (`:666-667`, confirmed by direct
  read this session). **`extra_slow` alone does not satisfy `-m "not slow"`** — the `api-tools`
  job's filter only excludes tests carrying the `slow` marker, and this function carries only
  `extra_slow` today, which is why it still runs (and busts budget) in the fast lane. Add
  `@pytest.mark.slow` as a **second, stacked** decorator alongside the existing
  `@pytest.mark.extra_slow` — do not remove `extra_slow` (it is still true — the test genuinely
  exceeds 60s — and the `slow` job's `-m "slow or extra_slow"` filter already matches either mark).

Only these 2 functions get the new marker — not the whole module. Confirmed
(investigation.md Group 1) the other 16 tests in the phase2 file and 30 tests in the phase3 file
are all comfortably under budget individually; over-marking would silently drop far more real fast
coverage than intended.

**Do NOT touch:** any other test function in either file, or the `slow`/`extra_slow` marker
registration in `pyproject.toml` (already present). Do not modify `.github/workflows/test.yml` —
confirmed no gap exists.

**Verify:**
`pytest tests/tools/test_kgmcp_phase2_baseline_recomparison.py
tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py -m "not slow" -v` shows exactly
**46 tests run** (16 + 30, not 17 + 31) — confirms the marker landed on exactly the 2 intended
functions and nothing else was silently dropped from the fast lane (test_plan.md Anti-Drift Test
Guards, Group 1 marker scope). Then
`pytest tests/tools/test_kgmcp_phase2_baseline_recomparison.py
tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py -m "slow" --resource-budget large -v`
shows both `test_zero_mutation_...` functions collected and passing.

### Step 9 — Full-lane verification

**Files:** none (verification only, no code change).

**Change:** After Steps 1-8 land, run the two commands that are this ticket's own Acceptance
Criteria in literal form:

```bash
# AC1 — the real api-tools CI-lane command, must be 0 failed / 0 errors
pytest tests/tools -m "not slow" --tb=short -q

# AC2 — the 2 re-marked tests, isolated, under the real slow-job budget
pytest tests/tools/test_kgmcp_phase2_baseline_recomparison.py \
       tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py \
       -m "slow" --resource-budget large --tb=short -q
```

The first command must report 0 failed, 0 errors (skips from Step 5's 10 `gate_a` skips are
expected and correct, not a failure). The second must report both `test_zero_mutation_...`
functions passing. If either shows a different result than predicted by Steps 1-8 (e.g. a failure
count other than 0, or a skip count other than 10 in `test_gate_a_readpath_review.py` specifically
— re-run that file alone with `-v` to check), stop and re-diagnose before considering the ticket
complete — do not adjust any assertion to force a pass.

**Do NOT touch:** nothing is edited in this step — it is verification-only. Never run
`pytest tests/` (full suite) for this ticket, per CLAUDE.md's Testing Rule and test_plan.md's own
"Scoped Pytest Commands" guidance.

**Verify:** both commands above, run fresh, with real output pasted into the ticket's Test
Summary / Completion Summary sections at Finalize.

## Scope Guards

- No `src/` engine/simulation behavior change anywhere in this plan (ticket Out of Scope) — Step 4
  is the only `src/` file touched, and it only prepends 6 static header lines to a report-string
  builder; no simulation logic changes.
- No change to Knowledge Gateway MCP code, tests, or docs beyond Step 8's marker additions (ticket
  Out of Scope) — Step 8 adds only `@pytest.mark.slow` decorators (+ one `import pytest` in
  phase2), never touches assertions, fixtures, or gateway code in either KGMCP test file.
- No fix to any OTHER pre-existing failure outside `tests/tools` (ticket Out of Scope) — Step 4's
  regression check touches `tests/unit/content/` only because it is the direct producer of the
  file Step 4 edits, not a scope expansion.
- Never fabricate, author, or restore `SYN-*` synthetic corpus content for `gate_a_corpus.json`
  under any framing (ticket Out of Scope, investigation.md Anti-Drift Hazards) — Step 5 is a
  disclosed skip only.
- Never repurpose `tickets/todos/codex-runtime-activation/` as the epic-staleness fixture target
  (investigation.md Anti-Drift Hazards, confirmed disqualified — it has real, non-zero activity
  today) — Step 6 uses a fully synthetic `tmp_path` fixture only.
- Do not remove or weaken any *other* (non-stale) entry in any of the 3 frozen-hash dicts (Step 1)
  beyond the one confirmed-stale entry per file.
- Do not remove the correct leading `src/observability/event_extractor.py (multiple sites)`
  citation while fixing `ENTITY-003`'s second bare mention (Step 3).
- Do not add `.github/workflows/test.yml` changes for Step 8 — confirmed no CI/CD gap exists; the
  `slow` job already covers `tests/tools` via `pytest tests/`.
- Never run `pytest tests/` (full suite) for this ticket's own verification.

## Dependency Map

All 9 steps are independent of one another — each edits a disjoint file (or disjoint region of a
shared file, in the case of `test_exact_lookup_convention_decision.py` where Steps 1 and 2 touch
different, non-overlapping parts: the hash dict vs. `_EPIC_TICKET_PATH`). They may be implemented
and verified in any order, but the ordering above (low-risk data/constant fixes first, more
surface-area fixes next, marker changes and full-lane verification last) is recommended so early
steps build implementer confidence before the more involved Steps 5/6/7. Step 9 depends on Steps
1-8 all being complete (it is the aggregate check).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — `tests/tools -m "not slow"` passes with 0 failures, 0 errors | Steps 1-8 (all fixes) | Step 9's first command |
| AC2 — the 2 re-marked tests pass under `-m "slow"` with a large budget; `slow` job already covers `tests/tools` | Step 8 | Step 9's second command |
| AC3 — every fix is a genuine correction to a stale reference/guard/CI-CD gap, never a loosened assertion, root cause documented | Steps 1-8 (each step's Change section states the confirmed real root cause) | `pytest tests/tools -m "not slow" -v` full output reviewed at Verify, plus this plan's own citations |
| AC4 — `gate_a_corpus.json`/`gate_a_results.json` provenance resolved with an explicit, disclosed answer | Step 5 | `pytest tests/tools/test_gate_a_readpath_review.py -v` shows 10 skipped (each with the dated `_SKIP_REASON` text visible via `-rs`), 6 passed |
| AC5 — `content_usage_matrix.md`'s frontmatter gap fixed at the real source (the generator) | Step 4 | `pytest tests/unit/content/test_content_usage_matrix.py tests/tools/test_generate_registry.py tests/tools/test_validate_frontmatter.py -q` + direct `validate_frontmatter.py` re-check |

## Anti-Drift Notes

- **Step 1/Step 5 frozen-hash and skip guards:** never remove or weaken any entry/test beyond the
  one confirmed-stale item per file — both mechanisms exist specifically to catch *future*
  unintended changes; over-narrowing silently defeats that purpose.
- **Step 5 is the one place fabrication risk is highest.** The test module's own hardcoded
  `SYN-*` IDs and the decision doc's own detailed §6.3 narration make a "plausible-looking"
  reconstruction easy to produce and easy to rationalize as "restoring," not "fabricating." It is
  neither — treat any temptation to construct `SYN-P0PAIR-001`/`SYN-MULTISHARD-001`/
  `SYN-MALFORMED-001` content as a stop-and-reconfirm-scope signal, not a shortcut.
  Skip-with-disclosure is the only acceptable resolution.
- **Step 6's synthetic fixture must exercise the same failure mode as the real one would.** The
  new `test_does_not_flag_never_started_synthetic_folder_epic` must go through the full
  `find_stale_epics`/`compute_stale_epics_report` pipeline (not just `is_epic_stale()` directly,
  which `test_does_not_flag_never_started_epic` at `:216-236` already covers at the unit level) —
  the missing coverage was specifically the end-to-end real-file-reading path, which this new test
  restores.
- **Step 7 requires verifying the whole chain, not just flipping the literal.** A shallow fix that
  only changes `test_command_is_python3`'s assertion without also fixing
  `test_args_point_to_search_mcp` would leave that second test broken — both must land together,
  plus the new wrapper-invokes-python3 test that proves the chain end-to-end.
- **Step 8's phase3 fix stacks `slow` onto the existing `extra_slow`, it does not replace it.**
  `extra_slow` is still an accurate, true statement about this test (it exceeds even the 60s
  "medium" budget by a wide margin) — removing it would be a regression in its own right, since
  the `slow` job's `-m "slow or extra_slow"` filter and any future budget-tier logic may key off
  either mark independently.
- **Self-referential agent-monitoring risk (checked, resolved, flag for Implement confirmation):**
  this ticket's own Investigate/Plan/Implement pipeline activity writes to
  `agent-monitoring/events.jsonl`/`runs.jsonl` during the same session these tests run in. Checked
  this session: the two Group 1 "zero mutation" tests compare a `git status --porcelain --
  agent-monitoring/` snapshot taken immediately before their own corpus run against one taken
  immediately after (`_agent_monitoring_porcelain_snapshot()`, confirmed at both files' tails read
  this session) — a live before/after diff computed entirely within the test's own execution
  window, not a cross-session frozen count or content-hash of `runs.jsonl`/`events.jsonl`. No test
  touched by this plan's 9 steps pins a row count or hash of either monitoring file. This differs
  from the earlier KGMCP Phase 5 self-contamination bug (which did pin a count). Residual
  instruction for Implement: if any new test added by this plan (Steps 5, 6, 8's verify runs)
  happens to run concurrently with an active agent-monitoring write from this ticket's own
  pipeline, re-confirm the snapshot-diff mechanism (not a frozen count) is what is being compared
  before treating any unexpected `agent-monitoring/` porcelain diff as a real bug.

## Deviations (recorded during Implement, 2026-08-17)

- **Step 1 — 2 additional stale frozen-hash entries beyond the plan's named ones.**
  `test_no_code_changes_to_named_tools_modules` in all 3 decision-doc test files asserts inside a
  `for entry in dict.items()` loop, which raises on the *first* mismatched entry and never checks
  the rest. This means investigation.md's "confirmed via direct pytest run" verification could
  only ever see the first stale entry per file — it never actually verified the "other 3 entries
  still match" claim for entries ordered after the confirmed-stale one. After applying Step 1's
  named fix and re-running each file individually, 2 more real stale entries surfaced:
  `tools/generate_registry.py` in both `test_context_kind_priority_decision.py` and
  `test_exact_lookup_convention_decision.py` (masked by `tools/parity_index.py`'s earlier failure
  in dict order), and `tools/validate_frontmatter.py` in `test_stored_artifact_kind_decision.py`
  (masked by `tools/generate_registry.py`'s earlier failure). Confirmed via `git log` that none of
  the 3 `TCK-20260802-*` decision tickets touched either file, and both files' real last-touch
  commit (`29d78798`, 2026-08-14) postdates all 3 tickets' authoring (2026-08-02) — same
  legitimately-changed-via-unrelated-later-work rationale the plan already used for the named
  entries. Fixed with matching disclosure comments, same template.
- **Step 3 — 3 additional malformed evidence citations in `docs/event_ledger/entity.yaml` beyond
  `ENTITY-003`.** `test_entity_ledger_evidence_citations_are_real_files` has the identical
  loop-stops-at-first-failure shape. Fixing `ENTITY-003` surfaced `ENTITY-007` (same bare
  `event_extractor.py-only` pattern as `ENTITY-003`, same fix), then `ENTITY-014` (bare
  `evolution.py` mention, corrected to `src/engine/evolution.py` after confirming via direct file
  read that it is the real goblin-evolution gear-grant producer), then `ENTITY-015` (a 3-file
  citation malformed as one concatenated path, `src/engine/tactical.py/executor.py/worker_logic.py`,
  corrected to 3 properly comma-separated real paths under `src/engine/`, each confirmed to
  exist). Same root-cause class the plan's Step 3 already named for `ENTITY-003` — more instances
  of it than the plan's single-loop-run verification could see.
- **Step 4 — `docs/REGISTRY.yaml` regeneration, not a named plan step.** Regenerating
  `content_usage_matrix.md` (now with frontmatter) via `test_generate_and_save_report` made it a
  newly-registrable doc, putting the committed `docs/REGISTRY.yaml` out of sync with a fresh
  regeneration (`TestRealDocsTree::test_check_flag_detects_no_drift_against_real_registry` failed).
  Regenerated `docs/REGISTRY.yaml` via `tools/generate_registry.py --output docs/REGISTRY.yaml` —
  a direct, necessary consequence of Step 4's fix and squarely inside CLAUDE.md's existing
  ticket-close convention ("`docs/REGISTRY.yaml` is regenerated unconditionally... stage the
  regenerated file"), not scope creep.

None of these deviations touch a file or behavior outside this ticket's own named scope (`tests/
tools`, `docs/event_ledger/entity.yaml`, `src/content/matrix.py`, `docs/mechanics/
content_usage_matrix.md`, `docs/REGISTRY.yaml`) — each is a genuine correction to a stale
reference the plan's own verification method could not see, found and fixed using the same
already-approved fix pattern, never a loosened assertion.
