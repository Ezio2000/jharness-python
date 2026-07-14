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
    assert "workflow_dispatch:" in workflow
    assert "source_run_id:" in workflow
    assert "id-token: write" in workflow
    for distribution in ("kernel", "toolkit", "providers"):
        assert f"testpypi-jharness-{distribution}" in workflow
        assert f"pypi-jharness-{distribution}" in workflow
    assert workflow.count("archive_prefix:") == 6
    assert workflow.count("find dist -maxdepth 1") == 5
    assert "actions/upload-artifact@" in workflow
    assert workflow.count("actions/download-artifact@") == 4
    assert "gh release create" in workflow
    assert 'version="${RELEASE_TAG#v}"' in workflow
    assert 'python scripts/verify_testpypi.py "${RELEASE_TAG#v}"' in workflow
    assert "sha256sum --check dist/SHA256SUMS" in workflow
    assert workflow.count("if: always() && needs.") == 3
    assert "required reviewers" not in workflow.lower()


def test_testpypi_smoke_project_uses_an_explicit_index() -> None:
    script = (ROOT / "scripts" / "verify_testpypi.py").read_text()
    assert script.count('{{ index = "testpypi" }}') == 3
    assert 'url = "https://test.pypi.org/simple"' in script
    assert "explicit = true" in script
    assert "jsonschema" not in script


def test_testpypi_smoke_project_rejects_invalid_versions() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify_testpypi.py"), "0.1.0; unsafe"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "invalid release version" in result.stderr
