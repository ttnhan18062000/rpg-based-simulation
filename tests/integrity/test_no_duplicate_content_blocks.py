"""Duplicate-content-block detection for every merge=union-covered file
(TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP).

merge=union only engages when git's own merge machinery runs (see
tests/integrity/test_merge_union_gitattributes.py::
test_squash_style_single_parent_commit_is_not_a_merge_and_bypasses_drivers). This repo's
PRs land almost exclusively via GitHub squash-merge, which never invokes a merge driver,
so a whole-block content duplication (like the confirmed ~1586-row tickets/working_log.csv
incident and the 79-line agent-monitoring/data/2026-W36/tools.jsonl incident) can land
silently. This test is the ongoing, automatic sweep mechanism: it scans every file matching
.gitattributes' own merge=union glob patterns for a *new* contiguous exact-duplicate line
block, and fails the moment one appears that isn't already accounted for in
KNOWN_DUPLICATE_BLOCKS.

This test detects, it does not prevent -- no .gitattributes-level mechanism can prevent a
squash-merge from reproducing content, since no merge driver runs for that operation. Its
value is turning "silent, undiscovered for days" into "loud, caught in the next CI run" (the
`arch-docs` job already runs this directory on every push to main and every pull_request).
"""
from __future__ import annotations

import hashlib
from collections import defaultdict
from pathlib import Path

MIN_BLOCK_LINES = 10

REPO_ROOT = Path(__file__).parent.parent.parent

# Keyed by (relative_file_path, block_length, sha256_of_block_content) -- never by absolute
# line number, since every covered file grows via legitimate ongoing appends. Each entry is
# one confirmed real incident, evidenced in
# staging_artifacts/TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP/investigation.md.
KNOWN_DUPLICATE_BLOCKS = {
    # tickets/working_log.csv's confirmed ~1586-row duplicate block (header row at physical
    # line 1 plus 1586 already-committed data rows, byte-identical to the embedded duplicate
    # header at line 1594 through line 3180, produced by PR #90's squash-merge / commit
    # 5993cac3) was remediated by this ticket's Step 6 one-time cleanup commit. This entry
    # is intentionally absent -- the block no longer exists in the live file.
    # agent-monitoring/data/2026-W36/tools.jsonl: physical lines 22831-22909 byte-identical
    # to lines 23240-23318 (79 lines), same squash-merge defect class as the working_log.csv
    # incident below. Deliberately NOT remediated by this ticket -- see this ticket's
    # Implementation Notes for the rationale (monitoring shards have a materially more
    # active writer profile than working_log.csv's occasional ticket-close appends, so a
    # cleanup edit there carries a higher, less-understood concurrent-write collision risk
    # than this ticket's evidence base justifies taking on). Tracked here, not ignored.
    (
        "agent-monitoring/data/2026-W36/tools.jsonl",
        79,
        "4c6792452731db52493cedf0314ced1ddeb943dd3d52481efd96ea5b4164c403",
    ),
}


def _merge_union_glob_patterns() -> list[str]:
    """Read .gitattributes directly rather than hardcoding the glob list separately, so
    this test tracks .gitattributes' own coverage instead of silently drifting from it.

    Takes the first whitespace-separated token as the path and looks for `merge=union`
    anywhere among the remaining tokens, rather than requiring the line to end in
    ` merge=union` -- a path can carry other attributes too (e.g. `text eol=lf`, added by
    TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION), and `merge=union` need not be
    the last one.
    """
    content = (REPO_ROOT / ".gitattributes").read_text(encoding="utf-8")
    patterns = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        tokens = line.split()
        if "merge=union" in tokens[1:]:
            patterns.append(tokens[0])
    return patterns


def _covered_files() -> list[Path]:
    files: list[Path] = []
    for pattern in _merge_union_glob_patterns():
        files.extend(sorted(p for p in REPO_ROOT.glob(pattern) if p.is_file()))
    return files


def _find_duplicate_blocks(lines: list[str], min_block_len: int = MIN_BLOCK_LINES):
    """Return every maximal contiguous duplicate block (start_i, start_j, length) with
    start_i < start_j and length >= min_block_len, as (0-indexed line, 0-indexed line,
    length) triples. A block is "maximal" in that it is not itself a sub-run of a longer
    block starting one line earlier -- this keeps one long incident from being reported as
    dozens of overlapping shorter ones.

    Cheap in practice for these files: real log/CSV rows carry a timestamp or sequence
    field, so distinct content is the overwhelming common case and duplicate-line groups
    are small and rare except for genuine whole-block-duplication incidents.
    """
    positions: dict[str, list[int]] = defaultdict(list)
    for idx, line in enumerate(lines):
        positions[line].append(idx)

    pair_set = set()
    for idxs in positions.values():
        if len(idxs) < 2:
            continue
        for a in range(len(idxs)):
            for b in range(a + 1, len(idxs)):
                pair_set.add((idxs[a], idxs[b]))

    blocks = []
    for (i, j) in sorted(pair_set):
        if (i - 1, j - 1) in pair_set:
            continue  # continuation of an earlier block, not a new one
        length = 0
        while True:
            ii, jj = i + length, j + length
            if ii >= len(lines) or jj >= len(lines) or lines[ii] != lines[jj]:
                break
            length += 1
        if length >= min_block_len:
            blocks.append((i, j, length))
    return blocks


def test_no_new_duplicate_content_block_beyond_documented_baseline():
    unexpected = []
    seen_allowlist_keys = set()

    for file_path in _covered_files():
        rel_path = file_path.relative_to(REPO_ROOT).as_posix()
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        for (i, j, length) in _find_duplicate_blocks(lines):
            block_content = "".join(lines[i : i + length])
            digest = hashlib.sha256(block_content.encode("utf-8")).hexdigest()
            key = (rel_path, length, digest)
            if key in KNOWN_DUPLICATE_BLOCKS:
                seen_allowlist_keys.add(key)
            else:
                unexpected.append(
                    {
                        "path": rel_path,
                        "first_occurrence_line": i + 1,
                        "second_occurrence_line": j + 1,
                        "length": length,
                        "sha256": digest,
                    }
                )

    assert not unexpected, (
        "New, undocumented duplicate content block(s) detected -- this is exactly the "
        "squash-merge-bypasses-merge=union defect class this test exists to catch: "
        f"{unexpected}. If this is a genuinely new confirmed incident, add its "
        "(path, length, sha256) key to KNOWN_DUPLICATE_BLOCKS with a comment citing the "
        "ticket that found it -- do not add it without first investigating whether it is a "
        "fresh, real duplication."
    )

    stale = KNOWN_DUPLICATE_BLOCKS - seen_allowlist_keys
    if stale:
        print(
            f"INFO: {len(stale)} allowlisted duplicate-block entrie(s) no longer detected "
            f"in the live repo (likely already remediated) -- safe to remove from "
            f"KNOWN_DUPLICATE_BLOCKS: {stale}"
        )
