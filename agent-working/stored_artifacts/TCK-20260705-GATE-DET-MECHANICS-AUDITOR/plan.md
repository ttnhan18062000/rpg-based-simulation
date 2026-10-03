---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260705-GATE-DET-MECHANICS-AUDITOR
artifact_type: plan
tags: [ai, workflows, determinism, mechanics-auditor, parity]
---

# Implementation Plan — TCK-20260705-GATE-DET-MECHANICS-AUDITOR

## Summary

Add `tools/gate_checks/mechanics_auditor_static.py`, a scoped, per-entry deterministic backstop that
answers exactly one question for a named `docs/parity_ledger/` entry: does its `test_path` field cite
a real test, and does that test currently pass? The module never scans the whole ledger — it looks up
one entry ID (or a small explicit set) via `CANONICAL_LEDGER_FILES` (imported from
`tools/parity_ledger_scan.py`, never re-derived), parses the `test_path` string through the four
legacy formats the investigation found (clean node-id, single backtick-wrapped, comma/`+`-joined
multi-citation, unparseable parenthetical-annotated), and — per the orchestrating session's resolved
decision — checks **every** citation in a multi-citation string, not just the first. A `tests_v2/`
citation short-circuits to FAIL without a subprocess call (the directory doesn't exist in this repo);
anything else runs `python3 -m pytest <citation> -x -q` scoped to that one file/node-id and reports the
real pytest output on failure. Wiring happens entirely inside `.claude/agents/mechanics-auditor.md`'s
own prompt (its existing "Checking Parity" section) — per the orchestrating session's resolved
decision, this ticket does **not** add a new `Agent(subagent_type: "mechanics-auditor")` call site to
`implement-ticket.js`, since the agent has zero pipeline call sites today and adding one would be new
pipeline architecture beyond this ticket's scope. Docs: extend `docs/ai/agents.md`'s existing
`mechanics-auditor` section with a `Step 0` paragraph mirroring the `done-checker`/`parity-updater`
precedent; add one minimal cross-referencing sentence (not a phase-table row) to each of
`docs/ai/workflows.md`, `docs/ai/system_overview.md`, `docs/ai/ticket-lifecycle.md` (per Step 5, revised
in architecture review round 1 — the ticket's own AC requires these updated, and a phase-table row would
misrepresent an agent that has no pipeline phase, but a single disclosure sentence does not).

## Steps

### Step 1 — Core check module: `tools/gate_checks/mechanics_auditor_static.py`
**Files:** `tools/gate_checks/mechanics_auditor_static.py` (new)
**Change:**
Create the module with this exact shape (plain functions, no CLI/argparse, mirrors
`done_checker_static.py`/`parity_updater_static.py`'s pattern of a `sys.path.insert` shim for the
`tools/` dir then importing siblings):

```python
import re
import subprocess
import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import yaml
from parity_ledger_scan import CANONICAL_LEDGER_FILES  # noqa: E402
from gate_checks.parity_updater_static import expected_subsystems_for_files  # noqa: E402
```

Module-level regexes:
- `_BACKTICK_FULL_RE = re.compile(r"^`([^`]+)`$")` — matches only when the *entire* stripped string
  is one backtick pair with nothing outside it.
- `_DELIM_SPLIT_RE = re.compile(r"\s*[,+;]\s*")` — top-level multi-citation splitter.
- `_NODE_ID_RE = re.compile(r"^[\w./\-]+\.py(::[\w \[\]./:\-]+)?$")` — a clean, invocable
  `path.py` or `path.py::test_name[param]` shape.

Function 1 — `parse_test_path_citations(raw) -> tuple[list[str] | None, str | None]`:
- `raw is None` or `not str(raw).strip()` → return `(None, "test_path is null/missing")`. This is the
  hard-FAIL case for AC's "non-null" requirement (ticket Scope item (a)) — never skip it.
- Strip whitespace. Split on `_DELIM_SPLIT_RE`. If more than one part results, treat as a genuine
  multi-citation **only if every part independently reduces to a clean `_NODE_ID_RE` match** after
  stripping a full backtick-wrap from each part (via a private `_strip_full_backtick(s)` helper that
  applies `_BACKTICK_FULL_RE` and returns the inner group, or `s` unchanged if it doesn't match). If
  any part fails to reduce cleanly, return `(None, f"unparseable test_path (multi-citation candidate "
  f"but one segment did not resolve to a clean path): {raw!r}")` — never silently drop the bad
  segment. If all parts are clean, return `(parts, None)` — **the orchestrating session's decision:
  every citation must be checked, not just the first.**
- If only one part: apply `_strip_full_backtick`. If the result matches `_NODE_ID_RE`, return
  `([result], None)`. This is the plain clean-path case (163 entries) and the fully-backtick-wrapped
  case (49 entries with no trailing prose).
- Otherwise (trailing prose survives stripping — the parenthetical-annotation case, 11 entries):
  return `(None, f"unparseable test_path: {raw!r}")`. **Do not attempt to extract the path from
  inside the prose** — per investigation's Anti-Drift Hazards, guessing a corrected path for this
  class is explicitly out of scope. Report the raw string and stop; never raise.

Function 2 — `check_test_path(test_path_raw, base_dir: Path = Path(".")) -> tuple[str, str]`:
- Call `parse_test_path_citations`. If it returns `(None, err)`, return `("FAIL", err)` immediately.
- For each citation in the returned list (checking **all**, per the resolved multi-citation policy):
  - `file_part = citation.split("::", 1)[0]`.
  - If `file_part.startswith("tests_v2/")`: record `("FAIL", "legacy path, tests_v2/ directory does "
    "not exist in this repo: " + citation)` for this citation **without calling `subprocess.run`** —
    cheap short-circuit per investigation's Conclusion step 5.
  - Else if `not (Path(base_dir) / file_part).exists()`: record `("FAIL", f"file does not exist: "
    f"{Path(base_dir) / file_part}")` — also no subprocess call.
  - Else: run `subprocess.run([sys.executable, "-m", "pytest", citation, "-x", "-q"], cwd=str(base_dir),`
    `capture_output=True, text=True, timeout=120)` inside a `try/except Exception` (never let a
    subprocess error escape as an unhandled exception — record `("FAIL", f"error invoking pytest: "
    f"{exc}")` instead). On `returncode == 0`, record `("PASS", f"{citation} passed")`. On nonzero,
    record `("FAIL", f"{citation} failed (exit {returncode}): {(stdout+stderr)[-2000:]}")` — the
    **actual pytest output**, truncated to the last 2000 chars, must appear in the evidence string
    (this is what AC's "not just a generic 'not found'" line requires and what test 2 asserts).
  - `base_dir` defaults to `Path(".")` (repo root in real use) but is overridable so tests can point
    it at `tmp_path` without changing the process's cwd.
- Aggregate: if any citation's result is `"FAIL"`, overall status is `"FAIL"`; otherwise `"PASS"`.
  Evidence is `"; ".join(f"{citation}: {msg}" for citation, status, msg in results)` — every
  citation's individual verdict must be visible, not collapsed into one bare accept/reject.

Function 3 — `find_entry(entry_id: str, ledger_dir="docs/parity_ledger") -> tuple[dict | None, str | None]`:
- Iterate `CANONICAL_LEDGER_FILES` (imported constant — do not re-list the 8 filenames). For each
  file that exists under `ledger_dir`, `yaml.safe_load` it (skip on any parse exception — legacy-data
  tolerance, mirrors `parity_updater_static.derive_mapping`'s own `except Exception: continue`).
  Return `(entry, filename)` on the first entry whose `id` field equals `entry_id`.
- Return `(None, None)` if no canonical file contains it. **Never** collect or return information
  about any other entry encountered while scanning — the function returns the instant it finds a
  match; sibling entries in the same YAML are read into memory transiently (unavoidable — YAML has no
  streaming-by-key API) but never surfaced in the return value. This is what test 11 asserts.

Function 4 — `verify_entry_test_path(entry_id: str, ledger_dir="docs/parity_ledger", base_dir: Path = Path(".")) -> dict`:
- Call `find_entry`. If not found, return
  `{"entry_id": entry_id, "status": "FAIL", "evidence": f"entry {entry_id} not found in any canonical "`
  `f"ledger file under {ledger_dir}", "verified_by": ["static:mechanics_auditor_static"]}`.
- Else call `check_test_path(entry.get("test_path"), base_dir)` and return
  `{"entry_id": entry_id, "ledger_file": filename, "status": status, "evidence": evidence,`
  `"verified_by": ["static:mechanics_auditor_static"]}`. The `verified_by` shape
  (`["static:mechanics_auditor_static"]`) matches the established convention from
  `done_checker_static.py`/`parity_updater_static.py` exactly — do not invent a different shape.

Function 5 — `verify_entries(entry_ids, ledger_dir="docs/parity_ledger", base_dir: Path = Path(".")) -> list[dict]`:
- `return [verify_entry_test_path(eid, ledger_dir, base_dir) for eid in entry_ids]`. This satisfies
  the ticket Scope's "a set of entries" wording without changing the single-entry function's
  contract.

Function 6 (thin reuse wrapper, satisfies AC1's "reusing `GATE-DET-PARITY-UPDATER`'s mapping module
if available") — `candidate_ledger_files_for_module(src_files, ledger_dir="docs/parity_ledger") -> dict`:
- `return expected_subsystems_for_files(src_files, ledger_dir)` — a direct pass-through. Document in
  its docstring that this is for the case where `mechanics-auditor` is auditing an entire mechanics
  chapter/module (not a single named entry ID yet) and needs to know which ledger YAML file(s) its
  `src/` files are cited in, **before** it has entry IDs to pass to `verify_entry_test_path`. This is
  the only genuinely reusable piece from `parity_updater_static.py` per the investigation — do not
  attempt to reuse `derive_mapping`/`cross_reference_touched` for anything beyond this discovery step;
  they solve a different problem (git-diff-vs-ledger cross-reference) with zero test-execution logic.

**Do NOT touch:** `tools/parity_ledger_scan.py`, `tools/gate_checks/parity_updater_static.py`,
`tools/gate_checks/done_checker_static.py` — import from them, never edit their public functions or
return shapes.
**Verify:** `tests/tools/test_mechanics_auditor_static.py` (Step 2) exercises every function above.

### Step 2 — Tests: `tests/tools/test_mechanics_auditor_static.py`
**Files:** `tests/tools/test_mechanics_auditor_static.py` (new)
**Change:** One file, mirroring `tests/tools/test_parity_updater_static.py`'s header/import shape
(`_TOOLS_DIR` sys.path insert, then `from gate_checks.mechanics_auditor_static import (...)`), plus a
local `_write_ledger(tmp_path, filename, entries)` helper identical to the sibling test file's. Add
all 11 tests from `test_plan.md` exactly as specified there:

1. `test_test_path_existence_check_passes_for_real_passing_test` — write a trivial always-green test
   file into `tmp_path` (e.g. `def test_ok(): assert True`), call `check_test_path("test_ok_file.py::test_ok", base_dir=tmp_path)`,
   assert `PASS`.
2. `test_test_path_existence_check_fails_for_genuinely_failing_test` — write a test file into
   `tmp_path` containing `def test_fails(): assert 1 == 2, "custom fail message"`, call
   `check_test_path(...)`, assert `FAIL` and assert the literal string `"custom fail message"` (or
   `"1 == 2"`) appears in the evidence — **not** a generic "not found" string.
3. `test_test_path_existence_check_fails_for_nonexistent_file` — `check_test_path("tests/does_not_exist.py::test_x", base_dir=tmp_path)`,
   assert `FAIL`, assert the missing path string appears in evidence, assert no exception raised.
4. `test_null_test_path_fails_not_crashes` — `check_test_path(None)` and `check_test_path("")`, both
   assert `FAIL`, no exception.
5. `test_backtick_wrapped_test_path_is_parsed` — write a real passing test file into `tmp_path`, call
   `check_test_path("`tests/<name>.py::test_ok`", base_dir=tmp_path)` with literal backticks in the
   string, assert `PASS` (proves stripping, not literal-path failure).
6. `test_legacy_tests_v2_path_fails_cleanly_as_stale` — `check_test_path("tests_v2/test_old.py::test_x")`;
   assert `FAIL`, assert "tests_v2" and "does not exist" (or equivalent) appear in evidence; monkeypatch
   `subprocess.run` to raise if called, proving the short-circuit never invokes it.
7. `test_parenthetical_annotation_suffix_is_unparseable_and_fails_gracefully` — 
   `check_test_path("`tests/tools/test_x.py` (indirectly via `Y` and `Z` flow)")`; assert `FAIL`, assert
   the raw string appears in evidence, assert no exception.
8. `test_multi_citation_test_path_policy` — write two test files into `tmp_path`, one passing one
   failing; `check_test_path("a.py::test_pass, b.py::test_fail", base_dir=tmp_path)`; assert overall
   `FAIL` (because not all citations pass — locks in "check ALL" policy) and assert **both** citations'
   individual verdicts appear in the evidence string (proving the failing one wasn't silently dropped
   and the passing one wasn't used to mask it).
9. `test_check_is_scoped_not_full_suite` — monkeypatch `subprocess.run` to capture `args`/`kwargs`
   instead of actually running pytest; call `check_test_path` with a valid existing-file citation;
   assert the captured argv's pytest-target element equals the citation (not `"tests/"` and not
   absent).
10. `test_verified_by_field_present_and_shaped_correctly` — call `verify_entry_test_path` against a
    `tmp_path`-fixture ledger entry; assert `result["verified_by"] == ["static:mechanics_auditor_static"]`.
11. `test_scoped_by_entry_id_not_whole_ledger` — `_write_ledger` a 3-entry fixture YAML file with IDs
    `A-001`, `A-002`, `A-003` (only `A-002` has a `test_path` that would fail); call
    `verify_entry_test_path("A-002", ledger_dir=tmp_path)`; assert the returned dict's `entry_id` is
    exactly `"A-002"` and nothing in the returned evidence/structure mentions `A-001`/`A-003` — proves
    the function never reports on sibling entries.

**Do NOT touch:** `tests/tools/test_parity_updater_static.py`, `tests/tools/test_done_checker_static.py`
(run them alongside, per the Scoped Pytest Commands below, but do not edit them).
**Verify:**
```
python3 -m pytest tests/tools/test_mechanics_auditor_static.py -v
python3 -m pytest tests/tools/test_parity_updater_static.py tests/tools/test_done_checker_static.py tests/tools/test_mechanics_auditor_static.py -v
```
Never run `pytest tests/`.

### Step 3 — Wire the check into `mechanics-auditor`'s own prompt
**Files:** `.claude/agents/mechanics-auditor.md`
**Change:** Edit the "Checking Parity" section (current lines 32-38). Insert a `Step 0` paragraph
directly above the existing "For each rule:" bullet list, mirroring `done-checker`'s/`parity-updater`'s
prose pattern exactly:

```
## Checking Parity

**Step 0 — static pre-check:** Before writing a final `Status`/`Finding` for any entry, run
`tools/gate_checks/mechanics_auditor_static.py`'s `verify_entry_test_path(entry_id)` (via
`python3 -c "..."`) for that entry's ID and cite its PASS/FAIL + evidence output verbatim. **This check
never overrides your own bit-identical code-vs-formula comparison (steps 1-4 above)** — it answers a
narrower, orthogonal question (does the cited `test_path` exist and pass?), not "does the code diverge
from the documented law?" A static `FAIL` here (most often: no `test_path` at all — 82% of `verified`
entries have none, per this ticket's own investigation) means the entry's parity claim currently lacks
automated evidence, not that the code is wrong. **Do not reclassify a row from `PARITY` to `DIVERGENT`
or `MISSING` solely because Step 0 returned `FAIL`** — `DIVERGENT`/`MISSING` mean something specific
(implementation differs / implementation absent) that a missing test citation does not establish.
Instead: continue to determine `Status` from your own independent comparison as before; if Step 0
returns `FAIL` for a row you'd otherwise classify `PARITY`, keep the `PARITY` classification but append
to the `Finding` column an explicit caveat, e.g. "Code matches documented formula by direct comparison;
however, automated test_path evidence could not be verified — {Step 0 evidence}." Self-report in a
`verified_by` field whether each row's `Status` came from independent judgment vs. was also
corroborated by Step 0's static `PASS`.

For each rule:
- Find the relevant parity ledger entry in `docs/parity_ledger/` (the subsystem YAML that covers this rule).
- Check its `status`: `verified` / `divergent` / `missing` / `unsupported` / `legacy_verified`.
- If `verified`: run the Step 0 static check above for this entry's ID and cite it; determine `Status`
  from your own bit-identical comparison as before, appending a Step-0-FAIL caveat to `Finding` if
  applicable (never changing `Status` to `DIVERGENT`/`MISSING` on that basis alone).
- If `missing`: flag as gap — this rule has no verified implementation.
- If `divergent`: read `divergence_note` and confirm the divergence is documented in `docs/guidelines/v2_intentional_divergences.md`.
```

Also update the "Output" section (current lines 40-50) to mention the new field: after the existing
status-values bullet list, add one line: `Each row also carries a `verified_by` field (e.g.
`["static:mechanics_auditor_static", "llm"]` or `["llm"]`) recording whether its Status was also
corroborated by the Step 0 static check or came from independent judgment alone.`

**Enforcement-asymmetry disclosure (architecture review round 1 finding):** add one sentence to the end
of the new Step 0 paragraph: `Unlike done-checker/parity-updater's Step 0 (which the orchestrator runs
and independently verifies), this Step 0 has no orchestrator-side enforcement — mechanics-auditor has
no pipeline call site — so compliance depends entirely on this agent actually running the script and
citing it honestly.` This is a real, disclosed limitation, not silently presented as equivalent-rigor to
the two pipeline-wired siblings.

**Do NOT touch:** The chapter table, the Registry Lookup section, or the `UNDOCUMENTED` classification
rule (per ticket Out of Scope: "Re-deciding whether an `UNDOCUMENTED` implementation is intended
behavior — remains LLM-judged" — leave that branch's instructions exactly as they are). Do **not** add
any `Agent(subagent_type: "mechanics-auditor")` call site to `.claude/workflows/implement-ticket.js` —
confirmed zero existing call sites and this ticket does not add one (orchestrating session's resolved
decision).
**Verify:** No automated test covers prompt-file prose; verify by re-reading the edited section for
internal consistency (the `divergent`-branch `test_path` requirement noted as a pre-existing minor
inconsistency in investigation.md is **not** being fixed here — out of scope, do not touch that
bullet).

### Step 4 — Update `docs/ai/agents.md`'s `mechanics-auditor` section
**Files:** `docs/ai/agents.md`
**Change:** In the existing `### \`mechanics-auditor\`` section (current lines 224-245), insert a
`**Step 0 — static pre-check:**` paragraph between the "Output classification" block and "When to
invoke directly," mirroring `done-checker`'s (lines 112-116) and `parity-updater`'s (lines 192-199)
phrasing exactly:

```
**Step 0 — static pre-check:** Before finalizing a `Status`/`Finding` for any entry, the agent runs
`tools/gate_checks/mechanics_auditor_static.py`'s `verify_entry_test_path(entry_id)` (via
`python3 -c "..."`) and cites its PASS/FAIL + evidence verbatim. This check only confirms whether the
entry's cited `test_path` exists and passes — it never overrides the agent's own bit-identical
code-vs-formula comparison. A static `FAIL` (commonly: no `test_path` at all — 82% of `verified`
entries have none) does not downgrade a `PARITY` row to `DIVERGENT`/`MISSING`; it is appended as a
caveat in `Finding` instead, since a missing test citation is a verification gap, not evidence of code
divergence. Unlike `done-checker`/`parity-updater`'s Step 0 (orchestrator-run and independently
verified), this Step 0 has no orchestrator-side enforcement — `mechanics-auditor` has no pipeline call
site — so compliance depends entirely on the agent actually running the script and citing it honestly.
The agent self-reports in `verified_by` whether each row's `Status` was corroborated by the static check
or came from independent judgment alone.
```

Also add one line noting the reuse: `A convenience wrapper, `candidate_ledger_files_for_module`,
reuses \`parity-updater\`'s \`expected_subsystems_for_files\` to locate candidate ledger files when
auditing a whole chapter/module rather than a single named entry.`

**Do NOT touch:** `docs/ai/workflows.md`, `docs/ai/system_overview.md`, `docs/ai/ticket-lifecycle.md`
in this step — those get their own minimal one-sentence edit in Step 5, not duplicated here. Do not touch `docs/ai/skills.md`'s
"Choosing the Right Tool" row (`docs/ai/skills.md:177`) — it already correctly points at
`Agent(subagent_type: "mechanics-auditor")` for ad hoc invocation and remains accurate; the ticket's
AC only names `agents.md` plus "the other 3 shared docs," which does not include `skills.md`.
**Verify:** No automated test; this is documentation. Confirm by grepping
`docs/ai/agents.md` for `Step 0` in the `mechanics-auditor` section post-edit.

### Step 5 — Minimal mention in `docs/ai/workflows.md`, `docs/ai/system_overview.md`, `docs/ai/ticket-lifecycle.md`
**Files:** `docs/ai/workflows.md`, `docs/ai/system_overview.md`, `docs/ai/ticket-lifecycle.md`
**Change (revised per architecture review round 1 finding — the ticket's own AC #4 requires "the other
3 shared docs updated," and `SEQUENCE.md`'s Dependency Notes state all 4 sibling tickets update these
same 3 docs; leaving them fully untouched left the AC literally unmet with no documented
reconciliation):** Re-run `grep -n -i "mechanics-auditor" docs/ai/workflows.md docs/ai/system_overview.md
docs/ai/ticket-lifecycle.md` first to confirm the zero-mentions finding from investigation.md still
holds. Then add exactly one minimal, accurate sentence to each file — **not** a new phase-table row
(that would misrepresent an agent with no pipeline phase) — framed per investigation.md's own proposed
middle ground ("ad hoc agents with their own static pre-checks"):
- `docs/ai/workflows.md`: near the existing pipeline-phase table, add one sentence noting that
  `mechanics-auditor` is an ad hoc agent (not a pipeline phase) that now has its own static pre-check,
  cross-referencing `docs/ai/agents.md`'s section for detail.
- `docs/ai/system_overview.md`: in whichever section already discusses ad hoc/non-pipeline agents (or,
  if none exists, in the same section that discusses `done-checker`/`parity-updater`'s static
  pre-checks), add one sentence noting `mechanics-auditor` now has an equivalent static pre-check,
  explicitly flagging that it is agent-self-invoked (no orchestrator enforcement), unlike its two
  pipeline-wired siblings.
- `docs/ai/ticket-lifecycle.md`: add one sentence in whichever section already mentions
  `mechanics-auditor` being available for ad hoc use (or near the Verify/Parity phase descriptions if no
  such section exists), noting the new static pre-check and its self-invoked nature.
If a mention has appeared in the interim (race with a sibling ticket), read it and extend it minimally
rather than duplicating.
**Do NOT touch:** Do not add a new phase-table row to any of these 3 files under any circumstance in
this ticket's scope — one cross-referencing sentence per file only.
**Verify:** Re-grep each file post-edit for a `mechanics-auditor` mention; confirm each is a single
sentence, not a new table row or section.

## Scope Guards

- Do not build a ledger-wide validator — every entry point (`verify_entry_test_path`, `verify_entries`)
  takes explicit entry ID(s); nothing iterates "all entries in a file" as a feature.
- Do not attempt to "fix," "modernize," or path-correct any of the 49 backtick-wrapped-with-prose or 11
  parenthetical-annotation `test_path` strings — report FAIL with the raw string, always.
- Do not re-derive `CANONICAL_LEDGER_FILES` — import from `tools/parity_ledger_scan.py`.
- Do not touch `tools/gate_checks/parity_updater_static.py`, `tools/gate_checks/done_checker_static.py`,
  or their tests, beyond importing from the former.
- Do not add any new call site to `.claude/workflows/implement-ticket.js`.
- Do not fold anything into `make lane-architecture` / the `architecture` pytest marker.
- Do not run or scope any check to the full test suite (`pytest tests/`) — every invocation is a single
  cited path/node-id.
- Do not touch `docs/parity_ledger/*.yaml` — read-only reference data for this ticket.
- Do not re-decide the `UNDOCUMENTED` classification rule in `mechanics-auditor.md` — remains
  LLM-judged, per ticket Out of Scope.
- Do not add token/cost telemetry (SEQUENCE.md decision 5).

## Dependency Map

Step 1 (module) must land before Step 2 (tests import it). Step 3 (agent prompt) and Step 4
(docs/ai/agents.md) both reference the function names from Step 1 but are otherwise independent of
each other and of Step 2 — order among 3/4/5 doesn't matter. Step 5 is a verification-only step best
run last, immediately before Finalize, since it's a freshness check against concurrent sibling-ticket
activity.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `mechanics_auditor_static.py` exists, verifies existence+pass/fail of cited `test_path`, reuses parity-updater's mapping module | Step 1 | Tests 1-9 in `test_mechanics_auditor_static.py` |
| `mechanics-auditor`'s invocation path instructs it to run this check before rendering PARITY | Step 3 | Manual re-read (prompt file, no automated test) |
| At least one coverage-honesty test per check function, incl. genuinely-failing-test fixture | Step 2 | Test 2 (`test_test_path_existence_check_fails_for_genuinely_failing_test`) specifically |
| `docs/ai/agents.md`'s section + other 3 shared docs updated | Steps 4, 5 | Grep confirmation in Step 5; manual re-read of Step 4's edit |

## Anti-Drift Notes

- **82% of `verified` entries have no `test_path` today** (investigation.md's format survey). This
  check will legitimately FAIL for the vast majority of the ledger if ever run in bulk — that's
  expected and correct, not a bug to "fix." The design keeps blast radius contained by only ever
  operating on explicit entry IDs the auditor is actively rendering a verdict for in the current
  session, never a sweep.
- **`tests_v2/` does not exist anywhere in this repo.** Any citation under it must FAIL cleanly and
  cheaply (no subprocess) — this is a distinct code path from generic "file does not exist," both
  because it's cheaper and because the evidence message should name it as a known-legacy-stale class,
  not a mysterious missing file.
- **Multi-citation policy is "check ALL, not first"** — this was an open question in investigation.md,
  resolved by the orchestrating session before planning began. Test 8 locks this in explicitly; do not
  silently narrow it to "first citation only" during implementation.
- **Corrected per architecture review round 1 (CONFIRMED finding): a static Step 0 `FAIL` must NEVER
  force a `PARITY` row to `DIVERGENT`/`MISSING`.** The original plan draft mapped a static FAIL directly
  onto those labels, which is factually wrong — `DIVERGENT` means "implementation differs" (a positive
  claim about code behavior mechanics-auditor's own steps 1-4 establish, never something a missing
  `test_path` citation establishes) and `MISSING` means "no implementation exists," neither of which
  follows from "no automated test was cited." Given 82% of `verified` entries have no `test_path`,
  applying the original (wrong) rule literally would have force-labeled the vast majority of likely-
  correct entries as `DIVERGENT`, corrupting `docs/guidelines/v2_intentional_divergences.md` if anyone
  later "resolved" those fabricated divergences. The corrected design (Steps 3/4 above) keeps `Status`
  determined solely by the auditor's own independent code comparison; Step 0's result is surfaced only
  as an additional `Finding` caveat, never a `Status` override.
- **The schema's `divergent`-status branch also requires `test_path`, but `mechanics-auditor.md`'s
  prose only checks it on the `verified` branch** — a pre-existing minor inconsistency investigation.md
  flagged. Do not silently fix it as part of this ticket; leave the `divergent` branch's instructions
  untouched.
- **`gate_checks/__init__.py` is empty** — do not add re-exports to it; both sibling modules are
  imported via their full dotted path (`gate_checks.parity_updater_static`, etc.), and the new module
  should follow the same convention.
