import os, shutil, sys
from visual_assets.drawing import api, compose
def fresh(name):
    shutil.rmtree(os.environ['ASEPRITE_MCP_WORKSPACE']+'/sprites/'+name, ignore_errors=True)
def preview(name, rev, frame, scale, path):
    open(path,"wb").write(api.render_preview(name, rev, frame, None, scale) if False else api.render_preview(name, revision=rev, frame=frame, scale=scale))
def strip(name, rev, scale, path):
    open(path,"wb").write(api.render_filmstrip(name, rev, scale))
