"""Schema-validating write path for docs/parity_ledger/*.yaml.

Built for TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL: before this module, nothing enforced
docs/parity_ledger/schema.json's rules when a ledger shard was actually written --
.claude/agents/parity-updater.md's "What to Do" section edited YAML via raw Read/Edit with no
validation step. `validate_entry` hand-rolls the same rules schema.json's `items.allOf` block and
`properties` enums express (rather than loading and interpreting the JSON file at runtime with a
`jsonschema` call), plus one write-time-only rule schema.json cannot express (test_path must parse
via the shared citation parser -- see below). Each check below cites the exact schema.json branch
it mirrors; any future edit to that file's rules must be mirrored here by hand -- nothing enforces
the two representations stay in sync automatically (TestStep3aLockstepWithSchemaJson in
tests/tools/test_parity_ledger_writer.py runs both against the same fixtures to catch drift).

This module lives beside, not inside, tools/parity_index.py: that module's own docstring states
twice it "never writes into docs/parity_ledger/ and implements no mutation CLI," and
tests/tools/test_parity_index.py::TestArchitectureGuards::
test_no_mutation_cli_or_write_path_to_docs_parity_ledger statically asserts no write call in its
source targets docs/parity_ledger -- adding a mutation path there would break that test and
contradict the module's own stated contract.

write_entry() is the only code path in this module that reaches docs/parity_ledger/*.yaml write
bytes, and always calls validate_entry() first, before any file I/O. On a successful write it
rebuilds tools/parity_index.py's derived SQLite index in-process (imported build(), a plain
function, no class state -- reuse precedent set by TCK-20260808-PARITY-INDEX-STALENESS-VISIBILITY)
so the index can never go stale relative to a validated write. This proves the writer's own
function-level behavior (testable via check_staleness() reporting FRESH immediately after a
successful write) but does NOT by itself move the `parity_write_safety` retro metric --
tools/agent-monitoring/generate_retro.py's `_is_parity_index_build_call` only matches a separate
Bash tool call whose command text literally contains "parity_index.py" and "build"; an in-process
Python call inside a script invoked via one Bash call is invisible to it. See
.claude/agents/parity-updater.md, which has the agent issue a second, visible
`python3 tools/parity_index.py build` Bash call for exactly this reason.
"""

import re
import sys
from pathlib import Path

import yaml

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from parity_index import DEFAULT_LEDGER_DIR, DEFAULT_DB_PATH, build  # noqa: E402
from parity_test_path import parse_test_path_citations  # noqa: E402

# mirrors docs/parity_ledger/schema.json:9-11 (properties.id.pattern) -- byte-identical, must
# never drift (TCK-20260831-PARITY-LEDGER-ID-PATTERN-MULTISEGMENT: the two fell out of sync once
# already, silently rejecting live multi-segment shard ids like WORLD-DEMO-001)
_ID_PATTERN = re.compile(r"^[A-Z]+(-[A-Z]+)*-[0-9]{3}$")

# mirrors docs/parity_ledger/schema.json's properties.evidence_kind.enum
_EVIDENCE_KIND_VALUES = {"existence", "invocation", "runtime_observation"}

# Statuses for which Step 3a's narrowed P0 rule substitutes support_boundary for test_path --
# a P0 entry saying the behavior is unverified cannot have a passing test citation, so requiring
# one only invites a fake or stale citation (TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT).
_P0_TEST_PATH_EXEMPT_STATUSES = ("missing", "unsupported")


class EntryValidationError(Exception):
    def __init__(self, field: str, reason: str):
        self.field = field
        self.reason = reason
        super().__init__(f"invalid parity ledger entry field {field!r}: {reason}")


def _require_non_empty_string(entry: dict, field: str) -> None:
    value = entry.get(field)
    if not isinstance(value, str) or not value:
        raise EntryValidationError(field, "must be a non-null, non-empty string")


