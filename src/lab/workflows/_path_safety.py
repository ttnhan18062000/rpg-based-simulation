from pathlib import Path


def safe_path_resolution(base_dir: Path, target_path: str | Path) -> Path:
    """Safely resolves path and blocks path traversal attempts outside the base directory."""
    target = Path(target_path)
    base_resolved = base_dir.resolve()
    if not target.is_absolute():
        resolved = (base_resolved / target).resolve()
    else:
        resolved = target.resolve()
    try:
        if not resolved.is_relative_to(base_resolved):
            raise PermissionError(f"Path traversal blocked: '{target_path}' is outside '{base_dir}'")
    except ValueError as e:
        raise PermissionError(f"Path traversal blocked: '{target_path}' is outside '{base_dir}': {e}") from e
    return resolved
