# Deterministic Concurrent RPG Engine

A high-fidelity, deterministic 2D RPG simulation engine in Python with a React frontend. Parallelized AI agents propose intents; a single authoritative WorldLoop validates and executes them. Every run is byte-identical replay-faithful.

---

## Quick Start

```bash
make install    # Install all dependencies (Python + Node)
make serve      # Build frontend + start server at :8000
make cli        # Run a headless simulation (200 ticks)
```

**Requirements:** Python ≥ 3.11, Node.js ≥ 18, Docker (optional — for Grafana/Loki telemetry).

---

## Running the Engine

### Server mode — visual client at `http://127.0.0.1:8000`
```bash
python3 -m src serve --seed 42 --entities 50 --workers 4
```

### Headless CLI mode
```bash
python3 -m src cli --seed 42 --ticks 1000 --entities 50
OBS_MODE=DEBUG python3 -m src cli --ticks 100 --seed 42   # full observability
```

See [docs/guides/simulation.md](docs/guides/simulation.md) for world authoring, CLI flags, and artifact paths. Full CLI reference: [docs/observability/how_to_run_simulation.md](docs/observability/how_to_run_simulation.md).

---

## Architecture

| Principle | Summary |
|---|---|
| **Determinism** | All randomness from xxhash generators seeded per run — 100% replay fidelity |
| **Intent / Effect split** | Parallel AI workers propose intents; WorldLoop validates and executes |
| **Aspect composition** | Entities are pure compositions (`IdentityAspect`, `BodyAspect`, `MindAspect`, `SocialAspect`) |
| **Decoupled reads** | Thread-safe isolated read models let the API serve without locking the tick loop |
| **Content pipeline** | World modules, compositions, and archetypes resolved through a typed content pipeline before runtime |

Core laws: [Simulation Kernel](docs/engine/kernel.md) · [Authoritative Pipeline](docs/engine/authoritative_pipeline.md) · [Project Lawbook](docs/engine/project_lawbook_m10.md)

---

## Documentation Site

The project has a unified Docusaurus 3 documentation site that covers all content layers: mechanics laws, engine contracts, architecture, tickets, stored artifacts, and archived historical docs.

```bash
make docs-serve      # Start site at http://localhost:3000
make docs-build      # Build static site (website/build/)
make docs-registry   # Regenerate docs/REGISTRY.yaml after adding new docs
make docs-artifacts  # Regenerate stored_artifacts/*/index.md landing pages
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

Never run `pytest tests/` without scoping — scope to the domain under change. See [testing taxonomy](docs/testing/v2_test_taxonomy.md).

---

## AI Tooling

This project uses Claude Code subagents and workflows to automate the development and simulation lifecycle:

- **`/implement-ticket`** — full ticket lifecycle (scope → investigate → plan → review → implement → test → close)
- **`/investigate-simulation-result`** — deep multi-agent run analysis
- **`/generate-simulation-setup`** — generate world/scenario/experiment specs

See [docs/ai/](docs/ai/) for the full agent and workflow reference.

---

## Infrastructure (Optional)

Docker Compose manages Grafana, Loki, Redis, and RabbitMQ for production telemetry.

```bash
docker compose up -d     # start telemetry stack
# Grafana: http://localhost:3000  (admin/admin)
```

If Kafka/Redis throws `InconsistentClusterIdException`: `docker compose down -v && docker compose up -d --build`

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Tickets live in [`tickets/`](tickets/); active work tracked in [`tickets/working_log.csv`](tickets/working_log.csv).
