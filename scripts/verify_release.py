"""Validate the coordinated version and changelog state for a JHarness release."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS = {
    "kernel": "jharness-kernel",
    "providers": "jharness-providers",
    "toolkit": "jharness-toolkit",
}
INTERNAL_DEPENDENCIES = {
    "kernel": set(),
    "providers": {"jharness-kernel"},
    "toolkit": {"jharness-kernel"},
}
_VERSION = re.compile(r"^(\d+)\.(\d+)\.(\d+)(.*)$")
_RELEASE_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_FULL_SHA = re.compile(r"[0-9a-f]{40}")
_SHA256 = re.compile(r"[0-9a-f]{64}")


def _project(owner: str) -> dict[str, Any]:
    path = ROOT / "python" / owner / "pyproject.toml"
    document = tomllib.loads(path.read_text())
    return cast(dict[str, Any], document["project"])


def _requirement_name(requirement: str) -> str:
    return re.split(r"[\s\[\]();<>=!~@]", requirement, maxsplit=1)[0].lower()


def _compatible_range(version: str) -> str:
    match = _VERSION.fullmatch(version)
    if match is None:
        raise ValueError(f"unsupported product version: {version!r}")
    major, minor, _, suffix = match.groups()
    lower = version if suffix else f"{major}.{minor}.0"
    upper = f"0.{int(minor) + 1}.0" if major == "0" else f"{int(major) + 1}.0.0"
    return f">={lower},<{upper}"


def _verify_versions() -> str:
    projects = {owner: _project(owner) for owner in PRODUCTS}
    for owner, expected_name in PRODUCTS.items():
        actual_name = str(projects[owner]["name"])
        if actual_name != expected_name:
            raise ValueError(f"{owner} distribution must be {expected_name!r}, got {actual_name!r}")
    versions = {owner: str(project["version"]) for owner, project in projects.items()}
    if len(set(versions.values())) != 1:
        detail = ", ".join(f"{owner}={version}" for owner, version in sorted(versions.items()))
        raise ValueError(f"product versions must match: {detail}")
    version = next(iter(versions.values()))
    expected_range = _compatible_range(version)

    for owner, project in projects.items():
        requirements = {
            _requirement_name(requirement): requirement
            for requirement in cast(list[str], project.get("dependencies", []))
        }
        actual_internal = set(requirements).intersection(PRODUCTS.values())
        if actual_internal != INTERNAL_DEPENDENCIES[owner]:
            raise ValueError(
                f"{owner} internal dependencies differ: "
                f"expected={sorted(INTERNAL_DEPENDENCIES[owner])}, "
                f"actual={sorted(actual_internal)}"
            )
        for dependency in actual_internal:
            expected = f"{dependency}{expected_range}"
            if requirements[dependency].replace(" ", "") != expected:
                raise ValueError(
                    f"{owner} must declare coordinated dependency {expected!r}, "
                    f"got {requirements[dependency]!r}"
                )
    return version


def _verify_changelog(version: str, *, released: bool) -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text()
    if "## [Unreleased]" not in changelog:
        raise ValueError("CHANGELOG.md must contain an [Unreleased] section")
    match = re.search(rf"^## \[{re.escape(version)}\] - (.+)$", changelog, re.MULTILINE)
    if match is None:
        raise ValueError(f"CHANGELOG.md has no section for version {version}")
    marker = match.group(1).strip()
    if released and _RELEASE_DATE.fullmatch(marker) is None:
        raise ValueError(f"release {version} must have a YYYY-MM-DD changelog date, got {marker!r}")
    if not released and marker != "Unreleased" and _RELEASE_DATE.fullmatch(marker) is None:
        raise ValueError(f"invalid changelog marker for {version}: {marker!r}")


def _verify_spec_lock() -> str:
    value: object = json.loads((ROOT / "spec.lock").read_text())
    if not isinstance(value, dict):
        raise ValueError("spec.lock must contain a JSON object")
    document = cast(dict[str, object], value)
    expected = {"repository", "version", "revision", "sha256"}
    if set(document) != expected:
        raise ValueError(f"spec.lock fields must be {sorted(expected)}")
    if document["repository"] != "https://github.com/Ezio2000/jharness":
        raise ValueError("spec.lock must reference the canonical JHarness repository")
    version = document["version"]
    revision = document["revision"]
    digest = document["sha256"]
    if not isinstance(version, str) or re.fullmatch(r"v\d+\.\d+\.\d+", version) is None:
        raise ValueError("spec.lock version must be a semantic v-prefixed tag")
    if not isinstance(revision, str) or _FULL_SHA.fullmatch(revision) is None:
        raise ValueError("spec.lock revision must be a full lowercase Git commit")
    if not isinstance(digest, str) or _SHA256.fullmatch(digest) is None:
        raise ValueError("spec.lock sha256 must be a lowercase SHA-256 digest")
    return version


def main() -> int:
    """Check versions normally and require a dated changelog for a release tag."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", help="release tag, exactly v<coordinated-version>")
    args = parser.parse_args()
    try:
        version = _verify_versions()
        if args.tag is not None and args.tag != f"v{version}":
            raise ValueError(f"tag must be v{version}, got {args.tag!r}")
        _verify_changelog(version, released=args.tag is not None)
        spec_version = _verify_spec_lock()
    except (
        json.JSONDecodeError,
        KeyError,
        OSError,
        TypeError,
        ValueError,
        tomllib.TOMLDecodeError,
    ) as exc:
        print(f"release verification failed: {exc}", file=sys.stderr)
        return 1
    print(
        f"release metadata ok: version={version}, spec={spec_version}, "
        f"tag={args.tag or 'not-required'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
