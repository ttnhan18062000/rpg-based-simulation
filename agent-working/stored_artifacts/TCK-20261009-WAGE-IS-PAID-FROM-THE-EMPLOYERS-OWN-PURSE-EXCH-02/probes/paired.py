import json,glob,statistics as st,collections
R={}
for f in glob.glob('/tmp/claude-1000/scratch27/out/arm*.out'):
    for l in open(f):
        if l.startswith('CH '):
            r=json.loads(l[3:]); R[(r['label'],r['world'],r['seed'])]=r
A,B='arm1','arm6'
def ms(v): return f"{st.mean(v):.1f}({st.pstdev(v):.1f})"
def line(name,va,vb):
    d=[b-a for a,b in zip(va,vb)]
    se=st.pstdev(d)/len(d)**.5 if len(d)>1 else 0
    flag=' **>2SE**' if se>0 and abs(st.mean(d))>2*se else ''
    return f"  {name:34s} {A} {ms(va):>11s}  {B} {ms(vb):>11s}  paired diff {st.mean(d):+.1f} SE {se:.1f}{flag}"
for w in ('crowded_frontier','frontier_living_world','urban_political'):
    seeds=[s for s in range(42,47) if (A,w,s) in R and (B,w,s) in R]
    print(f"\n== {w}  seeds {seeds}")
    if not seeds: continue
    for t in ('1000','2500','5000'):
        print(line(f'alive total @{t}',[R[(A,w,s)]['alive'][t] for s in seeds],[R[(B,w,s)]['alive'][t] for s in seeds]))
    groups=sorted({g for s in seeds for x in (A,B) for g in R[(x,w,s)]['groups']})
    for g in groups:
        for t in ('1000','2500','5000'):
            va=[R[(A,w,s)]['groups'].get(g,{}).get('alive_at',{}).get(t,0) for s in seeds]; vb=[R[(B,w,s)]['groups'].get(g,{}).get('alive_at',{}).get(t,0) for s in seeds]
            if t=='5000' or any(va) or any(vb): print(line(f'{g} alive @{t}',va,vb))
        print(line(f'{g} starved',[R[(A,w,s)]['groups'].get(g,{}).get('dead',{}).get('STARVATION',0) for s in seeds],[R[(B,w,s)]['groups'].get(g,{}).get('dead',{}).get('STARVATION',0) for s in seeds]))
        print(line(f'{g} ever-ate',[R[(A,w,s)]['groups'].get(g,{}).get('ever_ate',0) for s in seeds],[R[(B,w,s)]['groups'].get(g,{}).get('ever_ate',0) for s in seeds]))
    print(line('tax paid by the poor (gold)',[R[(A,w,s)]['tax_poor_total'] for s in seeds],[R[(B,w,s)]['tax_poor_total'] for s in seeds]))
    dA=collections.Counter(); dB=collections.Counter()
    for s in seeds: dA.update(R[(A,w,s)]['deaths_by_reason']); dB.update(R[(B,w,s)]['deaths_by_reason'])
    print('  deaths/run',A,{k:round(v/len(seeds),1) for k,v in sorted(dA.items())}); print('  deaths/run',B,{k:round(v/len(seeds),1) for k,v in sorted(dB.items())})
