"""analyse.py <zones.jsonl> [--pairs a,b ...]: per-zone death counts (zone = set of regions containing the position by inclusive bounds),
the credited region per zone, victim faction, killer faction (or ENVIRONMENT for hazard/passive deaths), and the credited region's hazard level."""
import sys, json, collections
rows = [json.loads(l) for l in open(sys.argv[1])]
hdr, deaths = rows[0], [r for r in rows[1:] if "tick" in r]
zone = collections.defaultdict(list)
for d in deaths: zone[" + ".join(d["zone"]) or "(no region)"].append(d)
print(f"{hdr['world']}: {len(deaths)} deaths, audit_mode={hdr['audit_mode']}")
for z, ds in sorted(zone.items(), key=lambda kv: -len(kv[1])):
    cred = collections.Counter(d["credited"] or "none" for d in ds)
    vic = collections.Counter(d["victim"]["faction"] for d in ds)
    kil = collections.Counter((d["killer"] or {}).get("faction", "ENVIRONMENT:" + d["outcome"]) for d in ds)
    haz = collections.Counter(d["outcome"] for d in ds)
    print(f"{z:55s} {len(ds):4d} credited={dict(cred)} victims={dict(vic)} killers={dict(kil)}")
