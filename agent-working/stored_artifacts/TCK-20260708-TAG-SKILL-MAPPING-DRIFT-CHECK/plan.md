---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK
artifact_type: plan
tags: [ai, workflows, tagging, ticket-scoper]
---

# Implementation Plan — TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK

## Summary

Build a proactive drift-detection check for the 4 hand-duplicated tag->skill mapping tables
(`.claude/agents/ticket-scoper.md`, `docs/guides/ticket_tagging.md`,
`.claude/workflows/implement-ticket.js`, `.claude/workflows/create-tickets.js`). The approach follows
`tools/tag_registry.py::check_tags_registered()`'s precedent exactly: a new `tools/` helper module
(`tools/tag_skill_mapping_check.py`) holds three format-specific parsers (Format A: raw markdown pipe
table; Format B: JS-escaped markdown pipe table; Format C: arrow-list with multi-line continuation), a
shared `normalize_target()` that reduces each raw target to a comparable
`(primary_skill, carveout_agent, carveout_paths)` tuple (ignoring legitimate prose differences), and a
root-parameterized `check_tag_skill_mapping_consistency(root=None)` that reads all 4 live files, compares
them pairwise per tag, and returns a structured mismatch list. `tests/tools/test_tag_skill_mapping_check.py`
imports this module via the same `sys.path.insert(0, "tools")` shim `test_tag_registry.py` and
`test_tag_report.py` already use. The module is built incrementally, one parser/function per step, each
step adding its own unit test(s) so every step is independently verifiable. The plan closes with a doc
update (`docs/guidelines/tag_taxonomy.md` Scenario 5 row) and a live verification run. No mapping content
in any of the 4 source files is touched; no dedup, hook, or CI wiring is attempted — matching the ticket's
Out of Scope exactly.

## Steps

### Step 1 — Module skeleton + known-tag allowlist + Format A parser (raw markdown pipe table)
**Files:** `tools/tag_skill_mapping_check.py` (new), `tests/tools/test_tag_skill_mapping_check.py` (new)
**Change:**
- Create `tools/tag_skill_mapping_check.py` with:
  - Module docstring stating its purpose (drift check for the 4 tag->skill mapping copies) AND
    explicitly disclosing the accepted limitation: the module's own `KNOWN_TAGS` allowlist
    (`{"api-design", "debugging", "performance", "security"}`) is itself a de-facto 5th copy of the
    tag set — if a 5th `Process/Skill-signal` tag is ever added to the real 4 copies, this allowlist
    must be updated too, or the check will silently ignore the new tag rather than compare it. This is
    the Decision recorded in this plan (see "Decision: Allowlist as a Disclosed 5th Copy" below) —
    document it verbatim in the docstring, do not attempt to derive the allowlist from one of the 4
    files (that would make that one file an implicit source of truth, contradicting the ticket's Out of
    Scope).
  - `KNOWN_TAGS = frozenset({"api-design", "debugging", "performance", "security"})` module-level
    constant.
  - `extract_pairs_markdown(text: str) -> dict[str, str]`: scan lines for `^\|\s*` prefix, split on
    `|`, strip leading/trailing empty strings and whitespace per cell, match `cell[0]` against
    `^\`([a-z][a-z-]*)\`$`, accept only rows whose captured tag is in `KNOWN_TAGS` (this naturally
    skips the header/separator rows without special-casing them). Return `{tag: raw_target}` where
    `raw_target` is `cell[1]` (raw text, backticks/prose included, untouched — normalization happens
    later in Step 4).
