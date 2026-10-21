"""Step-1 measurement for TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH (read-only).
For each ISO week given, take the distinct session ids on committed run rows (`runs.jsonl`, any shard), count the tool
rows each session has anywhere (committed shards at the ref, plus every local worktree's data folder, tracked or not),
and for the sessions with none classify by transcript: project dir, cwd class of tool calls, and whether any project
hook ever reported through the transcript (hook_success attachment) -- the canary for 'project settings were loaded'.
usage: measure.py REF WEEK [WEEK...]   (CSV on stdout, summary on stderr)"""
import collections, csv, glob, json, os, re, subprocess, sys

REPO = "/data/vboxuser/Work/rpg-based-simulation"
REF, WEEKS = sys.argv[1], sys.argv[2:]
SID = re.compile(r'"session_id":\s*"([0-9a-f-]{36})"')


def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True, cwd=REPO).stdout


def committed_rows(kind, week):
    """Lines of every <kind>.jsonl shard of `week` at REF."""
    out = []
    for path in git("ls-tree", "-r", "--name-only", REF, f"agent-working/agent-monitoring/data/{week}/").split():
        if path.endswith(f"{kind}.jsonl"):
            out.extend(git("show", f"{REF}:{path}").splitlines())
    return out


def tool_rows_everywhere():
    counts, where = collections.Counter(), collections.defaultdict(set)
    for week_dir in ("*",):
        for line in git("grep", "-h", "-o", '"session_id":"[0-9a-f-]*"', REF, "--", "*tools.jsonl").splitlines():
            m = SID.search(line)
            if m:
                counts[m.group(1)] += 1
                where[m.group(1)].add("committed")
    pats = glob.glob(f"{REPO}/.claude/worktrees/*/agent-working/agent-monitoring/data/*/*tools.jsonl") + \
        glob.glob(f"{REPO}/agent-working/agent-monitoring/data/*/*tools.jsonl")
    for p in pats:
        for m in SID.finditer(open(p, errors="replace").read()):
            counts[m.group(1)] += 1
            where[m.group(1)].add("local-file")
    return counts, where


def transcript(sid):
    hits = glob.glob(os.path.expanduser(f"~/.claude/projects/*/{sid}.jsonl"))
    return hits[0] if hits else None


def classify_transcript(path):
    calls = collections.Counter()
    hook_events = collections.Counter()
    first = None
    for line in open(path, errors="replace"):
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        first = first or rec.get("timestamp")
        att = rec.get("attachment")
        if isinstance(att, dict) and att.get("type") == "hook_success":
            hook_events[att.get("hookEvent")] += 1
        msg = rec.get("message")
        if rec.get("type") == "assistant" and isinstance(msg, dict) and isinstance(msg.get("content"), list):
            n = sum(1 for c in msg["content"] if isinstance(c, dict) and c.get("type") == "tool_use")
            if n:
                c = (rec.get("cwd") or "").rstrip("/")
                if "/rpg-based-simulation" in c and "/worktrees/" in c or c.endswith("rpg-based-simulation"):
                    sub = re.sub(r".*/rpg-based-simulation/?(\.claude/worktrees/[^/]+)?/?", "", c)
                    calls["repo-subdir" if sub else "repo-root"] += n
                else:
                    calls["outside"] += n
    return calls, hook_events, first


writer = csv.writer(sys.stdout)
writer.writerow(["week", "session_id", "run_rows", "tool_rows", "where", "transcript", "project_dir", "calls_total",
                 "repo_root", "repo_subdir", "outside", "hook_success_events", "verdict"])
tool_counts, tool_where = tool_rows_everywhere()
tot = collections.Counter()
for week in WEEKS:
    runs = collections.Counter()
    for line in committed_rows("runs", week):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("session_id"):
            runs[r["session_id"]] += 1
        else:
            tot[(week, "run rows without session_id")] += 1
    tot[(week, "closing sessions")] = len(runs)
    for sid, n in sorted(runs.items()):
        rows = tool_counts.get(sid, 0)
        if rows:
            tot[(week, "has rows")] += 1
            writer.writerow([week, sid, n, rows, "+".join(sorted(tool_where[sid])), "", "", "", "", "", "", "", "has_rows"])
            continue
        tp = transcript(sid)
        if not tp:
            tot[(week, "no rows, no transcript on this host")] += 1
            writer.writerow([week, sid, n, 0, "", "", "", "", "", "", "", "", "no_transcript"])
            continue
        calls, hooks, _ = classify_transcript(tp)
        total = sum(calls.values())
        project = tp.split("/projects/")[1].split("/")[0]
        if total == 0:
            verdict = "no_tool_calls"
        elif calls["repo-root"] + calls["repo-subdir"] == 0:
            verdict = "outside_repo"
        elif not hooks:
            verdict = "repo_but_no_hook_ever_reported"
        else:
            verdict = "hooks_loaded_rows_missing"
        tot[(week, "no rows, transcript: " + verdict)] += 1
        writer.writerow([week, sid, n, 0, "", "yes", project, total, calls["repo-root"], calls["repo-subdir"], calls["outside"],
                         sum(hooks.values()), verdict])
for k, v in sorted(tot.items()):
    print(f"{k[0]}  {k[1]}: {v}", file=sys.stderr)
