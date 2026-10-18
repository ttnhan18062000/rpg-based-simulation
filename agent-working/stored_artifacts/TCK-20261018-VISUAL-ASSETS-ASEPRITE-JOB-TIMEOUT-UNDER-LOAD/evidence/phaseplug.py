"""pytest plugin: time every sandbox.bwrap call; if one runs >4 s, sample the process tree states + mem pressure every 2 s."""
import os, threading, time, subprocess as sp
from visual_assets.drawing.backend import sandbox
LOG = open(os.environ["PHASELOG"], "a", buffering=1)
orig_popen = sp.Popen
def tree_states(pid):
    out=[]
    try:
        for l in sp.run(["ps","-o","pid,stat,wchan:20,pcpu,args","--ppid" ,str(pid),"-p",str(pid)],capture_output=True,text=True).stdout.splitlines()[1:]:
            out.append(l.strip()[:110])
        for l in sp.run(["ps","-eo","pid,ppid,stat,wchan:20,pcpu,args","--no-headers"],capture_output=True,text=True).stdout.splitlines():
            if "aseprite -b" in l or "bwrap --unshare-all --die" in l: out.append(l.strip()[:130])
    except Exception as e: out.append(repr(e))
    return out
def psi():
    try: return open("/proc/pressure/memory").read().replace("\n"," | ")+open("/proc/pressure/cpu").read().replace("\n"," | ")
    except Exception: return "n/a"
real = sandbox.bwrap
def timed(job, argv):
    t0=time.monotonic(); w0=time.time(); done=threading.Event()
    def watch():
        n=0
        while not done.wait(2.0):
            n+=1
            if time.monotonic()-t0>4:
                LOG.write(f"  +{time.monotonic()-t0:6.1f}s mono, +{time.time()-w0:6.1f}s wall, load {open('/proc/loadavg').read().split()[0]} PSI {psi()}\n")
                for s in tree_states(os.getpid()): LOG.write("     "+s+"\n")
    th=threading.Thread(target=watch,daemon=True); th.start()
    try: return real(job, argv)
    finally:
        done.set(); LOG.write(f"bwrap {argv[0]} took mono {time.monotonic()-t0:.3f}s wall {time.time()-w0:.3f}s load {open('/proc/loadavg').read().split()[0]}\n")
sandbox.bwrap = timed
