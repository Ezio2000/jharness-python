# Release Process

JHarness releases exactly three product distributions from one version, one tag,
and one immutable artifact set:

- `jharness-kernel`;
- `jharness-toolkit`;
- `jharness-providers`.

The `conformance` workspace project is never published.

## One-Time Repository Setup

Before the first release, a repository administrator must configure these external
controls. They cannot be expressed solely in the repository:

1. Create one GitHub environment per distribution and package index:

   | Distribution | TestPyPI environment | PyPI environment |
   | --- | --- | --- |
   | `jharness-kernel` | `testpypi-jharness-kernel` | `pypi-jharness-kernel` |
   | `jharness-toolkit` | `testpypi-jharness-toolkit` | `pypi-jharness-toolkit` |
   | `jharness-providers` | `testpypi-jharness-providers` | `pypi-jharness-providers` |

2. Leave all six environments without required reviewers or wait timers so a release
   tag can complete without manual intervention.
3. Configure one Pending Trusted Publisher for every table row on both TestPyPI
   and PyPI. Each publisher uses repository `Ezio2000/jharness-python`, workflow
   `release.yml`, and its exact environment name from the table. Separate
   environments give each new project a unique initial OIDC identity.
4. Protect `main`: require pull requests, the CI jobs, resolved review comments, and
   a linear or otherwise intentional history policy.
5. Protect `v*` tags so only release maintainers can create or delete them.
6. Enable private vulnerability reporting and GitHub security advisories.

No long-lived PyPI token is stored in GitHub. The release workflow requests a scoped,
short-lived OIDC credential from each package index.

## Prepare a Release Pull Request

1. Choose one PEP 440 version for all three product manifests.
2. Update each internal dependency range when the coordinated version line changes.
3. Move the relevant entries from `[Unreleased]` into the version section.
4. Replace `Unreleased` after the version heading with the intended UTC release date
   in `YYYY-MM-DD` form.
5. Update the comparison links at the bottom of `CHANGELOG.md`.
6. Refresh and verify the lock file:

   ```bash
   uv --project python lock
   uv --project python sync --locked
   uv --project python run python scripts/sync_spec.py
   ```

7. Run the local release gate:

   ```bash
   uv --project python run python scripts/verify_release.py
   uv --project python run pytest -c python/pyproject.toml -q -p no:cacheprovider
   uv --project python run ruff check --config python/pyproject.toml .
   uv --project python run ruff format --check --config python/pyproject.toml .
   uv --project python run pyright --project python
   uv --project python run conformance \
     .jharness-spec/conformance/cases \
     --spec-dir .jharness-spec/contracts/v0
   uv --project python run python benchmarks/runtime_smoke.py
   ```

The pull request must merge before the release tag is created. Do not build or upload
release artifacts from a developer workstation.

## Publish

For coordinated version `X.Y.Z`, create and push an annotated tag on the reviewed
merge commit:

```bash
git switch main
git pull --ff-only
git tag -a vX.Y.Z -m "JHarness vX.Y.Z"
git push origin vX.Y.Z
```

The tag starts `.github/workflows/release.yml`, which:

1. proves the tag, manifests, internal dependency ranges, and changelog agree;
2. reruns lint, formatting, strict types, tests with coverage, conformance, and benchmark;
3. builds the three wheels and three source distributions exactly once;
4. verifies archive ownership, isolated imports, package metadata, and checksums;
5. publishes each distribution to TestPyPI through its own trusted publisher;
6. installs all three TestPyPI versions and executes public smoke examples;
7. pauses for the three configured `pypi-*` environment approvals;
8. publishes each distribution through its own PyPI trusted publisher and verifies
   a clean installation;
9. creates the GitHub Release with all distributions and `SHA256SUMS`.

The release is complete only when every job is green and all three PyPI projects show
the same version. No environment approval or package-index token is required.

## Failure and Recovery

- Before PyPI publication, fix the release commit, choose a new version if TestPyPI
  already contains the old one, and create a new tag. Do not move a published tag.
- If TestPyPI publication succeeded but a later pre-PyPI job failed, dispatch the same
  release workflow with the immutable tag and source run ID. The recovery path checks
  that the run belongs to the tagged commit, verifies every stored checksum, skips the
  completed TestPyPI upload, and continues the automated pipeline.
- After any PyPI artifact is published, never reuse or overwrite that version. Finish
  the coordinated set if safe; otherwise yank the affected version and publish a patch.
- A GitHub Release failure after successful PyPI verification may be repaired by
  creating the release from the workflow artifact. Do not rebuild the distributions.
- Compromised or materially broken releases are yanked, documented in the changelog
  and security advisory when applicable, and superseded by a new version.

## Pre-Releases

Use normal PEP 440 pre-release versions such as `0.2.0a1` or `0.2.0rc1`. Internal
dependency lower bounds must include that exact pre-release version. The same tag and
workflow rules apply. The workflow marks a tag containing letters as a GitHub
pre-release; package installers continue to follow PEP 440.
