---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261024-GRAPHIFY-ON-PATH-IS-NOT-THE-PINNED-VERSION
artifact_type: investigation
tags: [knowledge-store, process-improvement]
---

# Investigation

- Host ubuntu (measured by lead-planner 2026-10-25, re-measured here 2026-10-26): `~/.local/bin/graphify` is a pip user-site script (`#!/usr/bin/python3`, `from graphify.__main__ import main`), graphifyy 0.6.7; the main checkout's `.venv-knowledge/bin/graphify` is 0.9.70 (pin). The venv has no pip (uv-built), so the printed fallback is `uv pip install --python`.
- `graphify --version` is not a command (`error: unknown command '--version'`), so the version is read with the script's own interpreter: `importlib.metadata.version('graphifyy')`. About 0.2 s.
- Running 0.9.70 warns that the agent skills under `~/.claude`, `~/.copilot` and `~/.agents` (`skills/graphify`) are from 0.6.7 and offers `graphify install --platform <name>`. Reported to the planner; not changed here.
- Host u24desktop (lead-planner-u24's read-only output from u24desktop on 2026-10-26, relayed by lead-planner): `~/.local/bin/graphify` is a uv-tool shim (interpreter `~/.local/share/uv/tools/graphifyy/bin/python`, graphify 0.8.39); graphifyy is NOT installed in `.venv-knowledge` there (its python is a symlink to `/usr/bin/python3`; torch and setuptools are present). So the shim must (a) accept a uv-tool shim as replaceable, (b) refuse to link until the venv has the pinned graphifyy, and fail loudly with the install command. `requirements-knowledge.txt` as a whole cannot install there (torch 2.13.0+cpu is not on that host's index), so the printed command installs only `graphifyy==<pin>`. u24 runs the shim after it pulls main; that is its lead's job.
- `.claude/settings.json` calls bare `graphify update .`; with the symlink the hook, `graphify query` and docs commands all run the pin without editing that file.
