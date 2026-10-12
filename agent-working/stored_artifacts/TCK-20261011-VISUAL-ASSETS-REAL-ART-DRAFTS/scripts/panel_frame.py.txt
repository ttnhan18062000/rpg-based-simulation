from visual_assets.drawing import api, compose
N="ui_panel_frame"
import shutil; shutil.rmtree(__import__('os').environ['ASEPRITE_MCP_WORKSPACE']+'/sprites/'+N, ignore_errors=True)
r=api.new_sprite(N,24,24)
rev=r["revision"]
O,M,H,S,F,I,G,GH="#0b0810","#6b5a88","#a08cc0","#4a3d62","#2f2742","#1c1628","#c8a24a","#f0d78c"
ops=[
 {"op":"rect","x":0,"y":0,"width":24,"height":24,"color":O},
 {"op":"rect","x":1,"y":1,"width":22,"height":22,"color":M},
 {"op":"line","x0":1,"y0":1,"x1":22,"y1":1,"color":H},{"op":"line","x0":1,"y0":1,"x1":1,"y1":22,"color":H},
 {"op":"line","x0":2,"y0":22,"x1":22,"y1":22,"color":S},{"op":"line","x0":22,"y0":2,"x1":22,"y1":22,"color":S},
 {"op":"rect","x":3,"y":3,"width":18,"height":18,"color":F},
 {"op":"line","x0":3,"y0":3,"x1":20,"y1":3,"color":I},{"op":"line","x0":3,"y0":3,"x1":3,"y1":20,"color":I},
]
for sx,sy in [(4,4),(17,4),(4,17),(17,17)]:
    ops+= [{"op":"rect","x":sx,"y":sy,"width":3,"height":3,"color":G},{"op":"pixels","pixels":[{"x":sx,"y":sy,"color":GH}]}]
ops+=[{"op":"pixels","pixels":[{"x":x,"y":y,"color":"#00000000"} for x,y in [(0,0),(23,0),(0,23),(23,23)]]},
 {"op":"set_slice","name":"panel","x":0,"y":0,"w":24,"h":24,"center":{"x":8,"y":8,"w":8,"h":8}}]
r=api.apply_ops(N,rev,ops); print(r)
print(compose.ascii_view(N)["grid"] if "grid" in compose.ascii_view(N) else compose.ascii_view(N))
print(compose.lint(N))
