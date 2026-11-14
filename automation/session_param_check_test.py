"""
Tests for automation/session_param_check.py.

Each test writes its modules under a temporary folder, makes that folder the
working directory, and runs the script's main() there, capturing what it
prints.
"""

import contextlib
import importlib.util
import io
import textwrap
from pathlib import Path
from typing import Dict, List, Tuple

import pytest

ROOT = Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location(
    "session_param_check", ROOT / "automation" / "session_param_check.py"
)
spc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(spc)

SERVICE = """
from sqlalchemy.orm import Session


def by_name(session, day):
    pass


def by_annotation(db: Session):
    pass


def optional_annotation(db: "Optional[Session]" = None):
    pass


def no_session(day):
    pass


class Service:
    def __init__(self, session: Session) -> None:
        self.session = session

    def method(self, value):
        def nested(session):
            pass
"""


def _write(root: Path, files: Dict[str, str]) -> None:
    """Write each relative path's text under root."""
    for relative, body in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(body))


def _run(root: Path, argv: List[str]) -> Tuple[int, List[str]]:
    """Run main() with root as the working directory; return its exit code and printed lines."""
    out = io.StringIO()
    with pytest.MonkeyPatch.context() as mp:
        mp.chdir(root)
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = spc.main(argv)
    return code, out.getvalue().splitlines()


class TestFindings:
    """Every session parameter in a module is listed, and nothing else."""

    def test_lists_each_session_parameter_and_none_other(self, tmp_path: Path) -> None:
        _write(tmp_path, {"workmain/services/svc.py": SERVICE})
        code, lines = _run(tmp_path, ["workmain/services/svc.py"])
        assert code == 1
        assert lines == [
            "workmain/services/svc.py:5 by_name",
            "workmain/services/svc.py:9 by_annotation",
            "workmain/services/svc.py:13 optional_annotation",
            "workmain/services/svc.py:22 __init__",
            "workmain/services/svc.py:26 nested",
        ]

    def test_parameter_named_session(self, tmp_path: Path) -> None:
        _write(tmp_path, {"m.py": "def f(session):\n    pass\n"})
        assert _run(tmp_path, ["m.py"]) == (1, ["m.py:1 f"])

    def test_parameter_annotated_session(self, tmp_path: Path) -> None:
        _write(tmp_path, {"m.py": "def f(db: Session):\n    pass\n"})
        assert _run(tmp_path, ["m.py"]) == (1, ["m.py:1 f"])

    def test_method_parameter(self, tmp_path: Path) -> None:
        _write(tmp_path, {"m.py": "class C:\n    def m(self, session):\n        pass\n"})
        assert _run(tmp_path, ["m.py"]) == (1, ["m.py:2 m"])

    def test_no_session_parameter_exits_zero(self, tmp_path: Path) -> None:
        _write(tmp_path, {"m.py": "def f(sessions, db: int):\n    pass\n"})
        assert _run(tmp_path, ["m.py"]) == (0, [])

    def test_sorted_by_path_and_line(self, tmp_path: Path) -> None:
        _write(tmp_path, {
            "b.py": "def g(session):\n    pass\n",
            "a.py": "\n\ndef f2(session):\n    pass\n\ndef f1(session):\n    pass\n",
        })
        assert _run(tmp_path, ["b.py", "a.py"]) == (1, ["a.py:3 f2", "a.py:6 f1", "b.py:1 g"])


class TestNarrowing:
    """`<path>::<name>` keeps only the functions and methods of that name."""

    def test_narrowed_to_one_name(self, tmp_path: Path) -> None:
        _write(tmp_path, {"workmain/services/svc.py": SERVICE})
        code, lines = _run(tmp_path, ["workmain/services/svc.py::__init__"])
        assert (code, lines) == (1, ["workmain/services/svc.py:22 __init__"])

    def test_narrowed_to_a_name_without_session(self, tmp_path: Path) -> None:
        _write(tmp_path, {"workmain/services/svc.py": SERVICE})
        assert _run(tmp_path, ["workmain/services/svc.py::no_session"]) == (0, [])


