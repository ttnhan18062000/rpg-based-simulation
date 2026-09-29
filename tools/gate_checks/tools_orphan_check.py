r"""On-demand, report-only orphan-file check over all of `tools/` (all subdirectories,
recursively) — never a CI gate, never a ratchet, always exits 0 regardless of findings, per the
user's stated decision that checks over agent tooling should stay proportionate to the risk
(`TCK-20260929-TOOLS-ORPHAN-FILE-CHECK`).

**Disambiguation**: this is NOT `tools/agent-monitoring/epic_scope_orphan_check.py`, which
detects a completely different "orphan" meaning — an epic-tier ticket present in both
`tickets/inprogress/` and `tickets/todos/**` simultaneously. This module finds `tools/` *files*
with no live cross-reference anywhere in the repo — the same population-level method
`TCK-20260820-SCRIPTS-TOOLS-GOVERNANCE-EPIC`'s investigation used by hand to find the `scripts/`
and `tools/` orphans `TCK-20260929-RETIRE-SCRIPTS-DIR` then disposed of, made permanent and
repeatable so a future orphan doesn't have to wait for another manual audit to be found.

**Method**: builds one repo-wide, one-pass identifier-token index (word-boundary tokens via
`IDENT_RE`, the same approach `tools/audit_unreachable_code.py` uses — reimplemented here rather
than imported, since that module's own entry point and CLI surface aren't a stable import target
for this narrower purpose) instead of a per-target-file regex scan of the whole corpus — the
`O(targets * corpus)` approach that took over 300s on this repo's real size. Each tracked
`tools/` file (except `__init__.py` and `__pycache__/`, and excluding the Codex subtree files
below into their own bucket) is classified by whether its bare stem (e.g. `audit_logs` for
`tools/maintenance/audit_logs.py`) appears as an identifier token anywhere else in the tracked
corpus. Matching on the bare stem alone already covers path-form citations too (e.g.
`tools/maintenance/audit_logs.py` appearing literally in a docstring or the Makefile still
contains the `audit_logs` token once split on `/` and `.`, which are not identifier characters)
— it also covers `sys.path` sibling imports in hyphenated `tools/agent-monitoring/` (which
cannot be a dotted Python package name, so a real live import there looks like a bare
`from epic_staleness_check import x`, not a package-qualified one).

**Buckets** (every tracked `tools/` file lands in exactly one, except Codex subtree files, which
land only in `excluded`):
- `LIVE`: at least one referencing file outside `tests/` and `docs/` (real code/config wiring:
  other `src/`, other `tools/`, the Makefile, `.claude/` hooks, etc.).
- `TEST_ONLY`: every referencing file is under `tests/`, and none is a `LIVE`-qualifying hit.
- `DOC_ONLY`: every referencing file is under `docs/`, and none is a `LIVE`- or `TEST_ONLY`-
  qualifying hit. Deliberately the *weakest* signal and checked last — the investigation measured
  that counting any doc mention as "referenced" hides every real orphan (a file can be named in
  prose without anything ever importing or running it), and `DOC_ONLY` does not mean dead (e.g. a
  documented hand-run tool) — the report must present it as "review", not "delete".
- `NO_REFERENCES`: no referencing file found anywhere in the tracked corpus.

Reference hits inside `tickets/done/`, `docs/archive/`, or `stored_artifacts/` never count as
evidence of liveness for any bucket (historical record, not current wiring) — those paths are
excluded from the token index entirely, so a file referenced *only* there is `NO_REFERENCES`.
Excludes a file's own self-mentions (a file's own content is never counted as its own evidence).

**Known, accepted imprecision** (not a bug): generic file stems (e.g. a hypothetical `utils.py`
or `common.py`) will collide with unrelated identical-spelling tokens elsewhere in the corpus and
be wrongly classified as referenced. This is the accepted, safer-than-the-alternative direction —
a false "looks referenced" is far cheaper than a false "looks orphaned" for a report whose whole
purpose is flagging candidates for a human to look at, never an automatic deletion.

One check function (`check_tools_orphans`), one `MARKER:`-prefixed JSON CLI entry point in
`__main__` — mirrors `status_drift_check.py`'s and `working_log_duplicate_check.py`'s shape,
except this module's own `__main__` never calls `sys.exit(1)`: report-only means report-only.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

# Codex subtree prefixes this check excludes from classification entirely, reported in their own
# "excluded" bucket rather than silently skipped — a separate, already-tracked initiative
# (TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC, currently blocked) with its own governance
# question, not this check's concern.
CODEX_SUBTREE_PREFIXES = (
    "tools/agent_codex_",
    "tools/agent_orchestration_",
    "tools/agent_replay_",
)

# Reference hits inside these path prefixes never count as evidence of liveness — historical
# record, not current wiring. Files under these prefixes are excluded from the token index
# entirely (not merely down-weighted), so a tools/ file referenced only there is NO_REFERENCES.
IGNORED_REFERENCE_PREFIXES = (
    "tickets/done/",
    "docs/archive/",
    "stored_artifacts/",
)

# Extensions read as text for the token index. Everything else (images, fonts, compiled
# artifacts) is skipped — a git-tracked binary file carries no textual identifier references.
# "" covers extensionless tracked files (Makefile, LICENSE, etc).
_TEXT_EXTENSIONS = {
    "", ".py", ".md", ".txt", ".yaml", ".yml", ".json", ".js", ".ts", ".tsx", ".jsx", ".sh",
    ".ps1", ".html", ".css", ".toml", ".cfg", ".ini", ".csv",
}


def git_ls_tracked_files(repo_root: Path) -> List[str]:
    """Deterministic, sorted, git-tracked file list for the whole repo (not a raw filesystem
    walk — avoids local __pycache__/untracked-file noise), per this project's stated preference
    for `git ls-files` over a raw walk (see `tools/gate_checks/ci_workflow_test_coverage.py`)."""
    result = subprocess.run(
        ["git", "ls-files"], cwd=repo_root, capture_output=True, text=True, check=True
    )
    return sorted(line for line in result.stdout.splitlines() if line)


def _is_ignored_reference(path: str) -> bool:
    return any(path.startswith(p) for p in IGNORED_REFERENCE_PREFIXES)


def is_codex_subtree(path: str) -> bool:
    return any(path.startswith(p) for p in CODEX_SUBTREE_PREFIXES)


def build_token_index(tracked_files: List[str], repo_root: Path) -> Dict[str, Set[str]]:
    """One-pass token index: identifier-token -> set of tracked file paths it occurs in at least
    once. Scans every tracked file's content exactly once (word-boundary identifier tokens via
    IDENT_RE), instead of a per-target-file regex scan of the whole corpus. Files under
    `IGNORED_REFERENCE_PREFIXES` or with an extension outside `_TEXT_EXTENSIONS` are skipped.
    Codex subtree files are also skipped here (never read as a reference *source*, not just
    excluded as a classification *target*) — out of scope is "scanning the codex subtrees'
    contents beyond listing them as excluded", so their content never contributes evidence for
    (or against) any other file's classification either."""
    index: Dict[str, Set[str]] = {}
    for rel_path in tracked_files:
        if _is_ignored_reference(rel_path):
            continue
        if is_codex_subtree(rel_path):
            continue
        if Path(rel_path).suffix not in _TEXT_EXTENSIONS:
            continue
        try:
            content = (repo_root / rel_path).read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for tok in set(IDENT_RE.findall(content)):
            index.setdefault(tok, set()).add(rel_path)
    return index


