"""Deterministic src/ -> parity-ledger-subsystem mapping and diff cross-reference.

Built for TCK-20260705-GATE-DET-PARITY-UPDATER: `parity-updater`'s ledger updates are entirely
LLM-judged today — nothing checks whether a `src/` file that maps to a ledger subsystem actually
got a corresponding YAML entry touched in the same Implement pass. This module gives the Parity
phase a deterministic backstop for that subset, split into two calls per the causality fix required
by architecture review (see plan.md's Summary/Unresolved Questions):

- `expected_subsystems_for_files` — runs *before* the `parity-updater` agent call (via the
  orchestrator's own `bash()`, mirroring the existing `p0ScanOutput` precedent in the Parity phase),
  producing the todo-list of which ledger file(s) each changed `src/` file is expected to touch.
- `cross_reference_touched` — runs *after* the agent call returns (via `bash()`, mirroring
  `run_finalize_selfcheck`'s JSON-marker-prefix pattern), comparing that todo-list against what
  `docs/parity_ledger/` actually shows touched in `git status`.

`derive_mapping` is deliberately general-purpose and Parity-name-decoupled (shared-package
convention from SEQUENCE.md decision 1) so the sibling `GATE-DET-MECHANICS-AUDITOR` ticket can
import it directly rather than deriving a second, possibly-inconsistent mapping.

Mirrors `tools/parity_ledger_scan.py` / `tools/gate_checks/done_checker_static.py`'s shape: plain
functions, plain tuple/dict returns, no argparse/CLI — consumed exclusively via `python3 -c "..."`.

TCK-20260824-PARITY-NEXT-ID-LOOKUP added `next_available_id` and `search_existing_entries`: the
Parity phase previously made `parity-updater` grep the raw YAML by hand for both "what's the next
free ID in this shard" and "does an entry already exist for this concern" — purely mechanical
lookups now done deterministically instead. `next_available_id` is wired into the Parity phase's
existing Step 0 orchestrator `bash()` call, same as `expected_subsystems_for_files`.
`search_existing_entries` is not auto-wired (there is no automatic query string to feed it) — it is
documented for the `parity-updater` agent to call directly via Bash when it needs one.
"""

import re
import sys
from pathlib import Path

import yaml

_TOOLS_DIR = Path(__file__).resolve().parent.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from parity_ledger_scan import CANONICAL_LEDGER_FILES  # noqa: E402

_SRC_PATH_RE = re.compile(r"src/[\w\-./]+\.py")

# mirrors tools/parity_ledger_writer.py's _ID_PATTERN (docs/parity_ledger/schema.json:9-11
# properties.id.pattern), with the full non-numeric prefix and numeric suffix captured separately
# for arithmetic instead of a bare match. The prefix group allows multi-segment prefixes (e.g.
# WORLD-DEMO) so a shard mixing WORLD-NNN and WORLD-DEMO-NNN families is not silently collapsed
# into one (TCK-20260831-PARITY-LEDGER-ID-PATTERN-MULTISEGMENT).
_ID_PATTERN = re.compile(r"^([A-Z]+(?:-[A-Z]+)*)-([0-9]{3})$")


def derive_mapping(ledger_dir: "Path | str" = "docs/parity_ledger") -> dict:
    """Return {src_path: {ledger_filename, ...}} derived from every `v2_evidence` citation in
    CANONICAL_LEDGER_FILES. A path cited in more than one canonical file accumulates every filename
    in its set — must never collapse to a single value (~16% of paths are cited in 2+ files).

    Skips a canonical file silently if it doesn't exist under ledger_dir, and skips (continues past)
    any file that fails to parse as YAML — legacy-data tolerance, never raises.
    """
    ledger_path = Path(ledger_dir)
    mapping: dict = {}
    for filename in CANONICAL_LEDGER_FILES:
        path = ledger_path / filename
        if not path.exists():
            continue
        try:
            entries = yaml.safe_load(path.read_text()) or []
        except Exception:
            continue
        for entry in entries:
            evidence = entry.get("v2_evidence") or ""
            for src_path in _SRC_PATH_RE.findall(evidence):
                mapping.setdefault(src_path, set()).add(filename)
    return mapping


def expected_subsystems_for_files(files_changed, ledger_dir="docs/parity_ledger") -> dict:
    """Filter files_changed to src/ paths and return {src_path: sorted(candidates) | None}.

    Non-src/ paths are excluded entirely from the returned dict. A src/ path with no citation
    anywhere in the canonical ledger files maps to None (rendered as NA by the caller) — never
    omitted, never silently treated as passing.
    """
    mapping = derive_mapping(ledger_dir)
    result = {}
    for path in files_changed:
        if not path.startswith("src/"):
            continue
        candidates = mapping.get(path)
        result[path] = sorted(candidates) if candidates else None
    return result


