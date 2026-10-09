---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING
artifact_type: investigation
date: 2026-10-08
tags: [architecture, planning]
---

# How mature 2D/game asset pipelines handle the foundation, and what a small pixel-art asset store may lack

Research date: 2026-10-08. Web research only. I did not inspect the repository. A practice is called "possibly missing" only because the brief does not describe it, so check each one against the store before acting on it.

## 1. Asset databases and registries

- **Stable IDs that are separate from paths.** Unity writes a `.meta` file for every asset. The file holds "the unique ID assigned to the asset, and values for all the asset's import settings". If the `.meta` file is lost, "any reference to that asset is broken" ([Unity: Asset metadata](https://docs.unity3d.com/Manual/AssetMetadata.html)). Godot's ResourceUID lets the engine "keep references between resources intact, even if files are renamed or moved" ([Godot ResourceUID](https://docs.godotengine.org/en/4.4/classes/class_resourceuid.html)). That only holds for moves made in the editor. A move made with the operating system breaks the UID cache ([bugnet.io](https://bugnet.io/blog/fix-godot-uid-resource-references-broken-after-move), a secondary source, UNVERIFIED against the official docs).
  - *Takeaway:* the store's semantic visual keys play the same role. The risk is that adoption records keyed by a file path break when a file is renamed.
- **Sidecar import settings with hash-triggered reimport.** Godot keeps the import configuration in a committed `<asset>.import` file next to each source. It reimports "when the MD5 checksum of the source asset changes". The `.godot/imported/` cache is not committed ([Godot import process](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/import_process.html)). Bevy 0.12 added optional `.meta` files that set loader and processor settings, and it preprocesses assets ahead of time ([Bevy 0.12](https://bevy.org/news/bevy-0-12/)).
- **A searchable registry with tags.** Unreal's Asset Registry collects metadata about unloaded assets, including searchable tag/value pairs ([Unreal Asset Registry](https://dev.epicgames.com/documentation/en-us/unreal-engine/asset-registry-in-unreal-engine)). Unity Addressables lets you load by address or by **labels**, combined as a union or an intersection ([Addressables labels](https://docs.unity3d.com/Packages/com.unity.addressables@1.21/manual/Labels.html)).
- **A reference graph.** Unreal's Reference Viewer shows both the dependencies of an asset and the other assets that reference it ([Reference Viewer](https://dev.epicgames.com/documentation/en-us/unreal-engine/reference-viewer-in-unreal-engine)). Addressables' Analyze tool has rules such as "Check Duplicate Bundle Dependencies", plus a "Bundle Layout Preview" ([Analyze tool](https://docs.unity3d.com/Packages/com.unity.addressables@1.21/manual/AnalyzeTool.html)).
- **Retiring assets with redirectors.** When an asset is moved or renamed, Unreal leaves a Redirector at the old path so existing references still resolve. A later "Fixup" step resaves the referencers and deletes the redirector ([Asset Redirectors](https://dev.epicgames.com/documentation/en-us/unreal-engine/asset-redirectors-in-unreal-engine)). This is the standard model for deprecation: alias, migrate, then remove.

## 2. Sprite atlases and texture packing on the web

- **Atlases cut draw calls in GPU renderers.** Unity: "Unity only needs to create one draw call for all the sprites in a sprite atlas" ([Unity Sprite Atlas](https://docs.unity3d.com/Manual/sprite/atlas/atlas-landing.html)). Defold combines images into atlases "for performance reasons" and supports flipbook animation groups, margin, inner padding and extruded borders against bleeding ([Defold atlas](https://defold.com/manuals/atlas/)). In PixiJS, a batch breaks once it exceeds a per-batch texture limit, and sprites that share one atlas texture batch together ([PixiJS skills: performance](https://skills.sh/pixijs/pixijs-skills/pixijs-performance), a secondary source, UNVERIFIED in the official PixiJS docs).
- **Atlases help much less for HTTP over HTTP/2.** HPBN advises removing "unnecessary HTTP/1.x workarounds ... such as concatenated files, image sprites" ([HPBN, HTTP/2](https://hpbn.co/http2/)). Separate files also cache separately.
- **What this means here.** If the React client draws tiles as DOM `<img>` elements or CSS, about 70 small PNGs served over HTTP/2 with immutable caching is fine. If it draws through canvas or WebGL (Pixi, Phaser), one atlas per set (terrain, icons) matters for batching. Pixel art at integer scale needs `image-rendering: pixelated` ([MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/image-rendering)). Atlases for 16x16 tiles need extrusion and padding to avoid seams ([Defold](https://defold.com/manuals/atlas/); Aseprite `--extrude`, `--shape-padding` in the [Aseprite CLI](https://www.aseprite.org/docs/cli/)).

## 3. Versioning, storage and cache busting

- **Git LFS** "replaces large files ... with text pointers inside Git, while storing the file contents on a remote server" ([git-lfs.com](https://git-lfs.com/)). With about 70 PNG files of a few KB each, LFS adds more trouble than it saves. It becomes relevant for `.aseprite` sources and review sheets only if the repository grows large (judgement, not sourced).
- **Content-hashed, immutable URLs.** MDN recommends putting "version/hashes in their URLs, while never modifying the resources", combined with `Cache-Control: ... immutable` ([MDN Cache-Control](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control)). Vite hashes the file names of imported assets. It inlines files below `assetsInlineLimit` as base64, and it leaves files in `public/` unhashed ([Vite assets](https://vite.dev/guide/assets)).
  - *Risk:* if the runtime manifest points at files under `public/`, they will not be cache-busted unless the store itself puts the pixel hash into each path.
- **Deterministic builds.** Embedded timestamps make outputs non-reproducible. `SOURCE_DATE_EPOCH` exists to fix that ([reproducible-builds.org](https://reproducible-builds.org/docs/source-date-epoch/)). PNG encoders can embed tIME or text chunks and differ in zlib settings (UNVERIFIED, general knowledge). Pixel hashing avoids that problem for identity, but the published bytes, atlases and the manifest also need byte-stable output if releases are meant to be reproducible.

## 4. Validation in CI

Mature engines ship analyzers: Unity Addressables Analyze ([link](https://docs.unity3d.com/Packages/com.unity.addressables@1.21/manual/AnalyzeTool.html)), Unity Project Auditor for "scripts, assets, and code" ([Project Auditor](https://docs.unity3d.com/Packages/com.unity.project-auditor@1.0/manual/index.html)), and Unreal's referencer graph. On the web side, Knip finds unused files and exports ([knip.dev](https://knip.dev/)). It does not understand data-driven asset keys, so a custom key-usage scan is needed.

Typical checks:
- dimensions and grid alignment
- palette membership
- size and colour-count budgets
- naming conventions
- **orphans** (adopted assets that no code or manifest uses)
- **dangling references** (code asks for a key that has no asset, or that only resolves through fallback)
- duplicate pixel hashes

## 5. Hot reload and live preview

Bevy reloads modified asset files at runtime once file watching is enabled ([Bevy cheatbook](https://bevy-cheatbook.github.io/assets/hot-reload.html)). In 0.12 this became a `file_watcher` feature you turn on during development and leave off for release ([Bevy 0.12](https://bevy.org/news/bevy-0-12/)). Godot reimports automatically when the source hash changes ([Godot](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/import_process.html)). Vite's dev server serves imported assets through the module graph ([Vite](https://vite.dev/guide/assets)).

Gap pattern: a gated adoption/build/release flow is slow for iterating on art. Mature pipelines keep a fast, ungated dev-only preview path (draft → in-game view in seconds) and leave the gate in front of release.

## 6. Metadata, localisation and accessibility

- **Accessibility.** W3C WAI: alt text on a functional icon should "convey the action that will be initiated ... rather than a description of the image" ([WAI functional images](https://www.w3.org/WAI/tutorials/images/functional/)). Decorative images get `alt=""` ([WAI decorative](https://www.w3.org/WAI/tutorials/images/decorative/)). An icon therefore needs a per-use *role* (decorative or functional) and a **localisable label key**, not a fixed English string.
  - The colour-vision and recognisability checks already cover the visual side. A text alternative is a separate requirement.
- **Tags and labels** for search and grouped loading, like Addressables labels and Unreal registry tags (links above).
- **Usage tracking**, meaning which code references which key, like Unreal referencers.

## 7. Art direction as data

- Palettes as files. Lospec distributes palettes as `.hex`, `.gpl`, `.pal`, `.ase` and PNG ([Lospec](https://lospec.com/palette-list)). A committed, versioned palette file can be both the lint source for palette membership and Aseprite's palette.
- Style rules as machine-checkable data: outline colour, light direction, maximum colours per tile. Reference boards linked from each key's spec. These are judgement calls with no single source; mature studios publish style guides, but I found no authoritative URL in the time available.

## 8. Pixel-art-specific pipeline (Aseprite)

The Aseprite CLI supports:
- `--sheet` and `--data` (JSON hash or array)
- `--list-tags` and `--list-slices`
- `--split-layers`, `--split-tags` and `--tag`
- `--sheet-pack`, `--trim`, `--extrude`, `--shape-padding`
- `--filename-format` with `{tag}`, `{frame}` and `{layer}`

([Aseprite CLI](https://www.aseprite.org/docs/cli/)). Slices carry 9-slice centre rectangles, a pivot, and user data ([Aseprite slices](https://www.aseprite.org/docs/slices/)). The Lua API exposes Tag, Slice and Properties ([Aseprite API](https://www.aseprite.org/api/)). On the web, nine-slice UI maps directly to CSS `border-image`, which uses 4 corners, 4 edges and an optional `fill` centre ([MDN border-image](https://developer.mozilla.org/en-US/docs/Web/CSS/border-image)). Animation frames come through tags and become frame ranges in the exported JSON.

Possible gaps:
- The manifest may not carry frames, durations, pivots or 9-slice insets yet.
- If animated tiles or UI panels arrive later, the schema needs these fields before the first such asset is adopted.

## Practice table

| # | Practice | Who uses it | Relevance (~70 assets, web 2D pixel art) | Why |
|---|---|---|---|---|
| 1 | Stable asset ID separate from path (GUID/UID) | Unity .meta, Godot UID | High | Renames should not orphan adoption, lineage and licence records. Semantic keys may already cover this. |
| 2 | Reference graph / usage tracking (key → code referencers) | Unreal Reference Viewer, Addressables Analyze | High | This is how you find orphans and dangling keys, and it is needed before retiring anything. |
| 3 | Orphan and dangling-reference CI check | Addressables Analyze, Knip (code) | High | Cheap to build, and it catches silent fallback use. |
| 4 | Redirector/alias-based deprecation | Unreal Redirectors | Medium | Retire or rename a key without breaking saves or code. Low volume today. |
| 5 | Content-hashed immutable URLs + `Cache-Control: immutable` | MDN guidance, Vite | High | Stops stale tiles after a release. Check that `public/` assets are not unhashed. |
| 6 | Byte-reproducible build outputs (no timestamps, fixed encoder) | Reproducible Builds | Medium | Release candidates should rebuild bit-for-bit. Pixel hashes cover identity, not the shipped bytes. |
| 7 | Atlas packing with extrude/padding | Unity Sprite Atlas, Defold, Pixi | Medium (High if canvas/WebGL) | Draw calls matter only on GPU renderers. Under HTTP/2 the request count matters little. |
| 8 | Labels/tags for grouping and search | Addressables labels, Unreal registry tags | Medium | Filters review sheets and set-level loading. Small catalogue. |
| 9 | Fast ungated dev preview / hot reload | Bevy file_watcher, Godot reimport, Vite dev | High | Artist and agent iteration speed. Keep the gate for release only. |
| 10 | Icon a11y metadata: role + localisable label key | W3C WAI | High | Recognisability checks cover sight, not screen readers. Icons are functional UI. |
| 11 | Palette and style rules as committed data used by lint | Lospec formats, Aseprite palettes | High | Gives one palette source for both the drawing and the linting. |
| 12 | Animation/slice/9-slice/pivot fields in manifest schema | Aseprite CLI/slices, CSS border-image | Medium | Needed before the first animated or UI-panel asset arrives. |
| 13 | Size, dimension and colour budgets in CI | Unity Project Auditor, Addressables Analyze | Medium | Cheap guardrail. Assets are tiny, so the payload risk is low. |
| 14 | Git LFS for binaries | GitHub/Git LFS | Low | Around 70 small PNGs do not justify it. Revisit when `.aseprite` sources or review sheets grow. |
| 15 | `image-rendering: pixelated` at integer scale | MDN | High (verify) | Without it, browsers blur pixel art. |

## Top 5 recommendations

1. **Usage graph + orphan/dangling CI gate.** Scan the frontend and backend for visual-key references. Join the result against the runtime manifest. Fail CI on unknown keys, and report adopted keys that nothing uses or keys served only through a fallback. This is the Unreal Reference Viewer and Addressables Analyze idea at the store's scale.
2. **Alias-based retirement.** Add a `deprecated → replaced_by` alias record to the manifest, the same idea as Unreal redirectors. The runtime then resolves old keys and CI tracks the remaining referencers until the alias can be removed. Retirement becomes a recorded state, not a deletion.
3. **Accessibility metadata on icon keys.** Each key gets a localisable label key that describes its *function*, plus a decorative/functional flag (W3C WAI), so the React layer emits correct `alt` and `aria-label`.
4. **Check the cache and determinism boundary.** Confirm that the exported files have content-hashed URLs, either through Vite imports or hashes in the paths, served `immutable`. Confirm that two builds of one release candidate give identical bytes, with no PNG time or text chunks and a fixed encoder.
5. **Palette/style-as-data plus a fast draft preview.** Commit one palette file in GPL or HEX format, used by both Aseprite and the lint. Add a dev-only path that renders an unadopted draft set in the real client with hot reload, separate from the gated adopt/build/release path. Extend the manifest schema with frames, pivot and 9-slice fields now, before animated or UI assets need them.
