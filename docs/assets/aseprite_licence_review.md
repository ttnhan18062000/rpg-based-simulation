---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-03
tags: [architecture, mcp, security, testing]
---

# Aseprite licence and binary provenance review (`U-02`, `U-14`)

**Status: decided by the user on 2026-10-03 (ADR `D10`).** This is the project's own reading of the licence that ships with the
binary, done to decide where the drawing tools and the store may run Aseprite. It is not legal advice. If the licensor's
written terms ever say otherwise, they win and `D10` is reopened.

## Binary in use

| Fact | Value | How it was read |
|---|---|---|
| Package | `aseprite` `1.3.18.6-1`, `amd64`, maintainer "Aseprite Team <support@aseprite.org>" | `dpkg -s aseprite` |
| Installed | 2026-10-02 (dpkg file list date), from the official `.deb` | `/var/lib/dpkg/info/aseprite.list` |
| Binary | `/usr/bin/aseprite`, sha256 `61019ef21fbe3b9a635ac33da0b1378f20c52ea522387fdd8bc07d1578543258` | `sha256sum` on 2026-10-03 |
| Reported version | `Aseprite 1.3.18.6-x64` | `aseprite --version` |
| Licence text | `/usr/share/doc/aseprite/EULA.txt` (Igara Studio S.A.) | read in full |
| Scripting API | the pinned `backend/lua/ops.lua` (hash-pinned as `LUA_SHA256`) runs against this version; integration tests prove it locally | `tests/visual_assets/` (`needs_aseprite`) |

The licence holder and the purchase are the owner's own: **confirmed by the owner on 2026-10-04** (this is their licence and their machine). This repository records no licence key and never will.

## Clauses that decide where Aseprite may run

| Clause | Text (abridged) | Consequence here |
|---|---|---|
| 1(a) Installation and Use | may install and use copies "on your computer" | the owner's own machine may run it (today: the Linux dev machine) |
| 1(b) Backup Copies | copies for backup and archival purposes | no other copying |
| 2(b) Distribution | may not distribute copies to third parties | no binary in git, in a CI cache, in a container image or as a workflow artifact |
| 2(d) Rental | may not rent, lease or lend | no shared or team machine runs it on the owner's licence |
| 2(g) Source code | may compile and modify the source only for your own personal purpose | building it from source on a hosted CI runner is not a personal-purpose build on your computer |
| Ownership | content made with the software belongs to its owner | the artwork the tools produce is the project's; the store's licence state is about the artwork, not the editor |

## Decision (`D10`)

- Real Aseprite runs only on the licence holder's own machine. It is never installed, compiled, cached, downloaded or uploaded on a
  GitHub-hosted runner or any machine that is not the owner's.
- `U-14` is answered **no** for GitHub-hosted CI. CI runs every visual-asset test that needs no Aseprite; the real-Aseprite tests are
  local evidence, run through one strict make target that fails instead of skipping, and CI reports how many it skipped.
- `adopt` and `build` keep needing Aseprite, so they stay local commands (as built). `verify` stays pure Python and keeps running in CI.

## Reversal triggers

- The licensor grants CI or server use in writing.
- The owner sets up a self-hosted runner on their own machine (a new decision: CI would then depend on that machine).
- The project switches the source format to one an open editor can render.
