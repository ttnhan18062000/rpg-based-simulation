---
status: active
layer: engine
authority: P1
audience: developer
---

# Frontend: Real-time Visualization

The WorldLoop Frontend is a high-performance React application built with **Vite** and **TypeScript**. It utilizes the **HTML5 Canvas API** to render thousands of entities and world objects at 60 FPS.

---

## 1. Technology Stack

- **Core**: React 18, TypeScript 5.
- **Rendering**: Custom Canvas rendering engine (`useCanvas.ts`).
- **Real-time**: EventSource (SSE) for state deltas.
- **Styling**: Tailwind CSS (for UI overlays) + CSS Modules.
- **Icons**: Lucide React.

---

## 2. The `useSimulation` Hook

Central to the frontend is the `useSimulation` custom hook, which manages the lifecycle of the simulation connection.

### A. Initial Load (Full State)
On mount, the hook performs two critical fetch calls:
1.  **`/api/v1/map`**: Fetches the RLE-encoded tile grid.
2.  **`/api/v1/static`**: Fetches all persistent world objects (Buildings, Resource Nodes, Treasure Chests).

### B. Delta Sync (SSE)
Once the base data is loaded, it connects to `/api/v1/stream`.
- **`onmessage`**: Receives a JSON delta containing `changed` and `removed` entity lists.
- **State Reconciliation**: A `Map` is used to efficiently upsert changed entities into the local React state, minimizing re-renders.

### C. Inspection Polling
When a user selects an entity, a secondary slow-poll (500ms) is triggered:
- **`/api/v1/state?selected={id}`**: Fetches the `FullSchema` for the selected entity, enabling the detailed "Cognitive Inspect" sidebar.

---

## 3. Rendering Engine (`useCanvas`)

The `useCanvas` hook manages the main 2D viewport.

- **Tile Layer**: Renders the base grid (Forest, Water, Road, etc.) using a cached off-screen canvas for static tiles.
- **Entity Layer**: Renders actor icons, HP bars, and state labels.
- **Interpolation**: While the simulation ticks at 12 TPS, the renderer uses **linear interpolation (lerp)** to ensure smooth movement between tick positions at 60 FPS.
- **Culling**: Only tiles and entities within the current camera frustum are drawn.

---

## 4. UI Components

- **Control Bar**: Allows the user to `PAUSE`, `RESUME`, and adjust the `TPS` (Ticks Per Second).
- **World Log**: A real-time scrolling list of global events (Kills, Level ups, Region discoveries).
- **Inspector Sidebar**: Displays the selected entity's "Brain" state, Equipment, and Combat History.
- **Minimap**: A high-level overview of entity clusters and fog-of-war.

---

## 5. State Handling Strategy

To prevent "React Lag" during high-frequency updates:
1.  **Refs for Hot Data**: Tick count and raw entity maps are stored in `useRef` and only synced to `useState` at a controlled frequency.
2.  **Memoization**: The Canvas renderer is passed the raw data and only re-draws when the `tick` or `camera` state changes.
3.  **Event Throttling**: UI-only events (like hover highlights) are debounced to ensure they don't block the main rendering loop.
