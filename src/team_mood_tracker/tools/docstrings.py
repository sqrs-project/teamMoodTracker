"""Minimal docstring coverage checker used by the project."""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MissingDocstring:
    """A public symbol that is missing a docstring."""

    path: Path
    symbol: str
    line: int


def main() -> int:
    """Run the docstring coverage check and return a shell exit code."""

    args = _parse_args()
    missing = _collect_missing(args.paths)
    if missing:
        _print_missing(missing, verbose=args.verbose)
        return 1
    print(f"Docstring coverage OK for {len(args.paths)} path(s).")
    return 0


def _parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description="Validate docstring coverage for public symbols.")
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("-v", "--verbose", action="count", default=0)
    return parser.parse_args()


def _collect_missing(paths: list[Path]) -> list[MissingDocstring]:
    """Collect public modules, classes, and functions without docstrings."""

    missing: list[MissingDocstring] = []
    for path in paths:
        for file_path in _python_files(path):
            tree = ast.parse(file_path.read_text(encoding="utf-8"))
            missing.extend(_module_issues(file_path, tree))
            missing.extend(_body_issues(file_path, tree.body, parent=""))
    return missing


def _python_files(path: Path) -> list[Path]:
    """Return Python files under a path."""

    if path.is_file():
        return [path]
    return sorted(file_path for file_path in path.rglob("*.py") if file_path.name != "__pycache__")


def _module_issues(path: Path, tree: ast.Module) -> list[MissingDocstring]:
    """Return missing-docstring issues for a module."""

    if ast.get_docstring(tree):
        return []
    return [MissingDocstring(path=path, symbol="module", line=1)]


def _body_issues(path: Path, body: list[ast.stmt], parent: str) -> list[MissingDocstring]:
    """Return missing-docstring issues for public symbols in a module or class body."""

    issues: list[MissingDocstring] = []
    for node in body:
        if isinstance(node, ast.ClassDef):
            issues.extend(_class_issues(path, node, parent))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            issue = _function_issue(path, node, parent)
            if issue is not None:
                issues.append(issue)
    return issues


def _class_issues(path: Path, node: ast.ClassDef, parent: str) -> list[MissingDocstring]:
    """Return missing-docstring issues for a public class and its public methods."""

    if _is_private(node.name):
        return []
    symbol = _symbol_name(parent, node.name)
    issues: list[MissingDocstring] = []
    if not ast.get_docstring(node):
        issues.append(MissingDocstring(path=path, symbol=symbol, line=node.lineno))
    issues.extend(_body_issues(path, node.body, parent=symbol))
    return issues


def _function_issue(
    path: Path, node: ast.FunctionDef | ast.AsyncFunctionDef, parent: str
) -> MissingDocstring | None:
    """Return a missing-docstring issue for a public function or method."""

    if _is_private(node.name) or node.name == "__init__":
        return None
    if ast.get_docstring(node):
        return None
    return MissingDocstring(
        path=path,
        symbol=_symbol_name(parent, node.name),
        line=node.lineno,
    )


def _is_private(name: str) -> bool:
    """Return whether a symbol should be treated as private."""

    return name.startswith("_") and not name.startswith("__")


def _symbol_name(parent: str, name: str) -> str:
    """Return a fully-qualified symbol name."""

    if not parent:
        return name
    return f"{parent}.{name}"


def _print_missing(missing: list[MissingDocstring], *, verbose: int) -> None:
    """Print missing docstring issues."""

    print("Missing docstrings:")
    for issue in missing:
        print(f"- {issue.path}:{issue.line} {issue.symbol}")
    if verbose:
        print(f"Total missing docstrings: {len(missing)}")


if __name__ == "__main__":
    raise SystemExit(main())
