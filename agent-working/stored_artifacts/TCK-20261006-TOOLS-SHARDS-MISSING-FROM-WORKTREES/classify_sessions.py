"""Classify every local Claude transcript since 2026-09-28 by the cwd of each tool call and by whether the session
wrote tools.jsonl rows (origin/main tree plus every local worktree's data folder, tracked or not).

Run: python classify_sessions.py > sessions.csv   (CSV on stdout, summary on stderr). Needs ~/.claude/projects. Rows are counted in `<week>/tools.jsonl` (the hook's unconsolidated file) and `<week>/<branch>.tools.jsonl`.
cwd classes per tool call: root (repo or worktree root), subdir (inside a repo/worktree), outside (not in the repo)."""
import collections, csv, datetime, glob, json, os, re, subprocess, sys

REPO = "/mnt/data/Working/rpg-based-simulation"
ALIAS = "/home/u24desktop/Working"  # symlink to /mnt/data/Working: both spellings appear in transcripts
CUT = datetime.datetime(2026, 9, 28).timestamp()
SID = re.compile(r'"session_id":"([0-9a-f-]{36})"')


def norm(cwd: str | None) -> str:
    cwd = (cwd or "").rstrip("/")
    return "/mnt/data/Working" + cwd[len(ALIAS):] if cwd.startswith(ALIAS) else cwd


def cwd_class(cwd: str | None) -> str:
    c = norm(cwd)
    if not c:
        return "unknown"
    if c == REPO or re.fullmatch(re.escape(REPO) + r"/\.claude/worktrees/[^/]+", c):
        return "root"
    if c.startswith(REPO + "/"):
        return "subdir"
    return "outside"


def tool_row_counts() -> collections.Counter:
    counts: collections.Counter = collections.Counter()
    out = subprocess.run(["git", "grep", "-h", "-o", '"session_id":"[0-9a-f-]*"', "origin/main", "--", "*tools.jsonl"],
                         capture_output=True, text=True, cwd=REPO).stdout
    counts.update(m.group(1) for m in SID.finditer(out))
    for p in glob.glob(f"{REPO}/.claude/worktrees/*/agent-working/agent-monitoring/data/*/*tools.jsonl") + \
            glob.glob(f"{REPO}/agent-working/agent-monitoring/data/*/*tools.jsonl"):
        counts.update(m.group(1) for m in SID.finditer(open(p, errors="replace").read()))
    return counts


def calls_by_class(path: str):
    by: collections.Counter = collections.Counter()
    first = None
    for line in open(path, errors="replace"):
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        first = first or rec.get("timestamp")
        msg = rec.get("message")
        if rec.get("type") == "assistant" and isinstance(msg, dict) and isinstance(msg.get("content"), list):
            n = sum(1 for c in msg["content"] if isinstance(c, dict) and c.get("type") == "tool_use")
            if n:
                by[cwd_class(rec.get("cwd"))] += n
    return by, first


rows_by_session = tool_row_counts()
out_rows = []
for p in glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")):
    if os.path.getmtime(p) < CUT:
        continue
    sid = os.path.basename(p)[:-6]
    by, first = calls_by_class(p)
    if sum(by.values()):
        out_rows.append([sid, first or "", p.split("/projects/")[1].split("/")[0], by["root"], by["subdir"], by["outside"],
                         by["unknown"], rows_by_session.get(sid, 0)])
w = csv.writer(sys.stdout)
w.writerow(["session_id", "first_ts", "project_dir", "calls_root", "calls_subdir", "calls_outside", "calls_unknown", "tools_rows"])
w.writerows(sorted(out_rows, key=lambda r: r[1]))
tot = collections.Counter()
for r in out_rows:
    key = "has rows" if r[7] else "NO rows"
    for name, n in zip(("root", "subdir", "outside", "unknown"), r[3:7]):
        tot[(name, key)] += n
sess = collections.Counter()
for r in out_rows:
    cls = "outside only" if r[3] + r[4] == 0 else "ever in a subdir" if r[4] else "root only"
    sess[(cls, "has rows" if r[7] else "NO rows")] += 1
print("sessions:", len(out_rows), dict(sess), file=sys.stderr)
print("tool calls by cwd class:", {f"{k[0]}/{k[1]}": v for k, v in sorted(tot.items())}, file=sys.stderr)
