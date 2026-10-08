import sys, itertools, json
from src.content_semantics.faction import get_faction_semantics_service
from src.engine.legality import LegalityServiceV2
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState
svc=get_faction_semantics_service()
facs=sorted(svc.repo.factions.keys())
def mk(i,fid,x):
    e=(V2EntityBuilder(i).kind("x").location(x,5.0).identity(role=EntityRole.HERO,faction=svc.get_legacy_faction_bucket(fid))
       .combat(hp=100,max_hp=100,atk=10,def_stat=5,readiness=100.0,attack_range=1.5).build())
    e.identity.properties["faction_id"]=fid
    return e
out={}
for a in facs:
    for b in facs:
        for engaged in (False,True):
            ea,eb=mk(1,a,5.0),mk(2,b,6.0)
            if engaged: ea.task.payload["target_id"]=2
            st=AuthoritativeState(tick=1,seed=1,entities={1:ea,2:eb})
            out[f"{a}>{b}|{int(engaged)}"]=LegalityServiceV2.verify_attack_legality(ea,eb,st)[0]
json.dump(out,open(sys.argv[1],'w'))
asym=[k for k in out if (lambda a,b,e:out[f"{a}>{b}|{e}"]!=out[f"{b}>{a}|{e}"])(*k.replace('|','>').split('>'))]
print(len(facs),"factions",len(out),"verdicts; asymmetric:",len(asym))
