"""Helpers for scanning public Python interfaces."""

from __future__ import annotations

import ast
from pathlib import Path


def _format_annotation(annotation: ast.expr | None) -> str:
    if annotation is None:
        return ""
    return ast.unparse(annotation)


def _format_arg(argument: ast.arg) -> str:
    annotation = _format_annotation(argument.annotation)
    if annotation:
        return f"{argument.arg}: {annotation}"
    return argument.arg


def _format_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    parts: list[str] = []

    positional_only = [_format_arg(arg) for arg in node.args.posonlyargs]
    regular_args = [_format_arg(arg) for arg in node.args.args]
    if positional_only:
        parts.extend(positional_only)
        parts.append("/")
    parts.extend(regular_args)

    if node.args.vararg is not None:
        vararg = node.args.vararg
        annotation = _format_annotation(vararg.annotation)
        parts.append(f"*{vararg.arg}: {annotation}" if annotation else f"*{vararg.arg}")
    elif node.args.kwonlyargs:
        parts.append("*")

    parts.extend(_format_arg(arg) for arg in node.args.kwonlyargs)

    if node.args.kwarg is not None:
        kwarg = node.args.kwarg
        annotation = _format_annotation(kwarg.annotation)
        parts.append(f"**{kwarg.arg}: {annotation}" if annotation else f"**{kwarg.arg}")

    signature = f"{node.name}({', '.join(parts)})"
    return_annotation = _format_annotation(node.returns)
    if return_annotation:
        return f"{signature} -> {return_annotation}"
    return signature


def _scan_python_file(file_path: Path) -> list[str]:
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(file_path))
    signatures: list[str] = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            signatures.append(_format_signature(node))

    return signatures


def scan_interfaces(project_root: str, patterns: list[str]) -> dict[str, list[str]]:
    """Scan matching files and return top-level function signatures."""
    if not patterns:
        return {}

    root = Path(project_root)
    matched_files: dict[str, Path] = {}
    for pattern in patterns:
        expanded_paths = list(root.glob(pattern))
        for path in expanded_paths:
            if path.is_file() and path.suffix == ".py":
                relative_path = path.relative_to(root).as_posix()
                matched_files[relative_path] = path

    scanned: dict[str, list[str]] = {}
    for relative_path in sorted(matched_files):
        signatures = _scan_python_file(matched_files[relative_path])
        if signatures:
            scanned[relative_path] = signatures

    return scanned
