"""워크로드(프로세스 단위) 찾기: k8s > compose > 코드 순서로 하나를 쓴다."""

from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from pathlib import PurePosixPath

from infrafit import kb
from infrafit.detect.artifacts import ParsedArtifact, as_dict, build_source, is_build_path, pod_spec
from infrafit.detect.manifests import GRADLE_FILES, MAVEN_FILE, SPRING_BOOT, Manifests, parent_dir
from infrafit.detect.testpaths import is_test_path
from infrafit.evidence import evidence, line_of
from infrafit.repo import Snapshot

WEB_FRAMEWORKS = ("next", "express", "fastify", "koa", "@nestjs/core", "hono", "fastapi", "flask", "django")
DEVCONTAINER = ".devcontainer"  # 개발 컨테이너용 compose·Dockerfile은 배포 대상(워크로드·환경)이 아니다
# 개발·테스트용 Dockerfile(배포하지 않는 이미지): 파일 이름의 변형 부분 조각, 경로 조각
DEV_DOCKERFILE_PARTS = {"dev", "test", "tests", "ci", "local", "debug", "e2e"}
PROC_KINDS = {"web": "web", "worker": "worker", "clock": "scheduled", "release": "migration-job"}
# 워커 프로세스를 뜻하는 토큰 끝(`board.worker`, `jobs/worker.py` 등). `--workers 4`, `uvicorn.workers.UvicornWorker`는 아니다
WORKER_SUFFIXES = (".worker", "/worker", ":worker", "worker.py", "worker.js", "worker.ts")
# 한 디렉터리에 기본 파일이 여럿이면 docker compose와 같은 순서로 하나를 고른다
COMPOSE_BASE_NAMES = ("compose.yaml", "compose.yml", "docker-compose.yaml", "docker-compose.yml")
COMPOSE_PREFIXES = ("docker-compose.", "compose.", "docker-compose-")
COMPOSE_OVERRIDE_NAMES = ("compose.override.yaml", "compose.override.yml",
                          "docker-compose.override.yaml", "docker-compose.override.yml")
# Spring Boot 웹 스타터 → 프레임워크(둘 다 있으면 Spring Boot처럼 MVC가 먼저)
SPRING_WEB = (("org.springframework.boot:spring-boot-starter-web", "spring-mvc"),
              ("org.springframework.boot:spring-boot-starter-webflux", "spring-webflux"))
SPRING_STARTER = "org.springframework.boot:spring-boot-starter"
JVM_BUILD_FILES = GRADLE_FILES + (MAVEN_FILE,)
GRADLE_SETTINGS = ("settings.gradle", "settings.gradle.kts")
_BOOT_APPLICATION = re.compile(r"^\s*@(?:org\.springframework\.boot\.autoconfigure\.)?SpringBootApplication\b",
                               re.MULTILINE)
_ROOT_PROJECT = re.compile(r"""\brootProject\.name\s*=\s*["']([^"']+)["']""")


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9.-]+", "-", text.lower()).strip("-") or "root"


@dataclass
class WorkloadInfo:
    id: str
    kind: str
    name: str
    entrypoint: dict
    status: str
    source: str
    app_dir: str = ""
    command: str = ""
    image: str = ""
    code_root: str | None = None
    build_context: str | None = None  # compose build 컨텍스트(저장소 경로)
    dockerfile: str | None = None  # compose build가 쓰는 Dockerfile(저장소 경로)
    proxy_component: str | None = None  # reverse-proxy 워크로드: 이미지 분류의 구성 요소
    root_guessed: bool = False  # 저장소에 하나뿐인 Dockerfile로 code_root를 정했다(규칙상 추측)
    framework: str = ""  # 코드에서 찾은 웹 프레임워크(Spring: spring-mvc·spring-webflux). 출력에는 쓰지 않는다
    framework_evidence: dict | None = None  # 프레임워크를 정한 의존성 줄(Spring 웹 스타터)

    def to_dict(self) -> dict:
        return {"id": self.id, "kind": self.kind, "name": self.name,
                "entrypoint": self.entrypoint, "status": self.status}


