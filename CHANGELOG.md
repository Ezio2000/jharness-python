# Changelog

All notable changes to JHarness are recorded here. The three product distributions
share one version and one changelog.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Expanded each distribution README into a standalone PyPI guide while keeping
  every page within its declared dependency boundary.
- Added explicit code ownership and weekly dependency update pull requests for
  the uv workspace and GitHub Actions.
- Made package-index publication fully unattended and added checksum-verified
  continuation from an immutable release artifact.
- Isolated TestPyPI package selection so third-party dependencies resolve only from
  PyPI.

## [0.1.0] - 2026-07-15

### Added

- Immutable model-neutral runtime kernel with atomic checkpoints and explicit wire codecs.
- Tool registry, validation, function adapters, retries, and circuit breaking.
- OpenAI Chat Completions, Anthropic Messages, and DeepSeek provider profiles.
- Portable v0 contracts, 66 conformance cases, diagnostics, and trace verification.
- Per-distribution Trusted Publisher environments for credential-free first releases.

[Unreleased]: https://github.com/Ezio2000/jharness-python/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Ezio2000/jharness-python/releases/tag/v0.1.0
