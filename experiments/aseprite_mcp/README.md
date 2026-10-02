# Aseprite MCP spike

Throwaway experiment, **not production code**. A minimal project-owned stdio MCP server that lets an
agent draw small RGB pixel-art sprites through the real Aseprite binary. Built to test the M1 claim in
`docs/plans/aseprite-mcp-pixel-art/01_supervised_headless_drawing_plan.md` (adapter option: project-owned
stdio MCP). It does not satisfy M0, does not produce production assets, and is not registered in
`.mcp.json`.

## Run

```
.venv/bin/python experiments/aseprite_mcp/server.py            # stdio MCP server
.venv/bin/python -m pytest experiments/aseprite_mcp -q          # needs aseprite + bwrap, else skips
```

Register for your own user only (not the repo) when you want to use it from Claude Code:

```
claude mcp add --scope user aseprite-pixel-art -- \
  /home/vboxuser/Work/rpg-based-simulation/.venv/bin/python \
  /home/vboxuser/Work/rpg-based-simulation/experiments/aseprite_mcp/server.py
```

Sprites live outside the repo in `~/.cache/rpg-aseprite-mcp` (override: `ASEPRITE_MCP_WORKSPACE`).

## Tools

`new_sprite`, `apply_ops` (one batch of operations -> exactly one new immutable revision, all-or-nothing),
`branch_sprite` (variants such as grayscale), `inspect` (layers, frames with duration/pixel count/checksum,
tags, palette, colours, optional 32x32 region), `preview` (one frame or one layer, 1-16x), `filmstrip`,
`list_sprites`.

Operations inside `apply_ops` (targeted ops take optional `layer` name and `frame`):

| Group | Ops |
|---|---|
| Draw | `pixels`, `line`, `rect`, `ellipse` (filled/outline), `flood_fill`, `outline`, `silhouette`, `flip`, `clear` |
| Colour | `replace_color`, `grayscale`, `set_palette` |
| Compose | `stamp` (composite another sprite/revision/frame at x,y; must fit) |
| Document | `add_layer`, `rename_layer`, `set_visible`, `add_frame` (copy inserted after its source), `set_duration`, `add_tag` |
| Structure | `delete_layer {layer}`, `delete_frame {frame}` (both refuse the last one; target required), `resize_canvas {width,height}` (1..128, top-left anchored crop or transparent pad on every layer/frame) |

### High-level tools (`highlevel.py` maths, `highlevel_tools.py` sprite tools)

Composed on top of `apply_ops`; rules, numbers and sources are in [TECHNIQUE_GUIDE.md](TECHNIQUE_GUIDE.md).
Each sprite tool creates exactly one new revision and rejects a stale `base_revision` before drawing.

| Tool | Does |
|---|---|
| `make_ramp` | Hue-shifted ramp, dark to light, base colour kept in place (pure, draws nothing) |
| `shade` | Hard-banded light-direction shading of an ellipse, rect, flat colour or all opaque pixels |
| `dither` | Ordered Bayer 2/4/8 dither between two colours, optionally a coverage gradient |
| `stroke` | Polyline through points; `pixel_perfect` cleans L-shaped doubles from freehand trace and keeps end points and corners next to longer segments |
| `auto_outline` | Silhouette outline on its own layer: `full` (one colour) or `selout` (reuses an existing darker colour) |
| `remap_palette` | Snap opaque pixels to the nearest colour of a given palette |
| `lint_sprite` | Advisory report: palette budget, orphans, value separation, edge clipping, outline mix |
| `ascii_view` | Text grid of the flattened frame with a colour legend |

Mapping to the art experiments: W01 `silhouette`; W02/W06 `grayscale` + `replace_color` on a `branch_sprite`
copy (identical geometry); W03 layers for state framing; W04 separate 16/24/32 sprites compared with
`stamp`; W05 `stamp` composition sheet; W07 `add_frame`/`set_duration`/`add_tag` + `filmstrip`.

## Safety properties (each covered by a test)

- Caller data reaches Lua only as parsed JSON; `lua/ops.lua` is fixed and hash-pinned (`LUA_SHA256`).
- Aseprite runs under `bwrap --unshare-all` (no network), read-only `/usr`, tmpfs home, one job dir.
  A probe test confirms the real home and `/etc/passwd` are not visible inside.
- Every edit publishes a new immutable revision via hard link (never overwrites); each revision has a
  sha256 sidecar that is verified on read. A stale `base_revision` is rejected.
- Bounds: 128x128, 256 ops and 8192 explicit pixels per batch, 16 layers, 16 frames, 8 stamp sources,
  64-colour palette, 32x32 readback, scale 1-16, 30s job timeout. Unknown ops/fields are rejected before
  Aseprite runs. After editing `lua/ops.lua`, run `./pin_hash.sh` (a reviewed, deliberate step).

## Not done (spike limits)

Indexed/grayscale colour modes (RGB only), layer groups, reorder layer, onion-skin/linked cels,
concurrency beyond a per-sprite file lock (tested: threads in one process; flock semantics only for
several processes), CI (Aseprite is a licensed binary; U-14 in the plan README), power-loss/crash
injection (publish-failure paths are tested, a kill mid-publish is not; an orphan `.sha256` without a
revision is harmless), and the M0 licence/provenance review (U-02). Passing these tests is evidence for `CAP-A01`/`A02`/`A04`/`A08`
at spike level only.

## Tests

`test_adapter.py`, `test_ops.py` (per-op), `test_negative.py` (real-Aseprite failure modes: timeout,
corrupt input with a matching hash, publish failure, same-base and first-creation races, `.jobs`
cleanup, oversize output, name/path/symlink attacks), `test_server_stdio.py` (real MCP over stdio).