def compose_variant(rel: str) -> str | None:
    """compose 파일 이름의 변형 부분: 기본 파일이면 "", `docker-compose.<x>.yml`·`compose.<x>.yaml`·
    `docker-compose-<x>.yml`이면 x, 그 밖의 이름은 None."""
    name = PurePosixPath(rel).name
    if name in COMPOSE_BASE_NAMES:
        return ""
    for prefix in COMPOSE_PREFIXES:
        for suffix in (".yml", ".yaml"):
            if name.startswith(prefix) and name.endswith(suffix) and len(name) > len(prefix) + len(suffix):
                return name[len(prefix):-len(suffix)]
    return None


def is_compose_override(rel: str) -> bool:
    """`docker-compose.override.yml`·`compose.override.yaml` 등: 같은 계열 기본 파일 위에 늘 병합하는 파일(docker 동작).
    `compose.prod.override.yml`, `docker-compose-override.yml` 같은 이름은 변형 파일이다."""
    return PurePosixPath(rel).name in COMPOSE_OVERRIDE_NAMES


def compose_family(rel: str) -> str:
    """`docker-compose` 또는 `compose`: override는 같은 계열의 기본 파일에만 병합한다."""
    return "docker-compose" if PurePosixPath(rel).name.startswith("docker-compose") else "compose"


def compose_file_order(rel: str) -> tuple:
    """compose 파일을 읽는 순서: 기본 파일(docker compose가 고르는 순서), override, 변형 파일, 그 밖의 이름."""
    name = PurePosixPath(rel).name
    if name in COMPOSE_BASE_NAMES:
        return (0, COMPOSE_BASE_NAMES.index(name), rel)
    if is_compose_override(rel):
        return (1, 0, rel)
    return (2 if compose_variant(rel) else 3, 0, rel)


def is_worker_command(text: str) -> bool:
    """옵션(`-`로 시작)이 아닌 토큰이 `worker`이거나 WORKER_SUFFIXES로 끝나면 워커 프로세스다."""
    for token in text.lower().split():
        token = token.strip("'\"[],")
        if token and not token.startswith("-") and (token == "worker" or token.endswith(WORKER_SUFFIXES)):
            return True
    return False


def is_worker(name: str, command: str) -> bool:
    """워커 프로세스인가: 이름 조각(`-`·`_`·`.`로 나눈)이 `worker`·`workers`이면 명령과 상관없이
    (`email-worker`가 `node dist/index.js`를 실행하는 경우 등), 아니면 명령 토큰 규칙(is_worker_command)."""
    return bool({"worker", "workers"} & set(re.split(r"[-_.]", name.lower()))) or is_worker_command(command)


def _dockerfiles(artifacts: list[ParsedArtifact]) -> list[ParsedArtifact]:
    return [a for a in artifacts if a.kind == "dockerfile"]


def _image_keys(image: str) -> list[str]:
    """분류에 쓰는 이름들: 레지스트리·태그·다이제스트를 뗀 마지막 이름, 그리고 `저장소/이름`."""
    parts = image.strip().lower().split("@")[0].split("/")
    parts[-1] = parts[-1].split(":")[0]
    if not parts[-1]:
        return []
    return [parts[-1]] + (["/".join(parts[-2:])] if len(parts) >= 2 else [])


def image_name(image: str) -> str:
    """레지스트리·태그·다이제스트를 뗀 이미지의 마지막 이름."""
    keys = _image_keys(image)
    return keys[0] if keys else ""


def dockerfile_for_image(image: str, artifacts: list[ParsedArtifact]) -> ParsedArtifact | None:
    last = image_name(image)
    for df in _dockerfiles(artifacts):
        if last and PurePosixPath(df.path).parent.name == last:
            return df
    return None


def _dockerfile_cmd_for_image(image: str, artifacts: list[ParsedArtifact]) -> str:
    df = dockerfile_for_image(image, artifacts)
    return str(df.get("cmd") or "") if df else ""


def _image_command(dockerfile: str, artifacts: list[ParsedArtifact]) -> str:
    """Dockerfile 최종 이미지의 실행 명령: ENTRYPOINT 뒤에 CMD(둘 다 최종 단계 체인에서 온다)."""
    df = next((a for a in _dockerfiles(artifacts) if a.path == dockerfile), None)
    if df is None:
        return ""
    return " ".join(str(df.get(k)) for k in ("entrypoint", "cmd") if df.get(k))