def cross_reference_touched(files_changed, touched_ledger_files, ledger_dir="docs/parity_ledger") -> list:
    """Return a list of {"file", "status", "evidence"} dicts, one per src/ path in files_changed.

    status is one of:
    - "NA" — no v2_evidence citation found in any canonical ledger file for this path.
    - "PASS" — at least one candidate subsystem's YAML file was touched (ANY-of-candidates
      semantics — a multi-mapped file only needs one of its candidates touched to clear).
    - "FAIL" — mapped to one or more candidates, but none were touched.

    touched_ledger_files tolerates raw `git status --porcelain` lines (e.g.
    " M docs/parity_ledger/combat_movement.yaml"), `git diff --name-only` output, or bare filenames —
    normalized to basenames before comparison.
    """
    touched_basenames = {Path(line.strip().split()[-1]).name for line in touched_ledger_files if line.strip()}

    expected = expected_subsystems_for_files(files_changed, ledger_dir)
    results = []
    for path, candidates in expected.items():
        if candidates is None:
            results.append({
                "file": path,
                "status": "NA",
                "evidence": "no v2_evidence citation found in any canonical ledger file",
            })
            continue
        touched_candidates = [c for c in candidates if c in touched_basenames]
        if touched_candidates:
            results.append({
                "file": path,
                "status": "PASS",
                "evidence": f"touched: {touched_candidates}",
            })
        else:
            results.append({
                "file": path,
                "status": "FAIL",
                "evidence": f"mapped to {candidates}, none touched",
            })
    return results


def next_available_id(shard_filename: str, ledger_dir="docs/parity_ledger") -> str:
    """Return `{prefix}-{max_suffix + 1}` (zero-padded to the shard's own observed width) for the
    next available ID in shard_filename.

    IDs are not dense — a shard's highest entry_id suffix can sit well below its entry count — so
    this walks every id and tracks the maximum numeric suffix rather than using len(entries) + 1.
    A shard can mix more than one id family (e.g. world_dynamics.yaml holds bare WORLD-NNN
    alongside multi-segment WORLD-DEMO-NNN and WORLD-CULT-NNN shard ids) -- max_suffix is tracked
    per full prefix, never globally across families, so proposing the next id for one family can
    never be skewed by a higher suffix that belongs to a different family. The reported family is
    whichever prefix belongs to the last matching entry in the shard (its ids' own file order),
    mirroring this function's pre-existing single-family behavior. Prefix and zero-pad width are
    derived from the shard's own existing ids, never a hardcoded shard->prefix table. Raises
    ValueError if the shard has no entry with an id matching _ID_PATTERN — there is nothing to
    derive a prefix from.
    """
    path = Path(ledger_dir) / shard_filename
    entries = yaml.safe_load(path.read_text()) if path.exists() else []
    entries = entries or []

    max_suffix_by_prefix = {}
    width_by_prefix = {}
    last_prefix = None
    for entry in entries:
        match = _ID_PATTERN.match(entry.get("id") or "")
        if not match:
            continue
        entry_prefix, suffix_str = match.groups()
        width_by_prefix[entry_prefix] = len(suffix_str)
        max_suffix_by_prefix[entry_prefix] = max(
            max_suffix_by_prefix.get(entry_prefix, -1), int(suffix_str)
        )
        last_prefix = entry_prefix

    if last_prefix is None:
        raise ValueError(f"{shard_filename} has no entry with an id matching {_ID_PATTERN.pattern!r}")

    width = width_by_prefix[last_prefix]
    max_suffix = max_suffix_by_prefix[last_prefix]
    return f"{last_prefix}-{max_suffix + 1:0{width}d}"


def search_existing_entries(query: str, ledger_dir="docs/parity_ledger", shard_filename=None) -> list:
    """Case-insensitive substring search of every entry's `text`/`v2_evidence` fields.

    A plain substring grep, not fuzzy/semantic — consistent with this module's deterministic
    character. Returns one {"id", "shard", "matched_field", "excerpt"} dict per field match (an
    entry matching in both fields produces two results). Scoped to shard_filename if given,
    otherwise searches every CANONICAL_LEDGER_FILES shard. A shard that doesn't exist or fails to
    parse is skipped, mirroring derive_mapping's legacy-data tolerance.
    """
    shards = [shard_filename] if shard_filename else CANONICAL_LEDGER_FILES
    query_lower = query.lower()
    excerpt_radius = 40
    ledger_path = Path(ledger_dir)
    results = []

    for filename in shards:
        path = ledger_path / filename
        if not path.exists():
            continue
        try:
            entries = yaml.safe_load(path.read_text()) or []
        except Exception:
            continue
        for entry in entries:
            for field in ("text", "v2_evidence"):
                value = entry.get(field) or ""
                index = value.lower().find(query_lower)
                if index == -1:
                    continue
                start = max(0, index - excerpt_radius)
                end = min(len(value), index + len(query) + excerpt_radius)
                results.append({
                    "id": entry.get("id"),
                    "shard": filename,
                    "matched_field": field,
                    "excerpt": value[start:end],
                })
    return results
