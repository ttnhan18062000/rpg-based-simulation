# Investigation - Lab CLI (Milestone 81)

We investigated the subcommands and repository layouts, ensuring full alignment with established V2 command-line patterns.

## Findings
* **CLI Library**:
  - We will use standard `argparse` as used in `src/cli/entry.py` and `src/worldbuilding/cli.py`.
  - We must print error trackbacks clearly when appropriate, but handle standard spec and file missing cases cleanly with concise, readable terminal error outputs and standard non-zero exit codes.
* **Paths and Defaults**:
  - Base repositories must resolve to `data/worlds`, `data/scenarios`, `data/experiments`, and `data/lab_runs` by default, but let's allow overriding these via environment variables or CLI flags (e.g. `--worlds-dir`) if needed (which makes testing extremely clean and self-contained!).
