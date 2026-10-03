"""S4 서비스 유형별 순위(knowledge/ranking.yaml, 설계 2026-10-03-infrafit-service-type-ranking-design.md).

유형 판정, 기준 값 계산 도우미, 비용 동률, decided_by. 순위는 사전식이고 유형마다 기준 순서만 다르다.
"""

from __future__ import annotations

from infrafit.fit.engine import dim_value, match_when

# 계산 함수가 있는 기준. ranking.yaml criteria 는 이 안에서만 고른다(kb_lint)
CRITERIA = ("certainty", "cost", "always_on", "request_headroom", "scaling", "data_safety", "config_burden")

DEFAULT_REASON = "근거 있는 차원 값이 어느 유형 조건에도 맞지 않음"


def _at(evidence) -> list[str]:
    out = []
    for e in evidence or []:
        if e.get("path"):
            out.append(f"{e['path']}:{e['line']}" if e.get("line") else e["path"])
    return out


def _hits(when: dict, dims: list[dict], datastores: list[dict]) -> list[dict] | None:
    """조건에 맞으면 근거 목록 [{dimension, value, at}], 아니면 None."""
    if "any" in when:
        found = [h for child in when["any"] if (h := _hits(child, dims, datastores)) is not None]
        return [x for h in found for x in h] if found else None
    if "datastores" in when:
        if bool(datastores) != bool(when["datastores"]):
            return None
        return [{"dimension": "datastores", "value": d["id"], "at": _at(d.get("evidence"))} for d in datastores]
    if "kinds" in when:
        rows = [d for d in dims if d["dimension"] == when["dimension"] and isinstance(d.get("value"), dict)
                and set(d["value"].get("kinds") or []) & set(when["kinds"])]
    else:
        rows = match_when(when, dims)
    if not rows:
        return None
    return [{"dimension": d["dimension"], "value": dim_value(d.get("value")), "at": _at(d.get("evidence"))}
            for d in rows]


def _dedupe(hits: list[dict]) -> list[dict]:
    out: list[dict] = []
    for h in hits:
        same = next((o for o in out if o["dimension"] == h["dimension"] and o["value"] == h["value"]), None)
        if same is None:
            out.append({**h, "at": list(dict.fromkeys(h["at"]))})
        else:
            same["at"] = list(dict.fromkeys(same["at"] + h["at"]))
    return out


def classify(dims: list[dict], datastores: list[dict], cfg: dict) -> dict:
    """앱 워크로드 차원 행(근거 있는 것만)과 데이터 저장소로 서비스 유형 하나를 고른다. 출력 `ranking` 블록."""
    usable = [d for d in dims if d.get("source") == "detector"]
    types = cfg["service_types"]
    matched = []
    for t in types:
        if t["when"] == "default":
            continue
        hits = _hits(t["when"], usable, datastores)
        if hits is not None:
            matched.append({"type": t["id"], "by": _dedupe(hits)})
    chosen = next((t for t in types if matched and t["id"] == matched[0]["type"]), None) \
        or next(t for t in types if t["when"] == "default")
    if not matched:
        coverage = "default"
    elif len(matched) == 1:
        coverage = "full"
    else:
        coverage = "partial"
    return {
        "service_type": chosen["id"], "label": chosen["label"], "coverage": coverage, "matched": matched,
        "unprioritized": [m["type"] for m in matched[1:]],
        "default_reason": None if matched else DEFAULT_REASON,
        "criteria_order": list(chosen["order"]), "why": chosen["why"], "refs": list(chosen["refs"]),
        "scope": dict(cfg["scope"]),
    }