def workload_dockerfile(w: WorkloadInfo, artifacts: list[ParsedArtifact]) -> ParsedArtifact | None:
    """워크로드 이미지의 Dockerfile: compose build의 Dockerfile, 이미지 이름 규칙, code_root의 Dockerfile 순서."""
    df = next((a for a in _dockerfiles(artifacts) if a.path == w.dockerfile), None) if w.dockerfile else None
    if df is None and w.image:
        df = dockerfile_for_image(w.image, artifacts)
    if df is None and w.code_root is not None:
        local = sorted((a for a in _dockerfiles(artifacts) if parent_dir(a.path) == w.code_root),
                       key=lambda a: (PurePosixPath(a.path).name != "Dockerfile", a.path))
        df = local[0] if local else None
    return df


def _code_root_for_image(image: str, artifacts: list[ParsedArtifact]) -> str | None:
    df = dockerfile_for_image(image, artifacts)
    return parent_dir(df.path) if df else None


def _repo_path(path: str) -> str:
    p = posixpath.normpath(path)
    return "" if p == "." else p


def compose_build(compose_path: str, svc: dict) -> tuple[str, str] | None:
    """compose 서비스의 build → (빌드 컨텍스트, Dockerfile) 저장소 경로. build가 없으면 None."""
    build = svc.get("build")
    base = parent_dir(compose_path)
    if isinstance(build, str):
        context = _repo_path(posixpath.join(base, build))
        return context, _repo_path(posixpath.join(context, "Dockerfile"))
    if isinstance(build, dict):
        context = _repo_path(posixpath.join(base, str(build.get("context") or ".")))
        return context, _repo_path(posixpath.join(context, str(build.get("dockerfile") or "Dockerfile")))
    return None


def compose_command(compose_path: str, svc: dict, artifacts: list[ParsedArtifact]) -> str:
    """compose 서비스의 실행 명령: `command`(목록은 공백으로 잇는다), 없으면 빌드하는 이미지의 명령."""
    cmd = svc.get("command") or ""
    cmd = " ".join(str(x) for x in cmd) if isinstance(cmd, list) else cmd if isinstance(cmd, str) else ""
    build = compose_build(compose_path, svc)
    if not cmd and build:
        cmd = _image_command(build[1], artifacts)
    return cmd


def _compose_code_root(compose_path: str, svc: dict, image: str, artifacts: list[ParsedArtifact]) -> str | None:
    build = compose_build(compose_path, svc)
    if build is None:
        return _code_root_for_image(image, artifacts)
    return parent_dir(build[1])


def _dockerfile_cmd_for_dir(app_dir: str, artifacts: list[ParsedArtifact]) -> str:
    for target in (app_dir, ""):
        for df in _dockerfiles(artifacts):
            if parent_dir(df.path) == target and df.get("cmd"):
                return str(df.get("cmd"))
    return ""


def _as_list(v) -> list:
    return v if isinstance(v, list) else []


def classify_image(image) -> dict | None:
    """knowledge/images.yaml로 이미지를 분류한다: {role, component, hosting_hint, label}, 맞는 항목이 없으면 None.
    label은 패턴에 맞은 이름(마지막 이름 또는 `저장소/이름`)이다."""
    keys = _image_keys(image) if isinstance(image, str) else []
    for entry in kb.images():
        for pattern in entry.get("match") or []:
            key = next((k for k in keys if fnmatchcase(k, str(pattern).lower())), None)
            if key:
                return {"role": entry.get("role"), "component": entry.get("component"),
                        "hosting_hint": entry.get("hosting_hint"), "label": key}
    return None


def _dockerfile_at(path: str | None, artifacts: list[ParsedArtifact]) -> ParsedArtifact | None:
    return next((a for a in _dockerfiles(artifacts) if a.path == path), None) if path else None


def _base_class(df: ParsedArtifact | None) -> dict | None:
    """Dockerfile 마지막 FROM 이미지의 분류."""
    return classify_image(str(df.get("base_image") or "")) if df else None


def _image_class(image: str, df: ParsedArtifact | None) -> dict | None:
    """워크로드 이미지의 분류: 이미지 이름, 없으면 빌드 Dockerfile의 마지막 FROM."""
    return classify_image(image) or _base_class(df)


