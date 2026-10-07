import sys, collections
from dataclasses import replace
from src.worldbuilding.repository import WorldRepository
from src.worldbuilding.compiler import WorldCompiler
from src.engine.kernel import Kernel
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG
spec=WorldRepository("data/worlds").load_world("urban_political")
state,_=WorldCompiler.compile(spec,seed=42)
fl=dict(state.feature_flags); fl["ENABLE_ADVENTURE_ROUTING"]=1.0
state=replace(state,feature_flags=fl)
prof=RuntimeProfile(name="p",hardware_class=HardwareClass.CLASS_B,max_ram_mb=2048,max_cpu_percent=100.0,max_worker_count=1,max_queue_depth=2000,max_replay_buffer_kb=0,max_observability_budget_percent=0.0,max_tick_budget_ms=1e9)
k=Kernel(profile=prof,state=state,rng=DeterministicRNG(42),flags={"no_frame_pacing":True,"audit_mode":True})
def dump(t):
    rows=[]
    for eid,e in k.state.entities.items():
        if e.combat.alive:
            rows.append((str(eid)[:14], str(getattr(e,"entity_type",None) or getattr(e,"kind",None)), str(getattr(getattr(e,"identity",None),"faction_id",None) or getattr(e,"faction",None)), round(e.biological.hunger,1), e.inventory.gold, e.lifecycle.age_ticks))
    print(t,len(rows)); [print("  ",r) for r in rows[:14]]
for t in range(1,1301):
    k.tick_once()
    if t in (500,1090,1300): dump(t)
k.shutdown()
