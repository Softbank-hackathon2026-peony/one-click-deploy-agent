"""계획 2b Task C: 워크로드별 판정, 토폴로지(vm-compose·services·kubernetes) 조합, 확장 규칙, 순위·결과.

합성 인벤토리·프로필·능력으로 검사한다(저장소 기대 출력 없음). 규칙은 지식 파일(knowledge/rules.yaml)의 것을 쓴다.
"""

from infrafit import kb
from infrafit.consistency import check_s3, check_s4
from infrafit.fit.matrix import build_fit
from infrafit.fit.recommend import SQLITE_TRANSFORM, build_recommendation
from infrafit.kb_lint import _lint_rules
from infrafit.schema import validate

EC2 = "cp:aws/ec2/docker-compose"
GCE = "cp:gcp/compute-engine/docker-compose"
REQ = "cp:gcp/cloud-run/request-billing"
INS = "cp:gcp/cloud-run/instance-billing"
ECS = "cp:aws/ecs-fargate/alb"
LAMBDA = "cp:aws/lambda/function-url"
GKE = "cp:gcp/gke/autopilot"
EKS = "cp:aws/eks/managed-node-group"
RDS = "ds:aws/rds-postgres/single-az"
SQL = "ds:gcp/cloudsql-postgres/single"
ELC = "ca:aws/elasticache/node-based"
MEM = "ca:gcp/memorystore/redis-basic"
VMPG = "ds:vm/compose-postgres/default"
VMRD = "ca:vm/compose-redis/default"
PGU = "ds:unspecified/postgresql/default"
RDU = "ca:unspecified/redis/default"
SQLITE = "ds:local/sqlite/wal"
SUPA = "ds:supabase/postgres/unspecified-plan"


def cap(value):
    return {"value": value, "source": {"doc": "capabilities/05-compute-tier1-2.md", "line": 10,
                                       "url": "https://example.com/doc", "quote": f"quote {value}"}}


def comp(cid, cloud, target=None, **caps):
    c = {"id": cid, "cloud": cloud, "family": cid.split(":")[0],
         "capabilities": {k.replace("__", "."): cap(v) for k, v in caps.items()}}
    if target:
        c["target"] = target
    return c