class TestExclude:
    """`--exclude` leaves a module out."""

    def test_excluded_module_not_checked(self, tmp_path: Path) -> None:
        _write(tmp_path, {
            "a.py": "def f(session):\n    pass\n",
            "b.py": "def g(session):\n    pass\n",
        })
        assert _run(tmp_path, ["a.py", "b.py", "--exclude", "b.py"]) == (1, ["a.py:1 f"])

    def test_repeatable(self, tmp_path: Path) -> None:
        _write(tmp_path, {
            "a.py": "def f(session):\n    pass\n",
            "b.py": "def g(session):\n    pass\n",
        })
        assert _run(tmp_path, ["a.py", "b.py", "--exclude", "a.py", "--exclude", "b.py"]) == (0, [])


class TestPackage:
    """`--package` checks every workmain/services/ module the package imports, at any depth."""

    SERVICES = {
        "workmain/services/top.py": "def top(session):\n    pass\n",
        "workmain/services/inner.py": "def inner(session):\n    pass\n",
        "workmain/services/plain.py": "def plain(session):\n    pass\n",
        "workmain/services/dotted.py": "def dotted(session):\n    pass\n",
        "workmain/services/unused.py": "def unused(session):\n    pass\n",
    }

    def test_module_level_import(self, tmp_path: Path) -> None:
        _write(tmp_path, {**self.SERVICES, "pkg/a.py": "from workmain.services.top import top\n"})
        assert _run(tmp_path, ["--package", "pkg"]) == (1, ["workmain/services/top.py:1 top"])

    def test_import_inside_function(self, tmp_path: Path) -> None:
        body = "def run():\n    from workmain.services.inner import inner\n    return inner\n"
        _write(tmp_path, {**self.SERVICES, "pkg/a.py": body})
        assert _run(tmp_path, ["--package", "pkg"]) == (1, ["workmain/services/inner.py:1 inner"])

    def test_each_import_form(self, tmp_path: Path) -> None:
        body = "import workmain.services.dotted\nfrom workmain.services import plain\n"
        _write(tmp_path, {**self.SERVICES, "pkg/sub/a.py": body})
        code, lines = _run(tmp_path, ["--package", "pkg"])
        assert (code, lines) == (1, ["workmain/services/dotted.py:1 dotted", "workmain/services/plain.py:1 plain"])

    def test_exclude_applies(self, tmp_path: Path) -> None:
        _write(tmp_path, {**self.SERVICES, "pkg/a.py": "from workmain.services.top import top\n"})
        argv = ["--package", "pkg", "--exclude", "workmain/services/top.py"]
        assert _run(tmp_path, argv) == (0, [])


class TestExitCodes:
    """Exit 0 for no finding, 1 for any, 2 for a usage error or a missing path."""

    def test_zero_when_none(self, tmp_path: Path) -> None:
        _write(tmp_path, {"m.py": "def f(day):\n    pass\n"})
        assert _run(tmp_path, ["m.py"])[0] == 0

    def test_one_when_any(self, tmp_path: Path) -> None:
        _write(tmp_path, {"m.py": "def f(session):\n    pass\n"})
        assert _run(tmp_path, ["m.py"])[0] == 1

    def test_two_with_no_arguments(self, tmp_path: Path) -> None:
        assert _run(tmp_path, [])[0] == 2

    def test_two_for_unknown_option(self, tmp_path: Path) -> None:
        assert _run(tmp_path, ["--nope"])[0] == 2

    def test_two_for_missing_module(self, tmp_path: Path) -> None:
        assert _run(tmp_path, ["missing.py"])[0] == 2

    def test_two_for_missing_narrowed_module(self, tmp_path: Path) -> None:
        assert _run(tmp_path, ["missing.py::f"])[0] == 2

    def test_two_for_missing_package(self, tmp_path: Path) -> None:
        assert _run(tmp_path, ["--package", "missing"])[0] == 2
