"""One in-process process: RSS after import, after the first query, after warm queries, and top-5 parity of the
server's SQL path (tools/search_server.py lines 167-230, reproduced) against search_mcp._search. Run from a checkout
with the knowledge index, under the knowledge venv and a memory cap. Env: REPO (default cwd)."""
import sys, os, time, json, importlib.util
REPO = os.environ.get("REPO", os.getcwd())
sys.path.insert(0, REPO + "/tools")
def rss_mb():
    for l in open("/proc/self/status"):
        if l.startswith("VmRSS"): return int(l.split()[1])/1024
t0=time.time()
spec=importlib.util.spec_from_file_location("search_mcp",REPO + "/tools/search_mcp.py")
m=importlib.util.module_from_spec(spec); sys.modules["search_mcp"]=m; spec.loader.exec_module(m)
out={"index_db":str(m._DB_PATH),"rss_after_import_mb":round(rss_mb(),1),"import_s":round(time.time()-t0,2)}
q=["damage formula","how does goal interruption work","import linter contracts","working log append helper","regional trauma ecology"]
t=time.time(); r=m._search(q[0],top_k=5); out["first_query_s"]=round(time.time()-t,2)
out["rss_after_first_query_mb"]=round(rss_mb(),1)
t=time.time(); [m._search(x,top_k=5) for x in q]; out["five_warm_queries_s"]=round(time.time()-t,2)
out["rss_after_warm_mb"]=round(rss_mb(),1)
inproc={x:[(d["doc_id"],d["score"]) for d in m._search(x,top_k=5)] for x in q}
# server path: tools/search_server.py lines 167-230 reproduced verbatim (fastapi is absent from .venv-knowledge),
# reusing the already-loaded model/bm25 so one process holds one model
import sqlite3, sqlite_vec
ks=m._ks
def server_search(query, top_k):
    query_tokens = ks._tokenize(query)
    q_bytes = ks._serialize_f32(m._STATE.model.encode(query).tolist())
    con = sqlite3.connect(str(m._DB_PATH)); con.enable_load_extension(True); sqlite_vec.load(con); con.enable_load_extension(False)
    sql = """SELECT kd.rowid, kd.doc_id, kd.path, kd.text, kd.heading, kd.section, distance
             FROM knowledge_vec kv JOIN knowledge_docs kd ON kd.rowid = kv.rowid
             WHERE kv.embedding MATCH ? AND k = ? ORDER BY distance"""
    rows = con.execute(sql, (q_bytes, min(top_k * 4, 50))).fetchall(); con.close()
    res=[]
    for row in rows[:top_k]:
        rowid, doc_id, path, text, heading, section, distance = row
        sem = max(0.0, 1.0 - float(distance)); kw = 0.0
        scores = m._STATE.bm25.get_scores(query_tokens)
        try: kw = float(scores[m._STATE.doc_ids.index(doc_id)]) / 10.0
        except ValueError: kw = 0.0
        tb, hb, cb = ks._compute_boosts(query_tokens, doc_id, heading, text)
        res.append((doc_id, round(ks._hybrid_score(sem, kw, tb, hb, cb), 4)))
    res.sort(key=lambda r: r[1], reverse=True); return res
par={}
for x in q:
    srv=server_search(x,5)
    par[x]={"inproc":[a for a,_ in inproc[x]],"server":[a for a,_ in srv],
            "same_set":set(a for a,_ in inproc[x])==set(a for a,_ in srv),
            "same_order":[a for a,_ in inproc[x]]==[a for a,_ in srv],
            "same_scores":[b for _,b in inproc[x]]==[b for _,b in srv]}
out["parity"]=par
print(json.dumps(out,indent=1))
