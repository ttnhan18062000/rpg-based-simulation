"""Runtime call-counter over corpus worlds, with positive controls (mechanism reachability)."""
import importlib, json, sys, collections
sys.path.insert(0, ".")
from pathlib import Path

TARGETS = [a for a in sys.argv[3:]] or [
    "src.world.calamity:CalamityService.apply_calamity_consequences",
    "src.systems.social_systems.memory:SocialMemoryService.tick_place_attachment",
    "src.systems.social_systems.memory:SocialMemoryService.check_nemesis_promotion",
    "src.domains.information.trust:SourceTrustUpdateService.update",
    "src.domains.information.phase:InformationBeliefPhase.apply",
    "src.systems.social_systems.relationships:RelationshipService.process_update",
]
WORLDS = sys.argv[1].split(",")
TICKS = int(sys.argv[2])
counts = collections.Counter()
originals = {}


def wrap(spec):
    modname, attr = spec.split(":")
    cls_name, meth = attr.split(".")
    mod = importlib.import_module(modname)
    cls = getattr(mod, cls_name)
    raw = cls.__dict__[meth]
    fn = raw.__func__ if isinstance(raw, (staticmethod, classmethod)) else raw

    def counted(*a, **k):
        counts[spec] += 1
        return fn(*a, **k)

    counted.__wrapped__ = fn
    if isinstance(raw, staticmethod):
        setattr(cls, meth, staticmethod(counted))
    elif isinstance(raw, classmethod):
        setattr(cls, meth, classmethod(counted))
    else:
        setattr(cls, meth, counted)
    return cls, meth, raw, fn, type(raw)


wrapped = {t: wrap(t) for t in TARGETS}

# Positive control: prove the counter can move for each wrapper (call through it once, ignoring
# argument errors -- the wrapper increments before delegating).
for spec, (cls, meth, raw, fn, kind) in wrapped.items():
    before = counts[spec]
    try:
        m = getattr(cls, meth)
        if kind is staticmethod or kind is classmethod:
            m()
        else:
            m(None)
    except Exception:
        pass
    assert counts[spec] == before + 1, f"positive control failed for {spec}"
control = dict(counts)
counts.clear()

from src.worldbuilding.compiler import WorldCompiler  # noqa: E402
from src.worldbuilding.repository import WorldRepository  # noqa: E402
from src.engine.kernel import Kernel  # noqa: E402
from src.config.profiles import PROD_SMALL  # noqa: E402
from src.platform.rng import DeterministicRNG  # noqa: E402

repo = WorldRepository(str(Path("data") / "worlds"))
per_world = {}
for world in WORLDS:
    counts.clear()
    spec, ctx = repo.load_world_with_context(world)
    state, _ = WorldCompiler.compile(spec, 42, context=ctx)
    k = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(42), flags={"no_frame_pacing": True})
    try:
        for _ in range(TICKS):
            k.tick_once()
    finally:
        k.shutdown()
    per_world[world] = dict(counts)
print(json.dumps({"positive_control_ok": True, "ticks": TICKS, "per_world": per_world}, indent=1))
