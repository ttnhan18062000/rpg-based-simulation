---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260606-DOCSITE-SCAFFOLD
artifact_type: investigation
tags: [docsite, scaffold]
---

# Investigation — TCK-20260606-DOCSITE-SCAFFOLD

## Current State

### Node.js / npm
- Node.js: v20.19.4 (satisfies Docusaurus 3 requirement of ≥ 18)
- npm: 9.2.0

### Existing Makefile Targets
The Makefile uses tab-indented shell blocks. Existing target groups:
- **Install**: `install`, `install-py`, `install-fe` (`cd frontend && npm install`)
- **Build**: `build` (`cd frontend && npm run build`)
- **Development**: `dev`, `dev-backend`, `dev-frontend`
- **Production**: `serve`, `serve-only`
- **Infrastructure**: `docker-up`, `docker-down`, `docker-logs`, `run-worker`, `run-engine`
- **CLI**: `cli`
- **Testing**: `test`, `test-quick`, `test-cov`, `lane-*`, `gate-expansion`
- **Profiling**: `profile`, `profile-full`, `profile-memory`, `profile-api`
- **Quality**: `lint`, `typecheck`
- **Agent monitoring**: `agent-monitoring-retro`, `agent-monitoring-validate`, `agent-monitoring-query`
- **Cleanup**: `clean` (removes `frontend/dist`, `frontend/node_modules/.tmp`, `__pycache__`)

No `docs-serve` or `docs-build` targets exist yet. The `.PHONY` line at the top currently lists:
`help install install-py install-fe build dev serve stop clean lint profile-api`

The `clean` target does NOT touch `website/` at all — a `docs-clean` extension may be desirable but is out of scope for this ticket.

### .gitignore Entries Relevant to Docsite
Currently gitignored for the frontend:
```
frontend/dist/
frontend/node_modules/
```

The ticket requires adding:
```
website/node_modules/
website/build/
website/.docusaurus/
```

None of these are present yet. The `/site` entry (for mkdocs) is present but applies only to `/site` at the root — no conflict with `website/build/`.

`build/` at root level is already gitignored (Python packaging artifact), but `website/build/` is a subdirectory path and needs its own entry.

### Existing `website/` Directory
No `website/` directory exists at the project root. Clean slate.

---

## Conflict Check

### `frontend/` vs `website/`
No naming or path conflict. `frontend/` is a Vite/React SPA that serves the game UI at `:5173`. It uses:
- `npm run dev` → Vite dev server
- `npm run build` → TypeScript + Vite build to `frontend/dist/`

`website/` will be a completely separate Docusaurus 3 installation. The two are:
- Different directories (no shared `node_modules`)
- Different ports (`website/` defaults to `:3000`, `frontend/` to `:5173`)
- Different npm workspaces (no workspace config exists at root — no package.json at root)
- Different build outputs (`website/build/` vs `frontend/dist/`)

No conflict. The existing `install-fe` / `build` / `lint` / `typecheck` Makefile targets all `cd frontend` explicitly — they will be unaffected.

### Port Conflict Risk
Docusaurus default port is `:3000`. The backend runs on `:8000`. Frontend dev server runs on `:5173`. No collision. However, `make docs-serve` should explicitly pass `--port 3000` (or a configurable port) to make it unambiguous.

### `clean` Target
The existing `clean` target does not reference `website/`. Adding `docs-serve`/`docs-build` targets does not change this behavior. If the team later wants `make clean` to also wipe `website/build/`, that is a follow-on concern — out of scope for this ticket.

---

## Docusaurus 3 Setup Approach

### Recommended: Manual scaffold (not `npx create-docusaurus@3`)
`npx create-docusaurus@3` generates a template site with a blog plugin, tutorials, and example content that would all need to be stripped out. For this project the setup is well-specified, so manual scaffolding is cleaner and leaves no dead template content.

