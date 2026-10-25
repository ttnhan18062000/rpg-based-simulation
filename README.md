# Deterministic Concurrent RPG Engine

A high-fidelity, deterministic 2D RPG simulation engine in Python with a React frontend. Parallelized AI agents propose intents; a single authoritative WorldLoop validates and executes them. The same seed replays to the same state hash on one machine under the Canonical signal contract; the [Deterministic Execution Contract](docs/engine/deterministic_execution.md) states the scope.

---

## Quick Start

```bash
make install    # Install all dependencies (Python + Node)
make serve      # Build frontend + start server at :8000
make cli        # Run a headless simulation (200 ticks)
```

**Requirements:** Python ≥ 3.12, Node.js ≥ 18, Docker (optional — for Grafana/Loki telemetry). On Windows, run `make` under WSL or Git Bash (there is no `make.bat`).

---

## Running the Engine

### Server mode — visual client at `http://127.0.0.1:8000`
```bash
python3 -m src serve --seed 42 --workers 4
```

### Headless CLI mode
```bash
python3 -m src cli --seed 42 --ticks 1000
OBS_MODE=DEBUG python3 -m src cli --ticks 100 --seed 42   # full observability
```

See [docs/guides/simulation.md](docs/guides/simulation.md) for world authoring, CLI flags, and artifact paths. Full CLI reference: [docs/observability/how_to_run_simulation.md](docs/observability/how_to_run_simulation.md).

---

## Architecture

| Principle | Summary |
|---|---|
| **Determinism** | Stateless seeded RNG: `DeterministicRNG` seeds a fresh `random.Random` per draw from the run seed, domain, tick and entity. A SHA-256 canonical state hash is the proof. Guaranteed tier, Canonical signal contract and known gaps: [Deterministic Execution Contract](docs/engine/deterministic_execution.md) |
| **Intent / Effect split** | Parallel AI workers propose intents; WorldLoop validates and executes |
| **Aspect composition** | Entities are pure compositions (`IdentityAspect`, `BodyAspect`, `MindAspect`, `SocialAspect`) |
| **Decoupled reads** | Thread-safe isolated read models let the API serve without locking the tick loop |
| **Content pipeline** | World modules, compositions, and archetypes resolved through a typed content pipeline before runtime |

Core laws: [Simulation Kernel](docs/engine/kernel.md) · [Authoritative Pipeline](docs/engine/authoritative_pipeline.md) · [Project Lawbook](docs/engine/project_lawbook_m10.md)

---

## For reviewers

- Determinism demo: [`make replay-check`](docs/guides/reviewer_replay_check.md) runs one seed twice and compares the final state hashes.

---

## Documentation Site

The project has a unified Docusaurus 3 documentation site that covers all content layers: mechanics laws, engine contracts, architecture, tickets, stored artifacts, and archived historical docs.

```bash
make docs-serve      # Start site at http://localhost:3000
make docs-build      # Build static site (website/build/)
make docs-registry   # Regenerate docs/REGISTRY.yaml after adding new docs
make docs-artifacts  # Regenerate agent-working/stored_artifacts/*/index.md landing pages
```

The site has four sections:

| Section | URL | Contents |
|---|---|---|
| **Docs** | `/docs/` | Mechanics Bible, engine contracts, architecture, guidelines — grouped by layer |
| **Tickets** | `/tickets/` | All closed tickets (~657), searchable |
| **Artifacts** | `/artifacts/` | Investigation, plan, and test_plan files per ticket |
| **Archive** | `/archive/` | Historical docs and design specs |

Full-text search works across all four sections. Every page shows a status badge (`authoritative` / `active` / `historical` / `archive`) drawn from the file's YAML frontmatter.

**How docs are classified:** every `.md` file carries a YAML frontmatter block (`status`, `layer`, `authority`, `audience`). The schema is defined in [`docs/guidelines/frontmatter_schema.md`](docs/guidelines/frontmatter_schema.md). Run `python3 tools/validate_frontmatter.py <path>` to check any file or directory.

**Machine-readable index:** [`docs/REGISTRY.yaml`](docs/REGISTRY.yaml) is a flat list of all tagged docs and closed tickets (912 entries). Agents and scripts query it instead of scanning 500+ files.

---

## Documentation Reference

| Area | Location |
|---|---|
| **Developer guides** (how-to, quickstarts) | [`docs/guides/`](docs/guides/) |
| Mechanics Bible (simulation laws and formulas) | [`docs/mechanics/`](docs/mechanics/) |
| Engine contracts and kernel spec | [`docs/engine/`](docs/engine/) |
| Core state, entities, attributes | [`docs/core/`](docs/core/) |
| Architecture decisions (ADRs) | [`docs/architecture/`](docs/architecture/) |
| Observability and how to run | [`docs/observability/`](docs/observability/) |
| Compliance, parity ledger, divergences | [`docs/parity_ledger/`](docs/parity_ledger/) · [`docs/guidelines/`](docs/guidelines/) |
| Design patterns and coding conventions | [`docs/guidelines/design_patterns.md`](docs/guidelines/design_patterns.md) |
| AI tooling (agents, workflows, skills) | [`docs/ai/`](docs/ai/) |
| Frontmatter schema (doc classification) | [`docs/guidelines/frontmatter_schema.md`](docs/guidelines/frontmatter_schema.md) |
| Doc registry (machine-readable index) | [`docs/REGISTRY.yaml`](docs/REGISTRY.yaml) |

Full doc index: [docs/README.md](docs/README.md)

---

## Testing

```bash
pytest tests/unit/            # unit tests (fast)
pytest tests/ -m "not slow"   # exclude long integration runs
```

Resource budgets (for memory/timeout control in constrained environments):
```bash
pytest tests/ --resource-budget=small    # 1 GB RAM, 15s timeout
pytest tests/ --resource-budget=medium   # 4 GB RAM, 60s timeout (default)
pytest tests/ --resource-budget=off      # no limits
```

Never run `pytest tests/` without scoping — scope to the domain under change. See [testing taxonomy](docs/testing/test_taxonomy.md).

---

## AI Tooling

This project uses Claude Code subagents and workflows to automate the development and simulation lifecycle:

- **`/implement-ticket`** — full ticket lifecycle (scope → investigate → plan → review → implement → test → close)
- **`/investigate-simulation-result`** — deep multi-agent run analysis
- **`/generate-simulation-setup`** — generate world/scenario/experiment specs

See [docs/ai/](docs/ai/) for the full agent and workflow reference.

---

## Infrastructure (Optional)

Docker Compose (`compose.yaml` at the root; Dockerfiles and ops configs in `docker/`) runs two profiles. The only broker is
Redis Streams; there is no Kafka or RabbitMQ (`docs/architecture/devops_baseline_adr.md`).

```bash
docker compose up -d                                  # backend, redis, ai_worker, frontend
docker compose --profile observability up -d          # adds Prometheus, Grafana, Loki, Promtail, Tempo, ntfy and the exporters
# Grafana: http://localhost:3000 (user admin; the password is the gitignored secret file docker/secrets/grafana_admin_password)
```

The observability profile needs its secret files first (Grafana password, ntfy topic and token): the steps are in the header of
`compose.yaml`. Alerts, drills and first checks are in [`docs/runbooks/`](docs/runbooks/README.md).

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Tickets live in [`agent-working/tickets/`](agent-working/tickets/); active work tracked in [`agent-working/tickets/working_log.csv`](agent-working/tickets/working_log.csv).
