"""
Lists every function and method that takes a SQLAlchemy session.

A session parameter is one named `session`, or one whose annotation's source
text contains `Session`, on a function or method at any depth of a module.
The modules checked are the ones named, optionally narrowed to the functions
of one name, or the workmain/services/ modules a package imports anywhere,
at module level or inside a function. Paths resolve against the current
working directory, and findings are printed relative to it, one per line as
`<path>:<line> <name>`, sorted by path and line.

Exit 0 when no session parameter is found, 1 when any is, and 2 on a usage
error or a path that does not exist.
"""

import argparse
import ast
import os
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set, Tuple

SERVICES_PACKAGE = "workmain.services"

# A module to check, and the one function name it is narrowed to, if any.
Target = Tuple[Path, Optional[str]]


def _relative(path: Path) -> str:
    """Return path relative to the working directory, in POSIX form."""
    return Path(os.path.relpath(path.resolve(), Path.cwd().resolve())).as_posix()


def _takes_session(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Whether any parameter of node is a session parameter."""
    args = node.args
    params = args.posonlyargs + args.args + args.kwonlyargs
    params += [a for a in (args.vararg, args.kwarg) if a is not None]
    return any(
        a.arg == "session" or (a.annotation is not None and "Session" in ast.unparse(a.annotation))
        for a in params
    )


def _find_session_params(path: Path, name: Optional[str] = None) -> List[Tuple[str, int, str]]:
    """
    Find the session-taking functions and methods in one module.

    Args:
        path: The module to read
        name: Only functions and methods of this name, or every one if None

    Returns:
        (relative path, line, function name) for each finding
    """
    tree = ast.parse(path.read_text(), filename=str(path))
    shown = _relative(path)
    return [
        (shown, node.lineno, node.name)
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and (name is None or node.name == name)
        and _takes_session(node)
    ]


def _service_module_file(dotted: str) -> Optional[Path]:
    """Resolve a dotted workmain.services module name to its file, if it has one."""
    base = Path(*dotted.split("."))
    for candidate in (base.with_suffix(".py"), base / "__init__.py"):
        if candidate.is_file():
            return candidate
    return None


def _service_imports(tree: ast.Module) -> Iterable[str]:
    """Yield the dotted name of every workmain.services module tree imports, at any depth."""
    prefix = SERVICES_PACKAGE + "."
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(prefix):
                    yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            if node.module.startswith(prefix):
                yield node.module
            elif node.module == SERVICES_PACKAGE:
                for alias in node.names:
                    yield f"{SERVICES_PACKAGE}.{alias.name}"


def _package_targets(package: Path) -> List[Path]:
    """
    Resolve the workmain/services/ modules a package imports.

    Args:
        package: The package directory whose modules are read

    Returns:
        The file of each imported services module, once each
    """
    found: Set[Path] = set()
    for module in sorted(package.rglob("*.py")):
        tree = ast.parse(module.read_text(), filename=str(module))
        for dotted in _service_imports(tree):
            resolved = _service_module_file(dotted)
            if resolved is not None:
                found.add(resolved)
    return sorted(found)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """
    Print every session parameter in the modules given, and return the exit code.

    Args:
        argv: Command-line arguments, without the program name

    Returns:
        0 for no finding, 1 for any, 2 for a usage error or a missing path
    """
    parser = argparse.ArgumentParser(description="List every function or method that takes a session.")
    parser.add_argument("paths", nargs="*", metavar="PATH[::NAME]", help="a module, optionally narrowed to the functions of NAME")
    parser.add_argument("--package", metavar="DIR", help="check the workmain/services/ modules this package imports")
    parser.add_argument("--exclude", action="append", default=[], metavar="PATH", help="leave this module out (repeatable)")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_:
        return 2 if exit_.code else 0
    if bool(args.paths) == bool(args.package):
        print("error: give module paths or --package, not both and not neither", file=sys.stderr)
        return 2

    targets: List[Target] = []
    if args.package:
        package = Path(args.package)
        if not package.is_dir():
            print(f"error: no such package directory: {args.package}", file=sys.stderr)
            return 2
        targets = [(path, None) for path in _package_targets(package)]
    else:
        for raw in args.paths:
            path_text, _, name = raw.partition("::")
            path = Path(path_text)
            if not path.is_file():
                print(f"error: no such module: {path_text}", file=sys.stderr)
                return 2
            targets.append((path, name or None))

    excluded = {Path(p).resolve() for p in args.exclude}
    findings: Set[Tuple[str, int, str]] = set()
    for path, name in targets:
        if path.resolve() not in excluded:
            findings.update(_find_session_params(path, name))

    for shown, line, name in sorted(findings):
        print(f"{shown}:{line} {name}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
