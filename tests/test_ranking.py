"""S4 서비스 유형별 순위(knowledge/ranking.yaml)."""

from infrafit import kb
from infrafit.fit.ranking import (a2_of, classify, cost_value, decided_by, lacks_always_on, lacks_headroom,
                                  lacks_scaling, sort_key, unsafe_data)


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


def comp(**caps):
    return {"id": "cp:x/y/z", "capabilities": {k.replace("__", "."): {"value": v} for k, v in caps.items()}}


def test_a2_of_takes_highest_detector_value():
    assert a2_of([dim("A2", "수십 초"), dim("A2", "수 분"), dim("A2", "그 이상", source="assumption")]) == "수 분"
    assert a2_of([dim("A2", "1초 미만", source="assumption")]) is None


def test_headroom_needs_one_tier_above():
    limited = comp(CP__platform_request_timeout=True, CP__max_request_seconds=300)
    long_ok = comp(CP__platform_request_timeout=True, CP__max_request_seconds=3600)
    unlimited = comp(CP__platform_request_timeout=False)
    unknown = comp(CP__platform_request_timeout=True)
    assert lacks_headroom(limited, "수십 초") is True        # 600 미만
    assert lacks_headroom(long_ok, "수십 초") is False
    assert lacks_headroom(long_ok, "수 분") is True          # 상한 없음이 필요
    assert lacks_headroom(unlimited, "그 이상") is False
    assert lacks_headroom(unknown, "수십 초") is True        # 모르면 나쁜 쪽
    assert lacks_headroom(limited, None) is False            # 근거 있는 A2 없음
    assert lacks_headroom(comp(CP__platform_request_timeout=True, CP__max_request_seconds=60), "1초 미만") is False


def test_capability_flags_count_unknown_as_bad():
    assert lacks_always_on(comp(CP__always_on=True)) is False
    assert lacks_always_on(comp(CP__always_on=False)) is True
    assert lacks_always_on(None) is True
    assert lacks_scaling(comp(CP__horizontal_scaling=True)) is False
    assert lacks_scaling(comp()) is True
    assert unsafe_data("ds:vm/compose-postgres/default", comp(DS__colocated_vm=True)) is True
    assert unsafe_data("ds:local/sqlite/wal", None) is True
    assert unsafe_data("ds:aws/rds-postgres/single-az", comp(DS__engine="postgres")) is False


def test_cost_value_ties_within_ratio_of_cheapest():
    assert cost_value(10.0, 0, 10.0, 10.0, 0.15) == (False, 0.0, 0)
    assert cost_value(11.5, 0, 11.5, 10.0, 0.15) == (False, 0.0, 0)
    assert cost_value(11.6, 0, 11.6, 10.0, 0.15) == (False, 11.6, 0)
    assert cost_value(0.0, 0, 0.0, 0.0, 0.15) == (False, 0.0, 0)
    assert cost_value(1.0, 0, 1.0, 0.0, 0.15) == (False, 1.0, 0)
    assert cost_value(None, 2, 5.0, 10.0, 0.15) == (True, 2, 5.0)
    assert cost_value(None, 1, 0, None, 0.15) > cost_value(99.0, 0, 99.0, 1.0, 0.15)


def test_sort_key_and_decided_by_follow_order():
    order = ["certainty", "always_on", "cost"]
    a = {"certainty": (False, 0, 0), "always_on": 0, "cost": (False, 30.0, 0), "scaling": 9}
    b = {"certainty": (False, 0, 0), "always_on": 1, "cost": (False, 0.0, 0), "scaling": 0}
    c = {"certainty": (False, 0, 0), "always_on": 1, "cost": (False, 0.0, 0), "scaling": 0}
    assert sort_key(a, order) < sort_key(b, order)
    assert decided_by([("C1", a), ("C2", b), ("C3", c)], order) == [
        {"criterion": "always_on", "over": "C2"}, {"criterion": "name", "over": "C3"}, None]
