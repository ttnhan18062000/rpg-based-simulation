"""Runtime per-method call counter for whole classes over one corpus world, with positive controls.
usage: reach2.py <world> <ticks> <out.json>"""
import importlib, json, sys, collections, inspect
sys.path.insert(0, ".")
from pathlib import Path
WORLD, TICKS, OUT = sys.argv[1], int(sys.argv[2]), sys.argv[3]
CLASSES = """src.world.spawn:SpawnService src.world.ecology:ResourceEcologyService src.world.transformation:TransformationService
src.economy.vacancy:EconomicVacancyService src.progression.veterancy:VeterancyService src.quests.service:QuestService
src.world.providers.requirements:RequirementEvaluator src.world.environment:EnvironmentService
src.world.reproduction_humanoid:HumanoidReproductionService src.strategy.role_model_phase:RoleModelSelectionPhase
src.world.raid:RaidService src.world.creature_territory:CreatureTerritoryService src.world.displacement:DisplacementService
src.world.camp:CampService src.world.threat:ThreatService src.world.calamity:CalamityService
src.systems.social_systems.memory:SocialMemoryService src.domains.information.trust:SourceTrustUpdateService
src.systems.social_systems.appraisal:SocialAppraisalSystem src.progression.skills:SkillScalingService
src.engine.rpg_depth:SkillScalingService src.strategy.capacity:CapacityService src.strategy.cognition_capacity:CapacityService
src.world.motivation.pressure_resolver:MotivationPressureResolver src.engine.domain.lead_routing:LeadRoutingSystem
src.ai.score_modifiers:ScoreModifierSystem src.engine.cognition:AppraisalSystem src.world.perception.gate:PerceptionGate
src.cognition.capability_estimate:CapabilityEstimateService src.ai.life_stage:LifeStageService src.core.inventory:InventoryService
src.town.shop:ShopService src.systems.social_systems.relationships:RelationshipService src.domains.information.phase:InformationBeliefPhase""".split()
counts = collections.Counter()
control = {}

def wrap_class(spec):
    modname, cname = spec.split(":")
    cls = getattr(importlib.import_module(modname), cname)
    first = None
    for name, raw in list(cls.__dict__.items()):
        if name.startswith("__"):
            continue
        kind = type(raw)
        fn = raw.__func__ if kind in (staticmethod, classmethod) else raw
        if not inspect.isfunction(fn):
            continue
        key = f"{spec}.{name}"

        def make(fn=fn, key=key):
            def counted(*a, **k):
                counts[key] += 1
                return fn(*a, **k)
            counted.__wrapped__ = fn
            return counted
        c = make()
        setattr(cls, name, staticmethod(c) if kind is staticmethod else classmethod(c) if kind is classmethod else c)
        if first is None:
            first = (key, name, kind, cls)
    return first

firsts = {s: wrap_class(s) for s in CLASSES}
for spec, f in firsts.items():
    if f is None:
        control[spec] = "no-methods"; continue
    key, name, kind, cls = f
    before = counts[key]
    try:
        m = getattr(cls, name)
        (m() if kind in (staticmethod, classmethod) else m(None))
    except Exception:
        pass
    control[spec] = counts[key] == before + 1
counts.clear()

from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
from src.engine.kernel import Kernel
from src.config.profiles import PROD_SMALL
from src.platform.rng import DeterministicRNG
repo = WorldRepository(str(Path("data") / "worlds"))
spec_, ctx = repo.load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec_, 42, context=ctx)
k = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(42), flags={"no_frame_pacing": True})
try:
    for _ in range(TICKS):
        k.tick_once()
finally:
    k.shutdown()
json.dump({"world": WORLD, "ticks": TICKS, "control": control, "counts": dict(counts)}, open(OUT, "w"), indent=1)
print("done", WORLD)