def caps_all(**overrides):
    """토폴로지 셋을 모두 갖춘 합성 능력 표. overrides: {component_id: {key: value | None(삭제)}}."""
    items = [
        comp(EC2, "aws", "aws_ec2", CP__platform_request_timeout=False, CP__runs_long_lived_server=True,
             CP__cpu_after_response=True, CP__persistent_local_disk=True, CP__always_on=True, CP__scale_to_zero=False,
             CP__horizontal_scaling=False, CP__single_instance_config="container_name", COST__monthly_floor_usd=20.7),
        comp(GCE, "gcp", "gcp_compute_engine", CP__platform_request_timeout=False, CP__runs_long_lived_server=True,
             CP__cpu_after_response=True, CP__persistent_local_disk=True, CP__always_on=True,
             CP__horizontal_scaling=False, CP__single_instance_config="container_name",
             COST__monthly_floor_usd=20.64),
        comp(REQ, "gcp", "gcp_cloud_run", CP__platform_request_timeout=True, CP__runs_long_lived_server=True,
             CP__max_request_seconds=3600, CP__websocket=True,
             CP__cpu_after_response=False, CP__persistent_local_disk=False, CP__scale_to_zero=True,
             CP__always_on=False, CP__single_instance_config="--scaling=1", CP__horizontal_scaling=True,
             COST__monthly_floor_usd=0, COST__monthly_pinned_usd=13.8),
        comp(INS, "gcp", "gcp_cloud_run", CP__platform_request_timeout=True, CP__runs_long_lived_server=True,
             CP__max_request_seconds=3600, CP__websocket=True,
             CP__cpu_after_response=True, CP__persistent_local_disk=False, CP__scale_to_zero=True,
             CP__always_on=False, CP__always_on_config="min-instances ≥ 1", CP__single_instance_config="--scaling=1",
             CP__horizontal_scaling=True, COST__monthly_floor_usd=0, COST__monthly_pinned_usd=59.9),
        comp(ECS, "aws", "aws_ecs_fargate", CP__platform_request_timeout=True, CP__runs_long_lived_server=True,
             CP__max_request_seconds=60, CP__websocket=True,
             CP__cpu_after_response=True, CP__persistent_local_disk=False, CP__always_on=True,
             CP__scale_to_zero=True, CP__horizontal_scaling=True, COST__monthly_floor_usd=37.74),
        comp(LAMBDA, "aws", "aws_lambda", CP__platform_request_timeout=True, CP__runs_long_lived_server=False,
             CP__max_request_seconds=900, CP__cpu_after_response=False,
             CP__always_on=False, CP__persistent_local_disk=False, CP__horizontal_scaling=True,
             CP__single_instance_config="reserved concurrency 1", COST__monthly_floor_usd=0),
        comp(GKE, "gcp", "gcp_gke", CP__platform_request_timeout=True, CP__runs_long_lived_server=True,
             CP__max_request_seconds=30, CP__max_request_seconds_config="BackendConfig timeoutSec",
             CP__websocket=True, CP__always_on=True, CP__single_instance_config="replicas: 1",
             CP__persistent_local_disk=True, CP__scale_to_zero=True, CP__horizontal_scaling=True,
             CP__multi_workload=True, CP__cpu_after_response=True,
             COST__monthly_floor_usd=31.11, COST__per_replica_usd=12.86),
        comp(EKS, "aws", "aws_eks", CP__platform_request_timeout=True, CP__runs_long_lived_server=True,
             CP__max_request_seconds=60, CP__websocket=True, CP__always_on=True,
             CP__single_instance_config="replicas: 1", CP__persistent_local_disk=True, CP__horizontal_scaling=True,
             CP__multi_workload=True, CP__cpu_after_response=True, COST__monthly_floor_usd=140.16),
        comp(RDS, "aws", DS__engine="postgres", COST__monthly_floor_usd=20.9),
        comp(SQL, "gcp", DS__engine="postgres", COST__monthly_floor_usd=12.21),
        comp(ELC, "aws", DS__engine="redis", COST__monthly_floor_usd=17.5),
        comp(MEM, "gcp", DS__engine="redis", COST__monthly_floor_usd=47.45),
        comp(VMPG, "local", DS__engine="postgres", DS__colocated_vm=True, COST__monthly_floor_usd=0),
        comp(VMRD, "local", DS__engine="redis", DS__colocated_vm=True, COST__monthly_floor_usd=0),
        comp(SQLITE, "local", DS__engine="sqlite"),
    ]
    by = {c["id"]: c for c in items}
    for cid, changes in overrides.items():
        for key, value in changes.items():
            if value is None:
                by[cid]["capabilities"].pop(key, None)
            else:
                by[cid]["capabilities"][key] = cap(value)
    return items


RULES = list(kb.rules())
EV = {"path": "app.py", "line": 3, "snippet": "x"}


def workload(wid, kind="web", scaling=None):
    w = {"id": wid, "kind": kind, "name": wid[2:], "status": "confirmed",
         "entrypoint": {"path": f"{wid[2:]}.py", "line": 1, "snippet": "main"}}
    if scaling:
        w["scaling"] = {"evidence": [], **scaling}
    return w


def inventory(workloads, datastores=()):
    inv = {"workloads": list(workloads), "endpoints": [], "request_paths": [], "datastores": [],
           "current_components": []}
    for sid, cid in datastores:
        inv["datastores"].append({"id": sid, "role": "primary-db", "used_by": [workloads[0]["id"]],
                                  "evidence": [EV], "status": "confirmed"})
        inv["current_components"].append({"scope": sid, "component": cid, "evidence": [EV], "status": "confirmed"})
    return inv


