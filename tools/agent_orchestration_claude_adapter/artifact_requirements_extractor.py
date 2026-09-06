"""Live artifact-requirements extraction — deliberately not a JS-text-regex scan.

Unlike `gate_policy_extractor.py`, there is no JS text to scan for this axis:
`tools/gate_checks/done_checker_static.py` is Python, imported directly here — matching
investigation.md's own conclusion that "importing is more robust... already the pattern
`tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py` uses for its
contract-side load" (`terminal_status_loader.load_terminal_statuses`).

Deliberately no parallel "artifact_requirements_loader.py" contract-side wrapper: the contract
side is already returned directly by `load_contract(repo_root).artifact_requirements` (see
`tools/agent_orchestration/loader.py`) — a second wrapper file here would be unnecessary
indirection for an axis this simple. This is a deliberate asymmetry against
`terminal_status_extractor.py`/`terminal_status_loader.py`'s file pair, not an oversight.
"""
from __future__ import annotations

from pathlib import Path

from tools.gate_checks.done_checker_static import REQUIRED_ARTIFACT_FILES


def extract_live_artifact_requirements(repo_root: Path) -> dict:
    """Reads `tools/gate_checks/done_checker_static.py`'s `REQUIRED_ARTIFACT_FILES` constant and
    its `check_staging_artifacts_complete`'s `tier == "hotfix"` branch directly via import.

    The `"hotfix"` string is a documented, hand-verified constant reflecting that function's own
    literal `if tier == "hotfix"` branch — the only branch condition that function has — not
    scraped by regex (there is exactly one branch, so a regex would be no more robust than stating
    the constant directly, and the import above already gives a live, always-fresh read of the
    file list itself, which is the part that actually changes). `repo_root` is accepted (and
    otherwise unused) to keep this function's signature symmetric with
    `extract_gate_policy(workflow_js_path)`'s repo-relative-path convention.
    """
    del repo_root  # unused — REQUIRED_ARTIFACT_FILES is a module-level constant, not file-scoped
    return {"required_files": list(REQUIRED_ARTIFACT_FILES), "exempt_tier": "hotfix"}
