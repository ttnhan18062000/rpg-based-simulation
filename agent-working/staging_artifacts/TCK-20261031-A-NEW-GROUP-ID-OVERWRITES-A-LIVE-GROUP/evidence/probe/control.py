"""Positive control: the probe on the repro_collision state must report 1 pre_loose, 1 pre_strict, 2 ghost_any; the clean state 0/0/0."""
import sys, os
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.dirname(__file__))
import importlib; P = importlib.import_module(os.environ.get("PROBE_MOD", "probe_groups"))
P.install()
from src.core.state import AuthoritativeState, GroupRecord
from src.core.strategic import ContractState, ContractKind, ContractStatus
from src.systems.world_systems.groups import GroupSystem
from src.engine.apply import ApplyPath
from src.core.builder import V2EntityBuilder
def build(collide):
    c = ContractState(id="r", kind=ContractKind.RECRUITMENT, source_id=1, target_id=2, status=ContractStatus.ACTIVE)
    e = {1: V2EntityBuilder(1).kind("actor").location(1.0,1.0).strategic(contracts={"r":c}).build(),
         2: V2EntityBuilder(2).kind("actor").location(1.2,1.2).strategic(contracts={"r":c}).build(),
         11: V2EntityBuilder(11).kind("actor").location(50.,50.).identity(group_id=10004).build(),
         12: V2EntityBuilder(12).kind("actor").location(50.5,50.5).identity(group_id=10004).build()}
    g = {10000: GroupRecord(id=10000,leader_id=99,member_ids={99},anchor=(0,0),dissolution_tick=3),
         10001: GroupRecord(id=10001,leader_id=98,member_ids={98},anchor=(0,0),dissolution_tick=4),
         (10004 if collide else 10002): GroupRecord(id=(10004 if collide else 10002),leader_id=11,member_ids={11,12},anchor=(50,50))}
    if not collide:
        for i in (11, 12): e[i] = V2EntityBuilder(i).kind("actor").location(50.+(i-11)*.5,50.+(i-11)*.5).identity(group_id=10002).build()
    return AuthoritativeState(tick=10, seed=1, entities=e, groups=g)
for collide in (True, False):
    P.S.update(pre_loose=0, pre_strict=0, formations=0); P.S["ghost_any"].clear(); P.S["ghost_persist"].clear(); P.S["prev_ghost"].clear(); P.S["overwritten_members"].clear()
    st = build(collide)
    u = GroupSystem.update_groups(st)
    ns = ApplyPath.apply_generation(st, u)
    u2 = GroupSystem.update_groups(ns); ApplyPath.apply_generation(ns, u2)
    s = P.summary(); print("collide" if collide else "clean", {k: s[k] for k in ("formations","pre_loose","pre_strict","post_lost","ghost_any","ghost_persist","ghost_preceded")})
