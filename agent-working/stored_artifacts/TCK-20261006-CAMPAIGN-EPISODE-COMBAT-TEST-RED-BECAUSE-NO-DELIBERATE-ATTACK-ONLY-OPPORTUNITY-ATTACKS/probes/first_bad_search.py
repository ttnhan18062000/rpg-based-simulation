"""Binary-search the commits between a good and a bad ref for the first one where the combat_initiated test fails.

Each candidate is exported with `git archive` and the test is run from the export's own root (content seeds from the
cwd-relative data/content). Result classes: GOOD (1 passed), BAD (the combat_initiated >= 3 assertion), OTHER (anything else:
reported, and the search steps to a neighbouring commit instead of guessing)."""
import shutil
import subprocess
import sys

REPO = "/mnt/data/Working/rpg-based-simulation/.claude/worktrees/attack-path-trace"
S = "/tmp/claude-1000/-mnt-data-Working-rpg-based-simulation--claude-worktrees-lane-a-tactical-path-batch/c3c03123-6c20-4694-bb97-f41faaa98a72/scratchpad"
PY = "/mnt/data/Working/rpg-based-simulation/.venv/bin/python"
TEST = "tests/integration/campaigns/test_catalog_entity_spawn_wiring.py::test_real_campaign_episode_event_stream_is_plausible_not_degenerate"
GOOD_REF, BAD_REF = sys.argv[1], sys.argv[2]


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


commits = sh(["git", "-C", REPO, "rev-list", "--reverse", f"{GOOD_REF}..{BAD_REF}"]).stdout.split()
print(f"{len(commits)} commits after good {GOOD_REF}, up to bad {BAD_REF}", flush=True)
CACHE = {}


def classify(sha):
    if sha in CACHE:
        return CACHE[sha]
    d = f"{S}/bisect_export"
    shutil.rmtree(d, ignore_errors=True)
    shutil.os.makedirs(d)
    a = subprocess.Popen(["git", "-C", REPO, "archive", sha], stdout=subprocess.PIPE)
    subprocess.run(["tar", "-x", "-C", d], stdin=a.stdout, check=True)
    a.wait()
    r = sh([PY, "-m", "pytest", TEST, "-m", "slow", "-q", "-p", "no:cacheprovider"], cwd=d, timeout=900)
    out = r.stdout + r.stderr
    if "1 passed" in out:
        res = "GOOD"
    elif "combat_initiated" in out and "assert 0 >=" in out.replace("  ", " "):
        res = "BAD"
    elif "assert" in out and "combat_initiated" in out:
        res = "BAD"
    else:
        res = "OTHER"
    CACHE[sha] = res
    subj = sh(["git", "-C", REPO, "log", "-1", "--format=%h %ad %s", "--date=short", sha]).stdout.strip()[:110]
    print(f"{res:5} {subj}", flush=True)
    if res == "OTHER":
        print("      tail:", out.strip().splitlines()[-1][:160] if out.strip() else "(no output)", flush=True)
    return res


lo, hi = -1, len(commits) - 1  # commits[lo] is good (or the good ref), commits[hi] is bad
assert classify(commits[hi]) == "BAD", "bad ref is not bad"
while hi - lo > 1:
    mid = (lo + hi) // 2
    res = classify(commits[mid])
    if res == "OTHER":
        # step to the nearest classifiable neighbour, alternating outward
        for off in range(1, hi - lo):
            found = None
            for cand in (mid + off, mid - off):
                if lo < cand < hi and classify(commits[cand]) != "OTHER":
                    found, res, mid = cand, classify(commits[cand]), cand
                    break
            if found is not None:
                break
        else:
            print("no classifiable commit between; stopping", flush=True)
            break
    if res == "GOOD":
        lo = mid
    else:
        hi = mid
first_bad = commits[hi]
print("FIRST-BAD", sh(["git", "-C", REPO, "log", "-1", "--format=%H %ad %an %s", "--date=short", first_bad]).stdout.strip(), flush=True)
print("LAST-GOOD", commits[lo] if lo >= 0 else GOOD_REF, flush=True)
print("BISECT-DONE", flush=True)