def dim(d, value, scope, ev=None, source="detector"):
    return {"dimension": d, "scope": scope, "value": value, "source": source, "confidence": "high",
            "evidence": [ev or {"path": f"{scope[2:]}.py", "line": 7, "snippet": f"{d} signal"}]}


def profile(*dims, batch_only=None):
    p = {"domain": {"value": "x", "votes": []}, "dimensions": list(dims), "assumptions": [],
         "dropped_inferences": [], "llm_used": False, "resolutions": []}
    if batch_only is not None:
        p["batch_only"] = batch_only
    return p


def run(inv, prof, caps=None):
    caps = caps_all() if caps is None else caps
    fit = build_fit(inv, prof, caps, RULES)
    rec = build_recommendation(inv, prof, fit, caps, RULES)
    catalog = {c["id"]: {} for c in caps} | {c["component"]: {} for c in inv["current_components"]}
    assert check_s3(fit, inv, prof, catalog) == []
    assert check_s4(rec, fit, inv, prof, catalog) == []
    for cand in rec["candidates"]:
        validate("Candidate", cand)
    return fit, rec


def cell(fit, scope, cand):
    return next(c for c in fit["matrix"] if c["scope"] == scope and c["candidate"] == cand)


# ---------- 규칙 ----------

def test_scale_rule_rejects_single_vm_for_replicas_or_autoscale():
    inv = inventory([workload("w-web", scaling={"min": 2, "max": 10, "autoscale": True})])
    for value in ("고정 다중", "자동 확장"):
        prof = profile(dim("D6", value, "w-web"))
        fit, rec = run(inv, prof)
        vm = cell(fit, "w-web", EC2)
        assert vm["result"] == "infeasible" and vm["violations"][0]["rule"] == "CAP-SCALE-001"
        assert vm["violations"][0]["capability_key"] == "CP.horizontal_scaling"
        assert cell(fit, "w-web", GKE)["result"] == "feasible"
        assert {c["topology"] for c in rec["candidates"]} == {"services", "kubernetes"}
        rejected = {r["id"] for r in rec["rejected"]}
        assert f"vm-compose/{EC2}" in rejected and f"vm-compose/{GCE}" in rejected
    # 수평 확장 키가 없으면 모름
    fit, _ = run(inv, profile(dim("D6", "자동 확장", "w-web")),
                 caps_all(**{EC2: {"CP.horizontal_scaling": None}}))
    assert cell(fit, "w-web", EC2)["result"] == "unknown"
    # 단일 인스턴스면 규칙이 걸리지 않는다
    fit, _ = run(inv, profile(dim("D6", "단일 인스턴스", "w-web")))
    assert cell(fit, "w-web", EC2)["result"] == "feasible"


