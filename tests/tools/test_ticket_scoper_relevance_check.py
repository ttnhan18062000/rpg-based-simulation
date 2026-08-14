"""Tests for TCK-20260720-TAG-RELEVANCE-VERIFY's relevance self-check mechanism (AC #1).

Both `ticket-scoper.md` (single-ticket path) and `create-tickets.js` (batch path, tested
separately in `test_create_tickets_tag_scope.py`) gain a `tag_relevance_flags` self-assessment
field, computed in the same agent turn that already assigns tags. This file covers:

- `test_ticket_scoper_relevance_self_check_instruction_present`: the new Output item is present
  in `ticket-scoper.md`.
- `test_relevance_flag_never_blocks_scope_phase`: `tag_relevance_flags` is never referenced inside
  a `pushEvent(...)` call anywhere in `create-tickets.js` — it must stay a `log(...)`-only,
  non-blocking signal (mirrors `mistag_warning`'s established precedent).
"""

import re
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_TICKET_SCOPER_MD = _REPO_ROOT / ".claude" / "agents" / "ticket-scoper.md"
_CREATE_TICKETS_JS = _REPO_ROOT / ".claude" / "workflows" / "create-tickets.js"


def test_ticket_scoper_relevance_self_check_instruction_present():
    source = _TICKET_SCOPER_MD.read_text(encoding="utf-8")
    assert "tag_relevance_flags" in source
    assert "self-assessment" in source
    # Empty-list-never-omit convention must be stated explicitly, mirroring `conflicts: []`.
    assert "empty list" in source or "empty array" in source


def test_relevance_flag_never_blocks_scope_phase():
    source = _CREATE_TICKETS_JS.read_text(encoding="utf-8")
    assert "tag_relevance_flags" in source

    push_event_lines = [line for line in source.splitlines() if "pushEvent(" in line]
    assert push_event_lines, "expected at least one pushEvent(...) call to check against"
    for line in push_event_lines:
        assert "tag_relevance_flags" not in line, (
            f"tag_relevance_flags must never be passed to pushEvent(...): {line!r}"
        )

    # Must be surfaced via log(...) instead.
    log_block = re.search(
        r"const tasksWithRelevanceFlags[\s\S]*?\n\}", source
    )
    assert log_block, "expected a tasksWithRelevanceFlags log-only wiring block"
    assert "log(" in log_block.group(0)
    assert "pushEvent(" not in log_block.group(0)
