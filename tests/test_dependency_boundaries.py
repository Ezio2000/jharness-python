from __future__ import annotations

import ast
import re
import sys
import tomllib
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ROOT / "packages"
PROJECTS = {"kernel", "toolkit", "providers", "conformance"}
IMPORT_ROOTS = {
    "kernel": "jharness.kernel",
    "toolkit": "jharness.toolkit",
    "providers": "jharness.providers",
    "conformance": "conformance",
}
ALLOWED: dict[str, set[str]] = {
    "kernel": set(),
    "toolkit": {"jharness.kernel"},
    "providers": {"jharness.kernel"},
    "conformance": {"jharness.kernel", "jharness.toolkit"},
}
PROJECT_NAMES = {
    "kernel": "jharness-kernel",
    "toolkit": "jharness-toolkit",
    "providers": "jharness-providers",
    "conformance": "conformance",
}
DEPENDENCY_IMPORTS = {
    **{distribution: IMPORT_ROOTS[root] for root, distribution in PROJECT_NAMES.items()},
    "httpx": "httpx",
    "jsonschema": "jsonschema",
    "referencing": "referencing",
}
PUBLIC_MODULES = {
    "jharness.kernel": {
        "jharness.kernel",
        "jharness.kernel.diagnostics",
        "jharness.kernel.wire",
    },
    "jharness.toolkit": {"jharness.toolkit"},
    "jharness.providers": {"jharness.providers"},
    "conformance": {"conformance"},
}
SOURCE_ROOTS = {
    "kernel": PACKAGES / "kernel" / "src" / "jharness" / "kernel",
    "toolkit": PACKAGES / "toolkit" / "src" / "jharness" / "toolkit",
    "providers": PACKAGES / "providers" / "src" / "jharness" / "providers",
    "conformance": PACKAGES / "conformance" / "src" / "conformance",
}


def import_target(module: str) -> str:
    parts = module.split(".")
    if parts[0] == "jharness":
        return ".".join(parts[:2])
    return parts[0]


def imports(path: Path) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend((import_target(alias.name), alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            found.append((import_target(node.module), node.module))
    return found


def source_files(owner: str) -> list[Path]:
    return sorted(SOURCE_ROOTS[owner].rglob("*.py"))


def requirement_name(requirement: str) -> str:
    return re.split(r"[\s\[\]();<>=!~@]", requirement, maxsplit=1)[0].lower()


def project_dependencies(owner: str) -> set[str]:
    document = tomllib.loads((PACKAGES / owner / "pyproject.toml").read_text())
    project = cast(dict[str, Any], document["project"])
    dependencies = cast(list[str], project.get("dependencies", []))
    return {
        DEPENDENCY_IMPORTS[name]
        for dependency in dependencies
        if (name := requirement_name(dependency)) in DEPENDENCY_IMPORTS
    }


def test_workspace_source_dependency_graph_is_one_way_and_public_rooted() -> None:
    violations: list[str] = []
    workspace_roots = set(IMPORT_ROOTS.values())
    for owner in sorted(PROJECTS):
        own_root = IMPORT_ROOTS[owner]
        for path in source_files(owner):
            for target, module in imports(path):
                if target not in workspace_roots or target == own_root:
                    continue
                if target not in ALLOWED[owner]:
                    violations.append(f"{path.relative_to(ROOT)} imports forbidden {module}")
                elif module not in PUBLIC_MODULES[target]:
                    violations.append(
                        f"{path.relative_to(ROOT)} bypasses public root with {module}"
                    )
    assert violations == []


def test_declared_direct_dependencies_are_exactly_the_used_edges() -> None:
    used = {
        owner: {
            target
            for path in source_files(owner)
            for target, _ in imports(path)
            if target != IMPORT_ROOTS[owner] and target not in sys.stdlib_module_names
        }
        for owner in PROJECTS
    }
    for owner in PROJECTS:
        assert used[owner] == project_dependencies(owner)
        assert used[owner].intersection(IMPORT_ROOTS.values()) == ALLOWED[owner]


def test_kernel_has_only_standard_library_dependencies() -> None:
    imported = {
        target
        for path in source_files("kernel")
        for target, _ in imports(path)
        if target != IMPORT_ROOTS["kernel"]
    }
    assert imported <= sys.stdlib_module_names


def test_workspace_contains_three_products_and_one_development_project() -> None:
    workspace = tomllib.loads((ROOT / "pyproject.toml").read_text())
    uv = cast(dict[str, Any], workspace["tool"])["uv"]
    members = set(cast(list[str], cast(dict[str, Any], uv)["workspace"]["members"]))
    assert members == {
        "packages/kernel",
        "packages/toolkit",
        "packages/providers",
        "packages/conformance",
    }
    owners = {Path(member).name for member in members}
    assert {PROJECT_NAMES[owner] for owner in owners if owner != "conformance"} == {
        "jharness-kernel",
        "jharness-toolkit",
        "jharness-providers",
    }


def test_workspace_projects_declare_local_readmes() -> None:
    for owner in sorted(PROJECTS):
        project_root = PACKAGES / owner
        document = tomllib.loads((project_root / "pyproject.toml").read_text())
        project = cast(dict[str, Any], document["project"])
        assert project.get("readme") == "README.md"
        assert (project_root / "README.md").is_file()


def test_product_namespace_has_single_owner_per_child_and_no_shared_initializer() -> None:
    for owner in ("kernel", "toolkit", "providers"):
        namespace = PACKAGES / owner / "src" / "jharness"
        assert not (namespace / "__init__.py").exists()
        assert {path.name for path in namespace.iterdir() if path.is_dir()} == {owner}
        assert (namespace / owner / "__init__.py").is_file()


def test_repository_has_no_language_aggregation_tree() -> None:
    assert not (ROOT / "sdks").exists()
    assert not (ROOT / "python").exists()
