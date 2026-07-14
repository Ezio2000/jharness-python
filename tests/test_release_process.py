from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_metadata_is_coordinated() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify_release.py")],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "release metadata ok" in result.stdout


def test_release_workflow_uses_one_artifact_and_trusted_publishers() -> None:
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text()
    assert "scripts/sync_spec.py" in workflow
    assert "verify_release.py --tag" in workflow
    assert workflow.count("uv --project python build") == 1
    assert "publish-testpypi" in workflow
    assert "verify-testpypi" in workflow
    assert "publish-pypi" in workflow
    assert "id-token: write" in workflow
    for distribution in ("kernel", "toolkit", "providers"):
        assert f"testpypi-jharness-{distribution}" in workflow
        assert f"pypi-jharness-{distribution}" in workflow
    assert workflow.count("archive_prefix:") == 6
    assert workflow.count("find dist -maxdepth 1") == 4
    assert "actions/upload-artifact@" in workflow
    assert workflow.count("actions/download-artifact@") == 3
    assert "gh release create" in workflow
    assert 'version="${GITHUB_REF_NAME#v}"' in workflow
