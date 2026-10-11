import json,glob,collections,sys
D=[]
for f in sorted(glob.glob('/tmp/claude-1000/scratch27/trace2/*.out')):
    for l in open(f):
        if l.startswith('TR2 '):
            r=json.loads(l[4:])
            for d in r['deaths']: d.update(arm=r['label'],world=r['world'],seed=r['seed']); D.append(d)
print('runs',len({(d['arm'],d['world'],d['seed']) for d in D}),'deaths',len(D))
for w,g in (('frontier_living_world','heroes_other'),('urban_political','town_guards_scouts')):
    print('\n###',w,g)
    for arm in ('arm1','arm6','arm7'):
        S=[d for d in D if d['arm']==arm and d['world']==w and d['group']==g]
        print(arm,len(S),dict(collections.Counter(d['cause'] for d in S)))
    for arm in ('arm1','arm6','arm7'):
        S=[d for d in D if d['arm']==arm and d['world']==w and d['group']==g and d['cause']!='COMBAT']
        # pattern summary of victims
        print('\n--',arm,'non-combat victims',len(S))
        pat=collections.Counter()
        for d in S:
            ring=d['ring']; last=ring[-1] if ring else {}
            eats=d['eats']
            acc=sum(1 for e in eats if e[3]); rej=sum(1 for e in eats if not e[3])
            pat[(d['ever_ate'], acc>0, rej>0)]+=1
        print('(ever_ate, accepted_eat_in_last15, rejected_eat) ->',dict(pat))
        print('gold at death',sorted(d['gold'] for d in S))
        wk=collections.Counter(); 
        for d in S:
            for r in d['ring'][-10:]: wk[(r['wk'],r['pl'][:50])]+=1
        print('last-10-decision payload mix:',wk.most_common(8))
        dinn=[d['ring'][-1]['d_inn'] for d in S if d['ring']]; print('d_inn at last decision',dinn)
