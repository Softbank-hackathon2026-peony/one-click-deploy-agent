"""의존성 매니페스트와 실행 정의 파싱."""

from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass, field

from infrafit.detect.jvm import read_gradle, read_maven
from infrafit.evidence import line_of
from infrafit.repo import Snapshot, parent_dir

_REQ_NAME = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


def _norm_py(name: str) -> str:
    return name.lower().replace("_", "-")


@dataclass
class Manifests:
    deps: dict[str, tuple[str, int | None]] = field(default_factory=dict)
    deps_by_dir: dict[str, set[str]] = field(default_factory=dict)
    locations: dict[str, list[tuple[str, int | None]]] = field(default_factory=dict)
    scripts: dict[str, tuple[str, str, int | None]] = field(default_factory=dict)
    procfile: dict[str, tuple[str, str, int]] = field(default_factory=dict)
    # (모듈 디렉터리, 의존성) → 그 모듈에 의존성을 준 (파일, 줄)들. 보통 모듈은 파일의 디렉터리이고, Gradle
    # subprojects·allprojects 블록의 의존성은 그 아래 하위 모듈들의 것이다
    module_locations: dict[tuple[str, str], list[tuple[str, int | None]]] = field(default_factory=dict)

    def add(self, name: str, rel: str, line: int | None, module: str | None = None) -> None:
        """module: 의존성이 속한 모듈 디렉터리(없으면 파일의 디렉터리)."""
        d = parent_dir(rel) if module is None else module
        self.deps.setdefault(name, (rel, line))
        self.deps_by_dir.setdefault(d, set()).add(name)
        if (rel, line) not in self.locations.setdefault(name, []):
            self.locations[name].append((rel, line))
        if (rel, line) not in self.module_locations.setdefault((d, name), []):
            self.module_locations[(d, name)].append((rel, line))


def _node(snap: Snapshot, m: Manifests) -> None:
    for rel in snap.glob("**/package.json"):
        try:
            data = json.loads(snap.read(rel))
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        for section in ("dependencies", "devDependencies"):
            section_data = data.get(section)
            if not isinstance(section_data, dict):
                section_data = {}
            for name in sorted(section_data):
                m.add(name.lower(), rel, line_of(snap, rel, f'"{name}"'))
        scripts_data = data.get("scripts")
        if not isinstance(scripts_data, dict):
            scripts_data = {}
        for name, cmd in sorted(scripts_data.items()):
            m.scripts[f"{parent_dir(rel)}:{name}"] = (str(cmd), rel, line_of(snap, rel, f'"{name}"'))


def _requirements(snap: Snapshot, m: Manifests) -> None:
    for rel in snap.glob("**/requirements*.txt"):
        for i, text in enumerate(snap.lines(rel), 1):
            body = text.split("#", 1)[0].strip()
            if not body or body.startswith("-"):
                continue
            # Skip URLs, VCS references, paths
            if body.startswith(("git+", "hg+", "svn+", "bzr+", ".", "/")):
                continue
            # Skip lines with :// before @ or name (e.g., https://host/a.whl)
            scheme_end = body.split("@")[0]
            if "://" in scheme_end:
                continue
            # Handle PEP 508 direct references (name @ url)
            if " @ " in body:
                name = body.split(" @ ")[0].strip()
                m.add(_norm_py(name), rel, i)
                continue
            # Standard package requirement
            match = _REQ_NAME.match(body)
            if match:
                m.add(_norm_py(match.group(1)), rel, i)


def _pyproject(snap: Snapshot, m: Manifests) -> None:
    for rel in snap.glob("**/pyproject.toml"):
        try:
            data = tomllib.loads(snap.read(rel))
        except tomllib.TOMLDecodeError:
            continue
        reqs = list((data.get("project") or {}).get("dependencies") or [])
        names = [mm.group(1) for r in reqs if (mm := _REQ_NAME.match(r))]
        poetry = ((data.get("tool") or {}).get("poetry") or {}).get("dependencies") or {}
        names += [k for k in poetry if k.lower() != "python"]
        for name in names:
            m.add(_norm_py(name), rel, line_of(snap, rel, name))


def _procfile(snap: Snapshot, m: Manifests) -> None:
    for rel in snap.glob("**/Procfile"):
        for i, text in enumerate(snap.lines(rel), 1):
            if ":" not in text or text.lstrip().startswith("#"):
                continue
            proc, cmd = text.split(":", 1)
            m.procfile[f"{parent_dir(rel)}:{proc.strip()}"] = (cmd.strip(), rel, i)


def parse_manifests(snap: Snapshot) -> Manifests:
    m = Manifests()
    _node(snap, m)
    _requirements(snap, m)
    _pyproject(snap, m)
    _procfile(snap, m)
    read_gradle(snap, m)
    read_maven(snap, m)
    return m
