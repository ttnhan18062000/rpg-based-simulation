---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261024-API-SERVER-OBSERVABILITY-UI-STATIC-PAGE
artifact_type: investigation
tags: [architecture, api-design, refactor]
---

# Investigation
- Packaging: `[tool.setuptools.packages.find]` has no package-data, so a wheel would omit the `.html`. Nothing ships a wheel. `docker/backend.Dockerfile` builds a non-editable venv install (the `.html` is absent from that copy) but the runtime stage also `COPY src/ /app/src/` and runs `python -m src` from `/app`, so the imported package is `/app/src` and the page is present. The same stage comment says other modules already rely on that. No `pyproject.toml` change is needed today; a `package-data` entry (`src.api = ["static_pages/*.html"]`) would only make the venv copy complete and is lead's file, offered to codebase-planner as optional.
- The page is 92,747 bytes with no CR; the file equals the served bytes.
- `tighten` also lowered or deleted rows in `src/engine/worker_manager.py`, `src/engine/pipeline_phases/capacity_enforcement.py`, `src/engine/kernel.py` and `src/observability/watchdog.py`: improvements already on main that no one had tightened.
