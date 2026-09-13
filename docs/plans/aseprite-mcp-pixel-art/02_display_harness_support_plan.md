---
status: active
layer: frontend
authority: P1
audience: agent
date: 2026-09-10
tags: [frontend, pixel-art, live-map, browser, testing, accessibility]
---

# Milestone 02 — Native-Scale Display-Harness Support

## Outcome

Provide a renderer-owned, sanitized candidate comparison path for `ART-W04` and `ART-W05` so source art can
be judged in the current game context. This milestone is independent of MCP and may use current or synthetic
fixtures. It does not select a renderer or import production assets.

## Prerequisites

- Existing Live Map/Surface `LMSI-G0` evidence/ownership rules accepted for this harness.
- Human-approved harness charter names browser, viewport, DPR, zoom, 16-pixel-cell condition, fixtures,
  capture ordering, thresholds, storage, and allowed conclusions.
- Candidate import format is sanitized, bounded, and outside production manifests.
- Canvas control remains runnable; browser matrix beyond headless Chromium is `UNVERIFIED`.

## Deliverables

| ID | Deliverable | Objective acceptance |
|---|---|---|
| `M2-W01` | Harness ownership and import contract | Renderer/evidence owners, accepted image metadata, dimensions, hashes, and no-repository-write boundary approved |
| `M2-W02` | Current-context fixture | Recorded 16-pixel cell, zoom 1.0, viewport/DPR, turn-based grid scene, overlays, HUD strip, and exact stress identities |
| `M2-W03` | Size comparison mode | Same identity shown from 16/24/32 sources with scaling, overhang, crop, and overlay collision recorded |
| `M2-W04` | Crowded composition mode | `ART-W05` entities, world objects, fog/memory, HP, selection, target, and objective cues render under one fixture |
| `M2-W05` | Evidence capture | Neutral candidate labels, native-scale screenshots, enlarged nearest-neighbor views, grayscale evidence, environment manifest, and human result |
| `M2-W06` | Isolation/fallback proof | Malformed or missing candidate fails safely; current Canvas behavior and normal game path remain unchanged |
| `M2-W07` | `CAP-A09` disposition | Sanitized M1 candidate can enter the harness without granting adapter repository access; source and displayed evidence remain distinct |

## Non-goals

- Replacing Canvas, adopting PixiJS/Godot, changing Live Map/HUD architecture, or adding a production loader.
- Proving source-art structure, MCP safety, adaptive improvement, or final visual quality.
- Freezing resolution, palette, style, overlay roster, UI dimensions, or browser support.
- Treating the existing Playwright smoke screenshot as sufficient comparison evidence.

## Authorization boundary

Planning is authorized; implementation and browser execution require later tickets and an approved charter.
The adapter never receives repository access. A human imports or transfers sanitized candidates through the
declared boundary and remains the only visual decision authority.

## Covered capability gates

Primary: `CAP-A09`. Supports evidence for `ART-W04` and `ART-W05`. It passes no core `CAP-A01`–`A08` or
`A11` **(2026-09-13, added by review)**, no `CAP-B` gate, and no renderer adoption gate.

## Required evidence and security checks

- Candidate/source hash, sanitizer result, import identity, display settings, browser/build revision, and capture order.
- Native-scale and nearest-neighbor captures using the same semantic fixture across candidates.
- Tests for malformed images, extreme dimensions, metadata payloads, alpha/color-mode edge cases, missing
  assets, path traversal, filename collisions, decode failure, and memory/resource bounds.
- No external URL loading, scriptable image format, production manifest mutation, or adapter repository access.
- Keyboard/accessibility and non-hue critical distinctions remain valid in the crowded scene.

## Objective exit criteria

M2 `PASS` requires a reproducible, bounded candidate import and native display capture under the approved
fixture, failure isolation, unchanged normal Canvas behavior, and a complete `CAP-A09` evidence record.
Human readability may be PASS/FAIL/EXPLORATORY independently; it does not determine harness correctness.

## Dependencies

M2 coordinates with the existing renderer package and Plan 07. It depends only on the approved
visual-test/evidence and bounded-import contract subset aligned during M0, not on an Aseprite tool option,
installation, executable feasibility result, or M1. It may begin with synthetic/manual assets, then accept
M1 outputs later. M1 never waits on M2 for core passage. Aseprite absent or CAP-A `NO-GO` must leave
ART-W04/W05-equivalent manual display evaluation usable.

## Rollback path

Disable/remove the experiment route or flag, delete/quarantine imported disposable copies under the charter,
restore the unchanged Canvas control, and retain evidence. Production asset paths and manifests remain untouched.

## Stop conditions

Stop if the harness requires production-loader changes, cannot reproduce the native display condition,
grants the adapter repository access, changes normal Canvas behavior, conflates source and display evidence,
or duplicates an active renderer milestone without owner agreement.

## Ticket-ready slices after authorization

Import/sanitizer contract; fixture/capture route; 16/24/32 mode; crowded composition; failure/security tests;
evidence packaging; rollback rehearsal. Route implementation through existing frontend owners.
