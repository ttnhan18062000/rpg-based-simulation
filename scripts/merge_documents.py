import os
from pathlib import Path

def merge_markdown_files(input_dir: str, output_file: str):
    input_path = Path(input_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Directory not found: {input_dir}")

    md_files = sorted(input_path.rglob("*.md"))

    if not md_files:
        print("No markdown files found.")
        return

    with open(output_file, "w", encoding="utf-8") as outfile:
        for md_file in md_files:
            filename = md_file.stem  # file name without extension

            # Write header
            outfile.write(f"# {filename}\n\n")

            # Write file content
            content = md_file.read_text(encoding="utf-8")
            outfile.write(content.strip())
            outfile.write("\n\n---\n\n")  # separator between files

    print(f"Merged {len(md_files)} files into {output_file}")


if __name__ == "__main__":
    # Change these paths as needed
    INPUT_DIRECTORY = "./docs"
    OUTPUT_FILE = "./docs/all.md"

    merge_markdown_files(INPUT_DIRECTORY, OUTPUT_FILE)