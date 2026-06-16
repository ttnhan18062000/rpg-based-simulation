from __future__ import annotations

import subprocess
from pathlib import Path

SEPARATOR = "\n\n#####\n\n"


def get_git_tracked_files(root_dir: Path) -> list[Path]:
    """Retrieves all files currently tracked by Git to ensure 100% deterministic exports."""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=root_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return [root_dir / line for line in result.stdout.splitlines() if line]
    except (subprocess.SubprocessError, FileNotFoundError):
        return []


def should_include(path: Path, suffixes: set[str]) -> bool:
    if path.suffix not in suffixes:
        return False

    parts = [p.lower() for p in path.parts]
    exclude_dirs = {
        "pycache", "node_modules", "dist", ".vite", ".pytest_cache", ".hypothesis",
        "runs", "test_cli_basic", "test_obs_replay", "archive",
    }
    for d in exclude_dirs:
        if d in parts:
            return False

    return path.is_file()


def export_directories(
    root_dir: Path,
    target_dirs: list[Path],
    output_file: Path,
    suffixes: set[str],
    extra_files: list[Path] | None = None
) -> None:
    tracked_files = get_git_tracked_files(root_dir)
    files: list[Path] = []

    if tracked_files:
        # Prioritize 100% deterministic git-tracked files
        for f in tracked_files:
            is_in_target = False
            for target_dir in target_dirs:
                try:
                    f.relative_to(target_dir)
                    is_in_target = True
                    break
                except ValueError:
                    continue

            if is_in_target and should_include(f, suffixes):
                files.append(f)
    else:
        # Fallback to local filesystem traversal if git is not initialized/installed
        for target_dir in target_dirs:
            if not target_dir.exists():
                print(f"Skipping non-existent directory: {target_dir}")
                continue

            for p in target_dir.rglob("*"):
                if should_include(p, suffixes):
                    files.append(p)

    if extra_files:
        for f in extra_files:
            if f.exists() and f.is_file():
                if f not in files:
                    files.append(f)
            else:
                print(f"Skipping non-existent extra file: {f}")

    files.sort(key=lambda p: p.as_posix())

    if not files:
        print(f"No matching files found for: {target_dirs}")
        return

    chunks: list[str] = []

    for file_path in files:
        try:
            rel_path = file_path.relative_to(root_dir).as_posix()
        except ValueError:
            rel_path = file_path.as_posix()

        content = file_path.read_text(encoding="utf-8", errors="replace").rstrip()

        # Premium syntax safety: Comment out non-python files in python exports
        if output_file.suffix == ".py" and file_path.suffix != ".py":
            commented_lines = [f"# {line}" for line in content.splitlines()]
            content = "\n".join(commented_lines)

        chunk = f"# {rel_path}\n{content}"
        chunks.append(chunk)

    merged = SEPARATOR.join(chunks) + "\n"

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(merged, encoding="utf-8")

    print(f"Exported {len(files)} files to: {output_file}")


def main() -> None:
    # Determine workspace root relative to the script location
    script_path = Path(__file__).resolve()
    reviews_dir = script_path.parent
    workspace_root = reviews_dir.parent

    # Define paths
    src_dirs = [
        workspace_root / "src",
        workspace_root / "scripts",
        workspace_root / "tools",
        workspace_root / "data",
    ]
    test_dirs = [
        workspace_root / "tests",
    ]
    frontend_dirs = [
        workspace_root / "frontend",
    ]

    # Explicit extra infrastructure and workflow files for Loki, Prometheus, Grafana, and agent workflows
    extra_infra_files = [
        workspace_root / ".claude/workflows/compact-simulation-result.js",
        workspace_root / ".claude/workflows/create-tickets.js",
        workspace_root / ".claude/workflows/generate-simulation-setup.js",
        workspace_root / ".claude/workflows/implement-epic.js",
        workspace_root / ".claude/workflows/implement-ticket.js",
        workspace_root / ".claude/workflows/investigate-simulation-result.js",
        workspace_root / ".claude/workflows/prepare-simulation-execution.js",
        workspace_root / ".claude/workflows/propose-simulation-enhancements.js",
        workspace_root / ".claude/workflows/register-simulation-result.js",
        workspace_root / ".claude/workflows/update-knowledge-store.js",
        workspace_root / "docker-compose.yml",
        workspace_root / "prometheus.yml",
        workspace_root / "promtail-config.yml",
        workspace_root / "nginx.conf",
        workspace_root / "src/observability/watchdog.py",
        workspace_root / "grafana/provisioning/datasources/datasource.yml",
        workspace_root / "grafana/provisioning/dashboards/dashboard.yml",
        workspace_root / "grafana/dashboards/simulation.json",
    ]

    docs_dirs = [
        workspace_root / "docs",
    ]

    src_output = reviews_dir / "src_export.py"
    test_output = reviews_dir / "test_export.py"
    frontend_output = reviews_dir / "frontend_export.txt"
    docs_output = reviews_dir / "docs_export.txt"
    tickets_todos_dir = workspace_root / "tickets" / "todos"

    print("Starting full project export...")
    print(f"Workspace Root: {workspace_root}")
    print(f"Output Directory: {reviews_dir}")

    # 0. Export epic ticket folders — one output file per subfolder in tickets/todos/
    if tickets_todos_dir.exists():
        for epic_dir in sorted(tickets_todos_dir.iterdir()):
            if epic_dir.is_dir():
                epic_output = reviews_dir / f"tickets_{epic_dir.name}.txt"
                export_directories(
                    workspace_root,
                    [epic_dir],
                    epic_output,
                    {".md"},
                )

    # 1. Export Backend Sources + Dynamic/Static Content Catalog & Configurations + Infrastructure Context
    export_directories(
        workspace_root,
        src_dirs,
        src_output,
        {".py", ".yaml", ".yml", ".json", ".jsonl"},
        extra_files=extra_infra_files
    )

    # 2. Export Backend Tests (unit, integration, parity, docs, performance, benchmarks)
    export_directories(workspace_root, test_dirs, test_output, {".py"})

    # 3. Export Frontend (React components, canvas boards, dashboards, TS, TSX, CSS, HTML)
    export_directories(workspace_root, frontend_dirs, frontend_output, {".ts", ".tsx", ".css", ".html", ".js", ".jsx"})

    # 4. Export Docs (all markdown + YAML — excludes archive/ via should_include)
    export_directories(workspace_root, docs_dirs, docs_output, {".md", ".yaml", ".yml"})

    print("Project export completed successfully!")


if __name__ == "__main__":
    main()
