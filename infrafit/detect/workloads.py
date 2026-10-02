"""워크로드(프로세스 단위) 찾기: k8s > compose > 코드 순서로 하나를 쓴다."""

from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass
from pathlib import PurePosixPath

from infrafit.detect.artifacts import ParsedArtifact, as_dict, build_source, is_build_path, pod_spec
from infrafit.detect.manifests import Manifests, parent_dir
from infrafit.evidence import evidence, line_of
from infrafit.repo import Snapshot

INFRA_IMAGE_TOKENS = ("postgres", "redis", "mysql", "mongo", "valkey", "memcached", "rabbitmq", "minio", "localstack")
WEB_FRAMEWORKS = ("next", "express", "fastify", "koa", "@nestjs/core", "hono", "fastapi", "flask", "django")
PROC_KINDS = {"web": "web", "worker": "worker", "clock": "scheduled", "release": "migration-job"}
# 워커 프로세스를 뜻하는 토큰 끝(`board.worker`, `jobs/worker.py` 등). `--workers 4`, `uvicorn.workers.UvicornWorker`는 아니다
WORKER_SUFFIXES = (".worker", "/worker", ":worker", "worker.py", "worker.js", "worker.ts")
# 한 디렉터리에 기본 파일이 여럿이면 docker compose와 같은 순서로 하나를 고른다
COMPOSE_BASE_NAMES = ("compose.yaml", "compose.yml", "docker-compose.yaml", "docker-compose.yml")
COMPOSE_PREFIXES = ("docker-compose.", "compose.", "docker-compose-")
COMPOSE_OVERRIDE_NAMES = ("compose.override.yaml", "compose.override.yml",
                          "docker-compose.override.yaml", "docker-compose.override.yml")


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


def image_name(image: str) -> str:
    """레지스트리·태그·다이제스트를 뗀 이미지의 마지막 이름."""
    return image.split("/")[-1].split(":")[0].split("@")[0]


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


def _is_infra(image: str) -> bool:
    return any(token in image.lower() for token in INFRA_IMAGE_TOKENS)


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
            if _is_infra(image):
                continue
            cmd = " ".join(str(x) for x in _as_list(c.get("command")) + _as_list(c.get("args")))
            text = f"{name} {cmd}".lower()
            if kind == "CronJob":
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
                code_root=_code_root_for_image(image, artifacts))
    return list(seen.values())


def _from_compose(snap: Snapshot, artifacts: list[ParsedArtifact]) -> list[WorkloadInfo]:
    out: list[WorkloadInfo] = []
    names: set[str] = set()
    # 같은 서비스가 여러 파일에 있으면 기본 파일, override, 변형 파일 순으로 먼저 본 정의의 사실을 쓴다
    for art in sorted((a for a in artifacts if a.kind == "compose"), key=lambda a: compose_file_order(a.path)):
        for obj in art.objects:
            if not isinstance(obj, tuple) or len(obj) != 2 or not isinstance(obj[0], str):
                continue
            name, svc = obj[0], as_dict(obj[1])
            image = str(svc.get("image") or "")
            if name in names or _is_infra(image):
                continue
            names.add(name)
            build = compose_build(art.path, svc)
            cmd = compose_command(art.path, svc, artifacts)
            text = f"{name} {cmd}".lower()
            wkind = "migration-job" if "migrat" in text else "worker" if is_worker(name, cmd) else "web"
            out.append(WorkloadInfo(
                id=f"w-{slug(name)}", kind=wkind, name=name,
                entrypoint=evidence(snap, art.path, line_of(snap, art.path, f"{name}:")),
                status="confirmed", source="compose", image=image, command=cmd,
                code_root=_compose_code_root(art.path, svc, image, artifacts),
                build_context=build[0] if build else None, dockerfile=build[1] if build else None))
    return out


def _from_code(snap: Snapshot, manifests: Manifests, artifacts: list[ParsedArtifact]) -> list[WorkloadInfo]:
    found: dict[tuple[str, str], dict] = {}
    for d, deps in sorted(manifests.deps_by_dir.items()):
        web_fw = next((fw for fw in WEB_FRAMEWORKS if fw in deps), None)
        if web_fw:
            found[("web", d)] = {"dep": web_fw}
        elif "vite" in deps:
            found[("static-frontend", d)] = {"dep": "vite"}
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
    for (wkind, d), info in sorted(found.items()):
        short = "static" if wkind == "static-frontend" else wkind
        wid = f"w-{short}" if len(by_kind[wkind]) == 1 else f"w-{short}-{slug(d)}"
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


def detect_workloads(snap: Snapshot, manifests: Manifests, artifacts: list[ParsedArtifact]) -> list[WorkloadInfo]:
    workloads = _from_k8s(snap, artifacts) or _from_compose(snap, artifacts) or _from_code(snap, manifests, artifacts)
    return sorted(workloads, key=lambda w: w.id)
