"""S3 적합성·S4 추천: 합성 능력·규칙·프로필로 검사한다(지식 파일에 의존하지 않음)."""

import copy

from infrafit.consistency import check_s3, check_s4
from infrafit.fit.matrix import build_fit
from infrafit.fit.recommend import SQLITE_TRANSFORM, agentcore_target, build_recommendation
from infrafit.run import RunContext
from infrafit.schema import validate
from infrafit.stages.s3_fit import run_s3
from infrafit.stages.s4_recommend import run_s4

RUN = "cp:gcp/cloud-run/unspecified"
EC2 = "cp:aws/ec2/docker-compose"
EKS = "cp:aws/eks/unspecified"
ECS = "cp:aws/ecs/unspecified"
RDS = "ds:aws/rds-postgres/single-az"
SQL = "ds:gcp/cloudsql-postgres/single"
SQLITE = "ds:local/sqlite/wal"


def cap(value, line=10):
    return {"value": value, "source": {"doc": "capabilities/05-compute-tier1-2.md", "line": line,
                                       "url": "https://example.com/doc", "quote": f"quote {value}"}}


def comp(cid, cloud, ops="low", target=None, cost=None, **caps):
    c = {"id": cid, "cloud": cloud, "family": cid.split(":")[0], "ops_burden": ops,
         "capabilities": {k.replace("__", "."): cap(v) for k, v in caps.items()}}
    if target:
        c["target"] = target
    if cost is not None:
        c["capabilities"]["COST.monthly_floor_usd"] = cap(cost)
    return c


def capabilities():
    return [
        comp(RUN, "gcp", target="gcp_cloud_run", cost=0, CP__websocket=True, CP__cpu_after_response=False,
             CP__cpu_after_response_config="instance-based billing", CP__persistent_local_disk=False),
        comp(EC2, "aws", ops="medium", target="aws_ec2", cost=10, CP__websocket=True,
             CP__cpu_after_response=True, CP__persistent_local_disk=True),
        comp(ECS, "aws", ops="medium", target="aws_ecs_fargate", cost=30, CP__websocket=True,
             CP__cpu_after_response=True, CP__persistent_local_disk=False),
        comp(EKS, "aws", ops="high", target="aws_eks", cost=70, CP__websocket=False,
             CP__persistent_local_disk=False),
        comp(RDS, "aws", cost=15, DS__engine="postgres"),
        comp(SQL, "gcp", cost=9, DS__engine="postgres"),
    ]


RULES = [
    {"id": "CAP-WEBSOCKET-001", "when": {"dimension": "A3", "equals": "장시간 양방향(웹소켓)"},
     "require": {"capability": "CP.websocket", "equals": True}, "otherwise": "infeasible",
     "config_from": None, "message": "websocket needed"},
    {"id": "CAP-AFTERRESP-001", "when": {"dimension": "A4", "equals": "있음"},
     "require": {"capability": "CP.cpu_after_response", "equals": True}, "otherwise": "config",
     "config_from": "CP.cpu_after_response_config", "message": "work after response"},
    {"id": "CAP-LOCALDISK-001", "when": {"dimension": "B2", "equals": "있음"},
     "require": {"capability": "CP.persistent_local_disk", "equals": True}, "otherwise": "infeasible",
     "config_from": None, "message": "local disk state"},
]

DS_EV = {"path": "db.py", "line": 8, "snippet": "sqlite3.connect(DB_PATH)"}


def inventory(sqlite=True):
    inv = {"workloads": [{"id": "w-web", "kind": "web", "name": "web", "status": "confirmed",
                          "entrypoint": {"path": "app.py", "line": 1, "snippet": "app"}}],
           "endpoints": [], "request_paths": [], "datastores": [],
           "current_components": [{"scope": "w-web", "component": EC2, "evidence": [], "status": "confirmed"}]}
    if sqlite:
        inv["datastores"].append({"id": "ds-sqlite", "role": "primary-db", "used_by": ["w-web"],
                                  "evidence": [DS_EV], "status": "confirmed"})
        inv["current_components"].append({"scope": "ds-sqlite", "component": SQLITE,
                                          "evidence": [DS_EV], "status": "confirmed"})
    return inv


