from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEANER = ROOT / "scripts" / "clean_workspace.py"


def _write(path: Path, content: str = "generated") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _run_cleaner(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLEANER), "--root", str(root), *arguments],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )


def _workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    _write(workspace / "python" / "pyproject.toml", "[project]\nname = 'test'\n")
    return workspace


def test_workspace_cleaner_previews_then_removes_only_generated_targets(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path)
    root_environment = workspace / ".venv" / "marker"
    uv_environment = workspace / "python" / ".venv" / "marker"
    nested_cache = workspace / "python" / "kernel" / "src" / "jharness" / "__pycache__" / "x.pyc"
    ordinary_cache = workspace / "examples" / "python" / "__pycache__" / "example.pyc"
    coverage_report = workspace / "coverage" / "index.html"
    retained_source = workspace / "src" / "application.py"
    for path in (
        root_environment,
        uv_environment,
        nested_cache,
        ordinary_cache,
        coverage_report,
        retained_source,
    ):
        _write(path)

    preview = _run_cleaner(workspace)

    assert preview.returncode == 0, preview.stderr
    assert "would remove .venv" in preview.stdout
    assert "would remove python/kernel/src/jharness/__pycache__" in preview.stdout
    assert "python/.venv" not in preview.stdout
    assert all(
        path.exists()
        for path in (
            root_environment,
            uv_environment,
            nested_cache,
            ordinary_cache,
            coverage_report,
            retained_source,
        )
    )

    applied = _run_cleaner(workspace, "--apply")

    assert applied.returncode == 0, applied.stderr
    assert not root_environment.exists()
    assert not nested_cache.exists()
    assert not ordinary_cache.exists()
    assert not coverage_report.exists()
    assert uv_environment.exists()
    assert retained_source.exists()


def test_workspace_cleaner_rejects_an_unrelated_root(tmp_path: Path) -> None:
    result = _run_cleaner(tmp_path)

    assert result.returncode == 1
    assert "not a recognized workspace root" in result.stderr
