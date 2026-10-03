---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261002-ASEPRITE-MCP-SPIKE-HARDENING
artifact_type: investigation
tags: [mcp, testing, security]
---

# Investigation — TCK-20261002-ASEPRITE-MCP-SPIKE-HARDENING

## Context scan done
`search_docs` / `graphify query` for "aseprite" returned nothing relevant (the graph indexes `src/`, not
`experiments/` plan docs); the plans were found by follow-up grep and read directly:
`docs/plans/aseprite-mcp-pixel-art/` (README, M1 plan), the P2 proposal §9/§11/§13/§14, and
`docs/plans/render-and-art/07_manual_art_experiment_execution_plan.md`. No duplicate ticket exists
(`tickets/` grep for aseprite/pixel returned none).

## Verified facts (all run on this machine, 2026-10-02)
- Aseprite 1.3.18.6 at `/usr/bin/aseprite`; headless `-b --script` works with `DISPLAY` empty.
- Lua in this build has `json.decode/encode`, so caller data never needs to be spliced into Lua source.
- `bwrap --unshare-all` runs Aseprite with only `/usr`, `/etc/ld.so.cache`, a tmpfs home and one job dir bound.
  A probe script inside the sandbox could not open the real home `aseprite.ini`, `/etc/passwd` or `/etc/shadow`.
- `Sprite:newFrame(n)` inserts the copy right after frame `n` (not appended); the returned Frame object's
  `frameNumber` is stale. `newEmptyFrame(#frames+1)` appends. Frame-range export writes a single named file.
- Palette default is 256 entries; `set_palette` resizes it.
- 54 tests pass (`test_adapter.py` 20, `test_ops.py` 34). A complex 16x16 asset was built through the real MCP
  stdio server and the output PNGs were inspected by eye.

## What the spike does NOT yet evidence (the gap this ticket closes)
| Plan item | Spike status |
|---|---|
| `M1-W06` timeout, malformed input, disk failure, stale hash, concurrency, path attacks | Stale hash and name-regex only; the rest untested |
| `M1-W02` no-clobber publication under failure | Hard-link publish exists; failure paths untested |
| Protocol-level behaviour | Only a scratch script (not in the repo) exercised stdio |
| Ops for ART-W04 (16/24/32 candidates) | No `resize_canvas`, no `delete_layer/frame` |

## Risks noted while reading the code (for the implementer to confirm, not assumptions)
1. `_publish` computes the next revision from a directory listing under `_SpriteLock`, but `new_sprite` takes the
   lock *before* the sprite dir exists on first use (`_SpriteLock` mkdirs it) — verify two simultaneous first
   creations cannot both publish `r0001`.
2. `_Job.__exit__` uses `rmtree(ignore_errors=True)`; a failing cleanup is silent. The negative suite should assert
   `.jobs/` is empty, which will surface this.
3. `subprocess.run(timeout=...)` kills `bwrap`, but `--die-with-parent` is what reaps Aseprite; confirm no orphan
   `aseprite` process survives a timeout (check with `pgrep` in the test).
4. `_resolve_revision` re-reads the whole file to hash it on every read; fine at spike sizes (cap 8 MiB), note only.
5. The pinned-hash design means `lua/ops.lua` edits require `./pin_hash.sh`; forgetting it makes every call fail
   closed with a clear message (desired).

## Architecture / authority check
Nothing in `experiments/aseprite_mcp/` touches `AuthoritativeState`, `src/`, or any durable simulation state.
Sprites live outside the repo (`~/.cache/rpg-aseprite-mcp`). The server is registered at user scope only
(`claude mcp add --scope user aseprite-pixel-art`), not in the repo's `.mcp.json`. No mechanics-bible or
parity-ledger entry is affected (no simulation behaviour change).
