---
status: active
layer: guidelines
authority: P1
audience: agent
tags: [setup, tooling, knowledge-search, docker, rag]
---

# Agent Working Environment Setup

This document is the single reference for setting up and operating the local context search environment. Read it once before your first search call. It covers first-time setup, daily workflow, all commands, and troubleshooting.

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Docker Engine | 24+ | Required for `make search-server-docker` (primary) |
| Python | 3.12+ (floor); 3.13 is the CI-tested version | The floor is `requires-python` in `pyproject.toml`, which is the source; `[tool.mypy] python_version` and `[tool.ruff] target-version` move with it. CI (`.github/workflows/test.yml`) and `.python-version` use 3.13. The floor is 3.12 (owner decision 2026-10-09, amending roadmap decision 12). The 3.13 floor needs, on every host: a 3.13 system `python3` (hooks and `python3 tools/...` commands run under it, not a venv) and a 3.13 `.venv-knowledge`. `ubuntu`: both 3.13 (verified 2026-10-09). `u24desktop-Virtual-Machine`: both 3.12.3 (agent-working-planner, PR #456). |
| `uv` | 0.11+ | Resolves and installs from `pyproject.toml` and `uv.lock`. On this machine every `uv` network command needs `--system-certs` (see "TLS interception" below). |
| `uv sync --system-certs` (or `make install-py`) | — | Core app, test and dev deps from `uv.lock` (`fastapi`, `uvicorn`, `pytest`, etc.), plus the `lint` group (`ruff`, `complexipy`). Dependencies are declared once, in `pyproject.toml`. CI installs this way too (`uv sync --locked --no-install-project`); every CI job except `tools-a-e` passes `--no-group lint`. |
| `uv export --frozen --no-hashes --no-emit-project \| uv pip install -r -` | — | Same set (including the `lint` tools) for an environment that is not the project's own `.venv`, such as another worktree or `.venv-knowledge`. There is no committed `requirements.txt` any more (`TCK-20261008-DROP-UNUSED-REQUIREMENTS-EXPORT`): the export is generated on demand from `uv.lock`, and no CI job uses it. |
| `pip install -r requirements-knowledge.txt` | — | Knowledge-search stack: `torch`, `sentence-transformers`, `sqlite-vec`, `rank_bm25`. Local agent tooling only — CI never installs this. |

First-time model download: `all-MiniLM-L6-v2` (~22 MB) is downloaded automatically on first `make knowledge-index`. Subsequent builds use the local cache.

---

## Which virtualenv to use (u24desktop)

**Two venvs exist on purpose. Use the wrong one and you will get misleading results.**

| Venv | Python | Use it for | Why |
|---|---|---|---|
| `.venv` | **3.13.14** | **Engine, API, and all test runs** | Matches what CI actually runs (`.github/workflows/test.yml` declares `python-version: "3.13"`); holds only the locked default deps (`uv.lock`), no editable install of this package. Running tests on anything else means a local pass cannot rule out a version-specific CI failure. |
| `.venv-knowledge` | 3.12.3 | Knowledge-search tooling (`tools/knowledge_search.py`, `search_mcp.py`, `search_server.py`) **and** general local dev use | Holds `torch`/`sentence-transformers` (cannot be migrated to 3.13 — see below), **plus** the locked core app deps, **plus** this package itself editable-installed (`pip install -e .`, giving the `rpg-sim`/`rpg-world`/`rpg-lab` console scripts), **plus** `headroom-ai==0.37.0` (pinned in `requirements-knowledge.txt` since PR #228 — see `TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT`). It is not narrowly scoped to the knowledge stack; despite the name, it is this machine's fuller general-purpose venv. |

**Run tests as `.venv/bin/python3 -m pytest …`**, not the bare `python3` on PATH (which is 3.12,
still resolving to `.venv-knowledge`'s interpreter — see above).

*(Renamed `TCK-20260914-VENV-NAMING-CI-PARITY-SWAP`, 2026-09-21: `.venv` is now the CI-matching
environment; it used to be the knowledge-only one, which is exactly backwards from how the names
read. `.venv313` no longer exists as a name — the same 3.13 environment is simply `.venv` now.
**Correction, same day, 2nd pass**: this table previously described `.venv-knowledge` as
"knowledge-search tooling only." That was never accurate — confirmed via `pip show` against the
real installed venv, not assumed: it has always been a full general-purpose venv that also happens
to hold the knowledge stack, including this package's own editable install and headroom-ai. The
row above now reflects what is actually installed, not the narrower intent the original naming
implied.)*

### Why the knowledge stack is stuck on 3.12

`download.pytorch.org` is **blocked by this network's content filter**, not merely TLS-intercepted. Confirmed 2026-09-14:

```
openssl s_client -connect download.pytorch.org:443 | openssl x509 -noout -subject -issuer
subject=O = Fortinet, CN = Fortiguard SDNS Blocked Page
```

So `torch==2.12.1+cpu` cannot be installed for a new Python version from this machine by any tool. The existing `.venv-knowledge` predates the block and **must be preserved** — deleting it permanently breaks `search_docs` for every session here. `tools/start_search_mcp.sh` hardcodes its absolute path for exactly this reason. On any host it also finds the main checkout's `.venv-knowledge` from a git worktree through `git rev-parse --git-common-dir`, and it only selects an interpreter that has both `mcp` and `sentence_transformers`. A worktree has no knowledge index of its own (`agent-working/.index/` is gitignored), so `search_mcp.py` queries the main checkout's index when the worktree's own is missing (`TCK-20261010-SEARCH-MCP-WORKTREE-VENV-RESOLUTION`).

**Symptoms the block produces, none of which name the real cause:**
- `pip`: `Could not find a version that satisfies the requirement torch==2.12.1+cpu (from versions: none)` — pip fetched the *block page*, which lists no packages.
- `pip --trusted-host`: identical, because skipping verification just accepts the block page.
- `uv`: `invalid peer certificate: Other(OtherError(CaUsedAsEndEntity))`.

### TLS interception — a separate problem that looks the same

This network also intercepts TLS generally, via a corporate CA in the system store (`/usr/local/share/ca-certificates/tma-ADCA-CA.crt`). Tools shipping their own trust store fail with *unknown issuer* until pointed at the system one:

- `uv`: add `--system-certs` (`--native-tls` is the deprecated spelling). Without it even `uv python install` fails.
- A host that is outright *blocked* still fails after this fix. The two failures look alike and are not the same.
- GitHub Actions raw log fetching is blocked the same way — see CLAUDE.md's CI Failure Triage section.

### Installing Python versions without sudo

`sudo` needs an interactive password here. `uv` installs standalone builds into the user directory, touching nothing system-wide:

```bash
uv python install 3.13 --system-certs
uv venv .venv --python 3.13 --system-certs
uv sync --python .venv/bin/python3 --system-certs
```

---

## First-Time Setup

Run these once after cloning or after a clean checkout.

```bash
# 1. Install core Python dependencies into .venv from uv.lock
#    (drop --system-certs on a network without TLS interception)
uv sync --python 3.13 --system-certs
#    For another environment (worktree, .venv-knowledge), export on demand:
#    uv export --frozen --no-hashes --no-emit-project | uv pip install --python <env>/bin/python3 -r -

# 1b. Install the knowledge-search stack (torch must come from the CPU wheel index)
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements-knowledge.txt

# 2. Build the full knowledge index (tickets + investigations + docs/)
#    Expected: ~3,000–4,000 chunks; takes 3–5 minutes on first run (model download included)
make knowledge-index

# 3. Start the search server (Docker — primary)
make search-server-docker

# 4. Verify the server is healthy
curl -s http://localhost:8765/api/health
# Expected: {"status": "ok", "chunks": <N>, "model": "sentence-transformers/all-MiniLM-L6-v2", ...}
```

The Docker container runs with `restart: unless-stopped` — it will come back automatically after system restarts as long as Docker Engine is running.

`uv sync` installs the default dependencies plus the `dev` and `lint` groups (`[tool.uv] default-groups`),
and installs this package itself as editable. `make install-py` runs plain `uv sync`, so it also installs
the project as an editable package, which an export-based install does not; on a machine with TLS
interception set `UV_SYSTEM_CERTS=1` before `make install-py` (the environment variable for `--system-certs`). It does not install the knowledge-search stack: that stays in
`requirements-knowledge.txt` and `.venv-knowledge` (step 1b), unchanged. The opt-in `profiling`
group (`memray`) is installed with `uv sync --group profiling`.

### Changing a dependency

Dependencies are declared in one place, `pyproject.toml` (`TCK-20261002-UV-DECLARE-AND-LOCK`):
runtime packages under `[project] dependencies`, test and dev tooling under
`[dependency-groups] dev`, and the code-health tools (`ruff`, `complexipy`) under `lint`. The `lint` group
is kept out of `dev` so that CI jobs that do not run the code-health tests can skip it with
`uv sync --no-group lint`; `default-groups` keeps a plain `uv sync` unchanged. After editing it, refresh the lock and commit
`pyproject.toml` and `uv.lock` together:

```bash
uv lock --system-certs
```

**After the Python Code Craft branch merges, every existing environment (the main checkout's
`.venv`, other worktrees) must re-run `uv sync --system-certs` (or the on-demand export above).**
`ruff` and `complexipy` are now `lint` dependencies (the `Code health` and `Code health SARIF (advisory)` jobs sync them too), and the codebase-health snapshot measures with them
live, so tests such as `tests/codebase/test_codebase_health_snapshot.py`'s throwaway-repository tests fail
in an older environment with `complexipy not found: install the project environment (uv sync)`. That
failure is deliberate: the snapshot never silently skips its craft metrics. CI is unaffected because
the one job that runs those tests (`tools-a-e`) syncs the `lint` group, and the default `uv sync` carries both tools.

`uv lock --check` exits non-zero if `uv.lock` is out of date with `pyproject.toml`. The export leaves out extras, so `torch`,
`sentence-transformers`, `sqlite-vec` and `rank-bm25` never reach the default install
(`tests/static/test_ci_requirements_no_ml_stack.py` pins this by walking `uv.lock` from the default roots).

### Reading code-health results on a PR

Three CI jobs report on a pull request. Two block it since `TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING`
(roadmap decisions 8.5, 8.10, 8.18): `Code health` and `Type check`. The third, `Code health SARIF (advisory)`,
is changed-line feedback only and stays advisory permanently (decision 8.19).

1. **Job summary first** (the run's Summary page, which agents can read without special access):
   `Code health` (the ratchet over `src/`, new or worse violations, those in files the PR
   changed first), `Code health SARIF (advisory)` (what the SARIF filter kept and dropped) and the
   `Type check` job's `mypy` step (new mypy errors and the baseline size). A new or worse violation of ruff,
   complexipy or a line count, a new mypy error, or a check that cannot run fails the job and leaves one
   `::error::` annotation; a tool that could not run says "could not run" in the summary. A new or worse
   ast-grep finding (rules N3, N4, E3, `codebase/rules/`) blocks too since
   `TCK-20261004-AST-GREP-RULE-PACK-FLIP-BLOCKING`. jscpd findings are **report-only**: listed and labelled in the
   summary, never failing. The `Code health` job also runs `python3 -m codebase.structure.packages validate`: a
   new top-level `src/` package without a row in `codebase/structure/package_registry.jsonl` (or a row for a
   package that is gone) fails it; run that command locally to reproduce it. The one tolerated failure is jscpd
   itself (it needs `npx` and
   the npm registry): if it cannot run, the check says "jscpd could not run (report-only); its findings were not
   measured" in the summary and as a `::warning::`, leaves its registry rows alone and still exits 0, so a local
   `make code-health` without network prints that note instead of exiting 2. `seed` and `tighten` never skip a tool.
2. **Code scanning second** (the PR's Files view and the Security tab, category `code-health`):
   `Code health SARIF (advisory)` uploads findings in the PR's changed `src/**/*.py` files that the
   registry does not already hold. SARIF results have no identity, so the filter works per ratchet unit: a
   ruff (file, rule) group above its ceiling is shown **whole, older findings of that rule in the file
   included**, and the summary says so; do not read every finding of such a group as new. A function is
   shown when its cognitive complexity is above its row's ceiling. The job runs only for pull requests from
   this repository (a fork's token is read-only) and uploads an empty SARIF when no `src` Python file
   changed, so the upload path is exercised on every such PR. If the upload is rejected, enabling code
   scanning for the repository is an owner setting; the job stays green either way (decision 8.19). Security note: this job
   runs the PR's own `uv.lock`, `pyproject.toml` and `tools/` while it holds `security-events: write`; that is
   accepted only because the `if` keeps fork PRs out and a same-repository author already has write access.
   Do not widen that `if` (for example to `pull_request_target`) without a new security review.
3. Locally: `make code-health` (ratchet), `make typecheck-py` (mypy through the baseline) and
   `python3 -m codebase.gates.sarif_feedback --changed FILE --out SARIF` (the SARIF the job would upload).

### Reading the import-contract result (advisory)

The `Import contracts` step is the last step of the `code-health` CI job. It runs the import-linter contracts in
`codebase/structure/importlinter.toml` (`TCK-20261004-IMPORT-LINTER-ADOPTION`) and can never fail the job: the
command exits 0 whatever it finds and the step has its own `continue-on-error`. `Code health` is a required check
(`TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING`), but this step stays advisory: a broken contract is a summary line
and a `::warning::`, never a red required check. Blocking is a separate, later step
(`TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT`).

- **Job summary:** one line `Import contracts (advisory): N kept, M broken` (plus stale ignored imports), then each
  broken contract by name. One `::warning::` annotation appears when a contract is broken, stale or could not
  run ("could not run" is shown instead of looking like a pass).
- **A broken contract** means a new import crosses a boundary: the `layers` contract (order from
  `codebase/structure/package_registry.jsonl`, 135 existing upward imports held in
  `codebase/structure/import_layers_baseline.txt`) or one of the class E and loophole contracts. Run locally for the
  import lines. **A stale ignored import** means an excepted import no longer exists: delete its entry.
- **Locally:** `make import-contracts` (the same step), or for the full import lines
  `uvx --from import-linter==2.15 lint-imports --config codebase/structure/importlinter.toml` (`lint-imports` is in
  the `lint` group). After a registry change: `python3 -m codebase.structure.import_contracts` rewrites the
  generated `layers` block, `--check` reports a stale one; `seed-baseline` accepts the current violations (a
  deliberate reseed, never to hide a new import).
- The existing `tests/architecture/` import tests still run beside the contracts; nothing is retired until
  `TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT`.

### Git hooks (opt-in)

The hook scripts and the installer live in `codebase/hooks/` (moved from `tools/hooks/` by `TCK-20261003-CODEBASE-DOMAIN-ROOT-MOVE`; `post-commit-reindex.sh` stays in `tools/hooks/`). prek's generated shim reads `.pre-commit-config.yaml` when a commit runs, so an existing install picks up the new paths by itself; re-running `make install-prek-hooks` is idempotent and safe if you want to be sure.

Two optional hooks, installed only when someone runs `make install-prek-hooks`; nothing installs them
automatically (no make target, script, CI step or session hook), and CI stays the real gate.

- **What they do.** `pre-commit` (run by [prek](https://github.com/j178/prek), pinned in the `dev` group,
  configured in `.pre-commit-config.yaml`): `code-health-ratchet` runs ruff on the staged `src/**/*.py` files
  and rejects the commit only for a violation that is **new or above its row** in
  `codebase/baselines/code_health_exceptions.jsonl` (a commit touching only grandfathered code passes; it uses the
  ratchet's own NEW / WORSE report); `uv-lock-check` runs `uv lock --check --offline` only when
  `pyproject.toml` or `uv.lock` is staged (no network, ever). `post-commit` is the incremental knowledge reindex
  (`tools/hooks/post-commit-reindex.sh`, a no-op unless docs/ or `agent-working/tickets/done/` changed and a
  knowledge index exists). The check sees the **staged** content: prek stashes unstaged changes while the
  hooks run and restores them afterwards.
- **Install affects every worktree on this machine.** `.git/hooks` is the common directory shared by all
  worktrees of this repository, so once anyone installs, the pre-commit hook runs on every commit in every
  worktree, including ones with no project environment and ones on a branch cut before this config existed. The
  hooks therefore never block for a missing environment: without ruff, without the registry, without
  `codebase.health` or without `uv` they print one visible `... skipped: ...` line and exit 0. The same holds for
  prek's own hook: the installer uses `--allow-missing-config` (a tree with no `.pre-commit-config.yaml` commits
  normally, silently) and adds a guard to prek's generated `pre-commit` script, so if prek itself cannot be found (the
  environment was re-synced without it, or deleted) it prints `pre-commit hook skipped: prek not found ...` and
  exits 0 instead of failing every commit on the machine. Only a real new or worse violation (or a stale
  `uv.lock`) blocks, and only where the config, prek and the project environment are all present.
- **`make install-prek-hooks` never overwrites.** `post-commit` is installed only when absent (identical ->
  no change; a different one is kept and reported). An existing foreign `pre-commit` hook is kept by prek as
  `pre-commit.legacy` and still runs. Running it twice changes nothing. By contrast the older
  `make install-hooks` **overwrites** `.git/hooks/post-commit` with `cp`; use `install-prek-hooks` unless you
  want exactly that. `post-merge` (from `make setup-merge-drivers`) and every other hook are never touched.
- **Bypass.** `git commit --no-verify` skips the hooks. Use it only with the owner's say-so (for example
  owner-approved debt, or fixing the gate itself), never to get a new violation past the ratchet; CI runs the
  same check as a required check and will fail the PR anyway.
- **Uninstall.** `make uninstall-prek-hooks` removes prek's pre-commit shim (restoring a legacy hook, if
  any) and removes `post-commit` only if it is byte-identical to the repository's reindex hook.
- **Verify in a scratch clone, never here.** To try the hooks, `git clone --no-hardlinks` the repository into a
  scratch directory and run the installer there (`python3 -m codebase.hooks.install_git_hooks install --repo <clone>`);
  installing in the main checkout changes the shared hooks of every session on the machine.

---

## Daily Workflow

The server is already running from first-time setup. Normal working sessions need no action unless docs change.

### After modifying or adding a file under `docs/`

The CLAUDE.md After Work rule also covers this — it is repeated here for completeness.

```bash
# Incremental reindex: only re-embeds changed files (~10–60 seconds)
make knowledge-index-update
```

The running Docker container picks up the new index on its next query — no restart needed.

### After closing a ticket (ticket moved to `agent-working/tickets/done/`)

```bash
make knowledge-index-update
```

Same command. The incremental build detects the new file in `agent-working/tickets/done/` and adds it.

### Automatic reindex on commit (optional but recommended)

```bash
# Install git post-commit hook — runs make knowledge-index-update automatically
# when a commit touches docs/ or agent-working/tickets/done/
make install-hooks
```

Once installed, the hook is silent on unrelated commits and self-skips if `agent-working/.index/knowledge-index/` does not exist.

---

### Derived indexes pile up in every worktree

Each git worktree builds its own `agent-working/.index/` (knowledge index ~105M, agent-monitoring index ~145M). Both are untracked and regenerable, and a per-worktree index is always current for that worktree's own docs, so there is deliberately no shared index across branches. Reclaim the space from worktrees you are no longer using:

```bash
python3 tools/prune_worktree_indexes.py                 # report only, 7-day idle threshold
python3 tools/prune_worktree_indexes.py --days 3 --apply  # delete idle worktrees' knowledge + monitoring indexes
```

It never touches the current worktree, the main checkout or the parity index. Rebuild a pruned one with `make knowledge-index` (re-runs the embedding model) or `make agent-monitoring-index`. The index path is anchored to the checkout that owns `tools/knowledge_search.py`, not the process working directory, so `search_docs` (MCP) and `tools/knowledge_search.py` resolve the same index from any start directory.

## Command Reference

| Command | What it does |
|---|---|
| `make knowledge-index` | Full rebuild — embeds all docs, tickets, investigations from scratch. Use after model change or first setup. |
| `make knowledge-index-update` | Incremental rebuild — re-embeds only changed/new/deleted files. Use after normal doc or ticket changes. |
| `make kgmcp-bootstrap` | Runs `parity-index` + `knowledge-index` together — one-command fresh-environment setup. See "Other Local, Gitignored Caches" below. |
| `make search-server-docker` | **Primary.** Start the search server in Docker (persistent, survives terminal close and system restart). |
| `make search-server-stop` | Stop the Docker container. |
| `make search-server-logs` | Tail the Docker container logs. |
| `make search-server` | **Fallback only** (no Docker). Starts uvicorn directly; exits when the terminal closes. |
| `make install-hooks` | Install git post-commit hook for automatic incremental reindex. |
| `make eval-search` | Run the curated 40-query evaluation set; reports Recall@5 and MRR@10. |

---

## Verifying Search Works

### HTTP (primary — requires Docker server running)

```bash
# Natural-language query
curl -s -X POST http://localhost:8765/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "how does the damage formula work", "top_k": 5}' \
  | python3 -m json.tool

# Exact-term query
curl -s -X POST http://localhost:8765/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "WorldRepository", "top_k": 3}'

# Filter by section
curl -s -X POST http://localhost:8765/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "authoritative mutation phases", "top_k": 5, "filters": {"section": "engine"}}'
```

Expected response shape:

```json
{
  "query": "how does the damage formula work",
  "top_k": 5,
  "results": [
    {
      "doc_id": "mechanics/02_combat_laws#h2-damage-formula-001",
      "title": "Combat Laws",
      "heading": "Damage Formula",
      "source_path": "docs/mechanics/02_combat_laws.md",
      "section": "mechanics",
      "score": 0.84,
      "semantic_score": 0.79,
      "keyword_score": 0.62,
      "excerpt": "..."
    }
  ]
}
```

### CLI (fallback — no server required)

```bash
python3 tools/knowledge_search.py query "how does the damage formula work" --top-k 5
python3 tools/knowledge_search.py query "WorldRepository" --top-k 3 --mode keyword
python3 tools/knowledge_search.py query "stamina pressure combat" --top-k 5 --mode hybrid
```

---

## MCP Setup (Agent-Native Tool — Recommended)

`search_docs` is a native Claude Code MCP tool — no curl or bash needed.

### Registration

`.mcp.json` (project root) contains:

```json
{
  "mcpServers": {
    "knowledge-search": {
      "command": "python3",
      "args": ["tools/search_mcp.py"],
      "description": "Local semantic search over project docs, tickets, and investigations"
    }
  }
}
```

Claude Code spawns `tools/search_mcp.py` on startup. The MCP server loads the index once and stays resident — it does **not** require the Docker HTTP server to be running.

### Verify MCP is working

```bash
make mcp-server-test
```

Or restart Claude Code and confirm `search_docs` appears in `/tools`.

### Using the MCP tool (agent calls this natively)

```
search_docs(query="how does the damage formula work", top_k=5)
search_docs(query="WorldRepository", top_k=3, mode="keyword")
search_docs(query="authoritative mutation phases", top_k=5, section="engine")
search_health()
```

No curl. No bash. Results arrive as a structured tool response directly in context.

### When the index is stale

Each worktree searches its own index (`agent-working/.index/knowledge-index/`), so a worktree on another branch, or one whose docs
and tickets changed since the last `make knowledge-index-update`, quietly searches an older corpus. Both search paths now compare
the index's `manifest.json` (source path to mtime) with the files on disk, by `stat` only (about 0.1 s on the real corpus), and say so:

- CLI `tools/knowledge_search.py query` prints one stderr line, `knowledge index is stale: N changed, N new, N removed -- run make knowledge-index-update`.
- MCP `search_docs` returns `{"results": [...], "stale": {"changed": N, "new": N, "removed": N}}` instead of the bare list. A current index still returns the bare list.
- A missing or unreadable `manifest.json` gives `staleness unknown` (CLI) or `"stale": {"unknown": true}` (MCP).

Results are returned either way; the warning never blocks and nothing is rebuilt for you. Run `make knowledge-index-update`, then search again.
A file that yields no document (an empty body, a ticket without a Request Summary) can count as `new` forever, so a small non-zero `new` is not by itself a problem.

### Priority order for agents

| Priority | Method | When |
|---|---|---|
| 1 | `search_docs` MCP tool | MCP server registered (normal case) |
| 2 | `curl POST http://localhost:8765/api/search` | Docker HTTP server running, MCP not registered |
| 3 | `python3 tools/knowledge_search.py query "..." --top-k 5` | No server, no MCP — CLI fallback |

---

## Agent Usage Pattern

In skill or workflow code, the agent calls the MCP tool natively. If MCP is not available, fall back to HTTP, then CLI:

```
# 1. MCP tool (preferred — native, no bash)
search_docs(query=QUERY, top_k=5)

# 2. HTTP fallback (if MCP not registered)
if curl -sf http://localhost:8765/api/health > /dev/null 2>&1; then
  curl -s -X POST http://localhost:8765/api/search \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"$QUERY\", \"top_k\": 5}"

# 3. CLI fallback (no server at all)
else
  python3 tools/knowledge_search.py query "$QUERY" --top-k 5
fi
```

If none of the above is available, skip the search step silently and continue — do not block the workflow.

---

## Fallback Mode (No Docker)

If Docker is not available in your environment:

```bash
# Start the server directly (exits when terminal closes)
make search-server

# Keep it running in the background
nohup make search-server &> /tmp/search-server.log &

# Or use a separate terminal window
```

All HTTP queries work identically. The only difference is the server does not auto-restart.

---

## Index Lifecycle Rules

| Situation | Command |
|---|---|
| First setup or after changing embedding model | `make knowledge-index` (full) |
| After adding/editing a doc in `docs/` | `make knowledge-index-update` |
| After closing a ticket (new file in `agent-working/tickets/done/`) | `make knowledge-index-update` |
| After deleting a doc | `make knowledge-index-update` |
| Index seems stale or returning wrong results | `make knowledge-index` (full rebuild) |
| Switching to a different embedding model | `make knowledge-index` (full rebuild) |

---

## Other Local, Gitignored Caches

The semantic search index above is one of four local, disposable caches this repository uses. None
of them are committed — all four are deliberately rebuildable-only. Three of the four (semantic
search index, parity ledger query index, Knowledge Gateway MCP cache) exist to support the Knowledge
Gateway MCP and follow its own principle that "the local database must remain disposable and
rebuildable" (`docs/plans/knowledge-gateway-mcp-proposal.md` §10, `tmp/mcp-followup-instruction.md`
§10); the fourth (the `graphify` CLI's code-graph index) is unrelated to the Knowledge Gateway MCP but
shares the same disposable/rebuildable design. If you are setting up a fresh checkout or moving to a
new environment, none of these need to be copied — rebuild them instead:

| Artifact | Real path | What it is | Gitignored? | How to rebuild |
|---|---|---|---|---|
| Semantic search index | `agent-working/.index/knowledge-index/knowledge.db`, `bm25.pkl`, `embeddings_cache.pkl`, `manifest.json` | The `search_docs` index described above | Yes (`.gitignore:264`) | `make knowledge-index` |
| Parity Ledger query index | `agent-working/.index/parity-index/parity.db` | Read-only SQLite index over `docs/parity_ledger/*.yaml`, built by `tools/parity_index.py` | Yes (`.gitignore:271`) | `make parity-index` |
| Knowledge Gateway MCP cache | `agent-working/.index/knowledge-index/retrieval_cache.db` | The Knowledge Gateway MCP's Level 1 (provider-result) and Level 2 (assembled-packet) cache — see `docs/plans/knowledge-gateway-mcp-proposal.md` §10 for the cache design | Yes (same `agent-working/.index/knowledge-index/` ignore rule) | No bootstrap command exists — see below |
| `graphify` code-graph index | `graphify-out/graph.json` (plus other `graphify-out/*` build output) | The `graphify` CLI's persistent knowledge graph — god nodes, community detection, and query/path/explain data described in `graphify-out/GRAPH_REPORT.md` | Yes (`.gitignore:260` `graphify-out/*`, `.gitignore:261` `src/graphify-out/`) | `graphify update .` (incremental, AST-only) or a full `/graphify` rebuild — see `CLAUDE.md`'s Graphify Integration section |

**One-command bootstrap for a fresh environment:**

```bash
make kgmcp-bootstrap    # runs parity-index + knowledge-index in sequence
```

**`retrieval_cache.db` has no explicit rebuild command.** Unlike the other two, its Level 1/Level 2
tables (`tools/retrieval_cache.py`'s `_get_level1_connection()`/`_get_level2_connection()`) are only
created lazily, the first time a real `knowledge_context` or `knowledge_status` MCP call runs against
a fresh environment — the schema self-initializes empty and then warms up from real usage. This is
intentional, not a gap: there is nothing meaningful to pre-populate it with (cached provider results
and assembled packets only exist after real queries run), so `kgmcp-bootstrap` does not attempt to
touch it. Expect the gateway's own cache-hit rate to start at 0 in any new environment and warm up
naturally.

---

## Troubleshooting

**Server not responding (`connection refused` on :8765)**
```bash
make search-server-logs        # check container logs
docker ps                      # verify container is running
make search-server-docker      # restart if stopped
```

**Index stale after doc changes**
```bash
make knowledge-index-update    # incremental reindex
# verify with: curl http://localhost:8765/api/health  (check "chunks" count increased)
```

**Model download is slow on first build**

`all-MiniLM-L6-v2` is ~22 MB. It downloads once to the sentence-transformers cache and is baked into the Docker image at build time. If `make knowledge-index` hangs on the first run, wait — it is downloading. Subsequent runs use the cache.

**Git hook failing on first commit (no `HEAD~1`)**

The hook guards against this: `git rev-parse HEAD~1 2>/dev/null || exit 0`. If you see an error, verify the hook file was installed correctly: `cat .git/hooks/post-commit`.

**`sqlite-vec` version mismatch**

If `make knowledge-index` fails with a sqlite-vec error, check: `python3 -c "import sqlite_vec; print(sqlite_vec.__version__)"`. The required minimum version is listed in `requirements-knowledge.txt`.

**Search returns no results for a doc that exists**

Run `make knowledge-index-update`. The file may have been added after the last build. If the problem persists after update, run `make knowledge-index` (full rebuild) and re-check.

---

## Related Tickets

- `TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH` — CLI tool foundation
- `TCK-20260612-LOCAL-CTX-DOCS-CORPUS` — docs/ corpus expansion
- `TCK-20260612-LOCAL-CTX-HYBRID-SEARCH` — BM25 + hybrid scoring
- `TCK-20260612-LOCAL-CTX-HTTP-API` — FastAPI server
- `TCK-20260612-LOCAL-CTX-OPS` — Docker, incremental reindex, git hook, skill wiring
- `TCK-20260612-LOCAL-CTX-MCP` — MCP server, `search_docs` native tool, settings.json registration
