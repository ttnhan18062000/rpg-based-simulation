import re
from pathlib import Path

import yaml

# Static architecture guard: proves the CI YAML and Makefile *text* wire the isolated
# per-test lane for test_corpus_diversity.py's -m slow guards correctly (right ordering,
# no hardcoded node-ID list, --ignore flag present on the now-duplicate sequential
# invocation). Does NOT execute pytest collection -- that runtime protection lives in
# the Makefile target's own `nodeid_count -lt 32` assertion (TCK-20260715-SIMQ-CORPUS-
# DIVERSITY-SESSION-LOAD-FLAKE), which runs live on every invocation.

_ROOT = Path(__file__).resolve().parent.parent.parent
_IGNORE_FLAG = "--ignore=tests/unit/worldassembly/test_corpus_diversity.py"
_ISOLATED_LANE_TARGET = "make simq-corpus-diversity-slow-isolated"


def _slow_job_steps() -> list[dict]:
    workflow = yaml.safe_load((_ROOT / ".github" / "workflows" / "test.yml").read_text())
    return workflow["jobs"]["slow"]["steps"]


def test_slow_ci_job_ignores_corpus_diversity_in_main_invocation() -> None:
    steps = _slow_job_steps()
    matches = [step for step in steps if _IGNORE_FLAG in (step.get("run") or "")]
    assert matches, (
        f"expected a step in the 'slow' CI job with '{_IGNORE_FLAG}' in its run command "
        "-- test_corpus_diversity.py must not be double-run by the sequential invocation"
    )


def test_slow_ci_job_runs_corpus_diversity_isolated_lane() -> None:
    steps = _slow_job_steps()
    isolated_index = next(
        (i for i, step in enumerate(steps) if _ISOLATED_LANE_TARGET in (step.get("run") or "")),
        None,
    )
    assert isolated_index is not None, (
        f"expected a step in the 'slow' CI job running '{_ISOLATED_LANE_TARGET}'"
    )

    ignore_index = next(
        (i for i, step in enumerate(steps) if _IGNORE_FLAG in (step.get("run") or "")),
        None,
    )
    assert ignore_index is not None, f"expected a step with '{_IGNORE_FLAG}' in its run command"

    assert isolated_index < ignore_index, (
        "the isolated lane step must run BEFORE the --ignore-flagged sequential step "
        f"(isolated at index {isolated_index}, ignore-flagged at index {ignore_index})"
    )


def test_isolated_lane_uses_dynamic_collection_not_hardcoded_list() -> None:
    makefile_text = (_ROOT / "Makefile").read_text()

    target_match = re.search(
        r"^simq-corpus-diversity-slow-isolated:.*?(?=\n\S|\Z)",
        makefile_text,
        re.DOTALL | re.MULTILINE,
    )
    assert target_match, "simq-corpus-diversity-slow-isolated target not found in Makefile"
    target_body = target_match.group(0)

    assert "--collect-only" in target_body, (
        "isolated lane must dynamically collect node IDs via --collect-only, not use a "
        "hardcoded list"
    )

    hardcoded_test_name = re.search(
        r"test_\w+_(grade_stability|bit_identical_under_load|population_stability)",
        target_body,
    )
    assert hardcoded_test_name is None, (
        f"found a literal test-function-name string in the target body "
        f"({hardcoded_test_name.group(0)!r}) -- node IDs must be collected dynamically, "
        "not hardcoded (a future test rename/addition would silently stop being covered)"
    )