def is_app(w: WorkloadInfo) -> bool:
    """앱 워크로드인가: 리버스 프록시가 아닌 것."""
    return w.kind != "reverse-proxy"


@dataclass
class ImageService:
    """이미지 분류로 워크로드가 아닌 compose 서비스(저장소·캐시·큐·기반 서비스)."""
    name: str
    label: str
    role: str
    component: str | None
    hosting_hint: str | None
    evidence: dict
    dependents: list[str] = field(default_factory=list)  # 이 서비스를 depends_on하는 서비스 이름


def _compose_services(artifacts: list[ParsedArtifact]):
    """(compose 파일, 서비스 이름, 서비스 정의). 같은 서비스가 여러 파일에 있으면 기본 파일, override, 변형 파일
    순으로 먼저 본 정의를 쓴다. 개발 컨테이너용 compose는 배포 대상이 아니므로 뺀다."""
    names: set[str] = set()
    for art in sorted((a for a in artifacts if a.kind == "compose"), key=lambda a: compose_file_order(a.path)):
        if DEVCONTAINER in PurePosixPath(art.path).parts:
            continue
        for obj in art.objects:
            if not isinstance(obj, tuple) or len(obj) != 2 or not isinstance(obj[0], str) or obj[0] in names:
                continue
            names.add(obj[0])
            yield art, obj[0], as_dict(obj[1])


def _depends_on(svc: dict) -> list[str]:
    deps = svc.get("depends_on")
    if isinstance(deps, dict):
        return [str(k) for k in deps]
    return [str(d) for d in deps if isinstance(d, (str, int))] if isinstance(deps, list) else []


def _service_line(snap: Snapshot, rel: str, name: str) -> int | None:
    """compose 서비스 정의 줄: 최상위 `services:` 블록 안의 `<이름>:` 키 줄 중 들여쓰기가 가장 얕은 첫 줄
    (앵커 값의 `@postgres:5432`, depends_on 맵의 같은 키, 이름이 같은 볼륨은 피한다). 없으면 None."""
    rx = re.compile(rf"^(\s+)[\"']?{re.escape(name)}[\"']?\s*:(\s|$)")
    found, inside = [], False
    for i, text in enumerate(snap.lines(rel), 1):
        if text[:1].strip() and not text.startswith("#"):  # 최상위 키에서 블록이 바뀐다
            inside = text.split(":", 1)[0].strip().strip("\"'") == "services"
        elif inside and (m := rx.match(text)):
            found.append((len(m.group(1)), i))
    return min(found)[1] if found else None


def _service_class(art: ParsedArtifact, svc: dict, artifacts: list[ParsedArtifact]) -> dict | None:
    build = compose_build(art.path, svc)
    return _image_class(str(svc.get("image") or ""), _dockerfile_at(build[1] if build else None, artifacts))


def image_services(snap: Snapshot, artifacts: list[ParsedArtifact]) -> list[ImageService]:
    """워크로드가 아닌 분류된 compose 서비스들(reverse-proxy·dev-tool 제외), 이름 순."""
    services = list(_compose_services(artifacts))
    out: list[ImageService] = []
    for art, name, svc in services:
        cls = _service_class(art, svc, artifacts)
        if not cls or cls["role"] in ("reverse-proxy", "dev-tool"):
            continue
        out.append(ImageService(
            name=name, label=cls["label"], role=cls["role"], component=cls["component"],
            hosting_hint=cls["hosting_hint"], evidence=evidence(snap, art.path, _service_line(snap, art.path, name)),
            dependents=sorted(n for _, n, other in services if name in _depends_on(other))))
    return sorted(out, key=lambda s: s.name)


