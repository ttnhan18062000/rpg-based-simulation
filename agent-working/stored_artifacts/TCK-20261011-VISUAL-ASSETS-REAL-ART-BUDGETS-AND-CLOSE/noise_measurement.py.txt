import random, shutil, os, sys
from visual_assets.drawing import api
def build(name, colour_fn):
    shutil.rmtree(os.environ['ASEPRITE_MCP_WORKSPACE']+'/sprites/'+name, ignore_errors=True)
    rev=api.new_sprite(name,64,64)["revision"]
    rev=api.apply_ops(name,rev,[{"op":"add_frame"} for _ in range(15)])["revision"]
    for k0 in range(0,16,2):
        ops=[]
        for k in range(k0,k0+2):
            ops.append({"op":"pixels","frame":k+1,"pixels":[{"x":x,"y":y,"color":colour_fn(x,y,k)} for y in range(64) for x in range(64)]})
        rev=api.apply_ops(name,rev,ops)["revision"]
    r=api.apply_ops(name,rev,[{"op":"add_tag","name":"burn","from_frame":1,"to_frame":16}])
    _,data,_=api.read_revision(name,r["revision"]); return len(data), r["n_colors"]
random.seed(7)
P2=["#3a2414","#ffcf3d"]; P16=[f"#{random.randrange(1<<24):06x}" for _ in range(16)]
print("2-colour dither, new pattern each frame:", build("n_dither", lambda x,y,k: P2[random.randrange(2)]))
print("16-colour noise:", build("n_16", lambda x,y,k: P16[random.randrange(16)]))
print("full-colour noise (worst case):", build("n_full", lambda x,y,k: f"#{random.randrange(1<<24):06x}"))