def dim(d, value, ev=None, scope="w-web"):
    return {"dimension": d, "scope": scope, "value": value, "source": "detector", "confidence": "high",
            "evidence": ev or [{"path": "app.py", "line": 3, "snippet": f"{d} signal"}]}


def profile(*dims):
    return {"domain": {"value": "x", "votes": []}, "dimensions": list(dims), "assumptions": [],
            "dropped_inferences": [], "llm_used": False, "resolutions": []}


def cell(fit, scope, cand):
    return next(c for c in fit["matrix"] if c["scope"] == scope and c["candidate"] == cand)


def test_websocket_rejects_candidate_without_websocket():
    prof = profile(dim("A3", "장시간 양방향(웹소켓)"))
    fit = build_fit(inventory(sqlite=False), prof, capabilities(), RULES)
    eks = cell(fit, "w-web", EKS)
    assert eks["result"] == "infeasible"
    v = eks["violations"][0]
    assert v["rule"] == "CAP-WEBSOCKET-001" and v["dimension"] == "A3"
    assert v["capability_key"] == "CP.websocket" and v["actual"] is False
    assert v["source"] == {"ref": "https://example.com/doc", "quote": "quote False"}
    assert "app.py:3" in v["message"] and "capabilities/05-compute-tier1-2.md:10" in v["message"]
    assert cell(fit, "w-web", RUN)["result"] == "feasible"
    rec = build_recommendation(inventory(sqlite=False), prof, fit, capabilities(), RULES)
    rejected = {r["id"]: r for r in rec["rejected"]}
    assert rejected[EKS]["reasons"][0]["violation"]["rule"] == "CAP-WEBSOCKET-001"
    assert EKS not in {c for cand in rec["candidates"] for c in cand["assignment"].values()}


def test_after_response_work_needs_config_and_missing_key_is_unknown():
    fit = build_fit(inventory(sqlite=False), profile(dim("A4", "있음")), capabilities(), RULES)
    run = cell(fit, "w-web", RUN)
    assert run["result"] == "feasible_with_config"
    assert run["requires_config"][0]["setting"] == "instance-based billing"
    assert run["requires_config"][0]["rule"] == "CAP-AFTERRESP-001"
    eks = cell(fit, "w-web", EKS)
    assert eks["result"] == "unknown" and eks["unknown_keys"] == ["CP.cpu_after_response"]
    assert cell(fit, "w-web", EC2)["result"] == "feasible"
    assert cell(fit, "w-web", EC2)["is_current"] is True


def test_config_rule_without_setting_is_violation():
    caps = capabilities()
    del caps[0]["capabilities"]["CP.cpu_after_response_config"]
    fit = build_fit(inventory(sqlite=False), profile(dim("A4", "있음")), caps, RULES)
    assert cell(fit, "w-web", RUN)["result"] == "infeasible"


def test_sqlite_kept_on_disk_compute_else_transformed():
    inv = inventory()
    prof = profile(dim("B2", {"value": "있음", "kinds": ["sqlite"]}, ev=[DS_EV]))
    fit = build_fit(inv, prof, capabilities(), RULES)
    assert cell(fit, "w-web", RUN)["result"] == "infeasible"   # 변형 전에는 B2 위반
    rec = build_recommendation(inv, prof, fit, capabilities(), RULES)
    by_compute = {c["assignment"]["w-web"]: c for c in rec["candidates"]}
    assert by_compute[EC2]["assignment"]["ds-sqlite"] == SQLITE
    assert by_compute[EC2]["transforms"] == [] and by_compute[EC2]["change_effort"] == "none"
    run = by_compute[RUN]
    assert run["assignment"]["ds-sqlite"] == SQL
    assert run["transforms"] == [SQLITE_TRANSFORM] and run["change_effort"] == "medium"
    assert by_compute[ECS]["assignment"]["ds-sqlite"] == RDS
    assert rec["transforms"][0]["title"] == "SQLite→관리형 Postgres"
    tf_cells = {(c["scope"], c["candidate"]): c for c in rec["transform_fits"][0]["matrix"]}
    assert tf_cells[("w-web", RUN)]["result"] == "feasible"
    assert check_s4(rec, fit, inv, prof) == []