def _from_k8s(snap: Snapshot, artifacts: list[ParsedArtifact]) -> list[WorkloadInfo]:
    seen: dict[str, WorkloadInfo] = {}
    for art in artifacts:
        if art.kind != "k8s":
            continue
        for doc in art.objects:
            if not isinstance(doc, dict):
                continue
            kind = doc.get("kind")
            if kind not in ("Deployment", "StatefulSet", "Job", "CronJob"):
                continue
            name = as_dict(doc.get("metadata")).get("name")
            containers = pod_spec(doc).get("containers")
            if not isinstance(name, str) or not name or name in seen:
                continue
            if not isinstance(containers, list) or not containers or not isinstance(containers[0], dict):
                continue
            c = containers[0]
            image = str(c.get("image") or "")
            cls = _image_class(image, dockerfile_for_image(image, artifacts))
            if cls and cls["role"] != "reverse-proxy":  # 저장소·기반 서비스 이미지는 워크로드가 아니다
                continue
            cmd = " ".join(str(x) for x in _as_list(c.get("command")) + _as_list(c.get("args")))
            text = f"{name} {cmd}".lower()
            if cls:
                wkind = "reverse-proxy"
            elif kind == "CronJob":
                wkind = "scheduled"
            elif kind == "Job":
                wkind = "migration-job" if "migrat" in text else "worker"
            else:
                wkind = "worker" if is_worker(name, cmd) else "web"
            # 렌더된 kustomize 결과(`...#build`)는 실제 파일이 아니므로 kustomization.yaml을 근거로 쓴다
            path = build_source(art.path)
            line = None if is_build_path(art.path) else line_of(snap, path, f"name: {name}")
            seen[name] = WorkloadInfo(
                id=f"w-{slug(name)}", kind=wkind, name=name, entrypoint=evidence(snap, path, line),
                status="confirmed", source="k8s", image=image,
                command=cmd or _dockerfile_cmd_for_image(image, artifacts),
                code_root=_code_root_for_image(image, artifacts), proxy_component=cls["component"] if cls else None)
    return list(seen.values())


def _from_compose(snap: Snapshot, artifacts: list[ParsedArtifact]) -> list[WorkloadInfo]:
    out: list[WorkloadInfo] = []
    for art, name, svc in _compose_services(artifacts):
        image = str(svc.get("image") or "")
        cls = _service_class(art, svc, artifacts)
        if cls and cls["role"] != "reverse-proxy":  # 저장소·기반 서비스·개발 도구 이미지는 워크로드가 아니다
            continue
        build = compose_build(art.path, svc)
        cmd = compose_command(art.path, svc, artifacts)
        text = f"{name} {cmd}".lower()
        if cls:
            wkind = "reverse-proxy"
        else:
            wkind = "migration-job" if "migrat" in text else "worker" if is_worker(name, cmd) else "web"
        out.append(WorkloadInfo(
            id=f"w-{slug(name)}", kind=wkind, name=name,
            entrypoint=evidence(snap, art.path, _service_line(snap, art.path, name)),
            status="confirmed", source="compose", image=image, command=cmd,
            code_root=_compose_code_root(art.path, svc, image, artifacts),
            build_context=build[0] if build else None, dockerfile=build[1] if build else None,
            proxy_component=cls["component"] if cls else None))
    return out


def spring_web(deps: set[str]) -> tuple[str, str] | None:
    """(웹 스타터 의존성, 프레임워크). Spring 웹 스타터가 없으면 None."""
    return next(((dep, fw) for dep, fw in SPRING_WEB if dep in deps), None)


def _spring_boot_dep(deps: set[str]) -> str | None:
    """Spring Boot 앱의 근거 의존성: 플러그인·parent, 없으면 이름 순 첫 스타터."""
    if SPRING_BOOT in deps:
        return SPRING_BOOT
    return next((d for d in sorted(deps) if d.startswith(SPRING_STARTER)), None)


def jvm_build_dirs(snap: Snapshot) -> list[str]:
    """Gradle·Maven 빌드 파일이 있는 디렉터리들(경로 순)."""
    return sorted({parent_dir(rel) for name in JVM_BUILD_FILES for rel in snap.glob(f"**/{name}")})


def _spring_name(snap: Snapshot, d: str) -> str:
    """settings.gradle(.kts)의 rootProject.name, pom의 프로젝트 artifactId, 없으면 디렉터리 이름(루트는 app)."""
    for name in GRADLE_SETTINGS:
        rel = f"{d}/{name}" if d else name
        m = _ROOT_PROJECT.search(snap.read(rel)) if snap.exists(rel) else None
        if m and m.group(1).strip():
            return m.group(1).strip()
    pom = f"{d}/{MAVEN_FILE}" if d else MAVEN_FILE
    if snap.exists(pom):
        # parent·의존성·빌드 블록의 artifactId를 빼고 남은 첫 artifactId가 프로젝트 자신이다
        text = re.sub(r"<!--.*?-->", "", snap.read(pom), flags=re.DOTALL)
        text = re.sub(r"<(parent|dependencies|dependencyManagement|build|profiles)>.*?</\1>", "", text, flags=re.DOTALL)
        m = re.search(r"<artifactId>\s*([^<]*?)\s*</artifactId>", text)
        if m and m.group(1):
            return m.group(1)
    return PurePosixPath(d).name or "app"


