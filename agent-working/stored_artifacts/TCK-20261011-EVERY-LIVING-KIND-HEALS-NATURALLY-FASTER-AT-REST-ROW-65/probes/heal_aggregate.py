import json, glob, statistics as st
from collections import defaultdict
D='/tmp/claude-1000/scratch/heal'
R=defaultdict(dict)
for f in glob.glob(D+'/*.json'):
    a,rest=f.split('/')[-1][:-5].split('_',1); w,seed=rest.rsplit('_',1); R[(w,int(seed))][a]=json.load(open(f))
def dsum(r,kind=None):
    out=defaultdict(int)
    for sp,c in r['deaths'].items():
        for cause,n in c.items(): out[cause]+=n
    return out
for w in sorted({k[0] for k in R}):
    seeds=[s for (ww,s),v in sorted(R.items()) if ww==w and len(v)==2]
    print('==',w,'seeds',seeds)
    def stat(name,fn):
        d=[fn(R[(w,s)]['new'])-fn(R[(w,s)]['base']) for s in seeds]
        b=st.mean(fn(R[(w,s)]['base']) for s in seeds); n=st.mean(fn(R[(w,s)]['new']) for s in seeds)
        se=(st.stdev(d)/len(d)**.5) if len(d)>1 else 0
        print(f'{name:38s} {b:9.3f} -> {n:9.3f}  d={st.mean(d):+.3f} SE {se:.3f}')
    stat('mean hp ratio (all alive, /100t)',lambda r:r['mean_hp_ratio'])
    stat('mean hp ratio of wounded',lambda r:r['mean_wounded_hp_ratio'])
    stat('wounded sample share',lambda r:r['wounded_samples']/max(1,r['alive_samples']))
    stat('alive at 5000',lambda r:sum(r['alive'].values()))
    stat('total deaths',lambda r:sum(dsum(r).values()))
    causes=sorted({c for s in seeds for a in ('base','new') for c in dsum(R[(w,s)][a])})
    for c in causes: stat('deaths '+c,lambda r,c=c:dsum(r).get(c,0))
    sps=sorted({sp for s in seeds for a in ('base','new') for sp in R[(w,s)][a]['attack_starts']})
    stat('attack starts (all)',lambda r:sum(r['attack_starts'].values()))
    for sp in sps: stat('attack starts '+sp,lambda r,sp=sp:r['attack_starts'].get(sp,0))
    for sp in sorted({sp for s in seeds for a in ('base','new') for sp in R[(w,s)][a]['deaths']}): stat('deaths of '+sp,lambda r,sp=sp:sum(r['deaths'].get(sp,{}).values()))