def test_memory_state_with_replicas_is_infeasible_everywhere_for_that_workload_only():
    inv = inventory([workload("w-api", scaling={"min": 2, "max": 2, "autoscale": False}),
                     workload("w-web", scaling={"min": 3, "max": 3, "autoscale": False})])
    b1_ev = {"path": "api/session.py", "line": 12, "snippet": "MemoryStore()"}
    prof = profile(dim("B1", {"value": "있음", "kinds": ["in-memory-session"]}, "w-api", ev=b1_ev),
                   dim("D6", "고정 다중", "w-api"), dim("D6", "고정 다중", "w-web"),
                   {**dim("B1", {"value": "있음", "kinds": ["in-memory-session"]}, "w-app", ev=b1_ev),
                    "aggregated_from": ["w-api", "w-web"]})
    fit, rec = run(inv, prof)
    for cid in (EC2, REQ, INS, ECS, GKE, EKS, LAMBDA):
        c = cell(fit, "w-api", cid)
        mem = [v for v in c["violations"] if v["rule"] == "CAP-MEMSTATE-002"]
        assert c["result"] == "infeasible" and len(mem) == 1, cid
        assert mem[0]["dimension"] == ["B1", "D6"]
        assert "프로세스 메모리 상태가 인스턴스 간 공유되지 않음" in mem[0]["message"]
        assert "api/session.py:12" in mem[0]["message"]
        # w-web은 자신의 B1이 없어 이 규칙에 걸리지 않는다(w-app 값을 빌리지 않는다)
        assert not any(v["rule"] == "CAP-MEMSTATE-002" for v in cell(fit, "w-web", cid)["violations"])
    assert rec["outcome"] == "no_feasible" and rec["candidates"] == []
    assert any(v["rule"] == "CAP-MEMSTATE-002" for v in rec["no_feasible"]["blocking"])
    # 레플리카가 1이면 B1은 인스턴스 1개 고정 설정(CAP-MEMSTATE-001)으로 통과한다
    prof = profile(dim("B1", {"value": "있음", "kinds": ["in-memory-session"]}, "w-api", ev=b1_ev))
    fit, rec = run(inventory([workload("w-api")]), prof)
    assert cell(fit, "w-api", GKE)["result"] == "feasible_with_config"
    assert rec["outcome"] == "recommended"


def test_gke_timeout_needs_backendconfig_others_stay_infeasible():
    inv = inventory([workload("w-web")])
    for a2 in ("수십 초", "수 분"):
        fit, _ = run(inv, profile(dim("A2", a2, "w-web")))
        gke = cell(fit, "w-web", GKE)
        assert gke["result"] == "feasible_with_config"
        assert gke["requires_config"][0]["setting"] == "BackendConfig timeoutSec"
        assert gke["requires_config"][0]["rule"].startswith("CAP-TIMEOUT-")
    fit, _ = run(inv, profile(dim("A2", "수 분", "w-web")))
    assert cell(fit, "w-web", ECS)["result"] == "infeasible"     # 설정 이름이 없으면 그대로 위반
    assert cell(fit, "w-web", EKS)["result"] == "infeasible"
    fit, _ = run(inv, profile(dim("A2", "그 이상", "w-web")))
    assert cell(fit, "w-web", GKE)["result"] == "infeasible"     # 상한이 있으면 설정으로도 "제한 없음"이 아니다


def test_cross_requirement_rule_lint():
    good = [r for r in RULES if r["id"] == "CAP-MEMSTATE-002"]
    assert good and _lint_rules(good) == []
    bad = [{**good[0], "when": {"dimension": "B1", "equals": "있음"}}]
    assert any("require가 없으면" in i for i in _lint_rules(bad))
    bad = [{**good[0], "when": {"all": [{"dimension": "B1", "equals": "있음"}, {"dimension": "Z9", "equals": "x"}]}}]
    assert any("Z9" in i for i in _lint_rules(bad))


# ---------- 토폴로지 ----------

