"""의존성 매니페스트와 실행 정의 파싱."""

from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import PurePosixPath

from infrafit.evidence import line_of
from infrafit.repo import Snapshot

_REQ_NAME = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


def parent_dir(rel: str) -> str:
    parent = PurePosixPath(rel).parent.as_posix()
    return "" if parent == "." else parent


def _norm_py(name: str) -> str:
    return name.lower().replace("_", "-")


@dataclass
class Manifests:
    deps: dict[str, tuple[str, int | None]] = field(default_factory=dict)
    deps_by_dir: dict[str, set[str]] = field(default_factory=dict)
    locations: dict[str, list[tuple[str, int | None]]] = field(default_factory=dict)
    scripts: dict[str, tuple[str, str, int | None]] = field(default_factory=dict)
    procfile: dict[str, tuple[str, str, int]] = field(default_factory=dict)

    def add(self, name: str, rel: str, line: int | None) -> None:
        self.deps.setdefault(name, (rel, line))
        self.deps_by_dir.setdefault(parent_dir(rel), set()).add(name)
        if (rel, line) not in self.locations.setdefault(name, []):
            self.locations[name].append((rel, line))


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


SPRING_BOOT = "org.springframework.boot"  # Spring Boot 플러그인·parent를 뜻하는 의존성 이름
GRADLE_FILES = ("build.gradle", "build.gradle.kts")
MAVEN_FILE = "pom.xml"
_GRADLE_CONF = re.compile(r"\b(implementation|api|runtimeOnly|compileOnly|annotationProcessor|kapt|developmentOnly"
                          r"|testImplementation|testRuntimeOnly)\b(.*)")
_GRADLE_COORD = re.compile(r"""["']([\w.\-]+):([\w.\-]+)(?::[^"']*)?["']""")
_GRADLE_MAP = re.compile(r"""\bgroup\s*[:=]\s*["']([\w.\-]+)["']\s*,\s*name\s*[:=]\s*["']([\w.\-]+)["']""")
_GRADLE_BOOT = re.compile(r"""\bid\s*\(?\s*["']org\.springframework\.boot["']"""
                          r"""|\bapply\s+plugin\s*:\s*["']org\.springframework\.boot["']""")
_GRADLE_APPLY_FALSE = re.compile(r"\bapply\s*\(?\s*false\b")
_XML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)


def _gradle(snap: Snapshot, m: Manifests) -> None:
    """build.gradle(.kts)의 의존성 좌표(`g:a`)와 Spring Boot 플러그인. `test*` 구성과 `apply false`인 플러그인
    선언(하위 모듈에만 적용하는 루트 선언)은 건너뛴다. 줄은 좌표가 있는 줄."""
    for rel in sorted(rel for pattern in GRADLE_FILES for rel in snap.glob(f"**/{pattern}")):
        for i, text in enumerate(snap.lines(rel), 1):
            if text.lstrip().startswith(("//", "/*", "*")):
                continue
            if _GRADLE_BOOT.search(text) and not _GRADLE_APPLY_FALSE.search(text):
                m.add(SPRING_BOOT, rel, i)
            conf = _GRADLE_CONF.search(text)
            if not conf or conf.group(1).startswith("test"):
                continue
            for g, a in _GRADLE_COORD.findall(conf.group(2)) + _GRADLE_MAP.findall(conf.group(2)):
                m.add(f"{g}:{a}".lower(), rel, i)


def _blank(match: re.Match) -> str:
    """지운 부분을 같은 길이의 공백으로 바꾼다(줄바꿈은 남겨 위치와 줄 번호를 지킨다)."""
    return re.sub(r"[^\r\n]", " ", match.group(0))


def _xml_tag(block: str, tag: str) -> re.Match | None:
    return re.search(rf"<{tag}>\s*([^<]*?)\s*</{tag}>", block)


def _line_at(text: str, pos: int) -> int:
    """text의 pos 글자가 있는 줄 번호(1부터, Snapshot.lines와 같은 줄 나눔)."""
    return len((text[:pos] + "x").splitlines())


def _maven(snap: Snapshot, m: Manifests) -> None:
    """pom.xml의 `<dependency>`마다 `groupId:artifactId`(scope test 제외, 줄은 artifactId 줄).
    `<dependencyManagement>`(버전 선언)와 `<build>`(플러그인 의존성)의 항목은 앱 의존성이 아니므로 뺀다.
    parent가 spring-boot-starter-parent이면 org.springframework.boot(packaging이 pom인 집계 모듈은 제외)."""
    for rel in snap.glob(f"**/{MAVEN_FILE}"):
        masked = re.sub(r"<(dependencyManagement|build)>.*?</\1>", _blank,
                        _XML_COMMENT.sub(_blank, snap.read(rel)), flags=re.DOTALL)
        for block in re.finditer(r"<dependency>(.*?)</dependency>", masked, re.DOTALL):
            body = block.group(1)
            group, artifact, scope = _xml_tag(body, "groupId"), _xml_tag(body, "artifactId"), _xml_tag(body, "scope")
            if not group or not artifact or (scope and scope.group(1) == "test"):
                continue
            m.add(f"{group.group(1)}:{artifact.group(1)}".lower(), rel,
                  _line_at(masked, block.start(1) + artifact.start()))
        parent = re.search(r"<parent>(.*?)</parent>", masked, re.DOTALL)
        packaging = _xml_tag(masked, "packaging")
        artifact = _xml_tag(parent.group(1), "artifactId") if parent else None
        if artifact and artifact.group(1) == "spring-boot-starter-parent" and not (
                packaging and packaging.group(1) == "pom"):
            m.add(SPRING_BOOT, rel, _line_at(masked, parent.start(1) + artifact.start()))


def parse_manifests(snap: Snapshot) -> Manifests:
    m = Manifests()
    _node(snap, m)
    _requirements(snap, m)
    _pyproject(snap, m)
    _procfile(snap, m)
    _gradle(snap, m)
    _maven(snap, m)
    return m
