## 7. File Placement

Where the development process keeps its own files. Where application code lives, and the files the application reads and writes, is `docs/ARCHITECTURE.md`.

| Content | Location |
| --- | --- |
| Design studies and recon | `docs/dev/design/` |
| Specs | `docs/dev/specs/` |
| Implementation results | `docs/dev/results/` |
| Application tests, `test_<component>.py` | `tests/` |
| Data files the application tests read | `tests/fixtures/` |
| Test doubles the application tests share | `tests/mocks/` |
| Utilities, diagnostics and demos | `scripts/` |
| Alembic's configuration, `alembic.ini` | repository root |
| Non-application dev tooling, its tests (`*_test.py`) and their fixtures | `automation/` |