def test_ranking_feasible_then_unknown_then_cost():
    inv = inventory(sqlite=False)
    prof = profile(dim("A3", "장시간 양방향(웹소켓)"))
    caps = capabilities()
    fit = build_fit(inv, prof, caps, RULES)
    rec = build_recommendation(inv, prof, fit, caps, RULES)
    order = [c["assignment"]["w-web"] for c in rec["candidates"]]
    assert order == [RUN, EC2, ECS]                     # 비용 0 < 10 < 30, EKS는 탈락
    assert [c["rank"] for c in rec["candidates"]] == [1, 2, 3]
    assert rec["recommended"] == "C1"
    assert agentcore_target(rec["candidates"][0], caps) == "gcp_cloud_run"
    # 비용을 모르면 합에서 빠지지만 unknown_count 때문에 뒤로 밀린다
    del caps[0]["capabilities"]["COST.monthly_floor_usd"]
    fit = build_fit(inv, prof, caps, RULES)
    rec = build_recommendation(inv, prof, fit, caps, RULES)
    order = [(c["assignment"]["w-web"], c["unknown_count"]) for c in rec["candidates"]]
    assert order == [(EC2, 0), (ECS, 0), (RUN, 1)]
    # 합을 모르면 0이나 부분합이 아니라 null이고, 모르는 구성 요소를 적는다
    run_cost = rec["candidates"][2]["cost"]
    assert run_cost["monthly_baseline_usd"] is None
    assert run_cost["unknown_cost_components"] == [RUN]
    assert all(item["component"] != RUN for item in run_cost["breakdown"])
    known = rec["candidates"][0]["cost"]
    assert known["monthly_baseline_usd"] is not None and known["unknown_cost_components"] == []


def test_unknown_cost_total_is_null_and_schema_valid():
    """데이터 구성 요소 하나의 비용을 모르면 컴퓨트 비용을 알아도 합은 null(무료로 읽히지 않게)."""
    inv = inventory()
    prof = profile(dim("A3", "장시간 양방향(웹소켓)"), dim("B2", {"value": "있음", "kinds": ["sqlite"]}, ev=[DS_EV]))
    caps = capabilities()
    for c in caps:
        if c["id"] == SQL:
            del c["capabilities"]["COST.monthly_floor_usd"]
    fit = build_fit(inv, prof, caps, RULES)
    rec = build_recommendation(inv, prof, fit, caps, RULES)
    run = next(c for c in rec["candidates"] if c["assignment"]["w-web"] == RUN)
    assert run["assignment"]["ds-sqlite"] == SQL
    assert run["cost"]["monthly_baseline_usd"] is None
    assert run["cost"]["unknown_cost_components"] == [SQL]
    for cand in rec["candidates"]:
        validate("Candidate", cand)
    assert check_s4(rec, fit, inv, prof) == []


def test_no_feasible_candidate():
    caps = [c for c in capabilities() if c["id"] == EKS]
    inv = inventory(sqlite=False)
    prof = profile(dim("A3", "장시간 양방향(웹소켓)"))
    fit = build_fit(inv, prof, caps, RULES)
    rec = build_recommendation(inv, prof, fit, caps, RULES)
    assert rec["recommended"] is None and rec["candidates"] == []
    assert rec["no_feasible"]["blocking"][0]["rule"] == "CAP-WEBSOCKET-001"


def test_stages_write_valid_deterministic_output(tmp_path):
    inv = inventory()
    prof = profile(dim("A3", "장시간 양방향(웹소켓)"), dim("A4", "있음"), dim("B2", {"value": "있음", "kinds": ["sqlite"]}, ev=[DS_EV]))
    caps = capabilities()
    outputs = []
    for run_id in ("r1", "r2"):
        ctx = RunContext.create(tmp_path / run_id, run_id=run_id)
        fit = run_s3(ctx, copy.deepcopy(inv), prof, caps, RULES)
        rec = run_s4(ctx, inv, prof, fit, caps, RULES)
        validate("Fit", fit)
        validate("Recommendation", rec)
        assert (ctx.out_dir / "fit.json").exists() and (ctx.out_dir / "recommendation.json").exists()
        assert check_s3(fit, inv, prof) == []
        assert check_s4(rec, fit, inv, prof) == []
        outputs.append(({k: v for k, v in fit.items() if k != "meta"},
                        {k: v for k, v in rec.items() if k != "meta"}, fit["meta"]["input_hash"]))
    assert outputs[0] == outputs[1]
    # 같은 입력이면 캐시를 쓴다
    ctx = RunContext.create(tmp_path / "r1", run_id="r3")
    assert ctx.cached("S3", outputs[0][2]) is not None


