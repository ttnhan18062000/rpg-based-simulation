import math, sys
sys.path.insert(0, __file__.rsplit("/",1)[0])
from common import *
N="fx_campfire"; fresh(N)
SH="#1c1517"          # ground shadow
GL1,GL2="#2b1c20","#40262a"   # dithered glow on the ground
ST_D,ST_M,ST_L="#2f3340","#6a7084","#b4b9ca"   # stones
LG_D,LG_M,LG_L,LG_E="#2e1a0e","#573519","#7d4f27","#d6a96a"  # logs, end grain
F_R,F_O,F_Y,F_W="#c92f1c","#f2761a","#ffcf3d","#fff2b0"   # flame bands
CO="#ff8a1f"; EM_D="#5a1410"
W=H=64; CX=32
canvas={}
def put(x,y,c):
    if 0<=x<W and 0<=y<H: canvas[(x,y)]=c
def ell(cx,cy,rx,ry,c):
    for y in range(int(cy-ry)-1,int(cy+ry)+2):
        for x in range(int(cx-rx)-1,int(cx+rx)+2):
            if ((x+.5-cx)/rx)**2+((y+.5-cy)/ry)**2<=1: put(x,y,c)
def thick(x0,y0,x1,y1,t,c):
    n=int(max(abs(x1-x0),abs(y1-y0))*2)+1
    for i in range(n+1):
        x=x0+(x1-x0)*i/n; y=y0+(y1-y0)*i/n
        for oy in range(t):
            put(int(round(x)),int(round(y))+oy,c)
def stone(x,y,w,h):
    for yy in range(h):
        for xx in range(w):
            if (xx in (0,w-1)) and (yy in (0,h-1)): continue
            put(x+xx,y+yy, ST_L if yy==0 else (ST_D if yy==h-1 else ST_M))
def render(k):
    canvas.clear()
    ph=2*math.pi*k/16
    # ground shadow and warm glow (dither) that breathes
    ell(32,55,26,7,SH)
    gr=(16+1.2*math.sin(ph))
    for y in range(44,64):
        for x in range(0,64):
            e=((x+.5-32)/gr*1.0)**2+((y+.5-55)/(gr*0.27))**2
            if e<=1 and (x+y)%2==0 and canvas.get((x,y))==SH: canvas[(x,y)]=GL2 if e<0.45 else GL1
    # back stones
    for i in range(-3,4):
        a=math.pi*(0.5+i*0.16)
        x=round(32+21*math.cos(a)*-1)-2; y=round(54-5*math.sin(a))-1
        if y<54: stone(x,y,5,3)
    # logs (crossed), lit from the top-left
    for off,(x0,y0,x1,y1) in enumerate(((17,57,44,52),(47,57,20,52))):
        thick(x0,y0,x1,y1,4,LG_M); thick(x0,y0,x1,y1,1,LG_L)
        thick(x0,y0+3,x1,y1+3,1,LG_D)
    ell(17.5,57.5,2.3,2.3,LG_E); ell(46.5,57.5,2.3,2.3,LG_E)
    for x,y in ((17,57),(46,57)): put(x,y,LG_L)
    # coals
    for i,(x,y) in enumerate(((27,56),(31,57),(36,56),(33,55),(39,57),(24,57))):
        if (i+k)%3: put(x,y,CO)
        else: put(x,y,EM_D)
    # flames: main + two tongues; heights flicker on integer harmonics of the 16-frame loop
    def flame(cx,base,Hh,Ww,amp,p0,hm,layers):
        for y in range(base-Hh,base+1):
            t=(base-y)/Hh
            sway=amp*t*t*math.sin(ph*hm+p0+t*2.4)
            prof=(math.sin(math.pi*min(1,(t**0.75)))**0.9)*(1-0.55*t**2)
            for (scale,col,top) in layers:
                hw=Ww*prof*scale
                if t>top: continue
                x0=cx+sway
                for x in range(int(x0-hw-1),int(x0+hw+2)):
                    if abs(x+.5-x0)<=hw and hw>0.4: put(x,y,col)
    def fl(base,Hh,Ww,cx,amp,p0,hm,w=1.0):
        flame(cx,base,Hh,Ww,amp,p0,hm,((1.0,F_R,1.0),(0.74,F_O,0.86),(0.46,F_Y,0.66),(0.2,F_W,0.36)))
    hmain=34+3*math.sin(ph*2)+2*math.sin(ph*3+1)
    hl=22+3*math.sin(ph*3+2); hr=20+3*math.sin(ph*2+4)
    fl(54,round(hl),7,22,2.0,1.3,3)
    fl(54,round(hr),7,42,2.0,3.9,2)
    fl(55,round(hmain),11,32,3.5,0.0,1)
    # sparks rise 4px per frame: 16 frames = 64px = one seamless loop
    for i,(x0,y0,dx) in enumerate(((26,12,3),(38,44,-4),(31,28,5),(35,60,-3),(29,4,4))):
        y=(y0+4*k)%52+3
        x=round(x0+dx*math.sin(ph*1+i*1.7))
        col=F_Y if y>34 else (F_O if y>20 else F_R)
        put(x,y,col)
        if y>34: put(x,y+1,F_O)
    # front stones
    for i in range(-3,4):
        a=math.pi*(0.5+i*0.16)
        x=round(32+21*math.cos(a)*-1)-2; y=round(54-5*math.sin(a))-1
        if y>=54: stone(x,y+2,5,3)
    return [{"x":x,"y":y,"color":c} for (x,y),c in canvas.items()]
if __name__=="__main__":
    rev=api.new_sprite(N,W,H)["revision"]
    rev=api.apply_ops(N,rev,[{"op":"add_frame"} for _ in range(15)])["revision"]
    for k0 in range(0,16,3):
        ops=[]
        for k in range(k0,min(16,k0+3)):
            px=render(k); ops.append({"op":"pixels","frame":k+1,"pixels":px})
        rev=api.apply_ops(N,rev,ops)["revision"]
    ops=[{"op":"add_tag","name":"burn","from_frame":1,"to_frame":16}]+[{"op":"set_duration","frame":i,"ms":80} for i in range(1,17)]
    ops.append({"op":"set_slice","name":"base","x":0,"y":0,"w":64,"h":64,"pivot":{"x":32,"y":63}})
    r=api.apply_ops(N,rev,ops); print(r["revision"],r["n_colors"],r["tags"],r["slices"])
    open(sys.argv[1]+"/fire_strip.png","wb").write(api.render_filmstrip(N,r["revision"],3))
    for f in (1,5,9):
        open(sys.argv[1]+f"/fire_f{f}.png","wb").write(api.render_preview(N,revision=r["revision"],scale=8,frame=f))
    print(compose.lint(N, frame=1))
