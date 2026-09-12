"""CR-byte guard for every merge=union-covered file (TCK-20260911-WORKING-LOG-LINE-ENDING-
UNION-DUPLICATION).

test_no_duplicate_content_blocks.py catches the *consequence* of mixed line endings on a
merge=union path: a whole-block duplicate after a merge resolves a line-ending-only change as a
both-sides edit. This test catches the *cause* directly -- a stray CRLF row -- before any merge
ever runs, so a broken writer is caught on the very commit that introduces it rather than on the
next merge someone happens to run. Root cause was
`tools/agent-monitoring/record_hand_orchestrated_closure.py`'s `csv.writer(...)` call having no
`lineterminator`, defaulting to Python's `\\r\\n`; `.gitattributes`' new `eol=lf` on these same
paths (added by this ticket) also normalizes any CR that slips in from a future writer, but this
test is the fast, direct signal that something regressed.

Reuses `_merge_union_glob_patterns()`/`_covered_files()` from test_no_duplicate_content_blocks.py
rather than reimplementing the file list, so the two detectors can never drift apart about which
files are actually covered by `.gitattributes`' `merge=union` lines.
"""
from __future__ import annotations

from tests.integrity.test_no_duplicate_content_blocks import REPO_ROOT, _covered_files


def test_no_cr_byte_in_any_merge_union_file():
    offenders = []
    for file_path in _covered_files():
        rel_path = file_path.relative_to(REPO_ROOT).as_posix()
        content = file_path.read_bytes()
        cr_count = content.count(b"\r")
        if cr_count:
            offenders.append(f"{rel_path}: {cr_count} CR byte(s)")

    assert not offenders, (
        "CR byte(s) found in merge=union-covered file(s) -- this is the root cause that turns "
        "into a duplicate content block the next time a real git merge runs over these lines "
        "(see test_no_duplicate_content_blocks.py). Every writer of these files must emit LF "
        "only: " + "; ".join(offenders)
    )