def _build_location(manifests: Manifests, dep: str, d: str, files=JVM_BUILD_FILES) -> tuple[str, int | None] | None:
    """디렉터리 d의 빌드 파일에서 dep가 있는 (파일, 줄)."""
    return next(((rel, ln) for rel, ln in manifests.locations.get(dep, [])
                 if parent_dir(rel) == d and PurePosixPath(rel).name in files), None)


def owning_build_dir(rel: str, build_dirs: set[str]) -> str | None:
    """파일을 품은 가장 가까운 빌드 파일 디렉터리(모듈). 없으면 None."""
    d = parent_dir(rel)
    while d not in build_dirs:
        if not d:
            return None
        d = parent_dir(d)
    return d


def _boot_application_dirs(snap: Snapshot, build_dirs: set[str]) -> set[str]:
    """테스트가 아닌 Java·Kotlin 파일에 `@SpringBootApplication`이 있는 모듈 디렉터리들."""
    out: set[str] = set()
    for pattern in ("**/*.java", "**/*.kt"):
        for rel in snap.glob(pattern):
            if not is_test_path(rel) and _BOOT_APPLICATION.search(snap.read(rel)):
                d = owning_build_dir(rel, build_dirs)
                if d is not None:
                    out.add(d)
    return out


def _spring_apps(snap: Snapshot, manifests: Manifests) -> dict[tuple[str, str], dict]:
    """빌드 파일 디렉터리마다 Spring Boot 앱: 웹 스타터가 있으면 web, Spring Boot만 있으면 worker(후보).
    모듈 안 코드에 `@SpringBootApplication`이 있거나 Gradle Boot 플러그인을 적용한 모듈만 앱이다(스타터만 쓰는
    라이브러리 모듈은 뺀다)."""
    found: dict[tuple[str, str], dict] = {}
    build_dirs = jvm_build_dirs(snap)
    apps = _boot_application_dirs(snap, set(build_dirs))
    for d in build_dirs:
        deps = manifests.deps_by_dir.get(d, set())
        web = spring_web(deps)
        dep = web[0] if web else _spring_boot_dep(deps)
        if dep is None or (d not in apps and _build_location(manifests, SPRING_BOOT, d, GRADLE_FILES) is None):
            continue
        loc = _build_location(manifests, dep, d)
        if loc is None:
            continue
        found[("web" if web else "worker", d)] = {
            "spring": (evidence(snap, *loc), web[1] if web else "", _spring_name(snap, d))}
    return found


