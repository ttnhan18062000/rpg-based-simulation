import sys

ROOT = sys.argv[1]
sys.path.insert(0, ROOT)
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

for world in ("crowded_frontier", "frontier_living_world"):
    spec, ctx = WorldRepository(f"{ROOT}/data/worlds").load_world_with_context(world)
    st, _ = WorldCompiler.compile(spec, 42, context=ctx)
    rows = sorted(((r.trauma_score, r.id, r.bounds) for r in st.regions.values()), reverse=True)
    print("TRAUMA0", world, "regions", len(rows), "initial trauma_score of top 5:", [(round(a, 2), b) for a, b, _ in rows[:5]],
          "nonzero:", sum(1 for a, _, _ in rows if a > 0))
