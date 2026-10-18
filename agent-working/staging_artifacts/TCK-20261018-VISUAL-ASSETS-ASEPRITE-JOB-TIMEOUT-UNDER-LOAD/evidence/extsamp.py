import time, subprocess, sys
out=open(sys.argv[1],"w",buffering=1); last=time.monotonic(); lastw=time.time()
def steal():
    f=open("/proc/stat").readline().split(); return f[8]  # steal jiffies
while True:
    time.sleep(1.0)
    n=time.monotonic(); w=time.time(); gap=n-last
    if gap>1.5 or w-lastw>1.5:
        out.write(f"{time.strftime('%H:%M:%S')} GAP mono {gap:.1f}s wall {w-lastw:.1f}s steal={steal()} load {open('/proc/loadavg').read().split()[0]}\n")
    # pytest state each 5 s
    if int(w)%5==0:
        ps=subprocess.run("ps -eo pid,stat,wchan:16,pcpu,etimes,args --no-headers | grep -E 'pytest|aseprite -b' | grep -v grep | cut -c1-120",shell=True,capture_output=True,text=True).stdout
        out.write(f"{time.strftime('%H:%M:%S')} load {open('/proc/loadavg').read().split()[0]} steal={steal()}\n{ps}")
    last=n; lastw=w