def _from_code(snap: Snapshot, manifests: Manifests, artifacts: list[ParsedArtifact]) -> list[WorkloadInfo]:
    found: dict[tuple[str, str], dict] = {}
    for d, deps in sorted(manifests.deps_by_dir.items()):
        web_fw = next((fw for fw in WEB_FRAMEWORKS if fw in deps), None)
        if web_fw:
            found[("web", d)] = {"dep": web_fw}
        elif "vite" in deps:
            found[("static-frontend", d)] = {"dep": "vite"}
    for key, info in _spring_apps(snap, manifests).items():
        found.setdefault(key, info)
    for key, (cmd, rel, line) in sorted(manifests.procfile.items()):
        d, proc = key.split(":", 1)
        wkind = PROC_KINDS.get(proc)
        if not wkind:
            continue
        entry = found.setdefault((wkind, d), {})
        entry.setdefault("proc", (cmd, rel, line))

    by_kind: dict[str, list[str]] = {}
    for wkind, d in found:
        by_kind.setdefault(wkind, []).append(d)

    out: list[WorkloadInfo] = []
    ids: set[str] = set()
    for (wkind, d), info in sorted(found.items()):
        short = "static" if wkind == "static-frontend" else wkind
        wid = f"w-{short}" if len(by_kind[wkind]) == 1 else f"w-{short}-{slug(d)}"
        if "spring" in info:
            entry, framework, name = info["spring"]
            wid = f"w-{slug(name)}"
            if wid in ids:
                wid, name = f"w-{slug(name)}-{slug(d)}", f"{name}-{slug(d)}"
            ids.add(wid)
            w = WorkloadInfo(id=wid, kind=wkind, name=name, entrypoint=entry,
                             status="confirmed" if framework else "candidate", source="code", app_dir=d,
                             code_root=d, framework=framework, framework_evidence=entry if framework else None)
            # 실행 명령은 연결된 Dockerfile의 마지막 체인 ENTRYPOINT+CMD, Procfile이 있으면 그 명령
            df = workload_dockerfile(w, artifacts)
            w.command = (_image_command(df.path, artifacts) if df else "") or (info["proc"][0] if "proc" in info else "")
            out.append(w)
            continue
        if wid in ids:
            wid = f"w-{short}-{slug(d)}"
        ids.add(wid)
        if "dep" in info:
            dep = info["dep"]
            rel, line = manifests.deps[dep]
            # 같은 의존성이 여러 디렉터리에 있으면 이 디렉터리의 매니페스트 줄을 근거로 쓴다
            for pattern in ("package.json", "requirements.txt", "pyproject.toml"):
                local = f"{d}/{pattern}" if d else pattern
                if snap.exists(local):
                    ln = line_of(snap, local, f'"{dep}"' if pattern == "package.json" else dep)
                    if ln:
                        rel, line = local, ln
                        break
            entry = evidence(snap, rel, line)
        else:
            _, rel, line = info["proc"]
            entry = evidence(snap, rel, line)
        proc_cmd = info["proc"][0] if "proc" in info else ""
        start = manifests.scripts.get(f"{d}:start")
        start_cmd = start[0] if start else ""
        if wkind == "web":
            # 이미지가 있으면 그 CMD가 실제로 배포되는 실행 명령이다
            command = _dockerfile_cmd_for_dir(d, artifacts) or proc_cmd or start_cmd
        else:
            command = proc_cmd
        out.append(WorkloadInfo(id=wid, kind=wkind, name=wid[2:], entrypoint=entry,
                                status="confirmed", source="code", app_dir=d, command=command, code_root=d))
    return out


def _is_dev_dockerfile(path: str) -> bool:
    """`Dockerfile.<x>`·`<x>.Dockerfile`·`<x>.dockerfile`의 x를 `.`·`-`·`_`로 나눈 조각이 개발·테스트용이거나,
    테스트 경로(testpaths.is_test_path)에 있는 Dockerfile."""
    p = PurePosixPath(path)
    name = p.name
    variant = ""
    if name.startswith("Dockerfile."):
        variant = name[len("Dockerfile."):]
    elif name.lower().endswith(".dockerfile"):
        variant = name[:-len(".dockerfile")]
    parts = set(re.split(r"[._-]", variant.lower())) if variant else set()
    return bool(parts & DEV_DOCKERFILE_PARTS) or is_test_path(path)


def _app_dockerfiles(workloads: list[WorkloadInfo], artifacts: list[ParsedArtifact]) -> list[ParsedArtifact]:
    """어떤 워크로드에도 연결되지 않은 앱 Dockerfile: 마지막 체인에 CMD나 ENTRYPOINT가 있고, 마지막 FROM이
    리버스 프록시 이미지가 아니며, 개발 컨테이너용·개발·테스트용이 아닌 것. 경로 순."""
    linked = {df.path for w in workloads if (df := workload_dockerfile(w, artifacts))}
    return [df for df in _dockerfiles(artifacts)
            if df.path not in linked and DEVCONTAINER not in PurePosixPath(df.path).parts
            and not _is_dev_dockerfile(df.path)
            and (df.get("cmd") or df.get("entrypoint"))
            and (_base_class(df) or {}).get("role") != "reverse-proxy"]


def _dockerfile_workload_name(path: str) -> str:
    """`<x>.Dockerfile`·`Dockerfile.<x>`이면 x, 아니면 Dockerfile 디렉터리 이름(저장소 루트는 root)."""
    name = PurePosixPath(path).name
    if name.endswith(".Dockerfile") and len(name) > len(".Dockerfile"):
        return name[:-len(".Dockerfile")]
    if name.startswith("Dockerfile.") and len(name) > len("Dockerfile."):
        return name[len("Dockerfile."):]
    return PurePosixPath(path).parent.name or "root"


