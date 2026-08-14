"""Agent Ops Dashboard — single-process production server.

Builds a *separate* FastAPI() instance from src/api/agent_ops_dashboard/main.py's
`app`, mounting the pre-built static SPA (via StaticFiles) onto that new
instance only. main.py's own `app` object is never mutated — its route list is
read via `include_router` (a copy operation), never appended to in place. This
keeps tests/tools/test_agent_ops_dashboard_api_boundary.py's
test_main_mounts_no_static_files guard (which forbids any "StaticFiles(" or
".mount(" substring, or Mount route, inside main.py itself) satisfied
structurally, regardless of whether this module is ever imported.

Standalone entry point, not a src.cli.entry subcommand — this dashboard is a
separate product/port from the simulation engine (see main.py's own
docstring).
"""
from __future__ import annotations

import argparse
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8420
DEFAULT_DIST_DIR = Path(__file__).resolve().parents[3] / "dashboard-frontend" / "dist"


def build_app(dist_dir: Path) -> FastAPI:
    dist_dir = Path(dist_dir)
    if not (dist_dir / "index.html").is_file():
        raise RuntimeError(
            f"Dashboard static assets not found at {dist_dir} (missing index.html). "
            "Run `make dashboard-build` to produce them."
        )

    from src.api.agent_ops_dashboard.main import app as main_app

    serve_app = FastAPI(title="Agent Ops Dashboard")
    serve_app.include_router(main_app.router)
    serve_app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="spa")
    return serve_app


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Agent Ops Dashboard production server")
    parser.add_argument("--host", type=str, default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--dist-dir", type=Path, default=DEFAULT_DIST_DIR)
    return parser


def main(argv=None) -> None:
    args = _build_parser().parse_args(argv)
    app = build_app(args.dist_dir)

    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
