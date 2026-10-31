from src.core.state import AuthoritativeState, GroupRecord
from src.core.strategic import ContractState, ContractKind, ContractStatus
from src.systems.world_systems.groups import GroupSystem
from src.engine.apply import ApplyPath
from src.core.builder import V2EntityBuilder
c = ContractState(id="r", kind=ContractKind.RECRUITMENT, source_id=1, target_id=2, status=ContractStatus.ACTIVE)
def ent(i,x,**kw):
    b=V2EntityBuilder(i).kind("actor").location(x,x)
    return b
e={}
e[1]=V2EntityBuilder(1).kind("actor").location(1.0,1.0).strategic(contracts={"r":c}).build()
e[2]=V2EntityBuilder(2).kind("actor").location(1.2,1.2).strategic(contracts={"r":c}).build()
e[11]=V2EntityBuilder(11).kind("actor").location(50.,50.).identity(group_id=10004).build()
e[12]=V2EntityBuilder(12).kind("actor").location(50.5,50.5).identity(group_id=10004).build()
g0=GroupRecord(id=10000,leader_id=99,member_ids={99},anchor=(0,0),dissolution_tick=3)
g1=GroupRecord(id=10001,leader_id=98,member_ids={98},anchor=(0,0),dissolution_tick=4)
live=GroupRecord(id=10004,leader_id=11,member_ids={11,12},anchor=(50,50))
st=AuthoritativeState(tick=10,seed=1,entities=e,groups={10000:g0,10001:g1,10004:live})
u=GroupSystem.update_groups(st)
print([(g.id,sorted(g.member_ids),g.dissolution_tick) for g in u.groups_add_or_update])
ns=ApplyPath.apply_generation(st,u)
print({k:sorted(g.member_ids) for k,g in ns.groups.items()})
for i in (11,12,1,2): print(i, ns.entities[i].identity.group_id)
u2=GroupSystem.update_groups(ns)
print("t+1 groups", [(g.id,sorted(g.member_ids)) for g in u2.groups_add_or_update])
print("t+1 entity_updates", {k:v.group_id_set for k,v in u2.entity_updates.items() if v.group_id_set is not None})