def validate_entry(entry: dict) -> None:
    """Raise EntryValidationError on the first violated rule; otherwise return None."""
    # mirrors docs/parity_ledger/schema.json:9-11 (properties.id.pattern)
    entry_id = entry.get("id")
    if not isinstance(entry_id, str) or not _ID_PATTERN.match(entry_id):
        raise EntryValidationError("id", f"must match pattern {_ID_PATTERN.pattern!r}")

    # mirrors docs/parity_ledger/schema.json's items.allOf[0]: status in
    # {verified, divergent} -> v2_evidence + test_path required, non-null
    if entry.get("status") in ("verified", "divergent"):
        _require_non_empty_string(entry, "v2_evidence")
        _require_non_empty_string(entry, "test_path")

    # mirrors docs/parity_ledger/schema.json's items.allOf[1]: status == divergent ->
    # divergence_note required, non-null
    if entry.get("status") == "divergent":
        _require_non_empty_string(entry, "divergence_note")

    # mirrors docs/parity_ledger/schema.json's items.allOf[2] (narrowed by Step 3a,
    # TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT): priority == P0 with status in
    # {missing, unsupported} -> support_boundary required instead of test_path; every other P0
    # status keeps the original test_path-required rule.
    if entry.get("priority") == "P0":
        if entry.get("status") in _P0_TEST_PATH_EXEMPT_STATUSES:
            _require_non_empty_string(entry, "support_boundary")
        else:
            _require_non_empty_string(entry, "test_path")

    # mirrors docs/parity_ledger/schema.json's properties.evidence_kind.enum
    evidence_kind = entry.get("evidence_kind")
    if evidence_kind is not None and evidence_kind not in _EVIDENCE_KIND_VALUES:
        raise EntryValidationError(
            "evidence_kind", f"must be one of {sorted(_EVIDENCE_KIND_VALUES)} or null"
        )

    # Write-time format contract (Step 3, TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT):
    # a non-null test_path must parse via the shared citation parser, or the write is rejected.
    # Applies only to entries passed through write_entry() -- never a sweep of on-disk entries
    # (TCK-20260705-GATE-DET-MECHANICS-AUDITOR's "never a sweep" decision; ~127 existing entries
    # have unparseable test_path and are fixed only when next written, not en masse). Not
    # mirrored in schema.json: JSON Schema's declarative rules cannot express the shared parser's
    # backtick-stripping/multi-citation-splitting logic, and nothing runs jsonschema validation
    # against the full on-disk ledger today.
    test_path = entry.get("test_path")
    if test_path is not None:
        _, parse_error = parse_test_path_citations(test_path)
        if parse_error is not None:
            raise EntryValidationError(
                "test_path",
                f"{parse_error}; prose/history belongs in support_boundary, not test_path",
            )


def _dump(items: list) -> str:
    """The one place this module serialises YAML. A list of one entry dumps as a `- id: ...` block."""
    return yaml.safe_dump(items, sort_keys=False)


_TOP_LEVEL_ITEM = re.compile(r"^-(?:\s|$)")


def _splice_entry(text: str, entries: list, entry: dict) -> str:
    """Return `text` with `entry` upserted by `id`, touching only that entry's own lines.

    Entry-local instead of a whole-shard dump: a `yaml.safe_dump` round-trip of the unmodified real
    shards reformats hundreds of lines (hand-written quoting and wrapping), which made agents
    deviate from the mandated writer (TCK-20261004-PARITY-LEDGER-WRITER-WHOLE-SHARD-REWRITE-CHURN).
    The i-th column-0 `- ` line starts the i-th entry; an update replaces that block, an add appends
    one. Anything unexpected (item count mismatch, or the spliced text not parsing back to exactly
    the intended entries) falls back to a whole-shard dump, so the result is always correct."""
    lines = text.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if _TOP_LEVEL_ITEM.match(line)]
    expected = [dict(e) for e in entries]
    position = next((i for i, e in enumerate(entries) if e.get("id") == entry["id"]), None)
    if position is None:
        expected.append(entry)
    else:
        expected[position] = entry

    if len(starts) == len(entries):
        block = _dump([entry])
        if position is None:
            body = text if text.endswith("\n") or not text else text + "\n"
            candidate = body + block
        else:
            end = starts[position + 1] if position + 1 < len(starts) else len(lines)
            # keep blank/comment lines that trail the old block: they belong to the gap, not the entry
            while end - 1 > starts[position] and (not lines[end - 1].strip() or lines[end - 1].lstrip().startswith("#")):
                end -= 1
            candidate = "".join(lines[: starts[position]]) + block + "".join(lines[end:])
        try:
            if yaml.safe_load(candidate) == expected:
                return candidate
        except yaml.YAMLError:
            pass
    return _dump(expected)


def write_entry(shard_filename: str, entry: dict, ledger_dir=None, db_path=None) -> dict:
    """Validate `entry` against validate_entry(), then upsert it (by `id`) into
    `ledger_dir/shard_filename`, creating the shard if it does not yet exist. Only the target
    entry's own lines change (see `_splice_entry`). On success, rebuilds the derived parity index
    in-process at `db_path` before returning."""
    validate_entry(entry)

    resolved_ledger_dir = Path(ledger_dir) if ledger_dir is not None else DEFAULT_LEDGER_DIR
    resolved_db_path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    shard_path = resolved_ledger_dir / shard_filename

    text = shard_path.read_text() if shard_path.exists() else ""
    entries = yaml.safe_load(text) if text else []
    entries = entries or []

    shard_path.write_text(_splice_entry(text, entries, entry))

    build_report = build(ledger_dir=resolved_ledger_dir, db_path=resolved_db_path)

    return {
        "status": "ok",
        "shard": shard_filename,
        "entry_id": entry["id"],
        "build_report": build_report,
    }
