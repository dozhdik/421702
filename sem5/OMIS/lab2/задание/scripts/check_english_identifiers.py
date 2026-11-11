#!/usr/bin/env python3
"""Fail when Python source uses non-English program identifiers.

Russian Unicode string literals (for UI labels or articles) are intentionally allowed.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".mypy_cache", ".pytest_cache"}


def iter_python_files(root: Path):
    if root.is_file() and root.suffix == ".py":
        yield root
        return
    for file_path in root.rglob("*.py"):
        if not any(part in SKIP_DIRS for part in file_path.parts):
            yield file_path


def identifier_candidates(node: ast.AST):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        yield node.name
    if isinstance(node, ast.Name):
        yield node.id
    if isinstance(node, ast.Attribute):
        yield node.attr
    if isinstance(node, ast.arg):
        yield node.arg
    if isinstance(node, ast.alias):
        yield node.name
        if node.asname:
            yield node.asname
    if isinstance(node, ast.keyword) and node.arg:
        yield node.arg
    if isinstance(node, ast.ExceptHandler) and node.name:
        yield node.name
    if isinstance(node, (ast.Global, ast.Nonlocal)):
        yield from node.names
    if isinstance(node, (ast.MatchAs, ast.MatchStar)) and node.name:
        yield node.name
    if isinstance(node, ast.MatchMapping) and node.rest:
        yield node.rest
    if isinstance(node, ast.MatchClass):
        yield from node.kwd_attrs


def has_non_ascii_char(value: str) -> bool:
    return not value.isascii()


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    violations = []
    for file_path in iter_python_files(root):
        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError) as exc:
            violations.append((file_path, 0, f"Cannot parse file: {exc}"))
            continue
        for node in ast.walk(tree):
            for value in identifier_candidates(node):
                if has_non_ascii_char(value):
                    violations.append((file_path, getattr(node, "lineno", 0), value))
    if violations:
        for file_path, line, name in violations:
            print(f"{file_path}:{line}: non-ASCII Python identifier: {name}")
        print(f"Found {len(violations)} non-ASCII identifier occurrences.")
        return 1
    print("OK: No non-ASCII Python identifiers found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
