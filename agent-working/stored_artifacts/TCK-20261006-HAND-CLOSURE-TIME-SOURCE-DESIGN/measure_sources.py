# Run from the repo root at origin/main 7ddcd4526: python measure_sources.py out.json
# Reads agent-working/agent-monitoring/data/2026-W40|W41 hand closures; prints coverage per source.
import json,glob,subprocess,os,collections,sys
from datetime import datetime
D="agent-working/agent-monitoring/data"
def ts(s): return datetime.fromisoformat(s.replace("Z","+00:00"))
GAP=1800
runs=[]
for wk in ["2026-W40","2026-W41"]:
    for f in sorted(glob.glob(f"{D}/{wk}/*.runs.jsonl")):
        shard=os.path.basename(f)[:-len(".runs.jsonl")]
        for l in open(f):
            r=json.loads(l)
            if r.get("execution_mode")=="hand": r["shard"]=shard; r["wk"]=wk; runs.append(r)
tools={}
def load_tools(shard,wk):
    k=(shard,wk)
    if k not in tools:
        rows=[]
        p=f"{D}/{wk}/{shard}.tools.jsonl"
        if os.path.exists(p): rows=[json.loads(l) for l in open(p)]
        # also other week's file
        for w2 in ["2026-W40","2026-W41"]:
            p2=f"{D}/{w2}/{shard}.tools.jsonl"
            if w2!=wk and os.path.exists(p2): rows+=[json.loads(l) for l in open(p2)]
        rows=sorted(rows,key=lambda r:r["ts"])
        tools[k]=rows
    return tools[k]
# git: ticket id -> commits across all refs
def git_commits(tid):
    out=subprocess.run(["git","log","--all","--format=%H|%aI|%s","--grep",tid,"-F"],capture_output=True,text=True).stdout.strip().splitlines()
    return [(l.split("|")[1],l.split("|",2)[2]) for l in out if l]
res=[]
byshard=collections.defaultdict(list)
for r in runs: byshard[(r["shard"],r["wk"])].append(r)
for r in runs:
    e=ts(r["end_ts"])
    declared = r.get("duration_s",0)>0
    rows=load_tools(r["shard"],r["wk"])
    prior=[x for x in rows if ts(x["ts"])<=e]
    # contiguous activity block ending at e
    block=[]
    last=e
    for x in reversed(prior):
        t=ts(x["ts"])
        if (last-t).total_seconds()>GAP: break
        block.append(x); last=t
    A=None
    if block:
        A=int((e-ts(block[-1]["ts"])).total_seconds())
    sess=len({x["session_id"] for x in block})
    # concurrent hand closures in the same shard whose end is within GAP of this one
    conc=sum(1 for o in byshard[(r["shard"],r["wk"])] if abs((ts(o["end_ts"])-e).total_seconds())<=GAP)
    g=git_commits(r["ticket_id"])
    B=None;gn=len(g)
    if g:
        tt=sorted(ts(a) for a,_ in g); B=int((tt[-1]-tt[0]).total_seconds())
    res.append(dict(run_id=r["run_id"],wk=r["wk"],shard=r["shard"],declared=declared,dur=r.get("duration_s"),A=A,A_rows=len(block),A_sessions=sess,conc=conc,B=B,B_commits=gn,tools_rows=len(rows)))
json.dump(res,open(sys.argv[1],"w"))
n=len(res)
for wk in ["2026-W40","2026-W41",None]:
    s=[x for x in res if wk is None or x["wk"]==wk]
    print(wk,"n",len(s),"C declared",sum(x["declared"] for x in s),"A dated",sum(x["A"] is not None for x in s),"B dated",sum(x["B"] is not None for x in s),"B>=2 commits",sum(x["B_commits"]>=2 for x in s),"A or B",sum(x["A"] is not None or x["B"] is not None for x in s),"none",sum(not x["declared"] and x["A"] is None and x["B"] is None for x in s),"A conc>1",sum(x["A"] is not None and x["conc"]>1 for x in s),"A multi-session",sum(x["A_sessions"]>1 for x in s),"shard has tools",sum(x["tools_rows"]>0 for x in s))

# --- B refinement (git span) used for the design table: exclude the squash-merge commit
# (subject ends "(#N)"), start at the commit that added the ticket under inprogress/ when found,
# else at the first commit citing the ticket ID.
import re
for x in res:
    tid = x["run_id"]
    cs = subprocess.run(["git","log","--all","--format=%aI|%s","-F","--grep",tid],capture_output=True,text=True).stdout.strip().splitlines()
    cs = [(datetime.fromisoformat(l.split("|",1)[0]), l.split("|",1)[1]) for l in cs if l]
    work = [c for c in cs if not re.search(r"\(#\d+\)\s*$", c[1])]
    ip = subprocess.run(["git","log","--all","--diff-filter=AR","--format=%aI","--",f"agent-working/tickets/inprogress/{tid}.md"],capture_output=True,text=True).stdout.split()
    x["B2"] = None; x["inprogress_entry"] = bool(ip)
    if work:
        end = max(c[0] for c in work)
        start = min(datetime.fromisoformat(i) for i in ip) if ip else min(c[0] for c in work)
        x["B2"] = max(0, int((end-start).total_seconds()))
json.dump(res, open(sys.argv[1], "w"))
print("B2 dated", sum(x["B2"] is not None for x in res), "inprogress entry found", sum(x["inprogress_entry"] for x in res))
