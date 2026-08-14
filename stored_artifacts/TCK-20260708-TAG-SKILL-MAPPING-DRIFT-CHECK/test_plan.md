---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK
artifact_type: test_plan
tags: [ai, workflows, tagging, ticket-scoper]
---

# Test Plan — TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK

## Regression Surface

This ticket adds a new test file and a new `tools/` helper module; it does not modify `tools/tag_registry.py`, `tools/tag_report.py`, or any of the 4 source files under test (unless a real divergence is discovered, which is out of scope to fix here per the ticket's Out of Scope). Regression surface is therefore narrow — confirm the existing `tests/tools/` suite is unaffected by the new module's presence.

**Unit (must keep passing):**
- `tests/tools/test_tag_registry.py` — all tests (`test_canonical_form_violation_*`, `test_is_phase_milestone_tag`, `test_is_tag_registered_*`, `test_load_registry_*`, `test_add_tag_*`, `test_check_tags_registered_*`). The new module imports nothing from `tag_registry.py` and vice versa — no coupling expected, but this is the direct sibling/precedent file and must still pass unmodified.
- `tests/tools/test_tag_report.py` — all tests (`test_categorize_tag_*`, `test_collect_*`, `test_build_tag_rows_*`). Same rationale — no coupling, but same directory, must remain green.

**Integration / architecture-guard:** none applicable — this ticket has no `src/` surface, no authoritative-state path, no durable-record schema. There is no arena-combat or simulation regression surface touched by this ticket at all.

## New Tests Required

All new tests live in `tests/tools/test_tag_skill_mapping_check.py`, importing from a new `tools/tag_skill_mapping_check.py` module (mirrors the `tests/tools/test_tag_registry.py` → `tools/tag_registry.py` import-shim pattern at `tests/tools/test_tag_registry.py:9-24`).

1. **`test_extract_pairs_markdown_parses_all_four_tags`**
   - Category: unit
   - Verifies: `extract_pairs_markdown()` given a synthetic markdown pipe-table string (mirroring `ticket-scoper.md`/`ticket_tagging.md`'s exact format, including a header row and separator row) returns exactly 4 `{tag: raw_target}` pairs, correctly skipping the header/separator rows.
   - Location: `tests/tools/test_tag_skill_mapping_check.py`

2. **`test_extract_pairs_js_escaped_parses_all_four_tags`**
   - Category: unit
   - Verifies: `extract_pairs_js_escaped()` given a synthetic string with backslash-escaped backticks (mirroring `implement-ticket.js`'s literal `\`` bytes) returns the same 4 pairs, tags correctly stripped of both backslash and backtick.
   - Location: `tests/tools/test_tag_skill_mapping_check.py`

3. **`test_extract_pairs_arrow_list_parses_all_four_tags_including_multiline_debugging`**
   - Category: unit
   - Verifies: `extract_pairs_arrow_list()` given a synthetic arrow-list string (mirroring `create-tickets.js`'s exact format, including the 4-line `debugging` continuation block) returns 4 pairs, and specifically that `debugging`'s raw target contains all 3 continuation lines joined (i.e. the multi-line block-continuation logic actually works, not just the single-line cases).
   - Location: `tests/tools/test_tag_skill_mapping_check.py`

4. **`test_normalize_target_captures_skill_and_carveout_paths`**
   - Category: unit
   - Verifies: `normalize_target()` on a `debugging`-style raw target string returns a tuple containing the primary skill (`/debugging-strategies`), the carve-out agent (`world-debugger`), and the full sorted path set (`src/content/`, `src/core/registries.py`, `src/worldassembly/`, `src/worldbuilding/`, `src/worldmodules/`) — regardless of surrounding prose/punctuation differences (test with two differently-worded raw strings encoding the same paths and assert equal normalized output).
   - Location: `tests/tools/test_tag_skill_mapping_check.py`

5. **`test_normalize_target_ignores_prose_only_differences`**
   - Category: unit
   - Verifies directly the Acceptance Criterion "tolerates the documented legitimate wording differences" — feed `normalize_target()` the actual `security` row text from `ticket-scoper.md` (with its parenthetical commentary) and from `create-tickets.js` (no commentary) and assert the two normalized outputs are equal.
   - Location: `tests/tools/test_tag_skill_mapping_check.py`

6. **`test_check_tag_skill_mapping_consistency_passes_against_live_repo_files`**
   - Category: integration (reads the real files, no `root` override)
   - Verifies: Acceptance Criteria #1 and #2 directly — `check_tag_skill_mapping_consistency()` called with no `root` override reads the actual `.claude/agents/ticket-scoper.md`, `docs/guides/ticket_tagging.md`, `.claude/workflows/implement-ticket.js`, `.claude/workflows/create-tickets.js` from the real repo and asserts the returned mismatch list is empty.
   - Location: `tests/tools/test_tag_skill_mapping_check.py`

7. **`test_check_tag_skill_mapping_consistency_detects_injected_divergence`**
   - Category: unit (uses `tmp_path` fixture files, not the real repo — mirrors `tests/tools/test_tag_registry.py`'s `tmp_path`+`root=` pattern used throughout, e.g. `test_load_registry_reads_entries`)
   - Verifies: Acceptance Criterion #3 (failure mode demonstrated) — write 4 synthetic files under `tmp_path` reproducing the 3 formats, with one file's `security` target deliberately changed to a different skill path; call `check_tag_skill_mapping_consistency(root=tmp_path)` and assert the mismatch list is non-empty, names `security` as the diverging tag, and names the mutated file among the disagreeing sources.
   - Location: `tests/tools/test_tag_skill_mapping_check.py`

8. **`test_check_tag_skill_mapping_consistency_reports_which_files_disagree`**
   - Category: unit
   - Verifies: the mismatch entry returned by `check_tag_skill_mapping_consistency()` in the failure case (test 7's fixture) is structured/informative enough to build a diff-style assertion message — i.e. it identifies file identity, not just "mismatch found" (satisfies the ticket's "diff-style message identifying which file(s) disagree and on which tag" requirement at the data-return level; the pytest assertion message itself is asserted in test 7 or a dedicated message-format test if the implementer separates the two concerns).
   - Location: `tests/tools/test_tag_skill_mapping_check.py`

9. **`test_extract_pairs_arrow_list_raises_on_missing_anchor`**
   - Category: unit (edge case / defensive)
   - Verifies: Investigation Risk #1 — if the arrow-list parser's start/end anchor substrings are not found in the given text, it raises a clear error rather than silently returning an empty or partial pair set.
   - Location: `tests/tools/test_tag_skill_mapping_check.py`

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/ -q
```

Scoped to the `tests/tools/` domain — this is the directory the ticket's own Acceptance Criteria names explicitly ("`python3 -m pytest tests/tools/ -q` ... runs clean, including the new test alongside existing `test_tag_registry.py` and `test_tag_report.py`"). A narrower `python3 -m pytest tests/tools/test_tag_skill_mapping_check.py -q` may be run first during development, but the full `tests/tools/` scoped command is the one that must be run and confirmed before closing this ticket, per Acceptance Criteria.

## Anti-Drift Test Guards

- **Test 6 (live-file integration test) is the actual guard against future drift** — every other test exercises synthetic fixtures and would keep passing even if the real repo's 4 files silently diverged. Test 6 must run against the unmodified real files (no `root=` override) so it is this ticket's literal enforcement mechanism, not just a demonstration.
- **Test 7 must use a genuinely different `security` (or `debugging`) target, not a whitespace/formatting change**, to prove the check compares semantics, not raw text — this guards against an implementer accidentally building a byte-identical/text-diff check that would false-positive on the legitimate prose differences Copy 1/Copy 2 carry, silently breaking Acceptance Criterion #2 the moment it's run for real (test 6 would then fail against the live files, which is the intended tripwire if this guard is skipped).
- **Test 3 (multi-line `debugging` continuation) guards specifically against a naive line-by-line arrow-list parser** that only captures the first line of `create-tickets.js`'s `debugging` entry and silently drops the 3 continuation lines carrying the actual carve-out path set — exactly the failure mode the ticket's Request Summary warns "a naive single-string target per tag would silently ignore the carve-out condition text."
- **Test 9 guards against a silent false-pass** if `create-tickets.js`'s prompt text is ever reworded near the anchor substrings without the table itself changing — without this guard, a broken block-boundary scan could return an empty pair set for `create-tickets.js`, which (depending on implementation) might either raise an unrelated error or, worse, be treated as "no data to compare" and silently skip that source from the consistency assertion entirely.
- No test in this plan touches `docs/parity_ledger/` — confirmed N/A in investigation.md, so no parity-ledger regression guard is needed here.
