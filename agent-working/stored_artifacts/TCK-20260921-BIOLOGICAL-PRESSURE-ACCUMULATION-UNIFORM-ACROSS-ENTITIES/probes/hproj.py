import sys
from src.worldbuilding.repository import WorldRepository
from src.worldbuilding.compiler import WorldCompiler
from src.engine.kernel import Kernel
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG
spec,ctx=WorldRepository("data/worlds").load_world_with_context("frontier_living_world")
state,_=WorldCompiler.compile(spec,seed=42,context=ctx)
prof=RuntimeProfile(name="p",hardware_class=HardwareClass.CLASS_B,max_ram_mb=2048,max_cpu_percent=100.0,max_worker_count=1,max_queue_depth=2000,max_replay_buffer_kb=0,max_observability_budget_percent=0.0,max_tick_budget_ms=1e9)
k=Kernel(profile=prof,state=state,rng=DeterministicRNG(42),flags={"no_frame_pacing":True,"audit_mode":True})
for t in range(1,1001): k.tick_once()
print("inns",[(b.id,b.position) for b in k.state.buildings.values() if b.kind=="inn"], "nodes near", sorted(k.state.resource_nodes)[:6])
n=0
for e in k.state.entities.values():
    p=e.strategic.projects.get(e.strategic.current_project_id or "")
    if e.combat.alive and p is not None and "HUNGER" in str(getattr(p,"kind","")):
        print(e.id,e.navigation.position,[ (o.id,str(o.kind),o.target,getattr(o,"target_position",None)) for o in p.objectives], e.strategic.current_objective_id, e.task.payload)
        n+=1
        if n>3: break
k.shutdown()
