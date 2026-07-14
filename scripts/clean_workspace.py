"""Safely preview or remove generated workspace artifacts."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]

_PROJECTS = ("kernel", "toolkit", "providers", "conformance")
_PROJECT_OUTPUT_NAMES = ("build", "coverage", "dist", "htmlcov")
_CACHE_DIRECTORY_NAMES = frozenset(
    {"__pycache__", ".mypy_cache", ".pyright", ".pytest_cache", ".ruff_cache"}
)
_GENERATED_FILE_NAMES = frozenset({".coverage", ".DS_Store"})
_GENERATED_FILE_SUFFIXES = frozenset({".pyc", ".pyo"})
_PROTECTED_PATHS = (Path(".git"), Path("python/.venv"))


@dataclass(frozen=True, slots=True)
class CleanupPlan:
    """Generated workspace targets that may be removed safely."""

    targets: tuple[Path, ...]


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _is_protected(path: Path, root: Path) -> bool:
    return any(
        path == (protected := root / relative) or _is_within(path, protected)
        for relative in _PROTECTED_PATHS
    )


def _project_roots(root: Path) -> tuple[Path, ...]:
    return (root, *(root / "python" / project for project in _PROJECTS))


def _minimal_targets(paths: set[Path], root: Path) -> tuple[Path, ...]:
    ordered = sorted(paths, key=lambda path: (len(path.relative_to(root).parts), str(path)))
    selected: list[Path] = []
    for candidate in ordered:
        if candidate == root or not _is_within(candidate, root):
            raise ValueError(f"cleanup target escapes repository root: {candidate}")
        if _is_protected(candidate, root):
            raise ValueError(f"cleanup target is protected: {candidate}")
        if any(_is_within(candidate, parent) for parent in selected):
            continue
        selected.append(candidate)
    return tuple(sorted(selected, key=lambda path: str(path.relative_to(root))))


def _initial_targets(root: Path) -> set[Path]:
    targets: set[Path] = set()
    synced_spec = root / ".jharness-spec"
    if synced_spec.exists() or synced_spec.is_symlink():
        targets.add(synced_spec)
    root_environment = root / ".venv"
    if root_environment.exists() or root_environment.is_symlink():
        targets.add(root_environment)
    for project_root in _project_roots(root):
        for name in _PROJECT_OUTPUT_NAMES:
            candidate = project_root / name
            if candidate.exists() or candidate.is_symlink():
                targets.add(candidate)
    return targets


def _prune_directory(candidate: Path, name: str, root: Path, targets: set[Path]) -> bool:
    if _is_protected(candidate, root):
        return True
    if any(candidate == target or _is_within(candidate, target) for target in targets):
        return True
    if name in _CACHE_DIRECTORY_NAMES or name.endswith(".egg-info"):
        targets.add(candidate)
        return True
    return False


def _collect_walk_targets(root: Path, targets: set[Path]) -> None:
    for current, directories, files in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        directories[:] = [
            name
            for name in directories
            if not _prune_directory(current_path / name, name, root, targets)
        ]
        for name in files:
            candidate = current_path / name
            if _is_protected(candidate, root):
                continue
            if name in _GENERATED_FILE_NAMES or candidate.suffix in _GENERATED_FILE_SUFFIXES:
                targets.add(candidate)


def build_cleanup_plan(root: Path) -> CleanupPlan:
    """Collect generated targets without traversing protected environments."""

    root = root.resolve()
    if not (root / "python" / "pyproject.toml").is_file():
        raise ValueError(f"not a recognized workspace root: {root}")

    targets = _initial_targets(root)
    _collect_walk_targets(root, targets)

    return CleanupPlan(_minimal_targets(targets, root))


def _remove(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
    elif path.is_dir():
        shutil.rmtree(path)


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def main() -> int:
    """Preview cleanup by default and mutate only with explicit confirmation."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="remove the displayed targets; the default is a dry run",
    )
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args()
    root = args.root.resolve()

    try:
        plan = build_cleanup_plan(root)
    except (OSError, ValueError) as exc:
        print(f"workspace cleanup failed: {exc}", file=sys.stderr)
        return 1

    if not plan.targets:
        print("workspace is clean")
        return 0

    root_environment = root / ".venv"
    if args.apply and _is_within(Path(sys.prefix).resolve(), root_environment.resolve()):
        print(
            "workspace cleanup failed: run through `uv --project python`; "
            "the active interpreter is inside the disposable root .venv",
            file=sys.stderr,
        )
        return 1

    action = "removing" if args.apply else "would remove"
    for path in plan.targets:
        print(f"{action} {_relative(path, root)}")
        if args.apply:
            _remove(path)

    if args.apply:
        print(f"removed {len(plan.targets)} generated workspace artifact(s)")
    else:
        print(f"previewed {len(plan.targets)} generated workspace artifact(s)")
        print("run again with --apply to remove them")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