**Manual scaffold steps:**
1. `mkdir website && cd website`
2. `npm init -y` → sets `name`, `version`, `private: true`
3. `npm install @docusaurus/core @docusaurus/preset-classic docusaurus-search-local`
4. Create `docusaurus.config.js` with four plugin instances (see below)
5. Create `src/pages/index.js` (minimal homepage with navigation map)
6. Create `sidebars.js` stubs for each plugin instance
7. No `blog/` directory — blog plugin disabled

**Alternative: `npx create-docusaurus@3 website classic --skip-install`**
If manual scaffolding proves error-prone (e.g., missing peer deps), the `create-docusaurus` generator can be run with `--skip-install` and the resulting template immediately stripped to the minimal config. This is a fallback path.

### Version Pin
Pin `@docusaurus/core` and `@docusaurus/preset-classic` to `^3.5.2` (latest stable as of mid-2025) to avoid accidental major upgrades.

---

## Plugin Configuration Plan

Docusaurus 3 supports multiple instances of `@docusaurus/plugin-content-docs` via the `id` field. Each instance maps to one content root and gets its own URL prefix.

### Four Instances

| Instance ID | `path` (source) | `routeBasePath` (URL prefix) | Notes |
|---|---|---|---|
| `docs` (default) | `../docs` | `/docs` | All subdirs of `docs/` — mechanics, engine, architecture, etc. |
| `tickets` | `../tickets/done` | `/tickets` | Closed ticket history only (`tickets/done/`) |
| `artifacts` | `../stored_artifacts` | `/artifacts` | Stored investigation/plan/test_plan artifacts per ticket |
| `archive` | `../docs/archive` | `/archive` | Historical archived docs (173 files in `docs/archive/`) |

**Note on `docs` vs `archive` overlap:** `docs/archive/` is a subdirectory of `docs/`. If the `docs` instance points at `../docs` and `archive` points at `../docs/archive`, Docusaurus will index `docs/archive/` twice — once under `/docs/archive/` and once under `/archive/`. This is intentional and acceptable (archive gets its own top-level URL). However, the `docs` instance should either:
  - **Option A:** Exclude `docs/archive/` via `exclude` patterns — cleaner, no duplication.
  - **Option B:** Accept duplication — simpler config, archive content searchable from both paths.

**Recommendation: Option A** — use `exclude: ['archive/**']` on the `docs` instance. This keeps the URL hierarchy clean and avoids search result duplication.

### `docusaurus.config.js` sketch

```js
// Four plugin instances
plugins: [
  // default docs instance (all non-archive docs)
  [
    '@docusaurus/plugin-content-docs',
    {
      id: 'docs',
      path: '../docs',
      routeBasePath: 'docs',
      sidebarPath: require.resolve('./sidebars.js'),
      exclude: ['archive/**', 'superpowers/specs/**'],
    },
  ],
  [
    '@docusaurus/plugin-content-docs',
    {
      id: 'tickets',
      path: '../tickets/done',
      routeBasePath: 'tickets',
      sidebarPath: require.resolve('./sidebars-tickets.js'),
    },
  ],
  [
    '@docusaurus/plugin-content-docs',
    {
      id: 'artifacts',
      path: '../stored_artifacts',
      routeBasePath: 'artifacts',
      sidebarPath: require.resolve('./sidebars-artifacts.js'),
    },
  ],
  [
    '@docusaurus/plugin-content-docs',
    {
      id: 'archive',
      path: '../docs/archive',
      routeBasePath: 'archive',
      sidebarPath: require.resolve('./sidebars-archive.js'),
    },
  ],
],
```

**`preset-classic` interaction:** `@docusaurus/preset-classic` includes its own default docs plugin instance. This MUST be disabled in the preset config (`docs: false`) when using manual plugin instances to avoid a "duplicate id" conflict at startup.