def _classify(referencing_files: Set[str]) -> str:
    """LIVE > TEST_ONLY > DOC_ONLY > NO_REFERENCES — see module docstring for the rationale."""
    if not referencing_files:
        return "NO_REFERENCES"
    if any(not f.startswith("tests/") and not f.startswith("docs/") for f in referencing_files):
        return "LIVE"
    if any(f.startswith("tests/") for f in referencing_files):
        return "TEST_ONLY"
    return "DOC_ONLY"


def check_tools_orphans(
    repo_root: Optional[Path] = None, tracked_files: Optional[List[str]] = None
) -> List[dict]:
    """Classify every tracked `tools/` file into NO_REFERENCES / DOC_ONLY / TEST_ONLY / LIVE
    (Codex subtree files, plus `__init__.py` and `__pycache__/`, go in `excluded` / are skipped
    respectively), each with its referencing files as evidence.

    `repo_root` defaults to this repo (three parents up from this file:
    `tools/gate_checks/<this>` -> `tools` -> repo root). `tracked_files` is injectable so tests
    can exercise this against a synthetic `tmp_path` mini-repo without a real git repo; the
    default (`None`) shells out to `git_ls_tracked_files(repo_root)`.

    Returns a flat `list[dict]` of `{"file", "status", "evidence"}`, sorted by `file` — evidence
    is the sorted list of referencing file paths (empty for `NO_REFERENCES` and `excluded`).
    Deterministic and side-effect-free: two consecutive calls against the same tree produce
    byte-identical output, and the working tree is never modified.
    """
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[2]
    if tracked_files is None:
        tracked_files = git_ls_tracked_files(repo_root)
    else:
        tracked_files = sorted(set(tracked_files))

    tools_files = [f for f in tracked_files if f.startswith("tools/")]
    index = build_token_index(tracked_files, repo_root)

    findings: List[dict] = []
    for rel_path in tools_files:
        name = Path(rel_path).name
        if name == "__init__.py" or "__pycache__" in rel_path:
            continue
        if is_codex_subtree(rel_path):
            findings.append({"file": rel_path, "status": "excluded", "evidence": []})
            continue

        stem = Path(rel_path).stem
        referencing = {f for f in index.get(stem, ()) if f != rel_path}
        findings.append({
            "file": rel_path,
            "status": _classify(referencing),
            "evidence": sorted(referencing),
        })

    return sorted(findings, key=lambda f: f["file"])


if __name__ == "__main__":
    result = check_tools_orphans()
    print("MARKER:" + json.dumps(result))
    sys.exit(0)