def test_vm_compose_colocates_datastores_or_uses_managed_and_keeps_sqlite_and_baas():
    inv = inventory([workload("w-web"), workload("w-worker", "worker")],
                    [("ds-postgresql", PGU), ("svc-redis", RDU), ("ds-sqlite", SQLITE), ("ds-supabase", SUPA)])
    prof = profile(dim("A1", ["워커"], "w-worker"))
    fit, rec = run(inv, prof)
    vms = [c for c in rec["candidates"] if c["topology"] == "vm-compose"]
    colocated = {c["placement"][0]["component"]: c for c in vms if c["assignment"]["ds-postgresql"] == VMPG}
    managed = {c["placement"][0]["component"]: c for c in vms if c["assignment"]["ds-postgresql"] != VMPG}
    assert set(colocated) == set(managed) == {EC2, GCE}
    aws = colocated[EC2]
    assert aws["assignment"] == {"w-web": EC2, "w-worker": EC2, "ds-postgresql": VMPG, "svc-redis": VMRD,
                                 "ds-sqlite": SQLITE, "ds-supabase": SUPA}
    assert aws["transforms"] == [] and aws["external_scopes"] == ["ds-supabase"]
    assert [p["target"] for p in aws["placement"]] == ["aws_ec2", "aws_ec2"]
    # SQLite·Supabase 비용은 모른다 → 합 null, 아는 부분은 VM 한 대(VM 안 저장소 0)
    assert aws["cost"]["monthly_baseline_usd"] is None
    assert aws["cost"]["unknown_cost_components"] == [SQLITE, SUPA]
    assert sum(i["monthly_usd"] for i in aws["cost"]["breakdown"]) == 20.7
    assert managed[EC2]["assignment"]["ds-postgresql"] == RDS and managed[EC2]["assignment"]["svc-redis"] == ELC
    assert managed[GCE]["assignment"]["svc-redis"] == MEM
    assert sum(i["monthly_usd"] for i in managed[EC2]["cost"]["breakdown"]) == 20.7 + 20.9 + 17.5
    # 서비스형·쿠버네티스는 VM 안 저장소를 쓰지 않는다
    for c in rec["candidates"]:
        if c["topology"] != "vm-compose":
            assert VMPG not in c["assignment"].values() and VMRD not in c["assignment"].values()


def test_vm_compose_cost_is_single_vm_floor_without_datastores():
    inv = inventory([workload("w-web"), workload("w-worker", "worker"), workload("w-nginx", "reverse-proxy")])
    fit, rec = run(inv, profile(dim("A1", ["워커"], "w-worker")))
    vm = next(c for c in rec["candidates"] if c["topology"] == "vm-compose" and c["placement"][0]["component"] == GCE)
    assert vm["cost"]["monthly_baseline_usd"] == 20.64
    assert [p["scope"] for p in vm["placement"]] == ["w-nginx", "w-web", "w-worker"]
    assert not any(r["id"].endswith("/managed-data") for r in rec["rejected"])
    assert not any(c["topology"] == "vm-compose" and c["assignment"] != vm["assignment"]
                   and c["placement"][0]["component"] == GCE for c in rec["candidates"])


def test_services_picks_platform_per_workload_and_sums_costs():
    inv = inventory([workload("w-web"), workload("w-worker", "worker")], [("ds-postgresql", PGU)])
    prof = profile(dim("A1", ["웹"], "w-web"), dim("A1", ["워커"], "w-worker"))
    fit, rec = run(inv, prof)
    gcp = next(c for c in rec["candidates"] if c["topology"] == "services" and c["assignment"]["w-web"] in (REQ, INS))
    # 웹은 요청 기반(바닥 0), 워커는 상시 실행이 필요해 인스턴스 기반 + min-instances(고정 $59.9)
    assert gcp["assignment"]["w-web"] == REQ and gcp["assignment"]["w-worker"] == INS
    assert gcp["assignment"]["ds-postgresql"] == SQL
    assert gcp["cost"]["monthly_baseline_usd"] == round(0 + 59.9 + 12.21, 4)
    assert {p["scope"]: p["target"] for p in gcp["placement"]} == {"w-web": "gcp_cloud_run", "w-worker": "gcp_cloud_run"}
    aws = next(c for c in rec["candidates"] if c["topology"] == "services" and c["assignment"]["w-web"] in (LAMBDA, ECS))
    # 웹은 Lambda(바닥 0), 워커는 상시 실행 ECS(바닥 비용 1회)
    assert aws["assignment"]["w-web"] == LAMBDA and aws["assignment"]["w-worker"] == ECS
    assert aws["cost"]["monthly_baseline_usd"] == round(37.74 + 20.9, 4)


