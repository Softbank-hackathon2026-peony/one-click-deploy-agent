"""S4 서비스 유형별 순위(knowledge/ranking.yaml)."""

from infrafit import kb
from infrafit.consistency import check_s4
from infrafit.fit.matrix import build_fit
from infrafit.fit.ranking import (a2_of, classify, cost_value, decided_by, lacks_always_on, lacks_headroom,
                                  lacks_scaling, sort_key, unsafe_data)
from infrafit.fit.recommend import build_recommendation
from infrafit.schema import validate


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
    b["unknown_count"], c["unknown_count"] = 0, 2
    assert decided_by([("C1", b), ("C2", c)], order)[0] == {"criterion": "unknown_count", "over": "C2"}

RUN = "cp:gcp/cloud-run/unspecified"
EC2 = "cp:aws/ec2/docker-compose"
ECS = "cp:aws/ecs/unspecified"
WS_RULE = {"id": "CAP-WEBSOCKET-001", "when": {"dimension": "A3", "equals": "장시간 양방향(웹소켓)"},
           "require": {"capability": "CP.websocket", "equals": True}, "otherwise": "infeasible",
           "config_from": None, "message": "websocket needed"}


def capc(cid, cloud, target, cost, **caps):
    src = {"doc": "capabilities/05-compute-tier1-2.md", "line": 10, "url": "https://example.com/doc", "quote": "q"}
    c = {"id": cid, "cloud": cloud, "family": "cp", "ops_burden": "low", "target": target,
         "capabilities": {k.replace("__", "."): {"value": v, "source": src} for k, v in caps.items()}}
    c["capabilities"]["COST.monthly_floor_usd"] = {"value": cost, "source": src}
    return c


def three_platforms(run_cost=0, ecs_cost=30, with_ec2=True):
    caps = [capc(RUN, "gcp", "gcp_cloud_run", run_cost, CP__websocket=True, CP__always_on=False,
                 CP__horizontal_scaling=True),
            capc(ECS, "aws", "aws_ecs_fargate", ecs_cost, CP__websocket=True, CP__always_on=True,
                 CP__horizontal_scaling=True)]
    if with_ec2:
        caps.append(capc(EC2, "aws", "aws_ec2", 10, CP__websocket=True, CP__always_on=True,
                         CP__horizontal_scaling=False))
    return caps


def web_inventory():
    return {"workloads": [{"id": "w-web", "kind": "web", "name": "web", "status": "confirmed",
                           "entrypoint": {"path": "app.py", "line": 1, "snippet": "app"}}],
            "endpoints": [], "request_paths": [], "datastores": [], "current_components": []}


def prof(*dims):
    return {"domain": {"value": "x", "votes": []}, "dimensions": list(dims), "assumptions": [],
            "dropped_inferences": [], "llm_used": False, "resolutions": []}


def recommend(p, caps):
    inv = web_inventory()
    fit = build_fit(inv, p, caps, [WS_RULE])
    rec = build_recommendation(inv, p, fit, caps, [WS_RULE])
    return rec, fit, inv


def compute_order(rec):
    return [c["placement"][0]["component"] for c in rec["candidates"]]


def test_same_candidates_rank_differently_by_service_type():
    caps = three_platforms()
    realtime, fit, inv = recommend(prof(dim("A3", "장시간 양방향(웹소켓)")), caps)
    assert realtime["ranking"]["service_type"] == "realtime"
    assert compute_order(realtime) == [ECS, EC2, RUN]     # 상시 응답 → 확장 → 비용
    assert [c["decided_by"] for c in realtime["candidates"]] == [
        {"criterion": "scaling", "over": "C2"}, {"criterion": "always_on", "over": "C3"}, None]
    light, _, _ = recommend(prof(), caps)
    assert light["ranking"]["service_type"] == "light_web" and light["ranking"]["coverage"] == "default"
    assert compute_order(light) == [RUN, EC2, ECS]        # 비용 0 < 10 < 30
    for rec in (realtime, light):
        for cand in rec["candidates"]:
            validate("Candidate", cand)
    assert check_s4(realtime, fit, inv, prof(dim("A3", "장시간 양방향(웹소켓)"))) == []


def test_cost_within_tie_ratio_falls_through_to_next_criterion():
    tied, _, _ = recommend(prof(), three_platforms(run_cost=10, ecs_cost=11, with_ec2=False))
    assert compute_order(tied) == [ECS, RUN]               # 11 ≤ 10×1.15 동률 → 상시 응답에서 ECS
    assert tied["candidates"][0]["decided_by"] == {"criterion": "always_on", "over": "C2"}
    assert tied["candidates"][0]["criteria"]["cost"] == {"monthly_usd": 11.0, "tied_with_cheapest": True}
    apart, _, _ = recommend(prof(), three_platforms(run_cost=10, ecs_cost=12, with_ec2=False))
    assert compute_order(apart) == [RUN, ECS]
    assert apart["candidates"][0]["decided_by"]["criterion"] == "cost"


def test_candidate_criteria_lists_all_seven():
    rec, _, _ = recommend(prof(dim("A3", "장시간 양방향(웹소켓)")), three_platforms())
    crit = rec["candidates"][0]["criteria"]
    assert set(crit) == {"certainty", "cost", "always_on", "request_headroom", "scaling", "data_safety",
                         "config_burden"}
    assert crit["certainty"] == {"evidence_unknown": False, "unknown_cost_components": 0, "unknown_count": 0}


def test_unknown_from_assumed_dimension_does_not_demote_cheaper_candidate():
    rule = {"id": "CAP-AFTERRESP-001", "when": {"dimension": "A4", "equals": "있음"},
            "require": {"capability": "CP.cpu_after_response", "equals": True}, "otherwise": "infeasible",
            "config_from": None, "message": "after response"}
    caps = [capc(RUN, "gcp", "gcp_cloud_run", 0),                                  # A4 키 없음 → unknown 셀
            capc(EC2, "aws", "aws_ec2", 10, CP__cpu_after_response=True)]
    assumed = {**dim("A4", "있음"), "source": "assumption", "evidence": []}
    p = prof(assumed)
    inv = web_inventory()
    fit = build_fit(inv, p, caps, [rule])
    rec = build_recommendation(inv, p, fit, caps, [rule])
    assert rec["ranking"]["service_type"] == "light_web"
    assert compute_order(rec) == [RUN, EC2]
    assert rec["candidates"][0]["criteria"]["certainty"] == {
        "evidence_unknown": False, "unknown_cost_components": 0, "unknown_count": 1}


def test_decided_by_reports_unknown_count_tie_breaker():
    rule = {"id": "CAP-AFTERRESP-001", "when": {"dimension": "A4", "equals": "있음"},
            "require": {"capability": "CP.cpu_after_response", "equals": True}, "otherwise": "infeasible",
            "config_from": None, "message": "after response"}
    caps = [capc(RUN, "gcp", "gcp_cloud_run", 10),                                 # A4 키 없음 → unknown 셀
            capc(EC2, "aws", "aws_ec2", 10, CP__cpu_after_response=True)]
    assumed = {**dim("A4", "있음"), "source": "assumption", "evidence": []}
    p = prof(assumed)
    inv = web_inventory()
    fit = build_fit(inv, p, caps, [rule])
    rec = build_recommendation(inv, p, fit, caps, [rule])
    assert compute_order(rec) == [EC2, RUN]
    assert rec["candidates"][0]["decided_by"] == {"criterion": "unknown_count", "over": "C2"}
    validate("Candidate", rec["candidates"][0])
