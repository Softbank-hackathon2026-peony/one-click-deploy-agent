"""차원 관찰 모으기: 인벤토리 사실(범위·엔드포인트·외부 서비스·unmapped·워크로드 scaling)과 코드 탐지기
(knowledge/profile_detectors.yaml).

관찰 하나 = (범위, 차원, 값 또는 종류, 근거, 신뢰도). 범위는 워크로드 ID, 요청 경로 탐지는 엔드포인트 ID.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from fnmatch import fnmatchcase

from infrafit.evidence import evidence
from infrafit.profile.owners import Imports, Owners, code_files, hit_lines, is_skipped
from infrafit.repo import Snapshot, match_glob

MAX_HITS_PER_FILE = 3


@dataclass(frozen=True)
class Observation:
    scope: str  # 워크로드 ID 또는 엔드포인트 ID
    dimension: str
    value: str | None  # ordered·flag·set 차원의 값
    kind: str | None  # kinds 차원의 종류
    evidence: tuple[dict, ...]
    confidence: str  # high | medium | low(후보 워크로드의 종류)


def _status_conf(status: str | None) -> str:
    return "high" if status in (None, "confirmed") else "medium"


def _app_evidence(evs) -> tuple[dict, ...]:
    """인벤토리 근거 중 테스트·보조 경로가 아닌 것(모두 그런 경로면 그대로)."""
    evs = list(evs or [])
    kept = [e for e in evs if not is_skipped(e["path"])]
    return tuple(kept or evs)


def _inventory_observations(inventory: dict, cfg: dict, app: set[str], owners: Owners) -> list[Observation]:
    out: list[Observation] = []
    comps: dict[str, list[str]] = {}
    for c in inventory["current_components"]:
        comps.setdefault(c["scope"], []).append(c["component"])
    scopes = [(d, d.get("used_by", [])) for d in inventory["datastores"]]
    for rule in cfg.get("components", []):
        for d, used_by in scopes:
            if rule.get("role") and d["role"] != rule["role"]:
                continue
            if not any(fnmatchcase(c, rule["component"]) for c in comps.get(d["id"], [])):
                continue
            ev = _app_evidence(d.get("evidence"))
            for w in used_by:
                if w in app:
                    out.append(Observation(w, rule["dimension"], rule.get("value"), rule.get("kind"), ev,
                                           _status_conf(d.get("status"))))
    for rule in cfg.get("unmapped", []):
        for u in inventory["unmapped"]:
            if u["label"] != rule["label"]:
                continue
            ev = _app_evidence(u.get("evidence"))
            ws = sorted({w for e in ev if not is_skipped(e["path"]) for w in owners.owners(e["path"])})
            for w in ws:
                out.append(Observation(w, rule["dimension"], rule.get("value"), rule.get("kind"), ev, "high"))
    for rule in cfg.get("endpoints", []):
        for e in inventory["endpoints"]:
            if e["method"] == rule["method"] and e["workload"] in app:
                out.append(Observation(e["id"], rule["dimension"], rule.get("value"), rule.get("kind"),
                                       (e["handler"],), _status_conf(e.get("status"))))
    for rule in cfg.get("external", []):
        for s in inventory["external_services"]:
            if s["kind"] not in rule["kinds"]:
                continue
            for w in s["used_by"]:
                if w in app:
                    out.append(Observation(w, rule["dimension"], rule.get("value"), s["id"],
                                           _app_evidence(s.get("evidence")), _status_conf(s.get("status"))))
    return out


def _hits(snap: Snapshot, rel: str, det: dict, cache: dict) -> list[dict]:
    key = (det["id"], rel)
    if key not in cache:
        lines = hit_lines(snap, rel, det["regex"], det.get("unless"))
        cache[key] = [evidence(snap, rel, n, "tech") for n in lines[:MAX_HITS_PER_FILE]]
    return cache[key]


def _code_observations(snap: Snapshot, inventory: dict, cfg: dict, app: set[str], owners: Owners) -> list[Observation]:
    out: list[Observation] = []
    detectors = cfg.get("code", [])
    globs = cfg.get("source_globs", [])
    files = code_files(snap, globs)
    imports = Imports(snap)
    depth = int(cfg.get("import_depth", 0))
    endpoints = [e for e in inventory["endpoints"] if e["workload"] in app]
    cache: dict = {}
    for det in detectors:
        scope = det["scope"]
        if scope == "workload":
            for rel in files:
                if not any(match_glob(rel, g) for g in det["glob"]):
                    continue
                ev = _hits(snap, rel, det, cache)
                if not ev:
                    continue
                for w in owners.owners(rel):
                    out.append(Observation(w, det["dimension"], det.get("value"), det.get("kind"), tuple(ev), "high"))
            continue
        for e in endpoints:
            handler = e["handler"]["path"]
            if is_skipped(handler) or not snap.exists(handler):
                continue
            reach = [(handler, 0)] if scope == "handler" else imports.closure(handler, depth)
            for rel, hop in reach:
                if not any(match_glob(rel, g) for g in det["glob"]):
                    continue
                ev = _hits(snap, rel, det, cache)
                if ev:
                    out.append(Observation(e["id"], det["dimension"], det.get("value"), det.get("kind"),
                                           tuple(ev), "high" if hop == 0 else "medium"))
    return out


def _load_test_hit(snap: Snapshot, rel: str, rules: list[dict], cache: dict) -> tuple[dict, dict] | None:
    """부하 테스트 스크립트 본문에서 처음 맞는 규칙과 그 줄의 근거(위 규칙부터)."""
    if rel not in cache:
        cache[rel] = None
        if snap.exists(rel):
            lines = snap.lines(rel)
            for rule in rules:
                rx = re.compile(rule["regex"])
                n = next((i for i, t in enumerate(lines, 1) if rx.search(t)), None)
                if n is not None:
                    cache[rel] = (rule, evidence(snap, rel, n, "tech"))
                    break
    return cache[rel]


def _scaling_observations(snap: Snapshot, inventory: dict, cfg: dict, app: set[str]) -> list[Observation]:
    """인벤토리 workloads[].scaling → D6(확장 요구), D2(평시 동시성), 부하 테스트 본문 → D3(폭증 형태)."""
    sc = cfg.get("scaling") or {}
    if not sc:
        return []
    out: list[Observation] = []
    cache: dict = {}
    d6, d2 = sc.get("D6") or {}, sc.get("D2") or {}
    for w in inventory["workloads"]:
        s = w.get("scaling")
        if w["id"] not in app or not s:
            continue
        ev = tuple(s["evidence"])
        if ev and d6:
            key = "auto" if s["autoscale"] else "fixed" if s["min"] >= 2 else "single"
            out.append(Observation(w["id"], "D6", d6[key], None, ev, "high"))
        if ev and d2 and (s["autoscale"] or s["min"] >= int(d2.get("min_replicas", 2))):
            # 설정이 밝힌 인스턴스 수에서 옮긴 값이라 medium. 부하 테스트는 보조 근거로 덧붙인다
            out.append(Observation(w["id"], "D2", d2["value"], None, ev + tuple(s.get("load_tests", [])), "medium"))
        for lt in s.get("load_tests", []):
            hit = _load_test_hit(snap, lt["path"], sc.get("load_tests") or [], cache)
            if hit:
                rule, hit_ev = hit
                out.append(Observation(w["id"], rule["dimension"], rule["value"], None, (hit_ev,), "medium"))
    return out


def observe(snap: Snapshot, inventory: dict, cfg: dict, app_ids: list[str]) -> list[Observation]:
    app = set(app_ids)
    owners = Owners(snap, inventory, app_ids)
    return (_inventory_observations(inventory, cfg, app, owners) + _scaling_observations(snap, inventory, cfg, app)
            + _code_observations(snap, inventory, cfg, app, owners))
