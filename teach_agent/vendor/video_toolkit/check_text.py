#!/usr/bin/env python3
"""Lightweight text sanity checker for Manim scene files.

This is intentionally video-only and dependency-light. It catches common issues
before rendering:

- mojibake / replacement characters,
- invisible control characters,
- risky Unicode math subscripts/superscripts in Text,
- missing obvious Chinese-capable font hints.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path


RISKY_CHARS = set("ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓₔⁱⁿ")
MOJIBAKE_HINTS = ("锛", "涓", "绋", "鏂", "鍔", "鐨", "�", "\ufffd")


def iter_text_calls(tree: ast.AST):
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = ""
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            name = node.func.attr
        if name not in {"Text", "MarkupText", "text_label", "label"}:
            continue
        if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
            yield node.lineno, node.args[0].value


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python check_text.py <scene.py>")
        return 2

    path = Path(sys.argv[1])
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    warnings = []
    for lineno, text in iter_text_calls(tree):
        if any(hint in text for hint in MOJIBAKE_HINTS):
            warnings.append((lineno, "possible mojibake", text))
        bad_controls = [ch for ch in text if ord(ch) < 32 and ch not in "\n\t"]
        if bad_controls:
            warnings.append((lineno, "control characters", repr(text)))
        risky = sorted(set(text) & RISKY_CHARS)
        if risky:
            warnings.append((lineno, f"risky font glyphs {''.join(risky)}", text))

    has_cjk = bool(re.search(r"[\u4e00-\u9fff]", source))
    has_font_hint = any(name in source for name in ["Microsoft YaHei", "SimHei", "Noto Sans CJK", "PingFang SC", "ZH_FONT"])
    if has_cjk and not has_font_hint:
        warnings.append((0, "Chinese text present but no obvious CJK font hint", "set font='Microsoft YaHei' or similar"))

    if warnings:
        print("[FAIL] text sanity warnings:")
        for lineno, kind, text in warnings:
            loc = f"{path}:{lineno}" if lineno else str(path)
            print(f"- {loc}: {kind}: {text}")
        return 1

    print("[PASS] text sanity check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
