"""Synchronize the immutable JHarness specification pinned by spec.lock."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import shutil
import tarfile
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "spec.lock"
DESTINATION = ROOT / ".jharness-spec"
MARKER = "spec.lock"


@dataclass(frozen=True, slots=True)
class SpecLock:
    repository: str
    version: str
    revision: str
    sha256: str

    def document(self) -> dict[str, str]:
        return {
            "repository": self.repository,
            "version": self.version,
            "revision": self.revision,
            "sha256": self.sha256,
        }


def _load_lock() -> SpecLock:
    value: object = json.loads(LOCK_PATH.read_text())
    if not isinstance(value, dict):
        raise ValueError("spec.lock must contain a JSON object")
    document = cast(dict[str, Any], value)
    expected = {"repository", "version", "revision", "sha256"}
    if set(document) != expected or not all(isinstance(document[key], str) for key in expected):
        raise ValueError("spec.lock fields must be repository, version, revision, and sha256")
    lock = SpecLock(**cast(dict[str, str], document))
    if lock.repository != "https://github.com/Ezio2000/jharness":
        raise ValueError(f"unexpected specification repository: {lock.repository}")
    if len(lock.revision) != 40 or any(char not in "0123456789abcdef" for char in lock.revision):
        raise ValueError("specification revision must be a full lowercase Git commit")
    if len(lock.sha256) != 64 or any(char not in "0123456789abcdef" for char in lock.sha256):
        raise ValueError("specification sha256 must be a lowercase SHA-256 digest")
    return lock


def _archive(lock: SpecLock) -> bytes:
    url = f"{lock.repository}/archive/{lock.revision}.tar.gz"
    request = urllib.request.Request(url, headers={"User-Agent": "jharness-python-spec-sync"})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read()
    digest = hashlib.sha256(data).hexdigest()
    if digest != lock.sha256:
        raise ValueError(
            f"specification archive digest mismatch: expected {lock.sha256}, got {digest}"
        )
    return data


def _selected_path(member: tarfile.TarInfo) -> Path | None:
    parts = PurePosixPath(member.name).parts
    if len(parts) < 2 or parts[1] not in {"contracts", "conformance"}:
        return None
    relative = Path(*parts[1:])
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"unsafe specification archive member: {member.name!r}")
    return relative


def _extract(data: bytes, staging: Path) -> None:
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        for member in archive.getmembers():
            relative = _selected_path(member)
            if relative is None:
                continue
            if member.issym() or member.islnk():
                raise ValueError(f"links are forbidden in the specification archive: {member.name}")
            target = staging / relative
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile():
                raise ValueError(f"unsupported specification archive member: {member.name}")
            source = archive.extractfile(member)
            if source is None:
                raise ValueError(f"cannot read specification archive member: {member.name}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read())


def _marker(lock: SpecLock) -> str:
    return json.dumps(lock.document(), indent=2, sort_keys=True) + "\n"


def _current(lock: SpecLock) -> bool:
    marker = DESTINATION / MARKER
    return (
        marker.is_file()
        and marker.read_text() == _marker(lock)
        and (DESTINATION / "contracts" / "v0").is_dir()
        and (DESTINATION / "conformance" / "cases").is_dir()
    )


def _sync(lock: SpecLock) -> None:
    if _current(lock):
        print(f"specification already synchronized: {lock.version} ({lock.revision})")
        return
    temporary = Path(tempfile.mkdtemp(prefix=".jharness-spec-", dir=ROOT))
    try:
        _extract(_archive(lock), temporary)
        (temporary / MARKER).write_text(_marker(lock))
        if DESTINATION.exists():
            shutil.rmtree(DESTINATION)
        temporary.replace(DESTINATION)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    print(f"synchronized specification: {lock.version} ({lock.revision})")


def main() -> int:
    """Synchronize or check the pinned specification snapshot."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify the snapshot without fetching")
    args = parser.parse_args()
    try:
        lock = _load_lock()
        if args.check:
            if not _current(lock):
                raise ValueError(".jharness-spec is absent or does not match spec.lock")
            print(f"specification snapshot matches {lock.version} ({lock.revision})")
        else:
            _sync(lock)
    except (OSError, ValueError, json.JSONDecodeError, tarfile.TarError) as exc:
        print(f"specification synchronization failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
