import hashlib, starlette
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from src.api.server import create_v2_app
from src.config.profiles import RuntimeProfile, HardwareClass
H=hashlib.sha256(b"k").hexdigest()
p=RuntimeProfile(name="p",hardware_class=HardwareClass.CLASS_B,max_ram_mb=256,max_cpu_percent=100.0,max_worker_count=0,max_queue_depth=100,max_replay_buffer_kb=64,max_observability_budget_percent=5.0,max_tick_budget_ms=200.0,api_key_hashes=f"c:{H}")
c=TestClient(create_v2_app(p))
print("starlette",starlette.__version__)
for path in ["/api/v1/ws","/api/v1/ws/observe","/api/v1/ws/observability/events"]:
    try:
        with c.websocket_connect(path) as ws: print(path,"ACCEPTED without key")
    except WebSocketDisconnect as e: print(path,"rejected",e.code)
    except Exception as e: print(path,"error",type(e).__name__,e)
    try:
        with c.websocket_connect(path, headers={"X-API-Key":"k"}) as ws: print(path,"with key: accepted")
    except Exception as e: print(path,"with key: ",type(e).__name__,e)
print("GET /api/v1/state no key",c.get("/api/v1/state").status_code)
