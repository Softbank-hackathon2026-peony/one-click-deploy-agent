"""knowledge/ 형식 검사."""

from __future__ import annotations

import re
from fnmatch import fnmatchcase

from infrafit import kb

COMPONENT_ID = re.compile(r"^(cp|ds|ca|qu|sc|rt|fs|nw):[a-z0-9._-]+/[a-z0-9._-]+/[a-z0-9._-]+$")
ROLES = {"primary-db", "cache", "session", "queue", "scheduler", "realtime", "file-storage", "search", "other"}
STATUSES = {"confirmed", "candidate"}
ARTIFACTS = {"dockerfile", "k8s", "terraform", "hop"}
IMAGE_ROLES = {"reverse-proxy", "datastore", "cache", "queue", "infra", "dev-tool"}
IMAGE_KEYS = {"match", "role", "component", "hosting_hint"}
# 이미지 role → component가 가져야 하는 family(infra·dev-tool은 정하지 않는다)
IMAGE_ROLE_FAMILIES = {"datastore": "ds", "cache": "ca", "queue": "qu", "reverse-proxy": "nw"}


def _lint_catalog() -> list[str]:
    issues: list[str] = []
    seen: set[str] = set()
    for c in kb._load("components/catalog.yaml")["components"]:
        cid = c.get("id", "")
        if not COMPONENT_ID.match(cid):
            issues.append(f"catalog: 잘못된 ID 형식 {cid!r}")
        if cid in seen:
            issues.append(f"catalog: 중복 ID {cid}")
        seen.add(cid)
        if c.get("family") != cid.split(":")[0]:
            issues.append(f"catalog: {cid}의 family가 접두어와 다름")
        if not c.get("name") or not c.get("source"):
            issues.append(f"catalog: {cid}에 name 또는 source 없음")
    return issues


def _lint_condition(sig_id: str, cond: dict, allow_env: bool = False) -> list[str]:
    issues: list[str] = []
    for leaf in kb.iter_conditions(cond):
        if allow_env and "env" in leaf:
            try:
                re.compile(leaf["env"])
            except (re.error, TypeError) as e:
                issues.append(f"{sig_id}: env 정규식 오류 {e}")
        elif "dependency" in leaf:
            if not isinstance(leaf["dependency"], str) or not leaf["dependency"]:
                issues.append(f"{sig_id}: dependency가 비었음")
        elif "code" in leaf:
            code = leaf["code"]
            if not code.get("glob") or not code.get("regex"):
                issues.append(f"{sig_id}: code에 glob 또는 regex 없음")
                continue
            if isinstance(code["glob"], list) and not all(isinstance(g, str) and g for g in code["glob"]):
                issues.append(f"{sig_id}: code glob 목록에 빈 값")
            try:
                re.compile(code["regex"])
            except re.error as e:
                issues.append(f"{sig_id}: 정규식 오류 {e}")
            if code.get("flags") not in (None, "i"):
                issues.append(f"{sig_id}: flags는 i만 허용")
            if code.get("multiline") not in (None, True, False):
                issues.append(f"{sig_id}: multiline은 true·false만 허용")
        else:
            issues.append(f"{sig_id}: 알 수 없는 조건 {leaf}")
    return issues


def _lint_signatures() -> list[str]:
    issues: list[str] = []
    catalog = kb.catalog()
    seen: set[str] = set()
    for s in kb.signatures():
        sid = s.get("id", "?")
        if sid in seen:
            issues.append(f"signature: 중복 ID {sid}")
        seen.add(sid)
        if s.get("component") not in catalog:
            issues.append(f"{sid}: catalog에 없는 구성 요소 {s.get('component')}")
        if s.get("role") not in ROLES:
            issues.append(f"{sid}: 잘못된 role {s.get('role')}")
        if s.get("status") not in STATUSES:
            issues.append(f"{sid}: 잘못된 status {s.get('status')}")
        if not s.get("when"):
            issues.append(f"{sid}: when 없음")
        else:
            issues += _lint_condition(sid, s["when"])
        for r in s.get("refine", []):
            if r.get("component") not in catalog:
                issues.append(f"{sid}: refine의 구성 요소가 catalog에 없음 {r.get('component')}")
            issues += _lint_condition(sid, r.get("when", {}))
    return issues


def _lint_defaults() -> list[str]:
    issues: list[str] = []
    for d in kb.defaults():
        name = f"default {d.get('artifact')}:{d.get('key')}"
        if d.get("artifact") not in ARTIFACTS:
            issues.append(f"{name}: 잘못된 artifact")
        if "key" not in d or "value" not in d:
            issues.append(f"{name}: key 또는 value 없음")
        if not (d.get("source") or {}).get("ref"):
            issues.append(f"{name}: source.ref 없음")
        if d.get("artifact") == "hop" and d.get("component") not in kb.catalog():
            issues.append(f"{name}: catalog에 없는 구성 요소")
        if d.get("artifact") == "k8s" and not d.get("match_kind"):
            issues.append(f"{name}: match_kind 없음")
        if d.get("artifact") == "terraform" and not d.get("resource"):
            issues.append(f"{name}: resource 없음")
    return issues