def test_services_shared_floor_is_not_double_counted():
    """ECS 바닥 비용에는 ALB가 들어 있다: 태스크가 여러 개면 레플리카 단가가 있을 때만 더하고, 없으면 모른다."""
    inv = inventory([workload("w-api", "worker"), workload("w-worker", "worker")])
    prof = profile(dim("A1", ["워커"], "w-api"), dim("A1", ["워커"], "w-worker"))
    caps = caps_all(**{INS: {"COST.monthly_pinned_usd": None}})
    fit, rec = run(inv, prof, caps)
    aws = next(c for c in rec["candidates"] if c["topology"] == "services" and c["assignment"]["w-api"] == ECS)
    assert aws["assignment"]["w-worker"] == ECS
    assert aws["cost"]["monthly_baseline_usd"] is None and aws["cost"]["unknown_cost_components"] == [ECS]
    fit, rec = run(inv, prof, caps_all(**{ECS: {"COST.per_replica_usd": 10.36}}))
    aws = next(c for c in rec["candidates"] if c["topology"] == "services" and c["assignment"]["w-api"] == ECS)
    assert aws["cost"]["monthly_baseline_usd"] == round(37.74 + 10.36, 4)


def test_services_min_replicas_pin_scale_to_zero_platform():
    inv = inventory([workload("w-web", scaling={"min": 2, "max": 5, "autoscale": True})])
    fit, rec = run(inv, profile(dim("D6", "자동 확장", "w-web")))
    gcp = next(c for c in rec["candidates"] if c["topology"] == "services" and c["assignment"]["w-web"] in (REQ, INS))
    assert gcp["assignment"]["w-web"] == REQ
    assert gcp["cost"]["monthly_baseline_usd"] == round(13.8 * 2, 4)
    assert gcp["placement"][0]["min_replicas"] == 2


def test_kubernetes_cost_adds_per_replica_or_is_null():
    inv = inventory([workload("w-web", scaling={"min": 2, "max": 4, "autoscale": True}),
                     workload("w-worker", "worker")])
    prof = profile(dim("D6", "자동 확장", "w-web"), dim("A1", ["워커"], "w-worker"))
    fit, rec = run(inv, prof)
    k8s = {c["placement"][0]["component"]: c for c in rec["candidates"] if c["topology"] == "kubernetes"}
    assert k8s[GKE]["assignment"] == {"w-web": GKE, "w-worker": GKE}
    assert k8s[GKE]["cost"]["monthly_baseline_usd"] == round(31.11 + 12.86 * 2, 4)    # 레플리카 3 = 1 + 2
    assert k8s[EKS]["cost"]["monthly_baseline_usd"] is None                          # 레플리카 단가 없음
    single = inventory([workload("w-web")])
    fit, rec = run(single, profile())
    k8s = {c["placement"][0]["component"]: c for c in rec["candidates"] if c["topology"] == "kubernetes"}
    assert k8s[EKS]["cost"]["monthly_baseline_usd"] == 140.16
    assert k8s[GKE]["cost"]["monthly_baseline_usd"] == 31.11   # 1개 고정 요구가 있어도 고정 비용을 쓰지 않는다


def test_sqlite_transform_on_services_and_kept_on_vm_and_kubernetes_with_disk():
    inv = inventory([workload("w-web")], [("ds-sqlite", SQLITE)])
    prof = profile(dim("B2", {"value": "있음", "kinds": ["sqlite"]}, "w-web", ev=EV))
    fit, rec = run(inv, prof)
    for c in rec["candidates"]:
        if c["topology"] == "services":
            assert c["transforms"] == [SQLITE_TRANSFORM] and c["assignment"]["ds-sqlite"] in (RDS, SQL)
        else:
            assert c["transforms"] == [] and c["assignment"]["ds-sqlite"] == SQLITE


# ---------- 순위·결과 ----------

