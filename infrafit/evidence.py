"""근거(Evidence) 만들기와 줄 검색."""

from __future__ import annotations

import re

from infrafit.repo import Snapshot


def evidence(snap: Snapshot, rel: str, line: int | None = None, kind: str | None = None) -> dict:
    snippet = rel
    if line is not None:
        lines = snap.lines(rel)
        if 0 < line <= len(lines):
            snippet = lines[line - 1].strip()[:200] or rel
    ev = {"path": rel, "line": line, "snippet": snippet}
    if kind:
        ev["kind"] = kind
    return ev


def line_of(snap: Snapshot, rel: str, needle: str) -> int | None:
    for i, text in enumerate(snap.lines(rel), 1):
        if needle in text:
            return i
    return None


def grep_lines(snap: Snapshot, rel: str, pattern: str, flags: int = 0) -> list[int]:
    rx = re.compile(pattern, flags)
    return [i for i, text in enumerate(snap.lines(rel), 1) if rx.search(text)]
