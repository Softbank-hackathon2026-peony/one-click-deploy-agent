"""설정이 없을 때 적용되는 기본값을 사실로 기록한다(설계 §6.5)."""

from __future__ import annotations

from infrafit.detect.artifacts import ParsedArtifact, pod_spec


def _is_full_object(doc: dict) -> bool:
    """kustomize 패치가 아니라 완전한 객체인가. 패치는 보통 이미지가 없다."""
    if doc.get("kind") == "CronJob":
        return "schedule" in (doc.get("spec") or {})
    containers = pod_spec(doc).get("containers") or []
    return bool(containers) and bool(containers[0].get("image"))


def _target_keys(art: ParsedArtifact, entry: dict) -> list[str]:
    if art.kind == "dockerfile":
        return [entry["key"]]
    if art.kind == "k8s":
        return [f"{d['kind']}/{(d.get('metadata') or {}).get('name', '?')}.{entry['key']}"
                for d in art.objects if d.get("kind") == entry["match_kind"] and _is_full_object(d)]
    if art.kind == "terraform":
        return [f"{rtype}.{rname}.{entry['key']}" for (rtype, rname, _) in art.objects
                if rtype == entry["resource"]]
    return []


def apply_defaults(artifacts: list[ParsedArtifact], entries) -> None:
    for art in artifacts:
        present = {s["key"] for s in art.settings}
        for entry in entries:
            if entry["artifact"] != art.kind:
                continue
            for key in _target_keys(art, entry):
                if key not in present:
                    art.settings.append({"key": key, "value": entry["value"], "defaulted": True,
                                         "default_source": entry["source"]})
                    present.add(key)


def hop_settings(component: str, explicit: dict, entries) -> list[dict]:
    out = [{"key": k, "value": v, "defaulted": False} for k, v in explicit.items()]
    for entry in entries:
        if entry["artifact"] == "hop" and entry["component"] == component and entry["key"] not in explicit:
            out.append({"key": entry["key"], "value": entry["value"], "defaulted": True,
                        "default_source": entry["source"]})
    return sorted(out, key=lambda s: s["key"])