def test_ranking_cheapest_known_feasible_first_across_topologies():
    inv = inventory([workload("w-web")], [("ds-postgresql", PGU)])
    fit, rec = run(inv, profile())
    first = rec["candidates"][0]
    # 서비스형 gcp(Cloud Run 0 + Cloud SQL 12.21)가 VM 안 Postgres(20.64)보다 싸다
    assert first["topology"] == "services" and first["cost"]["monthly_baseline_usd"] == 12.21
    # 데이터 저장 유형: 인증성 → 데이터 안전 → 비용 순이라 VM 안 Postgres 는 더 싸도 안전한 쪽 뒤로 간다
    assert rec["ranking"]["service_type"] == "stateful"
    for unsafe in (0, 1):
        group = [c["cost"]["monthly_baseline_usd"] for c in rec["candidates"] if c["criteria"]["data_safety"] == unsafe]
        assert group == sorted(group)
    flags = [c["criteria"]["data_safety"] for c in rec["candidates"]]
    assert flags == sorted(flags) and flags[0] == 0 and flags[-1] == 1
    assert {c["topology"] for c in rec["candidates"]} == {"vm-compose", "services", "kubernetes"}


def test_batch_only_is_not_deployable():
    inv = inventory([workload("w-cli", "batch")])
    batch = {"value": True, "reason": "사람이 실행하는 도구", "workloads": ["w-cli"], "evidence": []}
    fit, rec = run(inv, profile(dim("A1", ["일회성 실행"], "w-cli"), batch_only=batch))
    assert rec["outcome"] == "not_deployable" and rec["candidates"] == [] and rec["recommended"] is None
    assert rec["outcome_detail"]["message"] == "사람이 실행하는 도구"
    rec["outcome"] = "recommended"
    assert any("batch_only" in i for i in check_s4(rec, fit, inv, profile(batch_only=batch), {}))


def test_check_s4_flags_mixed_placement_for_single_cluster_topology():
    inv = inventory([workload("w-web"), workload("w-worker", "worker")])
    fit, rec = run(inv, profile(dim("A1", ["워커"], "w-worker")))
    k8s = next(c for c in rec["candidates"] if c["topology"] == "kubernetes")
    k8s["placement"][1]["component"] = EKS if k8s["placement"][0]["component"] == GKE else GKE
    catalog = {c["id"]: {} for c in caps_all()}
    issues = check_s4(rec, fit, inv, profile(), catalog)
    assert any("several compute components" in i for i in issues)
    assert any("not in assignment" in i for i in issues)


# ---------- 유도 값(정의상/유도)·리버스 프록시·Lambda 레플리카 ----------

def derived(value, reasoning="한 단계 유도"):
    return {"value": value, "source": {"basis": "derived", "reasoning": reasoning,
                                       "from": {"doc": "post-response-work.md", "line": 74,
                                                "url": "https://example.com/premise", "quote": "premise quote"}}}


def with_derived(caps, cid, key, value, reasoning="한 단계 유도"):
    next(c for c in caps if c["id"] == cid)["capabilities"][key] = derived(value, reasoning)
    return caps


def test_derived_pass_is_explained_in_fit_and_candidate():
    caps = with_derived(caps_all(), ECS, "CP.cpu_after_response", True, "태스크 단위 CPU라 응답 뒤에도 쓴다")
    inv = inventory([workload("w-web")])
    fit, rec = run(inv, profile(dim("A4", "있음", "w-web")), caps)
    ecs = cell(fit, "w-web", ECS)
    assert ecs["result"] == "feasible"
    [p] = ecs["derived_passes"]
    assert p["rule"] == "CAP-BGWORK-001" and p["capability_key"] == "CP.cpu_after_response" and p["actual"] is True
    assert p["source"] == {"ref": "https://example.com/premise", "quote": "premise quote", "basis": "derived",
                           "reasoning": "태스크 단위 CPU라 응답 뒤에도 쓴다"}
    assert "정의상/유도: 태스크 단위 CPU라 응답 뒤에도 쓴다" in p["message"]
    assert "docs/research/post-response-work.md:74" in p["message"]
    assert cell(fit, "w-web", EKS)["derived_passes"] == []          # 공식 값으로 통과하면 설명 없음
    aws = [c for c in rec["candidates"] if c["assignment"].get("w-web") == ECS]
    for cand in aws:
        assert any(f["component"] == ECS and f["source"]["basis"] == "derived" for f in cand["derived_facts"])


