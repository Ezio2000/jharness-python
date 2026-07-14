"""Repository build-artifact gate for the three product distributions."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from dataclasses import dataclass
from email.parser import BytesParser
from pathlib import Path, PurePosixPath

EXPECTED_IMPORTS = {
    "jharness-kernel": (
        "jharness.kernel",
        "jharness.kernel.diagnostics",
        "jharness.kernel.wire",
    ),
    "jharness-providers": (
        "jharness.providers",
        "jharness.providers.anthropic",
        "jharness.providers.deepseek",
        "jharness.providers.openai",
    ),
    "jharness-toolkit": ("jharness.toolkit",),
}
_OWNED_CHILD = {
    "jharness-kernel": "kernel",
    "jharness-providers": "providers",
    "jharness-toolkit": "toolkit",
}
_ALLOWED_SDIST_ROOT_CHILDREN = frozenset(
    {".gitignore", "LICENSE", "PKG-INFO", "README.md", "pyproject.toml", "src", "tests"}
)
_FORBIDDEN_PRODUCT_SEGMENTS = frozenset({"conformance", "test", "tests"})


@dataclass(frozen=True, slots=True)
class WheelMetadata:
    """Relevant metadata read directly from one wheel artifact."""

    path: Path
    internal_dependencies: frozenset[str]


def _normalize_distribution(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _requirement_name(requirement: str) -> str:
    name = re.split(r"[\s\[\]();<>=!~@]", requirement, maxsplit=1)[0]
    if not name:
        raise ValueError(f"cannot parse requirement name: {requirement!r}")
    return _normalize_distribution(name)


def _read_wheel(path: Path) -> tuple[str, tuple[str, ...]]:
    with zipfile.ZipFile(path) as archive:
        metadata_names = [
            name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
        ]
        if len(metadata_names) != 1:
            raise ValueError(f"{path.name} must contain exactly one METADATA file")
        metadata = BytesParser().parsebytes(archive.read(metadata_names[0]))
        distribution = metadata.get("Name")
        if distribution is None:
            raise ValueError(f"{path.name} metadata has no Name field")
        normalized = _normalize_distribution(distribution)
        _verify_wheel_members(
            path,
            normalized,
            archive.namelist(),
            PurePosixPath(metadata_names[0]).parts[0],
        )
        requirements = tuple(metadata.get_all("Requires-Dist", ()))
    return normalized, requirements


def _member_parts(path: Path, name: str) -> tuple[str, ...]:
    member = PurePosixPath(name)
    if member.is_absolute() or ".." in member.parts:
        raise ValueError(f"{path.name} contains unsafe archive member {name!r}")
    parts = tuple(part for part in member.parts if part not in {"", "."})
    if not parts:
        raise ValueError(f"{path.name} contains an empty archive member")
    return parts


def _product_import_root(distribution: str) -> str:
    return EXPECTED_IMPORTS[distribution][0].partition(".")[0]


def _verify_wheel_members(
    path: Path,
    distribution: str,
    names: list[str],
    metadata_root: str,
) -> None:
    if distribution not in EXPECTED_IMPORTS:
        return
    product_root = _product_import_root(distribution)
    owned_child = _OWNED_CHILD[distribution]
    namespace_init = f"{product_root}/__init__.py"
    product_init = f"{product_root}/{owned_child}/__init__.py"
    license_path = f"{metadata_root}/licenses/LICENSE"
    if namespace_init in names:
        raise ValueError(f"{path.name} must not install shared {namespace_init}")
    if product_init not in names:
        raise ValueError(f"{path.name} is missing {product_init}")
    if license_path not in names:
        raise ValueError(f"{path.name} is missing {license_path}")
    for name in names:
        parts = _member_parts(path, name)
        if parts[0] == metadata_root:
            continue
        if parts == (product_root,):
            continue
        if len(parts) < 2 or parts[:2] != (product_root, owned_child):
            raise ValueError(f"{path.name} contains unexpected top-level member {name!r}")
        if any(part in _FORBIDDEN_PRODUCT_SEGMENTS for part in parts[2:]):
            raise ValueError(f"{path.name} contains development-only member {name!r}")


def _verify_sdist(path: Path, distribution: str) -> None:
    product_root = _product_import_root(distribution)
    owned_child = _OWNED_CHILD[distribution]
    with tarfile.open(path, mode="r:gz") as archive:
        members = [_member_parts(path, member.name) for member in archive.getmembers()]
    archive_roots = {parts[0] for parts in members}
    if len(archive_roots) != 1:
        raise ValueError(f"{path.name} must contain exactly one archive root")
    archive_root = next(iter(archive_roots))
    root_children = {parts[1] for parts in members if len(parts) >= 2}
    unexpected_root_children = root_children - _ALLOWED_SDIST_ROOT_CHILDREN
    if unexpected_root_children:
        raise ValueError(
            f"{path.name} contains unexpected source-distribution members: "
            f"{sorted(unexpected_root_children)}"
        )
    namespace_init = (archive_root, "src", product_root, "__init__.py")
    product_init = (archive_root, "src", product_root, owned_child, "__init__.py")
    _verify_sdist_license(path, members, archive_root)
    if namespace_init in members:
        raise ValueError(f"{path.name} must not install shared {'/'.join(namespace_init)}")
    if product_init not in members:
        raise ValueError(f"{path.name} is missing {'/'.join(product_init)}")
    source_roots = {
        parts[2] for parts in members if len(parts) >= 3 and parts[:2] == (archive_root, "src")
    }
    if source_roots != {product_root}:
        raise ValueError(
            f"{path.name} source-root mismatch: expected={[product_root]}, "
            f"actual={sorted(source_roots)}"
        )
    source_children = {
        parts[3]
        for parts in members
        if len(parts) >= 4 and parts[:3] == (archive_root, "src", product_root)
    }
    if source_children != {owned_child}:
        raise ValueError(
            f"{path.name} namespace ownership mismatch: expected={[owned_child]}, "
            f"actual={sorted(source_children)}"
        )
    for parts in members:
        if (
            len(parts) >= 5
            and parts[:4] == (archive_root, "src", product_root, owned_child)
            and any(part in _FORBIDDEN_PRODUCT_SEGMENTS for part in parts[4:])
        ):
            raise ValueError(
                f"{path.name} contains development-only product member {'/'.join(parts)!r}"
            )


def _verify_sdist_license(
    path: Path,
    members: list[tuple[str, ...]],
    archive_root: str,
) -> None:
    license_path = (archive_root, "LICENSE")
    if license_path not in members:
        raise ValueError(f"{path.name} is missing {'/'.join(license_path)}")


def _load_artifacts(dist_dir: Path) -> dict[str, WheelMetadata]:
    wheel_paths = sorted(dist_dir.glob("*.whl"))
    sdist_paths = sorted(dist_dir.glob("*.tar.gz"))
    expected_count = len(EXPECTED_IMPORTS)
    if len(wheel_paths) != expected_count or len(sdist_paths) != expected_count:
        raise ValueError(
            f"expected {expected_count} wheels and {expected_count} source distributions, "
            f"found {len(wheel_paths)} wheels and {len(sdist_paths)} source distributions"
        )

    expected = set(EXPECTED_IMPORTS)
    sdist_distributions = {
        _normalize_distribution(path.name.removesuffix(".tar.gz").rsplit("-", maxsplit=1)[0])
        for path in sdist_paths
    }
    if sdist_distributions != expected:
        missing = sorted(expected - sdist_distributions)
        unexpected = sorted(sdist_distributions - expected)
        raise ValueError(f"sdist set mismatch: missing={missing}, unexpected={unexpected}")
    for sdist_path in sdist_paths:
        distribution = _normalize_distribution(
            sdist_path.name.removesuffix(".tar.gz").rsplit("-", maxsplit=1)[0]
        )
        _verify_sdist(sdist_path, distribution)

    raw_artifacts: dict[str, tuple[Path, tuple[str, ...]]] = {}
    for wheel_path in wheel_paths:
        distribution, requirements = _read_wheel(wheel_path)
        if distribution in raw_artifacts:
            raise ValueError(f"duplicate wheel for distribution {distribution}")
        raw_artifacts[distribution] = (wheel_path, requirements)

    actual = set(raw_artifacts)
    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        raise ValueError(f"wheel set mismatch: missing={missing}, unexpected={unexpected}")

    artifacts: dict[str, WheelMetadata] = {}
    for distribution, (path, requirements) in raw_artifacts.items():
        internal_dependencies = frozenset(
            dependency
            for requirement in requirements
            if (dependency := _requirement_name(requirement)) in expected
        )
        artifacts[distribution] = WheelMetadata(path, internal_dependencies)
    return artifacts


def _dependency_closure(
    target: str,
    artifacts: dict[str, WheelMetadata],
) -> tuple[Path, ...]:
    pending = [target]
    selected: set[str] = set()
    while pending:
        distribution = pending.pop()
        if distribution in selected:
            continue
        selected.add(distribution)
        pending.extend(artifacts[distribution].internal_dependencies)
    return tuple(artifacts[name].path for name in sorted(selected))


def _verify_imports(artifacts: dict[str, WheelMetadata]) -> None:
    uv = shutil.which("uv")
    if uv is None:
        raise RuntimeError("uv executable is required")

    with tempfile.TemporaryDirectory(prefix="wheel-imports-") as temporary_directory:
        work_dir = Path(temporary_directory)
        for distribution, import_names in EXPECTED_IMPORTS.items():
            command = [
                uv,
                "run",
                "--isolated",
                "--python",
                sys.executable,
            ]
            for wheel in _dependency_closure(distribution, artifacts):
                command.extend(("--with", str(wheel)))
            imports = "; ".join(f"import {name}" for name in import_names)
            command.extend(("python", "-I", "-c", imports))
            subprocess.run(command, cwd=work_dir, check=True)
            print(f"isolated imports passed: {distribution} -> {', '.join(import_names)}")


def main() -> int:
    """Validate artifact completeness and import every wheel in a clean environment."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dist_dir", type=Path, help="directory containing built artifacts")
    args = parser.parse_args()

    try:
        artifacts = _load_artifacts(args.dist_dir.resolve())
        _verify_imports(artifacts)
    except (
        OSError,
        RuntimeError,
        ValueError,
        tarfile.TarError,
        subprocess.CalledProcessError,
    ) as exc:
        print(f"wheel verification failed: {exc}", file=sys.stderr)
        return 1
    print("all three product distributions passed isolated import verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
