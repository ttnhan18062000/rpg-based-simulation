"""Which file group of the first-bad commit breaks the combat_initiated test? Export the bad commit, restore one group of
files to the parent's version, run the test from the export root. A group whose restoration makes the test pass is implicated."""
import shutil
import subprocess

REPO = "/mnt/data/Working/rpg-based-simulation/.claude/worktrees/attack-path-trace"
S = "/tmp/claude-1000/-mnt-data-Working-rpg-based-simulation--claude-worktrees-lane-a-tactical-path-batch/c3c03123-6c20-4694-bb97-f41faaa98a72/scratchpad"
PY = "/mnt/data/Working/rpg-based-simulation/.venv/bin/python"
TEST = "tests/integration/campaigns/test_catalog_entity_spawn_wiring.py::test_real_campaign_episode_event_stream_is_plausible_not_degenerate"
BAD, PARENT = "bc00caa1a", "bc00caa1a^"
GROUPS = {
    "none (control: bad commit as is)": [],
    "G1 governor/worker_manager/kernel/pipeline (DEGRADED fix)": [
        "src/engine/governor.py", "src/engine/worker_manager.py", "src/engine/kernel.py", "src/engine/pipeline.py"],
    "G2 candidate_selector": ["src/engine/candidate_selector.py"],
    "G3 contracts (phase + system)": ["src/engine/pipeline_phases/contracts.py", "src/systems/social_systems/contracts.py"],
    "G4 campaigns orchestrator+state": ["src/domains/campaigns/orchestrator.py", "src/domains/campaigns/state.py"],
}


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


for name, files in GROUPS.items():
    d = f"{S}/group_export"
    shutil.rmtree(d, ignore_errors=True)
    shutil.os.makedirs(d)
    a = subprocess.Popen(["git", "-C", REPO, "archive", BAD], stdout=subprocess.PIPE)
    subprocess.run(["tar", "-x", "-C", d], stdin=a.stdout, check=True)
    a.wait()
    for f in files:
        content = run(["git", "-C", REPO, "show", f"{PARENT}:{f}"])
        if content.returncode == 0:
            open(f"{d}/{f}", "w").write(content.stdout)
    r = run([PY, "-m", "pytest", TEST, "-m", "slow", "-q", "-p", "no:cacheprovider"], cwd=d, timeout=900)
    out = r.stdout + r.stderr
    import re
    m = re.search(r"assert (\d+) >= 3", out)
    if "1 passed" in out:
        res = "PASSES (>=3)"
    elif m:
        res = f"combat_initiated={m.group(1)}"
    else:
        err = [l for l in out.splitlines() if l.startswith("E  ")]
        res = "OTHER: " + (err[0][:100] if err else (out.strip().splitlines()[-1][:100] if out.strip() else "no output"))
    print(f"{res:28} <- restoring {name}", flush=True)
print("GROUPS-DONE", flush=True)