def test_derived_violation_and_config_show_reasoning():
    caps = with_derived(caps_all(), LAMBDA, "CP.cpu_after_response", False, "호출 뒤 동결된다")
    fit, _ = run(inventory([workload("w-web")]), profile(dim("A4", "있음", "w-web")), caps)
    [v] = cell(fit, "w-web", LAMBDA)["violations"]
    assert v["source"]["basis"] == "derived" and v["source"]["reasoning"] == "호출 뒤 동결된다"
    assert "(정의상/유도: 호출 뒤 동결된다)" in v["message"]
    # 실패한 값이 유도 값이고 설정으로 풀리면 why에 적는다
    caps = with_derived(caps_all(**{REQ: {"CP.cpu_after_response_config": "instance billing"}}), REQ,
                        "CP.cpu_after_response", False, "요청 밖 CPU 없음")
    fit, _ = run(inventory([workload("w-web")]), profile(dim("A4", "있음", "w-web")), caps)
    [req] = cell(fit, "w-web", REQ)["requires_config"]
    assert "정의상/유도: 요청 밖 CPU 없음" in req["why"]


def test_timeout_rules_pass_without_platform_request_timeout():
    inv = inventory([workload("w-web")])
    for a2 in ("수십 초", "수 분", "그 이상"):
        fit, _ = run(inv, profile(dim("A2", a2, "w-web")))
        assert cell(fit, "w-web", EC2)["result"] == "feasible", a2
        assert cell(fit, "w-web", GCE)["result"] == "feasible", a2
    fit, _ = run(inv, profile(dim("A2", "그 이상", "w-web")))
    assert cell(fit, "w-web", REQ)["result"] == "infeasible"


def test_reverse_proxy_is_not_placed_on_lambda():
    inv = inventory([workload("w-web"), workload("w-nginx", "reverse-proxy")])
    caps = with_derived(caps_all(), LAMBDA, "CP.runs_long_lived_server", False, "환경당 요청 하나, 호출 뒤 동결")
    fit, rec = run(inv, profile(), caps)
    lam = cell(fit, "w-nginx", LAMBDA)
    assert lam["result"] == "infeasible" and lam["violations"][0]["rule"] == "CAP-PROXY-001"
    assert "정의상/유도: 환경당 요청 하나, 호출 뒤 동결" in lam["violations"][0]["message"]
    assert cell(fit, "w-web", LAMBDA)["result"] == "feasible"        # 앱 워크로드에는 걸리지 않는다
    for cand in rec["candidates"]:
        assert cand["assignment"]["w-nginx"] != LAMBDA
    aws = next(c for c in rec["candidates"] if c["topology"] == "services" and c["assignment"]["w-web"] in (LAMBDA, ECS))
    assert aws["assignment"]["w-nginx"] == ECS


def test_lambda_cost_is_not_multiplied_by_min_replicas():
    inv = inventory([workload("w-web", scaling={"min": 3, "max": 3, "autoscale": False})])
    caps = caps_all(**{LAMBDA: {"COST.monthly_floor_usd": 5, "COST.per_replica_usd": 2, "CP.scale_to_zero": True,
                                "COST.monthly_pinned_usd": 7}})
    fit, rec = run(inv, profile(dim("D6", "고정 다중", "w-web")), caps)
    aws = next(c for c in rec["candidates"] if c["topology"] == "services" and c["assignment"]["w-web"] == LAMBDA)
    assert aws["cost"]["monthly_baseline_usd"] == 5
    assert [i["item"] for i in aws["cost"]["breakdown"]] == ["monthly_floor"]
