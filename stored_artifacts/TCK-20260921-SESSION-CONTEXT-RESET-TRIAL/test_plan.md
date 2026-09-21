# Test Plan — TCK-20260921-SESSION-CONTEXT-RESET-TRIAL

| Case | Verification |
|---|---|
| Hook: no handover dir → empty output | `test_build_additional_context_empty_when_dir_missing` |
| Hook: dir exists, no `.md` files → empty output | `test_build_additional_context_empty_when_dir_has_no_md_files` |
| Hook: lists paths + first-line titles | `test_build_additional_context_lists_paths_and_first_line_titles` |
| Hook: blank file falls back to filename | `test_build_additional_context_falls_back_to_filename_for_blank_file` |
| Hook: non-`clear` source → no output | `test_hook_prints_nothing_for_non_clear_source` |
| Hook: `clear` source, no notes → no output | `test_hook_prints_nothing_when_no_handover_notes_exist` |
| Hook: `clear` source, notes present → real JSON `additionalContext` | `test_hook_prints_additional_context_json_on_clear_with_notes` |
| Hook: malformed stdin fails open | `test_hook_fails_open_on_malformed_stdin` |
| Boundary doc frontmatter valid | `validate_frontmatter.py docs/guides/agent_session_reset_boundaries.md` |
| Skill edits don't break phase-title conformance | `pytest tests/tools/test_workflow_meta_conformance.py` (25 passed, 1 xfailed, unchanged) |
| `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` verified from 2 independent authoritative sources (installed CLI binary strings; official docs excerpt), default value explicitly left unconfirmed and left out | `investigation.md` |
| Real baseline captured, cross-checked against the peer's own quoted figures | `investigation.md` — 40,250 requests vs. peer's 40,039 (a few hours' difference, consistent); 69 compactions (exact match); 482k avg ctx vs. 481k (consistent); 968k max vs. ~967k (consistent) |

## Full suite run
- `pytest tests/tools/test_session_start_handover_hook.py -v` — 8 passed.
- `pytest tests/tools/test_workflow_meta_conformance.py -q` — 25 passed, 1 xfailed (unchanged by
  the 5 skill-doc pointer additions).
