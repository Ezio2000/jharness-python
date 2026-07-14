from __future__ import annotations

from pathlib import Path

import pytest

from conformance import ConformanceRunner
from conformance.cli import main

ROOT = Path(__file__).resolve().parents[3]
PINNED_SPEC = ROOT / ".jharness-spec"
CASES = PINNED_SPEC / "conformance" / "cases"
SPECS = PINNED_SPEC / "contracts" / "v0"


def runner() -> ConformanceRunner:
    return ConformanceRunner(cases_dir=CASES, spec_dir=SPECS)


def test_case_inventory_is_unique_sorted_and_complete() -> None:
    cases = runner().load_cases()
    names = [str(case["name"]) for case in cases]

    assert len(cases) == 66
    assert names == sorted(names)
    assert len(names) == len(set(names))
    assert {str(case["kind"]) for case in cases} == {"scenario", "validation"}


@pytest.mark.asyncio
async def test_every_portable_case_passes_reference_runner() -> None:
    suite = runner()
    results = [await suite.run_case(case) for case in suite.load_cases()]

    assert len(results) == 66
    assert sum(result.invocation_count for result in results) == 67


def test_cli_returns_success_for_complete_suite() -> None:
    assert main((str(CASES), "--spec-dir", str(SPECS), "--quiet")) == 0


def test_runner_rejects_missing_case_directory() -> None:
    suite = ConformanceRunner(
        cases_dir=PINNED_SPEC / "conformance" / "missing",
        spec_dir=SPECS,
        case_schema_path=PINNED_SPEC / "conformance" / "case.schema.json",
    )
    with pytest.raises(FileNotFoundError, match="cases directory"):
        suite.load_cases()
