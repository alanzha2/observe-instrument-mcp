"""File I/O utilities: read, backup, write, diff summary."""

import difflib
import shutil
from pathlib import Path


def read_python_file(file_path: str) -> str:
    """Read and return the content of a Python file."""
    path = Path(file_path).resolve()
    if not path.exists():
        raise FileNotFoundError(file_path)
    if path.suffix != ".py":
        raise ValueError(f"Expected a .py file, got: {path.suffix}")
    if path.stat().st_size > 500_000:
        raise ValueError(f"File is too large ({path.stat().st_size} bytes). Max 500KB.")
    return path.read_text(encoding="utf-8")


def make_backup(file_path: str) -> str:
    """Copy file to <file_path>.bak and return the backup path."""
    path = Path(file_path).resolve()
    backup = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(path, backup)
    return str(backup)


def write_python_file(file_path: str, content: str) -> None:
    """Write content back to the file."""
    path = Path(file_path).resolve()
    path.write_text(content, encoding="utf-8")


def build_diff_summary(original: str, modified: str) -> str:
    """Return a compact unified diff as a markdown code block."""
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)
    diff = list(difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile="original",
        tofile="instrumented",
        n=2,
    ))
    if not diff:
        return "_No changes detected._"
    if len(diff) > 100:
        diff = diff[:100]
        diff.append("... (diff truncated)\n")
    return "```diff\n" + "".join(diff) + "\n```"