- Create `tests/tools/test_tag_skill_mapping_check.py` with the same `sys.path.insert(0, "tools")`
  shim pattern as `tests/tools/test_tag_registry.py:9-24`, and add
  `test_extract_pairs_markdown_parses_all_four_tags`: feed a synthetic markdown pipe-table string
  (header row + separator row + the 4 data rows, mirroring `ticket-scoper.md`'s exact format) and
  assert exactly 4 `{tag: raw_target}` pairs are returned with header/separator correctly skipped.
**Do NOT touch:** `tools/tag_registry.py`, `tools/tag_report.py`, any of the 4 real source files, `docs/guidelines/tag_registry.jsonl`.
**Verify:** `test_extract_pairs_markdown_parses_all_four_tags` (test_plan.md item 1).

### Step 2 — Format B parser (JS-escaped markdown pipe table)
**Files:** `tools/tag_skill_mapping_check.py`, `tests/tools/test_tag_skill_mapping_check.py`
**Change:** Add `extract_pairs_js_escaped(text: str) -> dict[str, str]` to the module: same pipe-split
approach as `extract_pairs_markdown`, but `cell[0]`'s tag-match regex tolerates an optional literal
backslash immediately before/after the backtick — `^\\?\`([a-z][a-z-]*)\\?\`$` — because
`implement-ticket.js`'s raw bytes contain `\`` (backslash + backtick, since the file is read as plain
text, not evaluated as JS). Same `KNOWN_TAGS` filter as Format A. Add
`test_extract_pairs_js_escaped_parses_all_four_tags`: feed a synthetic string with backslash-escaped
backticks (mirroring `implement-ticket.js`'s literal format) and assert the same 4 pairs are returned,
tags correctly stripped of both backslash and backtick.
**Do NOT touch:** `extract_pairs_markdown` from Step 1 (no shared-regex refactor across the two — keep
them as two independent functions per the investigation's 3-distinct-parsers design; do not
over-abstract into one parameterized parser, since Format C is structurally different enough that a
shared abstraction would add complexity without reducing it).
**Verify:** `test_extract_pairs_js_escaped_parses_all_four_tags` (test_plan.md item 2).

### Step 3 — Format C parser (arrow-list with multi-line continuation + anchor bounding)
**Files:** `tools/tag_skill_mapping_check.py`, `tests/tools/test_tag_skill_mapping_check.py`
**Change:** Add `extract_pairs_arrow_list(text: str) -> dict[str, str]` to the module:
- Locate the scan window by anchor substrings, not line numbers: start scanning after the line
  containing `"Map each assigned tag against this table"`, stop at the line containing `"Do not invent
  mappings for tags outside this 4-entry table"` (both stable, already present in
  `create-tickets.js`). If either anchor is not found in the given text, raise a clear, explicit error
  (e.g. `ValueError("could not locate arrow-list mapping block: missing anchor ...")`) — do not
  silently return an empty or partial pair set (this is Investigation Risk #1 / Anti-Drift Hazard,
  and Test Plan's Anti-Drift Test Guard for Test 9).
- Within the window, run a line-based state machine: try `^\s*([a-z][a-z-]*)\s*->\s*(.+)$` on each
  line. If it matches and the captured tag is in `KNOWN_TAGS`, open a new `(tag, target)` entry seeded
  with `match.group(2).strip()`. If a line does not match, append `line.strip()` (space-joined) to the
  currently open entry's target — this is what correctly captures `debugging`'s 3 continuation lines
  in `create-tickets.js` into one target string.
- Add two tests:
  - `test_extract_pairs_arrow_list_parses_all_four_tags_including_multiline_debugging`: synthetic
    arrow-list string mirroring `create-tickets.js`'s exact format including the 4-line `debugging`
    continuation block; assert 4 pairs returned and `debugging`'s raw target contains all 3
    continuation lines joined.
  - `test_extract_pairs_arrow_list_raises_on_missing_anchor`: synthetic string missing one of the two
    anchor substrings; assert the parser raises rather than returning an empty/partial result.
**Do NOT touch:** the anchor substrings themselves are read from the real `create-tickets.js` content
only at call time in Step 5 — do not hardcode a copy of `create-tickets.js`'s actual table text inside
this module; the parser must work generically against any text containing the two anchors.
**Verify:** `test_extract_pairs_arrow_list_parses_all_four_tags_including_multiline_debugging` and
`test_extract_pairs_arrow_list_raises_on_missing_anchor` (test_plan.md items 3 and 9).

### Step 4 — Normalization function
**Files:** `tools/tag_skill_mapping_check.py`, `tests/tools/test_tag_skill_mapping_check.py`
**Change:** Add `normalize_target(raw_target: str) -> tuple[str, str | None, tuple[str, ...]]` to the
module:
- `primary_skill = re.search(r'(/[a-z][a-z-]*)', raw_target).group(1)`.
- `carveout_agent = "world-debugger" if "world-debugger" in raw_target else None`.
- `carveout_paths = tuple(sorted(set(re.findall(r'src/[\w./]+', raw_target))))`.
- Return `(primary_skill, carveout_agent, carveout_paths)`.
- Add two tests:
  - `test_normalize_target_captures_skill_and_carveout_paths`: feed two differently-worded raw
    `debugging` target strings encoding the same skill + carve-out paths, assert both normalize to the
    identical tuple (`/debugging-strategies`, `world-debugger`, the 5 sorted `src/...` paths).
  - `test_normalize_target_ignores_prose_only_differences`: feed the actual `security` row text as it
    appears in `ticket-scoper.md` (with its "first codification..." parenthetical) and as it appears
    in `create-tickets.js` (no commentary); assert the two normalized outputs are equal. This is the
    test that directly proves AC4 (tolerates legitimate wording differences) at the normalization
    level.
**Do NOT touch:** do not attempt byte-identical or raw-text comparison anywhere in this module — the
ticket's own AC2 ("passes against current state") is only satisfiable under normalized comparison,
since Copies 1/2 carry extra prose Copies 3/4 omit.
**Verify:** `test_normalize_target_captures_skill_and_carveout_paths` and
`test_normalize_target_ignores_prose_only_differences` (test_plan.md items 4 and 5).

### Step 5 — Top-level `check_tag_skill_mapping_consistency(root=None)` + mismatch reporting
**Files:** `tools/tag_skill_mapping_check.py`, `tests/tools/test_tag_skill_mapping_check.py`
**Change:** Add to the module:
- A `root`-parameterized function (mirroring `tag_registry.py`'s `registry_path(root)` testability
  convention) that resolves the 4 real file paths relative to `root` (default: repo root when `root`
  is `None`):
  - `.claude/agents/ticket-scoper.md` -> `extract_pairs_markdown`
  - `docs/guides/ticket_tagging.md` -> `extract_pairs_markdown`
  - `.claude/workflows/implement-ticket.js` -> `extract_pairs_js_escaped`
  - `.claude/workflows/create-tickets.js` -> `extract_pairs_arrow_list`
- For each file, read its text, run the appropriate parser, then run `normalize_target()` on each
  extracted raw target, building `{file_path: {tag: normalized_tuple}}`.
- For each tag in `KNOWN_TAGS`, compare all 4 sources' normalized tuples pairwise. Return a structured
  result (e.g. a list of mismatch records, each naming the tag, the disagreeing file paths, and their
  differing normalized tuples) — empty list means fully consistent. This structure is what a caller
  (a pytest assertion, or a future consumer) turns into a diff-style message identifying which
  file(s) disagree and on which tag.
- Add three tests:
  - `test_check_tag_skill_mapping_consistency_passes_against_live_repo_files`: call with no `root`
    override (reads the real repo files); assert the returned mismatch list is empty. This is the
    literal AC1/AC2 enforcement mechanism — it must run against unmodified real files.
  - `test_check_tag_skill_mapping_consistency_detects_injected_divergence`: using `tmp_path`, write 4
    synthetic files reproducing the 3 formats, with one file's `security` target deliberately changed
    to a genuinely different skill path (not a whitespace/formatting change — this guards against
    accidentally building a byte-identical check per the Test Plan's Anti-Drift Test Guard). Call with
    `root=tmp_path`; assert the mismatch list is non-empty, names `security`, and names the mutated
    file among the disagreeing sources.
  - `test_check_tag_skill_mapping_consistency_reports_which_files_disagree`: using the same fixture as
    the previous test, assert the mismatch record structure carries file identity (not just "mismatch
    found") — sufficient to build a diff-style assertion message.
**Do NOT touch:** do not write results to disk, do not add any git-hook or CI invocation of this
function — it is called only from pytest in this ticket's scope.
**Verify:** `test_check_tag_skill_mapping_consistency_passes_against_live_repo_files`,
`test_check_tag_skill_mapping_consistency_detects_injected_divergence`,
`test_check_tag_skill_mapping_consistency_reports_which_files_disagree` (test_plan.md items 6, 7, 8).

### Step 6 — Update `docs/guidelines/tag_taxonomy.md` Scenario 5 row
**Files:** `docs/guidelines/tag_taxonomy.md`
**Change:** Locate the Purpose section's Scenario 5 row ("Automatable skill-catalog health check"),
currently naming only the future scenario with no implementation pointer. Edit it to reference the new
check's location: `tools/tag_skill_mapping_check.py` (the extraction/comparison logic) and
`tests/tools/test_tag_skill_mapping_check.py` (the pytest entry point that runs it,
`python3 -m pytest tests/tools/test_tag_skill_mapping_check.py -q`). Keep the edit narrowly scoped to
this one row — do not rewrite surrounding rows or the Purpose section's framing.
**Do NOT touch:** any other row or section of `tag_taxonomy.md`; do not edit `docs/guides/ticket_tagging.md`'s mapping table content itself (it is read-only input to the check, per ticket Out of Scope).
**Verify:** Manual review — row now names both file paths (no dedicated automated test for doc prose; satisfies AC5 directly by inspection).

### Step 7 — Live verification run
**Files:** none (verification only)
**Change:** Run `python3 -m pytest tests/tools/ -q` and confirm it passes clean, including the new
`test_tag_skill_mapping_check.py` tests alongside the pre-existing `test_tag_registry.py` and
`test_tag_report.py`. This is the run that concretely confirms AC2 ("passes against current state,
run and confirmed, not assumed") and AC6 (full `tests/tools/` scoped command runs clean). Record the
command and outcome in the ticket's Test Summary section during implementation.
**Do NOT touch:** do not run the full `pytest tests/` suite — scope stays at `tests/tools/` per
Testing Rule and the ticket's own AC6 wording.
**Verify:** `python3 -m pytest tests/tools/ -q` exits 0 (test_plan.md "Scoped Pytest Commands").

## Scope Guards

- Do NOT modify the actual mapping table content in any of the 4 files
  (`.claude/agents/ticket-scoper.md`, `docs/guides/ticket_tagging.md`,
  `.claude/workflows/implement-ticket.js`, `.claude/workflows/create-tickets.js`) — this ticket only
  adds detection, per its own Out of Scope. If Step 7's live run somehow reveals a real divergence,
  do not fix it in this ticket; flag it and stop (see Anti-Drift Notes).
- Do NOT attempt to de-duplicate the 4 copies into one true single source of truth (no shared
  imported constant, no generated-from-YAML template, no build step). The `tools/` helper is a
  reader/comparator of the 4 independent texts, not a source-of-truth generator for them.
- Do NOT wire the new check into any git pre-commit hook, CI config, or `.claude/settings.json` —
  pytest-level only, per ticket Out of Scope.
- Do NOT touch `tools/tag_registry.py` or `docs/guidelines/tag_registry.jsonl` — no coupling to the
  tag-registration system; this is a separate concern (tag->skill routing, not tag registration).
- Do NOT expand the tag->skill mapping itself (no 5th tag, no changed target for any existing tag).
- Do NOT edit `stored_artifacts/TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION/investigation.md`'s
  pre-existing "3 places" undercount — that artifact is historical/immutable.
- Do NOT expand the `debugging` carve-out path set or touch the pre-existing `worldgeneration/`
  CLAUDE.md-vs-world-debugger.md mismatch — separately flagged, deliberately deferred, not in scope.

## Dependency Map

- Steps 1-5 are sequential (each adds one function to the same module and one test to the same test
  file; Step 5 depends on Steps 1-4's functions existing). Do not reorder — Format A/B/C parsers must
  exist before the top-level consistency function that calls them, and `normalize_target` (Step 4)
  must exist before Step 5's comparison logic uses it.
- Step 6 (docs update) only depends on Step 1 (module must exist to reference its path) — it can run
  any time after Step 1, but is sequenced last-but-one for narrative order.
- Step 7 (live verification) depends on all of Steps 1-6 being complete — it is the final confirmation
  step and must run last.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — check exists, extracts from all 4 files, asserts pairwise equal on normalized `{tag: target}` pairs | Steps 1, 2, 3, 4, 5 | `test_check_tag_skill_mapping_consistency_passes_against_live_repo_files` |
| AC2 — check passes against current state of all 4 files (run and confirmed) | Step 5 (live-file test), Step 7 (live run) | `test_check_tag_skill_mapping_consistency_passes_against_live_repo_files`; `python3 -m pytest tests/tools/ -q` |
| AC3 — failure mode demonstrated (mutation causes loud, identifying failure) | Step 5 | `test_check_tag_skill_mapping_consistency_detects_injected_divergence`, `test_check_tag_skill_mapping_consistency_reports_which_files_disagree` |
| AC4 — tolerates legitimate wording differences, no false-positive on prose | Step 4 | `test_normalize_target_ignores_prose_only_differences` |
| AC5 — `docs/guidelines/tag_taxonomy.md` Scenario 5 row references new check's location | Step 6 | Manual review (no dedicated test) |
| AC6 — `python3 -m pytest tests/tools/ -q` runs clean including new test alongside existing suite | Steps 1-6 | Step 7 live run |

## Anti-Drift Notes

- **Format C's anchor-bounded scan (Step 3) must raise on a missing anchor, not silently return an
  empty/partial result.** If `create-tickets.js`'s prompt text is ever reworded near the anchor
  substrings without the table itself changing, a silent empty-result parser could cause the
  consistency check to skip `create-tickets.js` entirely from comparison and false-pass. This is
  Investigation Risk #1 and is directly covered by `test_extract_pairs_arrow_list_raises_on_missing_anchor`.
- **Normalization, not byte-identical comparison, is the only semantics under which AC2 is satisfiable.**
  `ticket-scoper.md` and `ticket_tagging.md` carry legitimately longer prose (the `world-debugger`
  carve-out's `worldgeneration/` parenthetical, and differently-worded `security` "first codification"
  commentary) that `implement-ticket.js`/`create-tickets.js` omit. Do not let Step 4's
  `normalize_target` regress toward raw-text comparison at any point — Test 5
  (`test_normalize_target_ignores_prose_only_differences`) exists specifically to catch that regression.
- **Decision: Allowlist as a Disclosed 5th Copy.** The module's `KNOWN_TAGS` allowlist
  (`api-design`, `debugging`, `performance`, `security`) is itself a de-facto 5th copy of the tag set.
  This plan adopts the investigation's recommendation: disclose this explicitly in
  `tools/tag_skill_mapping_check.py`'s module docstring (Step 1) as an accepted, stated limitation — a
  future 5th-tag addition to the real 4 copies would silently bypass this check until the allowlist is
  also updated. This is a deliberate decision, not deferred: deriving the allowlist from one of the 4
  existing files was considered and rejected, because it would make that one file an implicit source
  of truth, contradicting the ticket's own Out of Scope ("not attempting true single-source-of-truth
  dedup"). No code-level mitigation is planned; the docstring disclosure is the complete mitigation for
  this ticket's scope.
- **Do not conflate this ticket's helper module with `tools/tag_registry.py`.** They solve adjacent but
  distinct problems (tag->skill routing consistency vs. tag registration/allowlisting) and must remain
  separate modules with no import coupling between them.
- **If Step 7's live run unexpectedly finds a real divergence** (contradicting the investigation's
  re-verified finding that all 4 copies are currently semantically identical), stop and flag it —
  fixing a real pre-existing divergence is explicitly Out of Scope for this ticket per its own text
  ("if the check reveals a real, pre-existing divergence, fixing that divergence is a separate
  follow-up ticket, not folded into this one").

## Unresolved Questions

None. The investigation resolved both of the ticket's own deferred Assumptions/Open Questions
(mechanism: pytest + `tools/` helper, matching `check_tags_registered()` precedent; comparison
semantics: normalized tuple comparison, the only semantics under which AC2 is satisfiable) with
concrete, adoptable designs. No new unresolved question surfaced during planning.

## Deviations

One deviation, discovered during Step 7's live verification run (not anticipated by this plan or
the investigation):

- **Step 4's `carveout_paths` regex needed a scoping fix.** The plan's literal spec
  (`re.findall(r'src/[\w./]+', raw_target)` over the *entire* raw target) produced a false mismatch
  on the very first live run: `ticket-scoper.md`'s `debugging` row has a trailing parenthetical that
  explicitly states `src/worldgeneration/` is *excluded* from the carve-out (already known and
  separately flagged — see this ticket's own Out of Scope: "Do NOT expand the debugging carve-out
  path set or touch the pre-existing `worldgeneration/` ... mismatch"). The naive regex read that
  excluded mention as a 6th included path, causing `ticket-scoper.md` to disagree with the other 3
  copies on `debugging` — a false positive on prose, directly violating AC4 ("does not false-positive
  on prose-only differences") and blocking AC2 ("passes against current state").
  - **Fix:** added `_CARVEOUT_LIST_RE` (`r"path under\s+((?:\\?`?src/[\w./]+\\?`?[,\s]*(?:or\s+)?)+)"`,
    case-insensitive) to `tools/tag_skill_mapping_check.py`, anchoring path extraction to the actual
    "path under X, Y, or Z" condition clause common to all 4 copies' debugging row, rather than
    scanning the row's full free-form prose. `normalize_target` now searches for this anchored list
    first and only runs `_SRC_PATH_RE.findall()` within the captured segment.
  - **Test added (not in the original plan):**
    `test_normalize_target_ignores_excluded_path_mentioned_outside_carveout_list` in
    `tests/tools/test_tag_skill_mapping_check.py` — asserts a target string with a trailing
    "intentionally excluded" mention normalizes identically to the same target without that mention,
    and that the excluded path does not appear in `carveout_paths`.
  - **Scope impact:** none. This is a fix to the check's own extraction logic, verified against the
    real `ticket-scoper.md` text; no content in any of the 4 real mapping-table source files was
    touched, and no plan step's Do-NOT-touch guard was violated.
- **Step 6's row edit kept the table's original 2-column shape.** The plan described referencing the
  new check's file paths "in" the Scenario 5 row without specifying column structure; appending a 3rd
  cell would have misaligned the table (the header only defines 2 columns). The reference was appended
  as additional text inside the existing "Category it reads" cell instead. No other row or the table's
  column structure was touched, consistent with the plan's "narrowly scoped to this one row" guard.

All other steps (1, 2, 3, 5, 7) were implemented exactly as specified, with no other deviations.
