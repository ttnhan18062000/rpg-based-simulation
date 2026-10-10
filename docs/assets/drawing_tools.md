---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-02
tags: [architecture, mcp, documentation, rendering]
---

# Drawing tools (`visual_assets/drawing`)

A project-owned stdio MCP server that lets an agent draw small RGB pixel-art sprites through the real
Aseprite binary. It began as the spike `experiments/aseprite_mcp/` (PR #286) and was moved here without
behaviour change by `TCK-20261002-VISUAL-ASSETS-FOUNDATION-INIT`. Evidence level is still **spike**: it does
not satisfy the M0 licence/provenance review, produces no production assets and activates nothing at
runtime. The module layout and layering rules are in `visual_assets/drawing/README.md` and
`docs/plans/visual-asset-foundation/README.md`; the store the drawings may later be handed to is described in
`docs/assets/store_contract.md` (built: intake, human-gated adoption, build, release candidates, runtime export, verify and gc).

## Run

```
python -m visual_assets.drawing.server          # stdio MCP server (from the repo root)
bash visual_assets/start_mcp.sh                 # same, via the launcher .mcp.json uses
python -m pytest tests/visual_assets -q         # integration tests need aseprite + bwrap, else they skip
python -m visual_assets.drawing.pin             # after a reviewed edit of backend/lua/ops.lua
make visual-assets-aseprite-local               # strict real-Aseprite run, local only (ADR D10)
```

### Timeouts and stray sandboxes

Every Aseprite job runs under `bwrap` with a timeout (`config.JOB_TIMEOUT_S`). On a timeout `sandbox.kill_tree` freezes (SIGSTOP) the
whole process tree and SIGKILLs it, because `bwrap --unshare-all` forks an inner process (the init of a new PID namespace) that
ignores SIGTERM and, killed too early, could outlive the job holding a bind mount of its job directory. If a machine ever shows a stray
anyway (a `bwrap --unshare-all ... aseprite -b --script /lua/ops.lua` with parent PID 1), list candidates with
`pgrep -af 'bwrap .*--bind .*\.jobs/'` (not the broader `^bwrap --unshare-all`: GNOME's own image-loader sandboxes match that too).
Kill only a process whose `--bind` names a `.jobs/` directory of a workspace you own, never another session's, with `kill -9 <pid>`;
SIGTERM does nothing to it. The tests scope their leak checks to their own workspace, so a stray from elsewhere cannot fail them.

### Strict local run (ADR D10)

Real Aseprite runs only on the licence holder's own machine (`docs/assets/aseprite_licence_review.md`); CI never
installs it, so every `needs_aseprite` test skips there and the CI job summary states how many.
`make visual-assets-aseprite-local` runs `tests/visual_assets -m needs_aseprite` with
`VISUAL_ASSETS_REQUIRE_ASEPRITE=1` under a 2 GB memory cap (`systemd-run`, when available). In that mode a missing
binary or bwrap, or a binary whose `aseprite --version` is not `config.ASEPRITE_VERSION` (`1.3.18.6`), makes every
`needs_aseprite` test **fail or error** (pytest reports it as an ERROR, raised in fixture setup) instead of skip, so a strict run can never pass or skip them, and the target exits non-zero on any failure, any skip or an empty run.
It writes `reports/visual_assets/aseprite_local_run.json` (gitignored run output): `commit` (HEAD; a dirty tree is
not reflected), `utc_time`, `aseprite_version`, `passed`, `failed`, `errors`, `skipped`, `total`, `duration_seconds`,
`pytest_exit_code` and `ok`. A guard test (`tests/visual_assets/test_aseprite_licence_guard.py`) fails if a workflow
names Aseprite or a tracked file is an Aseprite executable or package.

**Review tooling (`visual_assets/review/`, `TCK-20261008-VISUAL-ASSETS-REVIEW-TOOLING-IN-STORE-CLI`).** The sheet rule, the compliance table, the look-alike report, the blind-check helpers and the owner review folder live in one peer package of `store` and `drawing`, with one command: `python -m visual_assets.review evaluate --set <id>` prints a set's evidence as JSON (`--recorded` prints the exact text committed as the frontend fixture's `rule_result.json`; `icon_draft_fixture --check` compares it byte for byte) and `python -m visual_assets.review review-sheets --set <id> [--out DIR]` writes the owner's review folder. For a set whose drafts declare revisions (`draft keep --revises`, ADR D22) the folder's README prints ONE `adopt-set` command with a NEW/REVISION summary (and the `draft drop` commands for drafts that are not proposed); for a set that predates it, the per-slot `review` and `adopt --parent` commands. The package reads drafts and catalog records only, imports no gate layer of the store and nothing from `src` (`tests/visual_assets/test_boundaries.py`, import contracts c14 and c15). Pilot colour vision's `tile_pixels()` now chooses the slot by key and detail through the export's manifest (default: the plain slot) instead of taking the first file, so `python -m visual_assets.review.pilot_colour_vision` prints the plain row (it printed the tree row before).

The server is registered for this repository in `.mcp.json` as `aseprite-pixel-art`. **Working in a git worktree while Claude Code runs in the main checkout:** start Claude Code with `VISUAL_ASSETS_CHECKOUT=<absolute path of the worktree>` (for example `VISUAL_ASSETS_CHECKOUT=/home/vboxuser/Work/rpg-aseprite-mcp claude`) so `submit_candidate` stages into that worktree (see `store_contract.md`, "Which checkout the server serves"); without it the server serves the checkout it was launched from, and every store tool result says which (`store_root`). Sprites live outside the
repo in `~/.cache/rpg-aseprite-mcp` (override: `ASEPRITE_MCP_WORKSPACE`; binary override:
`ASEPRITE_MCP_BINARY`). That experiment workspace is not the asset store (`visual_assets/catalog/`).

## Tools

`new_sprite`, `apply_ops` (one batch of operations -> exactly one new immutable revision, all-or-nothing),
`branch_sprite` (variants such as grayscale), `inspect` (layers, frames with duration/pixel count/checksum,
tags, palette, colours, optional 32x32 region), `preview` (one frame or one layer, 1-16x), `filmstrip`,
`list_sprites`, `export_handoff`, and three store tools (19 tools in all): `submit_candidate`, `store_list`, `store_show`.

`submit_candidate {handoff_id}` runs intake on a handoff written by `export_handoff` (found only by its `handoff_id`: never a path, never a bare candidate id) and returns the verdict and findings; it writes only the
local quarantine and is not an adoption. `store_list {kind, limit}` and `store_show {kind, id}` (kinds: `intake`, `source`, `artifact`, `release`) are read-only shaped summaries with bounded output and no absolute paths;
producer statements are labelled as claims. Restart the MCP server for new tools to appear in a running session. The full command and tool table is in `docs/assets/store_contract.md`.

`export_handoff {name, revision, licence_state, licence_evidence_ref, brief_id, review_evidence_ref, limitations}` packages one exact
revision (the revision is required, never defaulted) as a handoff directory `<workspace>/handoffs/<handoff_id>/` with exactly
`package.json` (a `CandidateHandoffPackage`), `source.aseprite` (the revision's exact bytes) and `preview.png`. `candidate_id` is `cand-` plus 16
hex of the source's sha256 (it identifies the source bytes); `handoff_id` is `<candidate_id>--` plus 12 hex of the sha256 of `package.json`. Each handoff directory is
immutable: rebuilding with the same inputs is idempotent, and changing any input (a corrected brief, a different licence statement) for the same revision creates a new handoff,
so several handoffs may exist for one candidate (intake tells them apart). Provenance is what the tools know (adapter version and Lua pin, Aseprite version, counts from Aseprite itself) and an explicit
`UNAVAILABLE` / `NOT_APPLICABLE` otherwise, e.g. the creator. It is a **candidate, not an adoption**: nothing is written to the asset store, and the
next step is the separate `python -m visual_assets.store intake <directory>`. The server has no adopt, adopt-set, build, release, revoke or gc tool. Agent flow for drafts: draw -> `export_handoff` -> `intake` -> `review` -> `python -m visual_assets.store draft keep <intake_id> --set <set_id> --as <key> [--detail <value>]` (not an MCP tool; it records no approval); a human later reviews the whole set and runs `adopt-set`.

Reviewing a draft set (`TCK-20261004-VISUAL-ASSETS-DRAFT-PREVIEW-PAGE`): `python -m visual_assets.store draft export <set_id> <out_dir>` writes a draft preview manifest and the preview PNGs into a new directory; then from `frontend/` run `npx vite` and open `http://localhost:5173/rehearsal-draft.html` (a dev-only page, never in the production build and never imported by the Live Map).
It opens the committed fixture set by default; use its "Open an exported set" picker and choose `<out_dir>` to review yours. The page draws one deterministic map that uses every Live Map terrain code in patches (23, from the explicit code-to-key table `TERRAIN_DRAFT_KEYS` in `frontend/src/visualAssets/terrainDrafts.ts`: `terrain.` plus the snake_case name),
picks forest-style detail values with `pickDetail`, marks a code with no draft with a diagonal over its flat fill, can show the plain colour fills beside it, lists per code which draft is shown, and prints the set id and the draft set hash, the same `sha256:` value the `adopt-set` confirmation prints, so a review record can name exactly what was reviewed.

The icon key set has its own preview page, `frontend/rehearsal-icons.html` (`TCK-20261006-VISUAL-ASSETS-ICON-KEY-DRAFT-SET`): the harness is a sibling of the terrain one because the terrain page is a map scene by tile code. It reads the committed `__fixtures__/icondraft/` export (`python -m visual_assets.review.icon_draft_fixture --write` refreshes it, ignoring only the manifest's `registry_hash`). What the set holds and how to review it: `docs/assets/icon_key_set_review.md`. The MCP server runs from the main checkout, so `submit_candidate` writes its intakes to the MAIN checkout's quarantine; from a worktree, run the CLI `intake` on the same handoff directory (the intake ids are content-derived, so they match).

**Rule for agents: an agent never runs `adopt` or `revoke`** (`python -m visual_assets.store adopt|revoke`). They are human decisions that write the tracked catalog; they refuse to run without a terminal and make the operator type the id, and the drawing code cannot import them.

Every sprite summary (`new_sprite`, `apply_ops`, `branch_sprite`, `inspect`) also carries `cels` (number of cels as Aseprite stores them,
linked cels included) and `aseprite_version` (string, from the running binary). Both are read-only facts added for candidate handoff.
Note: `palette_size` of `new_sprite` is the in-memory palette; `inspect` reports the size Aseprite gives after reloading the file.

Operations inside `apply_ops` (targeted ops take optional `layer` name and `frame`):

| Group | Ops |
|---|---|
| Draw | `pixels`, `line`, `rect`, `ellipse` (filled/outline), `flood_fill`, `outline`, `silhouette`, `flip`, `clear` |
| Colour | `replace_color`, `grayscale`, `set_palette` |
| Compose | `stamp` (composite another sprite/revision/frame at x,y; must fit) |
| Document | `add_layer`, `rename_layer`, `set_visible`, `add_frame` (copy inserted after its source), `set_duration`, `add_tag` |
| Structure | `delete_layer {layer}`, `delete_frame {frame}` (both refuse the last one; target required), `resize_canvas {width,height}` (1..128, top-left anchored crop or transparent pad on every layer/frame) |

### High-level tools (`technique/` maths, `compose.py` sprite tools, `server/highlevel_tools.py` registration)

Composed on top of `apply_ops`; rules, numbers and sources are in [pixel_art_technique.md](pixel_art_technique.md).
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

- Caller data reaches Lua only as parsed JSON; `backend/lua/ops.lua` is fixed and hash-pinned (`config.LUA_SHA256`).
- Aseprite runs under `bwrap --unshare-all` (no network), read-only `/usr`, tmpfs home, one job dir.
  A probe test confirms the real home and `/etc/passwd` are not visible inside.
- Every edit publishes a new immutable revision via hard link (never overwrites); each revision has a
  sha256 sidecar that is verified on read. A stale `base_revision` is rejected.
- Bounds: 128x128, 256 ops and 8192 explicit pixels per batch, 16 layers, 16 frames, 8 stamp sources,
  64-colour palette, 32x32 readback, scale 1-16, 30s job timeout. Unknown ops/fields are rejected before
  Aseprite runs. After editing `backend/lua/ops.lua`, run `python -m visual_assets.drawing.pin` (a reviewed, deliberate step).

## Not done (spike limits, unchanged by the move)

Indexed/grayscale colour modes (RGB only), layer groups, reorder layer, onion-skin/linked cels,
concurrency beyond a per-sprite file lock (tested: threads in one process; flock semantics only for
several processes), CI (Aseprite is a licensed binary; U-14 in the plan README), power-loss/crash
injection (publish-failure paths are tested, a kill mid-publish is not; an orphan `.sha256` without a
revision is harmless), and the M0 licence/provenance review (U-02). Passing these tests is evidence for `CAP-A01`/`A02`/`A04`/`A08`
at spike level only.

## Tests

`tests/visual_assets/drawing/`: `unit/` (pure technique maths, config-isolation and pin tests; no Aseprite, runs in CI),
`integration/` (per-operation, real-Aseprite failure modes such as timeout, corrupt input with a matching hash, publish
failure, same-base and first-creation races, `.jobs` cleanup, oversize output, name/path/symlink attacks, and the stdio
protocol tests that draw; skip cleanly without Aseprite and bwrap), and `test_server_stdio.py` (tool list and error
reporting over real stdio; no Aseprite needed). `tests/visual_assets/test_boundaries.py` enforces the layering.
