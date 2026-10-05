"""Static guard for TCK-20261005-CI-SKIP-HEAVY-JOBS-ON-REGISTRY-ONLY-RESYNC.

Pins which CI jobs may skip on a registry-only re-sync push and which must keep running. The skip set is
exactly the jobs a measured audit found read no real `docs/REGISTRY.yaml`; the keep set holds the real
readers (`tests/tools`, `tests/codebase`) and the cheap docs/registry/lint checks. Adding the skip to a keep
job, or removing it from a skip job, must be a deliberate edit here, with a new audit behind it.
"""
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parent.parent.parent
_JOBS = yaml.safe_load((_ROOT / ".github" / "workflows" / "test.yml").read_text())["jobs"]

SKIP_JOBS = {
    "unit-core-world",
    "unit-gameplay",
    "unit-infra",
    "integration",
    "api-cli-engine",
    "agent-orchestration",
    "simulation-quality",
    "perf-cert-arena",
    "migration-lanes",
    "scenario-lane",
    "frontend",
}
KEEP_JOBS = {"tools-a-e", "tools-f-z", "arch-docs", "typecheck", "code-health", "code-health-sarif"}


def _references_gate(job: dict) -> bool:
    return "resync-gate" in str(job.get("if", "")) or "resync-gate" in str(job.get("needs", ""))


def test_exactly_the_audited_jobs_skip_on_a_resync() -> None:
    skipping = {name for name, job in _JOBS.items() if _references_gate(job) and name != "resync-gate"}
    assert skipping == SKIP_JOBS


def test_jobs_holding_real_registry_readers_and_cheap_checks_never_skip() -> None:
    for name in KEEP_JOBS:
        assert name in _JOBS, name
        assert not _references_gate(_JOBS[name]), f"{name} must keep running on a re-sync"


def test_every_skip_condition_fails_open() -> None:
    for name in SKIP_JOBS:
        job = _JOBS[name]
        assert "resync-gate" in job["needs"], name
        condition = job["if"]
        assert "!cancelled()" in condition, name
        # Skips only on a successful gate that said exactly 'true'; a failed or missing gate runs the job.
        assert "needs.resync-gate.result != 'success'" in condition, name
        assert "needs.resync-gate.outputs.pr_content_unchanged != 'true'" in condition, name


def test_the_gate_itself_cannot_be_skipped_and_installs_nothing() -> None:
    gate = _JOBS["resync-gate"]
    assert "if" not in gate
    assert gate["permissions"] == {"contents": "read", "actions": "read"}
