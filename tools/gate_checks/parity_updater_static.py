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
