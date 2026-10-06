"""Draw the re-tinted tiles through the drawing library (same calls the MCP tools make) and package each as a handoff. Prints one JSON line per tile:
{"name", "key", "handoff_dir"}. Usage: python retint_draw.py name [name ...]   (names as in tile_generator.NAMES; sprite = tdraft_<name>_b)."""
import collections, json, sys
import tile_generator as g
import tile_retint as r
from visual_assets.drawing import api, handoff

BY_NAME = {v: k for k, v in g.NAMES.items()}

for name in sys.argv[1:]:
    code = BY_NAME[name]
    grid, rep = r.retint(code)
    bg = collections.Counter(c for row in grid for c in row).most_common(1)[0][0]
    sprite = f"tdraft_{name}_b"
    first = api.new_sprite(sprite, g.S, g.S, background=bg)
    px = [{"x": x, "y": y, "color": grid[y][x]} for y in range(g.S) for x in range(g.S) if grid[y][x] != bg]
    rev = api.apply_ops(sprite, first["revision"], [{"op": "pixels", "pixels": px}])["revision"] if px else first["revision"]
    out = handoff.build_handoff(
        sprite, rev, licence_state="UNREVIEWED", licence_evidence_ref="UNAVAILABLE", brief_id=f"terrain-v1-{name.replace('_', '-')}-tint",
        review_evidence_ref="NOT_APPLICABLE",
        limitations=[f"re-tint of the terrain-v1 draft of terrain.{name}: same drawing, tile mean moved onto the flat fill for the set colour-vision rule; periodic so it repeats seamlessly; light from the top-left"])
    print(json.dumps({"name": name, "key": f"terrain.{name}", "revision": rev, "handoff_dir": out["directory"]}), flush=True)
