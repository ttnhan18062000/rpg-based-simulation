> **Note:** This is the original design proposal. The backend API was implemented as described. The frontend was later redesigned from a single `index.html` to a **React 19 + TypeScript + Vite + Tailwind CSS v4** SPA — see [docs/frontend.md](frontend.md) for the current frontend architecture.

This is a technical proposal to wrap your existing deterministic RPG engine with a **FastAPI** layer.

The core challenge here is **Concurrency integration**. Your current engine likely runs a blocking `while` loop. To serve a Web API, we must move the simulation loop to a **background thread** while the main thread handles HTTP requests, utilizing a thread-safe "latest snapshot" buffer for the API to read.

---

# Proposal: Real-Time Visualization via REST API

## 1. System Architecture Update

We will transform the application from a CLI tool into a Web Service.

**Current:** `Main Process -> WorldLoop (Blocking)`
**New:** `Main Process (FastAPI) -> Background Thread (WorldLoop)`

### Modified Directory Structure
We add an `api/` directory and update `src/__main__.py`.

```text
src/
├── api/                     # NEW: Web Server Layer
│   ├── app.py               # FastAPI app instance
│   ├── routes.py            # Endpoints (GET /state, POST /control)
│   ├── schemas.py           # Pydantic models for JSON response
│   └── engine_manager.py    # Singleton wrapper managing the WorldLoop thread
├── __main__.py              # UPDATED: Starts uvicorn server
└── ... (existing core/engine files remain generic)
```

---

## 2. The Integration Strategy (EngineManager)

We cannot have the API query the `WorldState` directly while the `WorldLoop` is writing to it (violates Single-Writer principle).

**Solution: Atomic Reference Swapping**
1.  The `WorldLoop` creates an immutable `Snapshot` at the end of every tick (as it already does for workers).
2.  The `EngineManager` holds a thread-safe reference to `latest_snapshot`.
3.  The API reads from `latest_snapshot`.

### The `EngineManager` Class
```python
import threading
from src.engine.world_loop import WorldLoop

class EngineManager:
    def __init__(self, config):
        self.loop = WorldLoop(config)
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.running = False
        self.latest_snapshot = None # The atomic buffer
        self.lock = threading.Lock()

    def _run_loop(self):
        """The background simulation loop."""
        while self.running:
            # 1. Tick the engine
            self.loop.tick()
            
            # 2. Update the shared buffer safely
            new_snap = self.loop.create_snapshot()
            with self.lock:
                self.latest_snapshot = new_snap
            
            # 3. Rate limiting (optional, to not burn 100% CPU)
            time.sleep(0.05) 

    def start(self):
        self.running = True
        self.thread.start()
```

---

## 3. REST API Specification

We need endpoints for **Static Data** (Map), **Dynamic Data** (Entities), and **Controls**.

### 3.1 Data Endpoints

**`GET /api/v1/map`**
*   **Purpose:** Fetch the static grid (walls, water, grass) once at startup.
*   **Response:**
    ```json
    {
      "width": 100,
      "height": 100,
      "grid": [ [1, 1, 0...], ... ] // 0=Grass, 1=Wall
    }
    ```

**`GET /api/v1/state`**
*   **Purpose:** Polled by the UI (e.g., every 100ms) to get moving parts.
*   **Response:**
    ```json
    {
      "tick": 405,
      "entities": [
        { "id": 101, "kind": "hero", "x": 10, "y": 15, "state": "COMBAT", "hp": 80 },
        { "id": 102, "kind": "goblin", "x": 11, "y": 15, "state": "COMBAT", "hp": 20 }
      ],
      "events": [ "Combat: Hero hit Goblin for 12 dmg" ]
    }
    ```

### 3.2 Control Endpoints

**`POST /api/v1/control/{action}`**
*   **Actions:** `start`, `pause`, `resume`, `step`, `reset`.
*   **Purpose:** debugging and playback control.

---

## 4. Frontend Visualization (The 2D Grid)

Since the map might be large (e.g., 50x50 or 100x100), DOM manipulation (creating 10,000 `<div>`s) is too slow.

**Recommendation: HTML5 Canvas**

### Concept
1.  **Layer 1 (Background Canvas):** Draws the `GET /map` data once.
2.  **Layer 2 (Entity Canvas):** Cleared and redrawn every time `GET /state` returns new data.

### Frontend Logic (Pseudocode)
```javascript
async function gameLoop() {
  // 1. Fetch State
  const state = await fetch('/api/v1/state');
  
  // 2. Clear Entity Canvas
  ctx.clearRect(0, 0, width, height);
  
  // 3. Draw Entities
  state.entities.forEach(ent => {
    // Interpolate position for smoothness if needed
    drawSprite(ent.kind, ent.x, ent.y);
    drawHealthBar(ent.x, ent.y, ent.hp);
  });
  
  // 4. Update UI Stats
  document.getElementById('tick-counter').innerText = state.tick;
  
  // 5. Schedule next frame
  requestAnimationFrame(gameLoop);
}
```

---

## 5. Implementation Roadmap

### Phase 1: Serialization (Backend)
*   Update `Snapshot` and `Entity` classes to have a `to_dict()` or Pydantic `model_dump()` method.
*   Ensure Enums (ActionType, AIState) serialize to strings, not Python objects.

### Phase 2: The Manager (Backend)
*   Create `api/engine_manager.py`.
*   Implement the background thread logic.
*   Ensure the `WorldLoop` can be paused/unpaused cleanly.

### Phase 3: FastAPI Setup (Backend)
*   Install FastAPI: `pip install fastapi uvicorn`.
*   Create routes that access the `EngineManager` singleton.
*   Enable CORS (Cross-Origin Resource Sharing) so a frontend hosted on a different port can talk to it.

### Phase 4: Basic UI (Frontend)
*   Create a simple `index.html`.
*   Use `fetch()` to grab JSON.
*   Render a simple HTML Table first to verify data, then upgrade to Canvas.

---

## 6. Example Code Snippets

### `src/api/schemas.py` (Pydantic)
```python
from pydantic import BaseModel
from typing import List, Optional

class EntitySchema(BaseModel):
    id: int
    kind: str
    x: int
    y: int
    hp: int
    state: str

class WorldStateResponse(BaseModel):
    tick: int
    entities: List[EntitySchema]
```

### `src/api/app.py`
```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.config import SimulationConfig
from src.api.engine_manager import EngineManager
from src.api.routes import router

# Global singleton
engine_mgr = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine_mgr
    config = SimulationConfig(seed=42)
    engine_mgr = EngineManager(config)
    engine_mgr.start() # Starts the background thread
    yield
    engine_mgr.stop()

app = FastAPI(lifespan=lifespan)
app.include_router(router)
```

## 7. Performance Considerations

1.  **Payload Size:** If you have 10,000 entities, sending the full list every 100ms is heavy.
    *   *Optimization:* Implement a `since_tick` parameter. `GET /state?since=500`. The backend only sends entities that changed since tick 500.
2.  **Visual Smoothness:** The simulation might run at 10 ticks/sec, but screens run at 60fps.
    *   *Frontend:* Use Linear Interpolation (Lerp) between the previous (x,y) and current (x,y) to make movement look smooth.

## 8. Requirements Addition
Add these to your `requirements.txt`:
```text
fastapi>=0.100.0
uvicorn[standard]>=0.20.0
pydantic>=2.0.0
```