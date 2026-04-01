from __future__ import annotations

import argparse
from pathlib import Path


SEPARATOR = "\n\n#####\n\n"


def should_include(path: Path) -> bool:
    return (
        path.is_file()
        and path.suffix == ".py"
        and "pycache" not in path.parts
    )


def export_src_tree(src_dir: Path, output_file: Path) -> None:
    if not src_dir.exists():
        raise FileNotFoundError(f"Source directory does not exist: {src_dir}")
    if not src_dir.is_dir():
        raise NotADirectoryError(f"Source path is not a directory: {src_dir}")

    files = sorted(
        [p for p in src_dir.rglob("*.py") if should_include(p)],
        key=lambda p: p.as_posix(),
    )

    if not files:
        raise ValueError(f"No Python files found under: {src_dir}")

    chunks: list[str] = []

    for file_path in files:
        rel_path = file_path.as_posix()
        content = file_path.read_text(encoding="utf-8", errors="replace").rstrip()

        chunk = f"# {rel_path}\n{content}"
        chunks.append(chunk)

    merged = SEPARATOR.join(chunks) + "\n"

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(merged, encoding="utf-8")

    print(f"Exported {len(files)} files to: {output_file}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export all Python files under src/ into a single text-like Python file."
    )
    parser.add_argument(
        "--src",
        default="src",
        help="Root source directory to scan. Default: src",
    )
    parser.add_argument(
        "--out",
        default="src_export.py",
        help="Output file path. Default: src_export.py",
    )

    args = parser.parse_args()

    src_dir = Path(args.src).resolve()
    output_file = Path(args.out).resolve()

    export_src_tree(src_dir, output_file)


if __name__ == "__main__":
    main()