def _shadowed_by(pattern: str, earlier: str) -> bool:
    """앞 패턴 earlier가 pattern에 맞는 이미지를 모두 먼저 잡는가(pattern의 와일드카드는 글자로 보고 맞춰 본다).
    분류는 마지막 이름과 `저장소/이름`을 함께 보므로 `저장소/이름` 패턴은 마지막 이름만으로도 가려진다."""
    keys = [pattern] + ([pattern.rsplit("/", 1)[1]] if "/" in pattern else [])
    return any(fnmatchcase(k, earlier) for k in keys)


def _lint_images(entries: list[dict] | None = None) -> list[str]:
    issues: list[str] = []
    catalog = kb.catalog()
    seen: list[str] = []  # 앞 항목들의 패턴(분류가 보는 순서)
    for i, e in enumerate(kb.images() if entries is None else entries):
        name = f"image {i}"
        match = e.get("match") if isinstance(e, dict) else None
        if not isinstance(match, list) or not match or not all(isinstance(m, str) and m for m in match):
            issues.append(f"{name}: match가 비었거나 문자열 목록이 아님")
            if not isinstance(e, dict):
                continue
            match = []
        else:
            name = f"image {match[0]}"
        for key in sorted(set(e) - IMAGE_KEYS):
            issues.append(f"{name}: 알 수 없는 키 {key}")
        for pattern in (m.lower() for m in match):
            if pattern in seen:
                issues.append(f"{name}: 중복 패턴 {pattern}")
            elif shadow := next((x for x in seen if _shadowed_by(pattern, x)), None):
                issues.append(f"{name}: 패턴 {pattern}이 앞 패턴 {shadow}에 가려짐")
            seen.append(pattern)
        if e.get("role") not in IMAGE_ROLES:
            issues.append(f"{name}: 잘못된 role {e.get('role')}")
        for key in ("component", "hosting_hint"):
            if key in e and e[key] not in catalog:
                issues.append(f"{name}: {key}가 catalog에 없음 {e[key]}")
        family = IMAGE_ROLE_FAMILIES.get(e.get("role"))
        if family and isinstance(e.get("component"), str) and e["component"].split(":")[0] != family:
            issues.append(f"{name}: role {e['role']}의 component family는 {family}여야 함 {e['component']}")
    return issues


EXTERNAL_KINDS = {"llm-api", "auth", "payments", "messaging", "email", "push", "maps", "video", "webhook", "other"}
EXTERNAL_ID = re.compile(r"^ext:[a-z0-9-]+$")
DEPLOY_TARGETS = {"source", "image", "job-build", "workflow-build", "compose", "cwd", "manifest", "name"}


def _lint_external(entries: list[dict] | None = None) -> list[str]:
    """외부 서비스: id 형식·중복, label, kind, when.any(dependency·code·env)."""
    issues: list[str] = []
    seen: set[str] = set()
    for i, e in enumerate(kb.external() if entries is None else entries):
        if not isinstance(e, dict):
            issues.append(f"external {i}: 항목이 매핑이 아님")
            continue
        eid = str(e.get("id", f"external {i}"))
        if not EXTERNAL_ID.match(eid):
            issues.append(f"{eid}: 잘못된 외부 서비스 ID 형식")
        if eid in seen:
            issues.append(f"external: 중복 ID {eid}")
        seen.add(eid)
        if not e.get("label"):
            issues.append(f"{eid}: label 없음")
        if e.get("kind") not in EXTERNAL_KINDS:
            issues.append(f"{eid}: 잘못된 kind {e.get('kind')}")
        when = e.get("when")
        if not isinstance(when, dict) or set(when) != {"any"} or not isinstance(when["any"], list) or not when["any"]:
            issues.append(f"{eid}: when은 any 목록이어야 함")
        else:
            issues += _lint_condition(eid, when, allow_env=True)
    return issues


def _lint_deploy(entries: list[dict] | None = None) -> list[str]:
    """CI 배포 패턴: match(run 정규식 또는 uses), compute(카탈로그 ID 또는 unmapped + label), target."""
    issues: list[str] = []
    catalog = kb.catalog()
    seen: set[str] = set()
    for i, d in enumerate(kb.deploy() if entries is None else entries):
        if not isinstance(d, dict):
            issues.append(f"deploy {i}: 항목이 매핑이 아님")
            continue
        did = str(d.get("id", f"deploy {i}"))
        if did in seen:
            issues.append(f"deploy: 중복 ID {did}")
        seen.add(did)
        match = d.get("match")
        if not isinstance(match, dict) or len(match) != 1 or not set(match) <= {"run", "uses"}:
            issues.append(f"{did}: match는 run 또는 uses 하나")
        elif "run" in match:
            try:
                re.compile(match["run"])
            except (re.error, TypeError) as e:
                issues.append(f"{did}: run 정규식 오류 {e}")
        compute = d.get("compute")
        if compute == "unmapped":
            if not d.get("label"):
                issues.append(f"{did}: compute가 unmapped이면 label 필요")
        elif compute not in catalog:
            issues.append(f"{did}: catalog에 없는 compute {compute}")
        target = d.get("target")
        if not isinstance(target, list) or not target or not set(target) <= DEPLOY_TARGETS:
            issues.append(f"{did}: 잘못된 target {target}")
    return issues


def lint() -> list[str]:
    return (_lint_catalog() + _lint_signatures() + _lint_defaults() + _lint_images() + _lint_external()
            + _lint_deploy())