### Sidebar Strategy for this Ticket
This ticket is the skeleton — sidebars do not need custom logic yet. Use `{autoCollapseCategories: false}` with `autogenerated` items for all four instances. Ticket 7 adds custom ordering and grouping.

---

## docusaurus-search-local Integration Notes

Package: `@easyops-cn/docusaurus-search-local` (most widely maintained fork) or `docusaurus-search-local` (original). Both are compatible with Docusaurus 3.

**Recommended package:** `@easyops-cn/docusaurus-search-local` — actively maintained, supports multi-instance docs.

**Configuration in `docusaurus.config.js`:**
```js
themes: [
  [
    require.resolve('@easyops-cn/docusaurus-search-local'),
    {
      hashed: true,
      docsRouteBasePath: ['docs', 'tickets', 'artifacts', 'archive'],
      docsPluginId: ['docs', 'tickets', 'artifacts', 'archive'],
      indexBlog: false,
    },
  ],
],
```

**Key notes:**
- `hashed: true` produces cache-busted search index filenames — required for production builds.
- `docsRouteBasePath` must list all four route base paths so the plugin indexes all content.
- `docsPluginId` must match the `id` fields of the four plugin instances.
- Search only works after `make docs-build` (offline index is built at build time). `make docs-serve` in development mode uses a dev-server search that may show "no results" until the index is built once.
- `indexBlog: false` since the blog plugin will be disabled.

---

## Risks and Open Questions

### Risk 1: `docs/engine/` has 137 files
The `docs` plugin instance will ingest all of `docs/engine/` (137 files). Many are historical phase packages. Without frontmatter `status` fields (which come in Ticket 3), Docusaurus will auto-generate sidebar entries for all 137 files. This produces a large, unorganized sidebar for this ticket. **Mitigation:** Accept it for this ticket — the sidebar is autogenerated and the ticket's acceptance criteria only require the site starts without errors, not that it looks polished. Ticket 7 wires proper sidebars.

### Risk 2: `stored_artifacts/` nested structure
`stored_artifacts/` has one subdirectory per ticket ID, each with 2-3 markdown files. Docusaurus will auto-generate a sidebar with one folder per ticket. This is acceptable for this scaffold ticket — artifact grouping by ticket ID is Ticket 7 scope.

### Risk 3: Markdown files without frontmatter
Docusaurus 3 requires at minimum a valid markdown file with or without frontmatter — it does not fail on missing frontmatter. However, files without `title` in frontmatter will have their title inferred from the first `#` heading or filename. For the skeleton this is acceptable.

### Risk 4: `stored_artifacts/**/*.json` gitignore pattern
The existing `.gitignore` has `stored_artifacts/**/*.json`. This does not affect Docusaurus — it only ignores JSON files, not markdown. No conflict.

### Risk 5: `make docs-serve` pure Node vs Python venv
The ticket assumption is correct: Docusaurus is pure Node. `make docs-serve` should be `cd website && npm start` with no Python venv activation. The `dev` target pattern (running `cd frontend && npm run dev`) is the correct model to follow.

### Open Question 1: `docs/superpowers/specs/` in `docs` instance
The PLAN-DOCSITE.md notes 33 spec files under `docs/superpowers/specs/`. The `docs` instance could exclude these too (like `archive/**`) to keep the main docs section focused, or include them. Recommendation: exclude them from `docs` and either leave them out of the site for this ticket (acceptable) or add a 5th `specs` instance. Since the ticket specifies exactly four instances, exclude `superpowers/specs/**` from the `docs` instance and leave a note for Ticket 7 to decide.

### Open Question 2: `tickets/inprogress/` and `tickets/todos/`
The `tickets` plugin instance points at `tickets/done/` only. Open (inprogress) and todo tickets are not surfaced. This is intentional per the ticket scope. Confirm this is correct before implementation.

### Open Question 3: Docusaurus version pinning
Pin to `3.5.x` or track `^3`? Recommend `^3.5.2` with `package-lock.json` committed so the exact version is reproducible.
