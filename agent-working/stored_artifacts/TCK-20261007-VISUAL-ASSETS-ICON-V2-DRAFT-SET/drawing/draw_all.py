import json, sys
sys.path.insert(0, "/home/vboxuser/Work/rpg-aseprite-mcp"); sys.path.insert(0, sys.argv[1])
import proto_eval
from visual_assets.drawing import api, handoff
cv = proto_eval.all_canvases()
out = {}
for key in sorted(cv):
    c = cv[key]; name = key.replace(".", "_")
    existing = [x for x in api.list_sprites() if x["name"] == name]
    if existing:  # left by an interrupted first run (its handoff step failed): reuse the latest revision, verified afterwards pixel by pixel
        r2 = {"revision": existing[0]["latest"], "n_colors": None, "nonempty_pixels": None}
    else:
        r1 = api.new_sprite(name, c.w, c.h)
        r2 = api.apply_ops(name, r1["revision"], c.ops())
    h = handoff.build_handoff(name, r2["revision"], licence_state="UNREVIEWED", licence_evidence_ref="UNAVAILABLE", review_evidence_ref="NOT_APPLICABLE", brief_id="icons-v2-" + key.removeprefix("icon.").replace(".", "-").replace("_", "-"),
                              limitations=[f"{key}: {c.w}x{c.h}, own pixels from palette icons-v1, no outside art, no AI generator; drawn through visual_assets.drawing.api (the code behind the MCP tools)"])
    out[key] = {"sprite": name, "revision": r2["revision"], "handoff_id": h["handoff_id"], "directory": h["directory"], "colors": r2.get("n_colors"), "nonempty": r2.get("nonempty_pixels")}
    print(key, r2["revision"], h["handoff_id"], r2.get("n_colors"), r2.get("nonempty_pixels"), flush=True)
json.dump(out, open(sys.argv[1] + "/drawn.json", "w"), indent=1)
