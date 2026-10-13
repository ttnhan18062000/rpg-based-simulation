"""Acceptance gate for TCK-20261012-SEARCH-MCP-SHARED-MODEL: N stdio MCP sessions against tools/search_mcp.py.

Usage (from a checkout that has the knowledge index; run under a memory cap, one run at a time):
  systemd-run --user --scope -p MemoryMax=2500M -p MemorySwapMax=0 $KNOWLEDGE_PY sessions.py after 9
  systemd-run --user --scope -p MemoryMax=2500M -p MemorySwapMax=0 $KNOWLEDGE_PY sessions.py before 2
`after` = RPG_SEARCH_SHARED=1 (first session spawns the shared server, in a tmp XDG_RUNTIME_DIR); `before` =
RPG_SEARCH_SHARED=0 (every session holds its own model). Records per-session RSS/PSS, the server's, the total,
MemAvailable, how many sessions held an in-process model (RSS above 300 MB), first-query latency, and the answers to
five fixed queries for parity (diff `parity_answers` between an `after` and a `before` run: identical = pass).
Env: REPO (checkout, default cwd), KNOWLEDGE_PY (interpreter, default this one), OUT (output dir, default cwd)."""
import asyncio, json, os, signal, subprocess, sys, tempfile, time
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REPO = Path(os.environ.get("REPO", os.getcwd()))
PY = os.environ.get("KNOWLEDGE_PY", sys.executable)
OUT = Path(os.environ.get("OUT", os.getcwd()))
QUERIES = ["damage formula", "how does goal interruption work", "import linter contracts", "working log append helper", "regional trauma ecology"]
mode = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 9
runtime = tempfile.mkdtemp(prefix="rpgrun-", dir=tempfile.gettempdir()); os.chmod(runtime, 0o700)

def kb(path, key):
    try:
        for l in open(path):
            if l.startswith(key): return int(l.split()[1]) / 1024
    except OSError: pass
    return 0.0
def mem(pid): return {"rss": round(kb(f"/proc/{pid}/status", "VmRSS"), 1), "pss": round(kb(f"/proc/{pid}/smaps_rollup", "Pss:"), 1)}
def children(pattern):
    out = []
    for p in os.listdir("/proc"):
        if p.isdigit():
            try:
                ppid = int(open(f"/proc/{p}/stat").read().rsplit(")", 1)[1].split()[1])
                if ppid == os.getpid() and pattern in open(f"/proc/{p}/cmdline").read(): out.append(int(p))
            except (OSError, IndexError, ValueError): pass
    return out
def server_pid():
    import glob
    for f in glob.glob(f"{runtime}/rpg-search/*/server.json"):
        return json.load(open(f))["pid"]
def avail(): return round(kb("/proc/meminfo", "MemAvailable"), 0)

env = dict(os.environ, XDG_RUNTIME_DIR=runtime, RPG_SEARCH_SHARED="0" if mode in ("before",) else "1", HF_HUB_OFFLINE="1")
async def session(i, results, ready, release):
    params = StdioServerParameters(command=PY, args=[str(REPO / "tools/search_mcp.py")], env=env)
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as cs:
            await cs.initialize()
            t = time.time(); res = await cs.call_tool("search_docs", {"query": QUERIES[0], "top_k": 5}); first = time.time() - t
            results[i] = {"first_query_s": round(first, 2)}
            if i == 0:
                ans = {}
                for q in QUERIES:
                    rr = await cs.call_tool("search_docs", {"query": q, "top_k": 5})
                    ans[q] = [c.text for c in rr.content if hasattr(c, "text")]
                results["parity_answers"] = ans
            ready.append(i)
            await release.wait()

async def main():
    results, ready, release = {}, [], asyncio.Event()
    out = {"mode": mode, "sessions": n, "avail_before_mb": avail()}
    tasks = []
    async def wait_ready(k):
        while len(ready) < k: await asyncio.sleep(0.1)
    if mode == "after":
        tasks.append(asyncio.create_task(session(0, results, ready, release))); await wait_ready(1)   # cold spawn
        t = time.time()
        tasks += [asyncio.create_task(session(i, results, ready, release)) for i in range(1, n)]; await wait_ready(n)
        out["rest_wall_s"] = round(time.time() - t, 2)
    else:
        t = time.time(); tasks = [asyncio.create_task(session(i, results, ready, release)) for i in range(n)]; await wait_ready(n)
        out["wall_s"] = round(time.time() - t, 2)
    await asyncio.sleep(1)
    procs = children("search_mcp.py"); per = [mem(p) for p in procs]
    out["session_procs"] = len(procs)
    out["sessions_holding_in_process_model(rss>300MB)"] = sum(1 for m in per if m["rss"] > 300)
    out["session_rss_mb"] = sorted(m["rss"] for m in per); out["session_pss_mb"] = sorted(m["pss"] for m in per)
    sp = server_pid(); out["server_pid"] = sp
    srv = mem(sp) if sp else {"rss": 0, "pss": 0}; out["server"] = srv
    out["total_rss_mb"] = round(sum(m["rss"] for m in per) + srv["rss"], 1)
    out["total_pss_mb"] = round(sum(m["pss"] for m in per) + srv["pss"], 1)
    out["avail_after_mb"] = avail()
    out["first_query_s"] = sorted(v["first_query_s"] for k, v in results.items() if k != "parity_answers")
    out["parity_answers"] = results.get("parity_answers")
    release.set(); await asyncio.gather(*tasks, return_exceptions=True)
    if sp:
        try: os.kill(sp, signal.SIGTERM)
        except OSError: pass
    json.dump(out, open(OUT / f"sessions_{mode}_{n}.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "parity_answers"}, indent=1))
asyncio.run(main())
