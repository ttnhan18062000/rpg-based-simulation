---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260606-DOCSITE-SCAFFOLD
artifact_type: test_plan
tags: [docsite, scaffold]
---

# Test Plan — TCK-20260606-DOCSITE-SCAFFOLD

## Regression Surface

The following existing Makefile targets must continue to work without modification after this ticket's changes. These are the blast-radius targets — any of them breaking would constitute a regression.

| Target | Command | What it does |
|---|---|---|
| `install-fe` | `cd frontend && npm install` | Installs Vite/React frontend deps |
| `build` | `cd frontend && npm run build` | Builds React SPA to `frontend/dist/` |
| `dev-frontend` | `cd frontend && npm run dev` | Starts Vite dev server on :5173 |
| `lint` | `cd frontend && npm run lint` | Runs ESLint on frontend |
| `typecheck` | `cd frontend && npx tsc --noEmit` | TypeScript check on frontend |
| `clean` | removes `frontend/dist`, `__pycache__` | Must not affect `website/` |
| `test` | `pytest tests_v2/` | Python suite — unaffected by Node changes |
| `test-quick` | `pytest tests/ -m "not slow"` | Python suite — unaffected |

**Verification method:** Run each target manually after scaffolding `website/` and adding Makefile entries. Confirm exit code 0 and no unexpected output.

---

## Verification Approach

### Primary Acceptance Gates

#### Gate 1: `make docs-serve` starts without errors
```
make docs-serve
```
Expected: Docusaurus dev server starts, prints a URL (`http://localhost:3000`), and all four plugin instances report successful initialization. No `Error:` lines in startup output.

Manual check: open `http://localhost:3000` in browser and confirm:
- Homepage loads with navigation links to all four sections
- `/docs/` is reachable (at least the index page)
- `/tickets/` is reachable
- `/artifacts/` is reachable
- `/archive/` is reachable

#### Gate 2: `make docs-build` produces a static build without errors
```
make docs-build
```
Expected: `website/build/` directory is created and populated. No `Error:` or `Warning:` lines that indicate broken links or missing plugin configuration. Exit code 0.

Post-build check:
- `website/build/index.html` exists
- `website/build/docs/` directory exists
- `website/build/tickets/` directory exists
- `website/build/artifacts/` directory exists
- `website/build/archive/` directory exists
- Search index file exists: `website/build/search-index.json` or equivalent (`search-index-*.json` if hashed)

#### Gate 3: `website/node_modules/` and `website/build/` are gitignored
```
git status
```
Expected: after running `npm install` inside `website/` and `make docs-build`, neither `website/node_modules/` nor `website/build/` nor `website/.docusaurus/` appear as untracked files.

Verify:
```
git check-ignore -v website/node_modules website/build website/.docusaurus
```
All three should return a matching `.gitignore` rule.

#### Gate 4: Existing frontend targets unaffected
```
make install-fe   # exit 0
make lint         # exit 0
make typecheck    # exit 0
```

---

## Scoped Pytest Commands

This ticket makes no changes to Python source code or test files. There are no Python tests that directly test the Makefile or `website/` scaffolding.

**Run after implementation to confirm no Python-side regressions:**

```bash
# Architecture guard — fastest, confirms no import or structural regressions
python3 -m pytest tests/ -m "architecture" -v --tb=short

# Catalog lane — content resolution and adapter heuristics
python3 -m pytest tests/ -m "catalog or content_graph" -v --tb=short
```

Do NOT run `pytest tests_v2/` or the full suite — this ticket has no Python surface area.

If CI runs `make test` as part of a pipeline, confirm it still exits 0 after the Makefile gains the two new targets.

---

## Anti-Drift Test Guards

These are checks that prevent the scaffold from silently diverging from the ticket's acceptance criteria as future tickets modify `website/`.

### Guard 1: Four plugin instances remain registered
After implementation, the `docusaurus.config.js` must contain exactly four `@docusaurus/plugin-content-docs` plugin entries with IDs `docs`, `tickets`, `artifacts`, `archive`.

Manual check (or future CI step):
```bash
grep -c "plugin-content-docs" website/docusaurus.config.js
# Expected: 4
```

### Guard 2: Search plugin references all four route bases
```bash
grep "docsRouteBasePath" website/docusaurus.config.js
# Expected: array containing 'docs', 'tickets', 'artifacts', 'archive'
```

### Guard 3: `.gitignore` covers all three website/ artifacts
```bash
grep "website/" .gitignore
# Expected: website/node_modules/, website/build/, website/.docusaurus/
```

### Guard 4: Makefile `.PHONY` updated
```bash
grep "^.PHONY" Makefile
# Expected: includes docs-serve and docs-build
```

### Guard 5: No new Python deps introduced
```bash
git diff requirements.txt
# Expected: empty (this ticket is pure Node)
```

### Guard 6: `make clean` does not wipe `website/build/`
```bash
grep "website" Makefile | grep "rm"
# Expected: no output (clean does not touch website/)
```
This is intentional — `website/build/` is a Docusaurus output, not a temporary run artifact. A future `make docs-clean` target may be added but is not part of this ticket's scope.

---

## Out-of-Scope Test Scenarios (deferred to Ticket 7)

- Sidebar ordering and custom category labels
- Tag index page generation from frontmatter
- Status badge rendering
- Artifact grouping by ticket ID
- Search result quality and ranking
- Cross-instance search (searching from `/tickets/` finds results in `/docs/`)
