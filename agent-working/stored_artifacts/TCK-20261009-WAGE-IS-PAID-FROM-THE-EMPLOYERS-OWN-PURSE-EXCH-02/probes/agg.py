import json,glob,collections,statistics as st,sys
rows=[]
for f in sorted(glob.glob('out/arm*.out')):
    for l in open(f):
        if l.startswith('CH '): rows.append(json.loads(l[3:]))
def ms(v): v=[x for x in v if x is not None]; return f"{st.mean(v):.1f}({st.pstdev(v):.1f})" if v else "-"
arms=sorted({r['label'] for r in rows}); worlds=['crowded_frontier','frontier_living_world','urban_political']
print("runs",collections.Counter((r['label']) for r in rows))
for w in worlds:
    print("\n==",w)
    for a in arms:
        rs=[r for r in rows if r['label']==a and r['world']==w]
        if not rs: continue
        al=lambda t:[r['alive'].get(str(t)) for r in rs]
        dead=collections.Counter(); 
        for r in rs: dead.update(r['deaths_by_reason'])
        print(f"{a} n={len(rs)} alive@1000 {ms(al(1000))} @2500 {ms(al(2500))} @5000 {ms(al(5000))} deaths/run {{{', '.join(f'{k}:{v/len(rs):.1f}' for k,v in sorted(dead.items()))}}} taxpoor {ms([r['tax_poor_total'] for r in rs])} payers {ms([r['tax_poor_payers'] for r in rs])} sales {ms([r['sales'] for r in rs])} s>meal {ms([r['sales_then_meal'] for r in rs])}")
        gs=collections.defaultdict(lambda: collections.defaultdict(list))
        for r in rs:
            for g,v in r['groups'].items():
                gs[g]['n'].append(v['n']); gs[g]['a1000'].append(v['alive_at'].get('1000',0)); gs[g]['a2500'].append(v['alive_at'].get('2500',0)); gs[g]['a5000'].append(v['alive_at'].get('5000',0)); gs[g]['ate'].append(v['ever_ate']); gs[g]['star'].append(v['dead'].get('STARVATION',0)); gs[g]['hung'].append(v['mean_hunger_end'])
        for g,d in sorted(gs.items()):
            print(f"    {g:20s} n {ms(d['n'])} alive 1000/2500/5000 {ms(d['a1000'])}/{ms(d['a2500'])}/{ms(d['a5000'])} starved {ms(d['star'])} ever-ate {ms(d['ate'])} hunger-end {ms(d['hung'])}")
