"""Finding 4: for the runs of one week at a ref, why is `duration_source` unknown although the session has tool rows?
Replays hand_closure_time.resolve() offline with ALL rows known now (committed at the ref plus every local worktree and main
checkout data folder), so a run that was unknown at closure time because its rows were not yet on that disk shows up as
'rows exist now, none at closure' only if they predate the closure. Read-only.
usage: unknown_durations.py REF WEEK"""
import collections, glob, json, subprocess, sys
sys.path.insert(0, "tools/agent-monitoring")
import hand_closure_time as hct  # noqa: E402

REPO = "/data/vboxuser/Work/rpg-based-simulation"
REF, WEEK = sys.argv[1], sys.argv[2]


def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True, cwd=REPO).stdout


def lines_at_ref(kind):
    out = []
    for p in git("ls-tree", "-r", "--name-only", REF, "agent-working/agent-monitoring/data/").split():
        if p.endswith(f"{kind}.jsonl"):
            out.extend(git("show", f"{REF}:{p}").splitlines())
    return out


def parse(lines):
    for l in lines:
        try:
            r = json.loads(l)
        except ValueError:
            continue
        if isinstance(r, dict):
            yield r


tools = list(parse(lines_at_ref("tools")))
for p in glob.glob(f"{REPO}/.claude/worktrees/*/agent-working/agent-monitoring/data/*/*tools.jsonl") + glob.glob(f"{REPO}/agent-working/agent-monitoring/data/*/*tools.jsonl"):
    tools.extend(parse(open(p, errors="replace").read().splitlines()))
seen, uniq = set(), []
for r in tools:  # the same row can be in the ref and on disk
    k = (r.get("session_id"), r.get("ts"), r.get("tool"), r.get("tool_use_id"))
    if k not in seen and hct._parse(r.get("ts")):
        seen.add(k)
        uniq.append(r)
by_sid = collections.defaultdict(list)
for r in uniq:
    by_sid[r.get("session_id")].append(r)
runs_all = list(parse(lines_at_ref("runs")))
week_runs = [r for r in parse(lines_at_ref("runs")) if str(r.get("start_ts", ""))[:10] >= "0" and r.get("_w") is None]
wk_lines = []
for p in git("ls-tree", "-r", "--name-only", REF, f"agent-working/agent-monitoring/data/{WEEK}/").split():
    if p.endswith("runs.jsonl"):
        wk_lines.extend(git("show", f"{REF}:{p}").splitlines())
week_runs = list(parse(wk_lines))
res = collections.Counter()
detail = []
for r in week_runs:
    sid, src = r.get("session_id"), r.get("duration_source")
    res[("duration_source", src)] += 1
    if src != "unknown":
        continue
    rows_all = by_sid.get(sid, [])
    unattributed = [x for x in rows_all if x.get("run_id") is None]
    end = r["end_ts"]
    if not rows_all:
        why = "session has no tool rows anywhere"
    elif not unattributed:
        why = "all the session's rows carry a run_id (sidecar attribution)"
    else:
        before = [x for x in unattributed if x["ts"] <= end]
        prior = [e for e in (q["end_ts"] for q in runs_all if q.get("execution_mode") == "hand" and q.get("session_id") == sid
                             and hct._parse(q.get("end_ts")) and hct._parse(end) and hct._parse(q["end_ts"]) < hct._parse(end))]
        if not before:
            why = "session has unattributed rows, none before this closure"
        else:
            claimed, peers = hct.claim_rows(sorted(before, key=lambda x: x["ts"]), end, prior)
            if len(claimed) >= hct.MIN_CLAIMED_ROWS:
                why = "replay derives tool_activity now (rows were not on the closer's disk at closure time)"
            elif prior and peers:
                why = f"rows after the previous closure < {hct.MIN_CLAIMED_ROWS} (back-to-back closure)"
            else:
                why = f"activity block has < {hct.MIN_CLAIMED_ROWS} rows (no earlier closure in it)"
    res[("unknown because", why)] += 1
    detail.append((r["run_id"], sid[:8] if sid else None, len(rows_all), why))
for k, v in sorted(res.items(), key=lambda kv: (kv[0][0], -kv[1])):
    print(k[0], "|", k[1], "|", v)
print("--")
for d in detail:
    print(*d, sep=" | ")
print("--")
for sid in sorted({d[1] for d in detail if d[1] and d[2]}):
    full = next(s for s in by_sid if s and s.startswith(sid))
    rows = by_sid[full]
    print("session", sid, "rows", len(rows), "unattributed", sum(1 for x in rows if x.get("run_id") is None), "attributed", sum(1 for x in rows if x.get("run_id") is not None))
print("--")
print("gap (s) from the last unattributed row at or before end_ts to end_ts, for the '< 3 rows' classes; threshold", hct.PAUSE_THRESHOLD_SECONDS)
gaps = collections.Counter()
for r in week_runs:
    if r.get("duration_source") != "unknown" or not r.get("session_id"):
        continue
    un = sorted((x for x in by_sid.get(r["session_id"], []) if x.get("run_id") is None and x["ts"] <= r["end_ts"]), key=lambda x: x["ts"])
    if not un:
        continue
    gap = (hct._parse(r["end_ts"]) - hct._parse(un[-1]["ts"])).total_seconds()
    gaps["gap > threshold (closure after a pause)" if gap > hct.PAUSE_THRESHOLD_SECONDS else "gap <= threshold"] += 1
print(dict(gaps))
