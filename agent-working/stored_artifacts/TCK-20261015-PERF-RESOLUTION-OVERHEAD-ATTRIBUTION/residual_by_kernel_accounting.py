"""Classifier for TCK-20261015-PERF-RESOLUTION-OVERHEAD-ATTRIBUTION (reproduction script, not a maintained tool).

Reads src/engine/pipeline.py as it was at the profiled commit (git show <sha>:src/engine/pipeline.py > file) and py-spy folded stacks (profile.folded).
Replays the KERNEL accounting: a timed block runs from the latest `t_start = perf_counter_ns()` line to the next `costs[... t_start]` line, so a re-assigned
t_start loses the earlier part, as at runtime. Prints, per folded file, the share of _phase_resolution samples that fall outside every counted block
(the residual) and its top call sites. Usage: python3 residual_by_kernel_accounting.py <pipeline.py> <profile.folded> ...  (python3 3.13, stdlib only; ran 2026-10-16).
"""
import re,sys,collections
pipe=open(sys.argv[1]).read().splitlines()
# timed block = line of `t_start = time.perf_counter_ns()` .. line of next `costs[...] = ... t_start`
blocks=[];start=None
for n,l in enumerate(pipe,1):
    if 't_start = time.perf_counter_ns()' in l: start=n
    if start and re.search(r'costs\[.*t_start',l): blocks.append((start,n)); start=None
def timed(line): return any(a<=line<=b for a,b in blocks)
for path in sys.argv[2:]:
    tot=res=timed_n=0; resid=collections.Counter(); outside=0; selfs=collections.Counter()
    for l in open(path):
        if l.startswith('#') or not l.strip(): continue
        stack,_,cnt=l.rstrip().rpartition(' '); cnt=int(cnt); tot+=cnt
        frames=stack.split(';')
        names=[f.split(' (')[0] for f in frames]
        if '_phase_resolution' not in names: continue
        res+=cnt
        ref=[f for f in frames if f.startswith('refine (')]
        if ref:
            line=int(ref[0].rsplit(':',1)[1].rstrip(')'))
            if timed(line): timed_n+=cnt; continue
        # residual: key by leaf-ish: frames after _phase_resolution
        i=names.index('_phase_resolution'); tail=frames[i+1:]
        resid[';'.join(tail[:3]) if tail else '(self _phase_resolution)']+=cnt
    r=res-timed_n
    print(f"== {path}\n total={tot} in_resolution={res} timed={timed_n} residual={r} ({100*r/max(res,1):.0f}% of resolution)")
    for k,v in resid.most_common(8): print(f"   {v:5d} {100*v/max(r,1):4.0f}%  {k[:150]}")