def test_check_s4_flags_bad_references():
    inv = inventory(sqlite=False)
    prof = profile(dim("A3", "장시간 양방향(웹소켓)"))
    fit = build_fit(inv, prof, capabilities(), RULES)
    rec = build_recommendation(inv, prof, fit, capabilities(), RULES)
    rec["candidates"][0]["assignment"]["w-web"] = EKS
    rec["recommended"] = "C9"
    issues = check_s4(rec, fit, inv, prof)
    assert any("infeasible assignment" in i for i in issues)
    assert any("C9" in i for i in issues)


def test_when_reads_list_membership_and_object_value():
    from infrafit.fit.engine import match_when
    a1 = dim("A1", ["웹", "워커"])
    assert match_when({"dimension": "A1", "in": ["워커", "정기 작업"]}, [a1]) == [a1]
    assert match_when({"dimension": "A1", "in": ["정기 작업"]}, [a1]) == []
    b1_on = dim("B1", {"value": "있음", "kinds": ["in-memory-session"]})
    b1_off = dim("B1", {"value": "없음", "kinds": []})
    assert match_when({"dimension": "B1", "equals": "있음"}, [b1_on]) == [b1_on]
    assert match_when({"dimension": "B1", "equals": "있음"}, [b1_off]) == []


def test_kb_timeout_rules_by_a2_value():
    from infrafit import kb
    rules = [r for r in kb.rules() if r["id"].startswith("CAP-TIMEOUT-")]
    caps = [comp(RUN, "gcp", CP__max_request_seconds=3600), comp(ECS, "aws", CP__max_request_seconds=300),
            comp(EKS, "aws")]
    results = {}
    for value in ("1초 미만", "수십 초", "수 분", "그 이상"):
        fit = build_fit(inventory(sqlite=False), profile(dim("A2", value)), caps, rules)
        results[value] = (cell(fit, "w-web", RUN)["result"], cell(fit, "w-web", ECS)["result"],
                          cell(fit, "w-web", EKS)["result"])
    assert results == {"1초 미만": ("feasible", "feasible", "feasible"),
                       "수십 초": ("feasible", "feasible", "unknown"),
                       "수 분": ("feasible", "infeasible", "unknown"),
                       "그 이상": ("infeasible", "infeasible", "unknown")}


def test_sqlite_kind_stripped_from_b2_object_keeps_other_kinds():
    from infrafit.fit.recommend import _strip_sqlite_b2
    from infrafit.fit.scopes import Scope
    sq = Scope(id="ds-sqlite", kind="data", dims=[], members=["ds-sqlite"], engine="sqlite")
    both = dim("B2", {"value": "있음", "kinds": ["local-files", "sqlite"]})
    only = dim("B2", {"value": "있음", "kinds": ["sqlite"]})
    assert _strip_sqlite_b2([both], [sq], inventory())[0]["value"]["kinds"] == ["local-files"]
    assert _strip_sqlite_b2([only], [sq], inventory()) == []


def test_app_scope_ignores_workload_values_aggregated_from_endpoints():
    from infrafit.fit.scopes import app_scopes
    a2_web = {**dim("A2", "수십 초"), "aggregated_from": ["ep-web-001"]}
    a2_app = {**dim("A2", "수십 초", scope="w-app"), "aggregated_from": ["w-web"]}
    scopes = app_scopes(inventory(sqlite=False), profile(a2_web, a2_app))
    assert [s.id for s in scopes] == ["w-app"]
    assert scopes[0].members == ["w-app", "w-web"] and scopes[0].current == [EC2]
