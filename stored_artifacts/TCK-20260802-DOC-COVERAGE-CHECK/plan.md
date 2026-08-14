---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260802-DOC-COVERAGE-CHECK
artifact_type: plan
tags: [workflows, documentation]
---

# Plan — TCK-20260802-DOC-COVERAGE-CHECK

## Step 1 — `tools/gate_checks/done_checker_static.py`: new helpers + check function

**File:** `tools/gate_checks/done_checker_static.py`

- Add `import subprocess` and `import re` at the top.
- Add `_git_touched_paths(root: Path = Path(".")) -> set[str]`: runs
  `git status --porcelain` via `subprocess.run(cwd=root, capture_output=True, text=True, timeout=10,
  check=False)`; on `OSError`/`subprocess.SubprocessError` returns `set()` (fail-open — never raises,
  never blocks the workflow on a missing/broken git binary). Parses each non-empty output line as
  `"XY PATH"` or `"XY PATH1 -> PATH2"` (rename) — for renames, takes the target path. Returns paths
  as-written by git (relative to `root`), not normalized further.
- Add `_DOCS_BULLET_RE = re.compile(r"^-\s+\`(docs/[^\`]+)\`", re.MULTILINE)`.
- Add `_parse_docs_to_update(section_text: str) -> list[str]`: strips the input; if the stripped,
  lowercased text is `""`, `"none"`, `"none."`, or `"n/a"`, returns `[]`. Otherwise returns
  `_DOCS_BULLET_RE.findall(section_text)`.
- Add `check_docs_to_update_coverage(ticket_id: str, tier: str, base_dir: Path =
  Path("staging_artifacts")) -> tuple[str, str]`:
  - `tier == "hotfix"` → `("NA", "hotfix tier — no investigation.md, no Docs Requiring Update section")`.
  - `investigation.md` missing → `("FAIL", ...)` (mirrors `check_staging_artifacts_complete`'s own
    missing-file handling — at Verify time, for standard/epic tier, this file must exist).
  - Extract `## Docs Requiring Update` via the existing `_extract_section_text` helper; parse via
    `_parse_docs_to_update`.
  - Empty parse result AND section text was itself empty/a recognized "none" phrase → `("PASS", "no
    docs/ paths flagged as requiring update")`.
  - Empty parse result but section text is non-empty and NOT a recognized "none" phrase → `("FAIL",
    "...no docs/ path could be parsed... expected one bullet per path...")` (format-regression
    guard).
  - Non-empty parse result → call `_git_touched_paths()`; compute `missing = [d for d in
    required_docs if d not in touched]`; `FAIL` listing `missing` if non-empty, else `PASS` listing
    all flagged paths as touched.
- Add `("docs_to_update_coverage", check_docs_to_update_coverage(ticket_id, tier))` as the 7th tuple
  entry in `run_static_precheck`. Update that function's docstring: "Aggregate all 6 Part A checks"
  → "Aggregate all 7 Part A checks".

**Do NOT touch:** Part B (`run_finalize_selfcheck` and its 4 checks) — out of scope, this ticket is
Part A only.

---

## Step 2 — `.claude/agents/investigator.md`: tighten section format

**File:** `.claude/agents/investigator.md`

- Replace the "## Docs Requiring Update" template-section description (added by the prior ticket)
  with an explicit format spec: "One bullet per path, in this exact form:
  `` - `docs/path/to/file.md`: one-line reason `` — the path MUST be backtick-wrapped and
  immediately follow `- ` so it can be machine-parsed by `done-checker`'s static coverage check. If
  none apply, write exactly: `None.` (no bullets)."

---

## Step 3 — `.claude/workflows/implement-ticket.js`: mirror the format in the Investigate prompt

**File:** `.claude/workflows/implement-ticket.js`, Investigate block

- Update the investigation.md sections list's "Docs Requiring Update" description (added by the
  prior ticket, currently free-prose) to match investigator.md's exact format spec from Step 2 —
  same wording, so the two files can't drift apart on what the required format is.
- No schema change needed — `docs_to_update` (the JSON return field) is unaffected; only the
  investigation.md prose section's format is being tightened.

---

## Step 4 — `.claude/workflows/implement-ticket.js`: Verify prompt cites condition 6

**File:** `.claude/workflows/implement-ticket.js`, Verify block (~line 1260)

- Change `"Before checking conditions 3, 4, 7, 10, 12 by hand, run the static pre-check script and
  cite its JSON output verbatim for those five conditions instead of re-deriving them:"` to include
  `6` in the list and drop the now-inaccurate "five" count (e.g. "these conditions").

---

## Step 5 — `docs/ai/ticket-lifecycle.md`: keep doc/code in parity

**File:** `docs/ai/ticket-lifecycle.md`

- Investigate section: note the tightened bullet format requirement.
- Verify section's Step 0b paragraph: "aggregates 6 checks" → "aggregates 7 checks", add
  `docs_to_update_coverage` to the named list, and update condition 6's table row to note it's now
  backed by this static check (independent of `behavior_changed`), not pure judgment.

---

## Acceptance Criteria Map

| AC | Step(s) |
|---|---|
| investigator.md format tightened | 2 |
| implement-ticket.js Investigate prompt mirrors format | 3 |
| `check_docs_to_update_coverage` NA/PASS/FAIL semantics | 1 |
| Independent of `behavior_changed` | 1 (reads only investigation.md + git, never implementation.*) |
| `run_static_precheck` aggregates 7 | 1 |
| Verify prompt cites condition 6 | 4 |
| ticket-lifecycle.md parity | 5 |
| Tests | (test_plan.md) |

## Dependency Map

Step 1 (Python) is independent and should land first. Steps 2/3 (format wording) must match each
other exactly but don't depend on Step 1's code. Step 4 is independent. Step 5 should land last,
once the actual shape is final.

## Open-Question Status

No unresolved questions remain — design decisions (advisory-vs-blocking split, investigation.md-
parsing over a durable sidecar) were both resolved with the user before this plan was written.
Deliberately not using a literal `## Unresolved Questions` heading — see
`TCK-20260802-DOC-UPDATE-DISCIPLINE/plan.md`'s identical note on why
(`plan_gate_static.py::plan_has_unresolved_questions_heading` triggers on heading presence alone).
