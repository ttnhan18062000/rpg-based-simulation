import math, sys
sys.path.insert(0, __file__.rsplit("/",1)[0])
from common import *
N="fx_selection_ring"; fresh(N)
D,B,L="#0e3342","#3fb8c9","#c4f6ee"  # outer shade, body, highlight
rev=api.new_sprite(N,32,32)["revision"]
rev=api.apply_ops(N,rev,[{"op":"add_frame"} for _ in range(7)])["revision"]
W=[24,25,26,27,28,27,26,25]  # pulse: grows then settles, loops seamlessly
ops=[]
D,B,LT,L="#0e3342","#3fb8c9","#7fe0dc","#d6fbf4"
def inside(dx,dy,a,b): return (dx/a)**2+(dy/b)**2<=1
for k in range(8):
    a=W[k]/2; b=a*0.5; f=k+1; px=[]
    th=-math.pi*0.75+2*math.pi*k/8
    spark={}
    for d,c in ((-0.3,LT),(-0.15,L),(0,L),(0.15,L),(0.3,LT)):
        x=16+(a-1.5)*math.cos(th+d); y=16+(b-0.8)*math.sin(th+d); spark[(math.floor(x),math.floor(y))]=c
    for y in range(32):
        for x in range(32):
            dx,dy=x+0.5-16,y+0.5-16
            if not inside(dx,dy,a+1.2,b+0.7): continue
            if inside(dx,dy,a-4.6,b-2.3): continue
            if not inside(dx,dy,a,b) or inside(dx,dy,a-3.4,b-1.7): c=D
            else: c=LT if (dy<0 and dx+dy<2) else B
            px.append({"x":x,"y":y,"color":spark.get((x,y),c) if c!=D else c})
    ops.append({"op":"pixels","frame":f,"pixels":px})
ops+=[{"op":"add_tag","name":"pulse","from_frame":1,"to_frame":8}]+[{"op":"set_duration","frame":i,"ms":100} for i in range(1,9)]
ops.append({"op":"set_slice","name":"anchor","x":0,"y":0,"w":32,"h":32,"pivot":{"x":16,"y":16}})
r=api.apply_ops(N,rev,ops); print(r["revision"],r["n_colors"],r["tags"],r["slices"])
open(sys.argv[1]+"/ring_strip.png","wb").write(api.render_filmstrip(N,r["revision"],6))
print(compose.lint(N, frame=1)["findings"])