def _from_dockerfiles(snap: Snapshot, workloads: list[WorkloadInfo],
                      artifacts: list[ParsedArtifact]) -> list[WorkloadInfo]:
    """앱 워크로드를 못 찾았을 때: 연결되지 않은 앱 Dockerfile마다 후보 워크로드 하나.
    code_root는 빌드 컨텍스트 후보 규칙(1b F3)처럼 Dockerfile 디렉터리로 둔다."""
    ids = {w.id for w in workloads}
    out: list[WorkloadInfo] = []
    for df in _app_dockerfiles(workloads, artifacts):
        name = _dockerfile_workload_name(df.path)
        command = _image_command(df.path, artifacts)
        wid = f"w-{slug(name)}"
        if wid in ids:
            wid = f"w-{slug(df.path)}"
        if wid in ids:
            continue
        ids.add(wid)
        fact = next((f for key in ("cmd", "entrypoint") for f in df.settings if f["key"] == key), None)
        entry = (fact or {}).get("evidence") or evidence(snap, df.path)
        d = parent_dir(df.path)
        out.append(WorkloadInfo(id=wid, kind="worker" if is_worker(name, command) else "web", name=name,
                                entrypoint=entry, status="candidate", source="dockerfile", app_dir=d,
                                command=command, code_root=d, dockerfile=df.path))
    return out


def _link_single_dockerfile(workloads: list[WorkloadInfo], artifacts: list[ParsedArtifact]) -> None:
    """이미지만 있는 k8s·compose 앱 워크로드에 Dockerfile이 없고, 연결되지 않은 앱 Dockerfile이 정확히 하나면
    그것을 연결한다(code_root, 비어 있으면 실행 명령). 연결이 필요한 워크로드가 여럿이면 모두 같은 이미지 이름일
    때만 연결한다(같은 이미지를 명령만 바꿔 쓰는 경우). 이렇게 정한 code_root는 추측이다."""
    apps = _app_dockerfiles(workloads, artifacts)
    if len(apps) != 1:
        return
    df = apps[0]
    needing = [w for w in workloads if w.source in ("k8s", "compose") and is_app(w) and w.dockerfile is None
               and workload_dockerfile(w, artifacts) is None]
    if len({image_name(w.image) for w in needing}) > 1:
        return
    for w in needing:
        w.dockerfile, w.code_root, w.root_guessed = df.path, parent_dir(df.path), True
        w.command = w.command or _image_command(df.path, artifacts)


def _spring_framework_at_root(snap: Snapshot, manifests: Manifests, workloads: list[WorkloadInfo]) -> None:
    """k8s·compose 앱 워크로드: code_root 모듈의 빌드 파일에 Spring 웹 스타터가 있으면 그 프레임워크와 의존성 줄."""
    build_dirs = set(jvm_build_dirs(snap))
    for w in workloads:
        if w.source not in ("k8s", "compose") or not is_app(w) or w.framework or w.code_root not in build_dirs:
            continue
        web = spring_web(manifests.deps_by_dir.get(w.code_root, set()))
        loc = _build_location(manifests, web[0], w.code_root) if web else None
        if loc:
            w.framework, w.framework_evidence = web[1], evidence(snap, *loc)


def detect_workloads(snap: Snapshot, manifests: Manifests, artifacts: list[ParsedArtifact]) -> list[WorkloadInfo]:
    workloads = _from_k8s(snap, artifacts) or _from_compose(snap, artifacts)
    if not any(is_app(w) for w in workloads):
        # k8s·compose에 앱이 없으면(프록시만 있는 경우 포함) 코드 탐지도 합친다
        ids = {w.id for w in workloads}
        for w in _from_code(snap, manifests, artifacts):
            if w.id in ids:
                w.id = f"{w.id}-{slug(w.app_dir)}"
                w.name = w.id[2:]
            if w.id not in ids:
                ids.add(w.id)
                workloads.append(w)
    if not any(is_app(w) for w in workloads):
        workloads += _from_dockerfiles(snap, workloads, artifacts)
    _link_single_dockerfile(workloads, artifacts)
    _spring_framework_at_root(snap, manifests, workloads)
    return sorted(workloads, key=lambda w: w.id)
