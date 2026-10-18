"""Per-phase timing of one sandboxed Aseprite job, N times. Usage: probe.py N"""
import subprocess, sys, time, tempfile, pathlib
from visual_assets.drawing import config
N = int(sys.argv[1])
def t(cmd, **kw):
    s = time.monotonic(); p = subprocess.run(cmd, capture_output=True, stdin=subprocess.DEVNULL, timeout=60, **kw); return time.monotonic()-s, p.returncode
BW = ["bwrap","--unshare-all","--die-with-parent","--new-session","--clearenv","--setenv","HOME","/home/sandbox","--setenv","PATH","/usr/bin",
 "--ro-bind","/usr","/usr","--symlink","usr/lib","/lib","--symlink","usr/lib64","/lib64","--symlink","usr/bin","/bin",
 "--ro-bind","/etc/ld.so.cache","/etc/ld.so.cache","--proc","/proc","--dev","/dev","--tmpfs","/tmp","--tmpfs","/home/sandbox"]
rows=[]
for i in range(N):
    with tempfile.TemporaryDirectory() as d:
        a,_ = t(BW+["/usr/bin/true"])                       # sandbox start only
        b,_ = t(BW+["--bind",d,"/job","--chdir","/job",config.ASEPRITE,"-b","--version"])  # + aseprite start
        c,rc = t(BW+["--bind",d,"/job","--chdir","/job",config.ASEPRITE,"-b","--script-param","x=1","--batch"])  # + trivial batch
        rows.append((a,b,c))
        print(f"{i:3d} sandbox={a:.3f} +aseprite_version={b:.3f} +batch={c:.3f}", flush=True)
for n,k in enumerate(("sandbox","aseprite --version","batch")):
    v=sorted(r[n] for r in rows); print(k,"min %.3f med %.3f max %.3f"%(v[0],v[len(v)//2],v[-1]))
