"""Classifies a CI failure into the four categories `CLAUDE.md`'s "CI Failure Triage" section
already defines, and names the path it prescribes (TCK-20260924-DELIVERY-CI-TRIAGE-CLASSIFIER).

Consumes `tools/delivery/pr_status.py`'s own `FAILING`/`ABSENT`/`UNKNOWN` payload rather than
re-fetching CI state itself — two fetchers would drift, and this module never calls `gh`.

Categories (`## CI Failure Triage` step 3, `docs/guides/delivery_process.md`):

1. ``REAL_REGRESSION``  a real regression caused by this session's own changes.
2. ``DOCUMENTED_FLAKE``  a category `docs/testing/regression_policy.md` already documents as
   environment-dependent/flaky.
3. ``BASELINE_DRIFT``  a hardcoded test baseline this session's own legitimate change caused to
   drift.
4. ``ENVIRONMENT``  environment/infrastructure, including an `ABSENT` verdict (no run was ever
   created) and the Fortiguard TLS block on log hosts.
5. ``UNCLASSIFIED``  the signals do not clearly place the failure into a known category. **This
   outcome is load-bearing, not a failure of the classifier** — a classifier that always returns a
   confident category trains an agent to trust it, and the first confident misclassification then
   costs more than the whole tool saves. Never forced into the nearest category to look decisive.

**`pr_status.py`'s `FAILING` payload only carries job name and per-step name/conclusion — no
individual failing test path** (fetching one would mean reading a log body, out of scope for both
tools). Changed-file correlation for category 1 therefore happens at *job* granularity: a job's
`.github/workflows/test.yml` `run:` step is parsed for the `pytest <paths...>` arguments it
actually invokes, and those paths are checked against the branch's changed files. This is a
signal, not proof — the classifier's evidence states the job-level basis explicitly rather than
implying test-file precision it does not have.

**Category 2 is read from `docs/testing/regression_policy.md`'s `## 3. Soft Monitors` table at
runtime** (its `Location` column's backtick-quoted paths), never carried as a second hardcoded
list that could drift from the source.

**Category 3 starts from a short, explicit, named-pattern allowlist** (only
`tests/tools/test_parity_index_baseline.py` is named in the originating ticket) rather than
generalizing — an unlisted failure never gets guessed into category 3.

Out of scope, deliberately: filing the ticket (classification is not action), editing any test,
assertion, baseline, or gate (the classifier's entire reason for existing is to make the correct
path obvious, not to take it), blocking, re-running or re-triggering a job, fetching PR/run state
or log bodies itself, and deciding a failure is acceptable (no category means "ignore").
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

try:
    from tools.delivery.pr_status import CommandResult, default_run_command, _TLS_BLOCK_KEYWORDS
except ImportError:
    _TOOLS_DIR = Path(__file__).resolve().parent.parent
    if str(_TOOLS_DIR / "delivery") not in sys.path:
        sys.path.insert(0, str(_TOOLS_DIR / "delivery"))
    from pr_status import CommandResult, default_run_command, _TLS_BLOCK_KEYWORDS  # noqa: E402

REAL_REGRESSION = "REAL_REGRESSION"
DOCUMENTED_FLAKE = "DOCUMENTED_FLAKE"
BASELINE_DRIFT = "BASELINE_DRIFT"
ENVIRONMENT = "ENVIRONMENT"
UNCLASSIFIED = "UNCLASSIFIED"

_DEFAULT_POLICY_PATH = Path("docs/testing/regression_policy.md")
_DEFAULT_WORKFLOW_PATH = Path(".github/workflows/test.yml")
_KNOWN_BASELINE_DRIFT_PATHS = frozenset({"tests/tools/test_parity_index_baseline.py"})
_KNOWN_PARKED_JOBS = frozenset({"Slow regression"})

_BACKTICK_PATH_RE = re.compile(r"`([^`]+)`")
_PYTEST_ARG_RE = re.compile(r"(tests/[A-Za-z0-9_/.\-]+)")


def _section_text(text: str, heading: str, next_heading_prefix: str = "## ") -> str:
    start = text.find(heading)
    if start == -1:
        return ""
    start += len(heading)
    rest = text[start:]
    next_idx = rest.find(f"\n{next_heading_prefix}")
    return rest if next_idx == -1 else rest[:next_idx]


def parse_regression_policy_soft_paths(policy_path: Path = _DEFAULT_POLICY_PATH) -> set:
    if not Path(policy_path).exists():
        return set()
    text = Path(policy_path).read_text(encoding="utf-8")
    section = _section_text(text, "## 3. Soft Monitors")
    paths = set()
    for match in _BACKTICK_PATH_RE.findall(section):
        if match.startswith("tests/"):
            paths.add(match)
    return paths


def parse_workflow_job_paths(workflow_path: Path = _DEFAULT_WORKFLOW_PATH) -> Dict[str, List[str]]:
    """Maps each job's `name:` field to the `tests/...` path tokens appearing in its `run:` step.
    A small, deliberately permissive regex scan (not a YAML-aware step-by-step parser) — good
    enough to answer "does this job cover this path," not a general workflow parser."""
    if not Path(workflow_path).exists():
        return {}
    import yaml

    try:
        doc = yaml.safe_load(Path(workflow_path).read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return {}
    if not isinstance(doc, dict):
        return {}

    jobs = doc.get("jobs", {})
    result = {}
    for job in jobs.values():
        if not isinstance(job, dict):
            continue
        name = job.get("name")
        if not name:
            continue
        paths = set()
        for step in job.get("steps", []) or []:
            if not isinstance(step, dict):
                continue
            run = step.get("run", "")
            paths.update(_PYTEST_ARG_RE.findall(run))
        result[name] = sorted(paths)
    return result


def _is_tls_blocked_reason(reason: Optional[str]) -> bool:
    lowered = (reason or "").lower()
    return any(kw in lowered for kw in _TLS_BLOCK_KEYWORDS)


def classify_absent(reason: Optional[str]) -> dict:
    reason = reason or ""
    if "CONFLICTING" in reason:
        remedy = (
            "No run was created because the PR is CONFLICTING and this workflow is "
            "pull_request-only for this branch. Fix: resolve the merge conflict. A re-trigger "
            "commit, force-push, or branch recreation will NOT help."
        )
    else:
        remedy = f"No run was created for this SHA. Investigate the specific reason: {reason}"
    return {"category": ENVIRONMENT, "remedy": remedy, "evidence": {"absent_reason": reason}}


def classify_unknown(reason: Optional[str]) -> dict:
    if _is_tls_blocked_reason(reason):
        return {
            "category": ENVIRONMENT,
            "remedy": (
                "The run/log fetch appears blocked (network/TLS), not a real failure signal. "
                "Use step-level conclusions instead of retrying the fetch."
            ),
            "evidence": {"unknown_reason": reason},
        }
    return {
        "category": UNCLASSIFIED,
        "remedy": "State could not be established and no known cause applies. Investigate manually.",
        "evidence": {"unknown_reason": reason},
    }


def classify_failing_job(
    job: dict,
    job_paths: Dict[str, List[str]],
    soft_paths: set,
    changed_files: List[str],
    known_baseline_drift_paths: frozenset = _KNOWN_BASELINE_DRIFT_PATHS,
    known_parked_jobs: frozenset = _KNOWN_PARKED_JOBS,
) -> dict:
    job_name = job.get("job_name") or ""
    covered = job_paths.get(job_name, [])
    parked = job_name in known_parked_jobs

    if any(p in soft_paths for p in covered):
        result = {
            "category": DOCUMENTED_FLAKE,
            "remedy": "Documented environment-dependent/flaky per regression_policy.md — do not "
            "code-fix; report as environment noise and let it re-run.",
            "evidence": {"job": job_name, "covered_paths": covered, "matched_soft_paths": True},
        }
    elif any(p in known_baseline_drift_paths for p in covered):
        result = {
            "category": BASELINE_DRIFT,
            "remedy": "Looks like a hardcoded test baseline this branch's own legitimate change "
            "caused to drift — file a hotfix ticket with fresh evidence, never a silent edit.",
            "evidence": {"job": job_name, "covered_paths": covered},
        }
    elif covered and any(any(cf.startswith(p) for p in covered) for cf in changed_files):
        result = {
            "category": REAL_REGRESSION,
            "remedy": "Likely a real regression from this branch's own changes (job-level "
            "correlation, not proof) — file a hotfix ticket and run the full pipeline.",
            "evidence": {"job": job_name, "covered_paths": covered, "changed_files": changed_files},
        }
    else:
        result = {
            "category": UNCLASSIFIED,
            "remedy": "Signals do not clearly place this failure into a known category. "
            "Investigate manually before acting — do not guess.",
            "evidence": {"job": job_name, "covered_paths": covered},
        }

    if parked:
        result["parked"] = True
        result["note"] = f"{job_name!r} is a known parked job — not a new finding."
    return result


def classify(
    payload: dict,
    run_command=default_run_command,
    base_ref: str = "origin/main",
    policy_path: Path = _DEFAULT_POLICY_PATH,
    workflow_path: Path = _DEFAULT_WORKFLOW_PATH,
    known_baseline_drift_paths: frozenset = _KNOWN_BASELINE_DRIFT_PATHS,
    known_parked_jobs: frozenset = _KNOWN_PARKED_JOBS,
) -> dict:
    verdict = payload.get("verdict")

    if verdict == "ABSENT":
        return classify_absent(payload.get("reason"))
    if verdict == "UNKNOWN":
        return classify_unknown(payload.get("reason"))
    if verdict != "FAILING":
        return {
            "category": UNCLASSIFIED,
            "remedy": f"Nothing to classify for verdict {verdict!r}.",
            "evidence": {},
        }

    failing_jobs = payload.get("failing_jobs") or []
    if not failing_jobs:
        return {"category": UNCLASSIFIED, "remedy": "FAILING verdict but no job detail provided.", "evidence": {}}

    job_paths = parse_workflow_job_paths(workflow_path)
    soft_paths = parse_regression_policy_soft_paths(policy_path)
    diff_result = run_command(["git", "diff", "--name-only", f"{base_ref}..HEAD"])
    changed_files = diff_result.stdout.splitlines() if diff_result.returncode == 0 else []

    per_job = [
        classify_failing_job(job, job_paths, soft_paths, changed_files, known_baseline_drift_paths, known_parked_jobs)
        for job in failing_jobs
    ]
    categories = {j["category"] for j in per_job}
    if len(categories) == 1:
        overall = dict(per_job[0])
        overall["evidence"] = {"jobs": [j["evidence"] for j in per_job]}
        if any(j.get("parked") for j in per_job):
            overall["parked"] = True
            overall["note"] = "; ".join(j["note"] for j in per_job if j.get("parked"))
        return overall

    return {
        "category": UNCLASSIFIED,
        "remedy": "Multiple failing jobs classify differently — signals do not agree. "
        "Investigate manually before acting.",
        "evidence": {"per_job": per_job},
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Classify a CI failure into the four CLAUDE.md categories plus UNCLASSIFIED. "
        "Read-only, advisory: exits 0 for every classification; non-zero only on a genuine "
        "internal error."
    )
    parser.add_argument("--payload-file", default=None, help="Path to a pr_status.py JSON payload; omit to read stdin")
    parser.add_argument("--base-ref", default="origin/main")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        raw = Path(args.payload_file).read_text(encoding="utf-8") if args.payload_file else sys.stdin.read()
        payload = json.loads(raw.split("MARKER:", 1)[-1])
        result = classify(payload, base_ref=args.base_ref)
    except Exception as exc:  # noqa: BLE001 - the one deliberate non-zero-exit path
        print(f"INTERNAL ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print("MARKER:" + json.dumps(result))
    else:
        print(f"category: {result['category']}")
        print(f"remedy: {result['remedy']}")
        if result.get("note"):
            print(f"note: {result['note']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
