"""S4 서비스 유형별 순위(knowledge/ranking.yaml)."""

from infrafit import kb
from infrafit.fit.ranking import classify


def dim(d, value, source="detector", path="app.py", line=3, scope="w-web"):
    return {"dimension": d, "scope": scope, "value": value, "source": source, "confidence": "high",
            "evidence": [{"path": path, "line": line, "snippet": f"{d} signal"}]}


DS = [{"id": "ds-pg", "role": "primary-db", "used_by": ["w-web"], "status": "confirmed",
       "evidence": [{"path": "db.js", "line": 2, "snippet": "new Pool()"}]}]


def test_single_type_is_full_coverage_with_evidence():
    r = classify([dim("A3", "장시간 양방향(웹소켓)", path="server.js", line=12)], [], kb.ranking())
    assert r["service_type"] == "realtime" and r["label"] == "실시간"
    assert r["coverage"] == "full" and r["unprioritized"] == [] and r["default_reason"] is None
    assert r["matched"] == [{"type": "realtime",
                             "by": [{"dimension": "A3", "value": "장시간 양방향(웹소켓)", "at": ["server.js:12"]}]}]
    assert r["criteria_order"] == ["certainty", "always_on", "scaling", "cost", "config_burden"]
    assert r["refs"] == ["T-006", "W-001", "T-016"] and r["scope"] == {"service_types": 5, "criteria": 7}


def test_higher_type_wins_and_rest_is_unprioritized():
    dims = [dim("B2", {"value": "있음", "kinds": ["sqlite"]}), dim("A1", ["웹", "실시간 연결"])]
    r = classify(dims, DS, kb.ranking())
    assert r["service_type"] == "realtime" and r["coverage"] == "partial"
    assert [m["type"] for m in r["matched"]] == ["realtime", "stateful"]
    assert r["unprioritized"] == ["stateful"]
    stateful = r["matched"][1]["by"]
    assert {"dimension": "datastores", "value": "ds-pg", "at": ["db.js:2"]} in stateful


def test_assumption_rows_do_not_classify():
    r = classify([dim("A2", "수십 초", source="assumption"), dim("A1", ["웹"])], [], kb.ranking())
    assert r["service_type"] == "light_web" and r["coverage"] == "default"
    assert r["matched"] == [] and r["default_reason"]


def test_llm_api_kind_is_long_request():
    r = classify([dim("E2", {"value": "있음", "kinds": ["llm-api", "payments"]})], [], kb.ranking())
    assert r["service_type"] == "long_request"
    assert r["matched"][0]["by"][0]["dimension"] == "E2"


def test_datastores_alone_is_stateful_and_background_detected():
    assert classify([], DS, kb.ranking())["service_type"] == "stateful"
    r = classify([dim("A1", ["워커"])], [], kb.ranking())
    assert r["service_type"] == "background" and r["coverage"] == "full"


def test_same_evidence_across_workloads_is_deduplicated():
    dims = [dim("A3", "장시간 양방향(웹소켓)", scope="w-a"), dim("A3", "장시간 양방향(웹소켓)", scope="w-b")]
    r = classify(dims, [], kb.ranking())
    assert r["matched"][0]["by"] == [{"dimension": "A3", "value": "장시간 양방향(웹소켓)", "at": ["app.py:3"]}]
