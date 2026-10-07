import json,sys
b=json.load(open("/tmp/claude-1000/-mnt-data-Working-rpg-based-simulation/3f65a0a8-5b41-4704-82d5-c64a0d15d761/scratchpad/before.json"));a=json.load(open("/tmp/claude-1000/-mnt-data-Working-rpg-based-simulation/3f65a0a8-5b41-4704-82d5-c64a0d15d761/scratchpad/after.json"))
print("flips",[ (k,b[k],a[k]) for k in a if a[k]!=b[k]])
seen=set();n=0
for k,v in sorted(a.items()):
    p,e=k.split('|'); x,y=p.split('>')
    if e!='0' or (y,x) in seen: continue
    r=a[f"{y}>{x}|0"]
    if v!=r: seen.add((x,y)); n+=1; print("ASYM",x,v,y,r)
print("asym pairs (engaged=0):",n)
