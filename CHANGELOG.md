# Changelog

All notable changes to **json2csv** will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [1.0.0] – 2026-06-23

### Added
- `converter.py`: core domain module with `convert_records`, `convert_string`,
  and `convert_file` functions.
- `cli.py`: thin CLI wrapper with descriptive exit codes (0–4).
- `_version.py`: single source of truth for `VERSION` and `BUILD`.
- Full typed exception hierarchy: `Json2CsvError`, `EmptyDataError`,
  `InvalidJsonStructureError`, `FileReadError`, `FileWriteError`.
- `--flatten` option to recursively flatten nested JSON objects/arrays
  into dotted-key columns.
- `--sep`, `--dialect`, `--encoding` options in the CLI.
- Unit tests with Pytest + Hypothesis achieving ≥ 85 % branch coverage.
- Static type checking with MyPy and PyRight (both in `strict` mode).
- Linting and format enforcement with Ruff and Black (PEP 8 / PEP 257).
- Security scan with Bandit (zero findings).
- GitHub Actions CI/CD pipeline (`ci.yml`): quality → tests → docs.
- Automatic pdoc documentation published to GitHub Pages on every merge
  to `main`.
- `CONTEXT.md` for Vibe Coding assistance.
- MIT license.
- `requirements.txt` for virtual environment setup.
- Example files in `ejemplos/`.

### Changed
- N/A (initial release)

### Fixed
- N/A (initial release)

### Removed
- N/A (initial release)

---

[Unreleased]: https://github.com/lu7did/json2csv/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/lu7did/json2csv/releases/tag/v1.0.0
