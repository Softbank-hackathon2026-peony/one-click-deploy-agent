"""knowledge/signatures/*.yaml의 시그니처를 저장소에 맞춰 본다."""

from __future__ import annotations

import re
from dataclasses import dataclass

from infrafit.detect.manifests import Manifests
from infrafit.detect.testpaths import is_test_path
from infrafit.evidence import evidence
from infrafit.repo import Snapshot

MAX_CODE_EVIDENCE = 5


@dataclass(frozen=True)
class Match:
    signature: str
    component: str
    role: str
    status: str
    evidence: tuple[dict, ...]


def _eval(cond: dict, snap: Snapshot, manifests: Manifests) -> list[dict]:
    """맞으면 근거 목록, 안 맞으면 빈 목록."""
    if "any" in cond:
        out: list[dict] = []
        for child in cond["any"]:
            out += _eval(child, snap, manifests)
        return out
    if "all" in cond:
        parts = [_eval(child, snap, manifests) for child in cond["all"]]
        return [e for part in parts for e in part] if all(parts) else []
    if "dependency" in cond:
        return [evidence(snap, rel, line, "tech")
                for rel, line in manifests.locations.get(cond["dependency"].lower(), [])]
    if "code" in cond:
        code = cond["code"]
        flags = re.MULTILINE | (re.IGNORECASE if code.get("flags") == "i" else 0)
        rx = re.compile(code["regex"], flags)
        out = []
        for rel in snap.glob(code["glob"]):
            if is_test_path(rel):  # 테스트 코드의 흔적은 실제 배포 구성의 근거가 아니다
                continue
            for i, text in enumerate(snap.lines(rel), 1):
                if rx.search(text):
                    out.append(evidence(snap, rel, i, "tech"))
                    if len(out) >= MAX_CODE_EVIDENCE:
                        return out
        return out
    raise ValueError(f"알 수 없는 조건: {cond}")


def match_signatures(snap: Snapshot, manifests: Manifests, sigs) -> list[Match]:
    out: list[Match] = []
    for sig in sigs:
        ev = _eval(sig["when"], snap, manifests)
        if not ev:
            continue
        component, status = sig["component"], sig["status"]
        for refine in sig.get("refine", []):
            extra = _eval(refine["when"], snap, manifests)
            if extra:
                component = refine["component"]
                status = refine.get("status", status)
                ev = ev + extra
                break
        out.append(Match(sig["id"], component, sig["role"], status, tuple(ev)))
    return out
