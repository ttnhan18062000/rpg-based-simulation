from pathlib import Path

import yaml

# Static guard for TCK-20260821-HOTFIX-GHPAGES-BUILD-OOM: every push-to-main "Deploy Docs to
# GitHub Pages" run crashed with a V8 heap-out-of-memory abort (observed peak ~4,129MB) because
# no NODE_OPTIONS old-space limit was set on the Build step, letting Node's unflagged ~4GB
# default apply. Follows the tests/static/test_ci_narrow_path_filtered_jobs.py precedent: parse
# the workflow YAML with yaml.safe_load and assert on step dict structure -- no live GitHub
# Actions execution is possible from pytest, so this only proves the env var stays wired, not
# that the runner has enough real RAM.

_ROOT = Path(__file__).resolve().parent.parent.parent
_WORKFLOW_PATH = _ROOT / ".github" / "workflows" / "deploy-docs.yml"

# The crash's observed peak was ~4,129MB; this is the minimum headroom this guard requires
# above that ceiling, not the exact configured value.
_MIN_HEAP_LIMIT_MB = 4129


def _load_workflow():
    return yaml.safe_load(_WORKFLOW_PATH.read_text())


def _find_build_step(workflow):
    steps = workflow["jobs"]["deploy"]["steps"]
    for step in steps:
        if step.get("name") == "Build":
            return step
    raise AssertionError("no step named 'Build' found in deploy-docs.yml's deploy job")


def test_deploy_docs_workflow_parses():
    workflow = _load_workflow()
    assert workflow["jobs"]["deploy"]["steps"]


def test_build_step_sets_node_options_heap_limit():
    build_step = _find_build_step(_load_workflow())
    env = build_step.get("env") or {}
    assert "NODE_OPTIONS" in env, (
        "Build step has no NODE_OPTIONS env var -- Node's unflagged ~4GB old-space default "
        "will apply again, reproducing the heap-OOM crash this ticket fixed"
    )


def test_node_options_max_old_space_size_has_real_headroom():
    build_step = _find_build_step(_load_workflow())
    node_options = build_step["env"]["NODE_OPTIONS"]
    assert "--max-old-space-size=" in node_options

    value_str = node_options.split("--max-old-space-size=", 1)[1].split()[0]
    heap_limit_mb = int(value_str)

    assert heap_limit_mb > _MIN_HEAP_LIMIT_MB, (
        f"--max-old-space-size={heap_limit_mb} is at or below the ~{_MIN_HEAP_LIMIT_MB}MB "
        "observed crash ceiling -- would not actually fix the OOM"
    )
