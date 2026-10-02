"""계획 2b Task B: 워크로드 확장 요구(S1 scaling → S2 D2·D3·D6), Supabase 접속 URL, batch_only."""

import json

import pytest

from infrafit import kb
from infrafit.consistency import check_run
from infrafit.detect.artifacts import kustomize_binary
from infrafit.pipeline import analyze
from infrafit.schema import validate

MAIN = "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/h')\ndef h():\n    return 'ok'\n"
DEPLOY = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
spec:
  replicas: {replicas}
  template:
    spec:
      containers:
        - name: {name}
          image: acme/{name}:1
"""
HPA = """apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {name}-hpa
spec:
  scaleTargetRef: {{apiVersion: apps/v1, kind: Deployment, name: {name}}}
  minReplicas: {lo}
  maxReplicas: {hi}
"""


def _write(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def _run(tmp_path, files: dict[str, str]):
    repo = tmp_path / "repo"
    for rel, text in files.items():
        _write(repo, rel, text)
    ctx = analyze(str(repo), tmp_path / "out", until="S2", run_id="r")
    assert check_run(ctx.out_dir) == []
    inv = json.loads((ctx.out_dir / "inventory.json").read_text())
    profile = json.loads((ctx.out_dir / "profile.json").read_text())
    validate("Inventory", inv)
    validate("Profile", profile)
    return inv, profile


def _w(inv, wid):
    return next(w for w in inv["workloads"] if w["id"] == wid)


def _dim(profile, scope, dim):
    rows = [r for r in profile["dimensions"] if r["scope"] == scope and r["dimension"] == dim]
    assert len(rows) == 1, (scope, dim, profile["dimensions"])
    return rows[0]


def _api(**extra):
    return {"api/requirements.txt": "fastapi==0.115\n", "api/main.py": MAIN,
            "api/Dockerfile": "FROM python:3.12\nCMD uvicorn main:app\n", **extra}


def test_hpa_in_separate_file_overrides_replicas(tmp_path):
    inv, p = _run(tmp_path, _api(**{"k8s/api.yaml": DEPLOY.format(name="api", replicas=1),
                                    "k8s/hpa.yaml": HPA.format(name="api", lo=2, hi=8)}))
    s = _w(inv, "w-api")["scaling"]
    assert (s["min"], s["max"], s["autoscale"]) == (2, 8, True)
    assert [(e["path"], e["snippet"]) for e in s["evidence"]] == [("k8s/hpa.yaml", "minReplicas: 2")]
    d6, d2 = _dim(p, "w-api", "D6"), _dim(p, "w-api", "D2")
    assert (d6["value"], d6["source"]) == ("자동 확장", "detector")
    assert (d2["value"], d2["source"], d2["confidence"]) == ("중간", "detector", "medium")
    assert _dim(p, "w-app", "D2")["value"] == "중간" and _dim(p, "w-app", "D2")["source"] == "detector"
    assert "D2" not in {a["key"] for a in p["assumptions"]}


def test_fixed_replicas_and_single_replica(tmp_path):
    inv, p = _run(tmp_path, _api(**{"k8s/api.yaml": DEPLOY.format(name="api", replicas=3)}))
    s = _w(inv, "w-api")["scaling"]
    assert (s["min"], s["max"], s["autoscale"]) == (3, 3, False)
    assert s["evidence"][0]["snippet"] == "replicas: 3"
    assert _dim(p, "w-api", "D6")["value"] == "고정 다중" and _dim(p, "w-api", "D2")["value"] == "중간"

    inv, p = _run(tmp_path / "b", _api(**{"k8s/api.yaml": DEPLOY.format(name="api", replicas=1)}))
    assert _w(inv, "w-api")["scaling"]["min"] == 1
    d2 = _dim(p, "w-api", "D2")
    assert (d2["value"], d2["source"], d2["assumption_key"]) == ("낮음", "assumption", "D2")
    assert _dim(p, "w-api", "D6")["value"] == "단일 인스턴스" and _dim(p, "w-api", "D6")["evidence"]


def test_keda_scaled_object_defaults_and_worker_scope(tmp_path):
    keda = ("apiVersion: keda.sh/v1alpha1\nkind: ScaledObject\nmetadata:\n  name: jobs\nspec:\n"
            "  scaleTargetRef:\n    name: jobs-worker\n  maxReplicaCount: 5\n")
    inv, p = _run(tmp_path, _api(**{"k8s/api.yaml": DEPLOY.format(name="api", replicas=1),
                                    "k8s/worker.yaml": DEPLOY.format(name="jobs-worker", replicas=1),
                                    "k8s/keda.yaml": keda}))
    s = _w(inv, "w-jobs-worker")["scaling"]
    assert (s["min"], s["max"], s["autoscale"]) == (0, 5, True)
    assert _dim(p, "w-jobs-worker", "D6")["value"] == "자동 확장"
    assert _dim(p, "w-jobs-worker", "D2")["value"] == "중간"
    assert _dim(p, "w-api", "D6")["value"] == "단일 인스턴스"
    # 앱 집계: 자동 확장 > 단일 인스턴스, D2 중간
    assert _dim(p, "w-app", "D6")["value"] == "자동 확장" and _dim(p, "w-app", "D2")["value"] == "중간"


@pytest.mark.skipif(kustomize_binary() is None, reason="kustomize·kubectl 없음")
def test_kustomize_overlays_take_max_across_environments(tmp_path):
    patch = "apiVersion: apps/v1\nkind: Deployment\nmetadata: {name: api}\nspec:\n  replicas: 4\n"
    inv, p = _run(tmp_path, _api(**{
        "k8s/base/kustomization.yaml": "resources: [api.yaml]\n",
        "k8s/base/api.yaml": DEPLOY.format(name="api", replicas=1),
        "k8s/overlays/dev/kustomization.yaml": "resources: [../../base]\n",
        "k8s/overlays/prod/kustomization.yaml": "resources: [../../base]\npatches: [{path: patch.yaml}]\n",
        "k8s/overlays/prod/patch.yaml": patch}))
    s = _w(inv, "w-api")["scaling"]
    assert (s["min"], s["max"], s["autoscale"]) == (4, 4, False)
    assert {"path": "k8s/overlays/prod/kustomization.yaml", "line": None,
            "snippet": "kustomize build: Deployment/api replicas: 4"} in s["evidence"]
    assert _dim(p, "w-api", "D6")["value"] == "고정 다중"


def test_compose_deploy_replicas_max_across_files(tmp_path):
    base = "services:\n  web:\n    build: ./api\n    deploy:\n      replicas: 2\n"
    prod = "services:\n  web:\n    build: ./api\n    deploy:\n      replicas: 5\n"
    inv, p = _run(tmp_path, _api(**{"docker-compose.yml": base, "docker-compose.prod.yml": prod}))
    s = _w(inv, "w-web")["scaling"]
    assert (s["min"], s["max"], s["autoscale"]) == (5, 5, False)
    assert [(e["path"], e["line"]) for e in s["evidence"]] == [("docker-compose.prod.yml", 5), ("docker-compose.yml", 5)]
    assert _dim(p, "w-web", "D6")["value"] == "고정 다중"


def test_no_scaling_config_keeps_assumptions(tmp_path):
    inv, p = _run(tmp_path, _api())
    assert all("scaling" not in w for w in inv["workloads"])
    d2 = _dim(p, "w-app", "D2")
    assert (d2["value"], d2["source"]) == ("낮음", "assumption")
    assert _dim(p, "w-app", "D3")["value"] == "없음" and _dim(p, "w-app", "D3")["source"] == "assumption"
    assert _dim(p, "w-app", "D6")["value"] == "단일 인스턴스"
    assert p["batch_only"] == {"value": False, "workloads": [], "evidence": []}


K6_SPIKE = "// 재난 상황: 30초 만에 20배 폭증\nimport http from 'k6/http';\nexport default function () { http.get('x'); }\n"
K6_PLAIN = "import http from 'k6/http';\nexport default function () { http.get('x'); }\n"
LOCUST = "from locust import HttpUser, task\n\nclass U(HttpUser):\n    @task\n    def t(self):\n        self.client.get('/')\n"
ARTILLERY = "config:\n  target: http://localhost:8000\n  phases:\n    - duration: 60\n      arrivalRate: 5\n" \
            "scenarios:\n  - flow:\n      - get: {url: /}\n"


def test_load_test_that_says_spike_sets_d3(tmp_path):
    inv, p = _run(tmp_path, _api(**{"loadtest/spike.js": K6_SPIKE}))
    (wid,) = [w["id"] for w in inv["workloads"] if w["kind"] == "web"]
    s = _w(inv, wid)["scaling"]
    assert (s["min"], s["max"], s["autoscale"], s["evidence"]) == (1, 1, False, [])
    assert [(e["path"], e["line"]) for e in s["load_tests"]] == [("loadtest/spike.js", 2)]
    d3 = _dim(p, wid, "D3")
    assert (d3["value"], d3["source"], d3["evidence"][0]["line"]) == ("예고 없는 폭증", "detector", 1)
    # 부하 테스트만으로는 D2를 바꾸지 않는다
    assert _dim(p, wid, "D2")["source"] == "assumption"


def test_plain_load_tests_are_only_supporting_evidence(tmp_path):
    inv, p = _run(tmp_path, _api(**{"perf/k6.js": K6_PLAIN, "perf/locustfile.py": LOCUST,
                                    "perf/artillery.yml": ARTILLERY,
                                    "k8s/api.yaml": DEPLOY.format(name="api", replicas=2)}))
    s = _w(inv, "w-api")["scaling"]
    assert [e["path"] for e in s["load_tests"]] == ["perf/artillery.yml", "perf/k6.js", "perf/locustfile.py"]
    assert _dim(p, "w-api", "D3")["source"] == "assumption"
    d2 = _dim(p, "w-api", "D2")
    assert d2["value"] == "중간" and {e["path"] for e in d2["evidence"]} >= {"k8s/api.yaml", "perf/k6.js"}


def test_profile_scaling_vocabulary_is_consistent():
    cfg = kb.profile_detectors()
    dims, sc = cfg["dimensions"], cfg["scaling"]
    assert set(sc["D6"].values()) == set(dims["D6"]["values"])
    assert sc["D2"]["value"] in dims["D2"]["values"]
    for rule in sc["load_tests"]:
        assert rule["value"] in dims[rule["dimension"]]["values"]


PG_DEP = {"api/requirements.txt": "fastapi==0.115\npsycopg2-binary==2.9\n"}


def _datastores(inv):
    comps = {c["scope"]: c["component"] for c in inv["current_components"]}
    return {d["id"]: comps[d["id"]] for d in inv["datastores"]}


def test_supabase_connection_url_replaces_generic_postgres(tmp_path):
    env = "DATABASE_URL=postgresql://postgres:pw@db.abcdefghijklmnop.supabase.co:5432/postgres\n"
    inv, _ = _run(tmp_path, _api(**PG_DEP, **{"api/.env.example": env}))
    assert _datastores(inv) == {"ds-supabase-postgres": "ds:supabase/postgres/unspecified-plan"}
    ds = inv["datastores"][0]
    assert ds["status"] == "confirmed" and {e["path"] for e in ds["evidence"]} >= {"api/.env.example",
                                                                                  "api/requirements.txt"}


def test_supabase_pooler_host_and_env_name(tmp_path):
    code = MAIN + "import os\nDB = os.environ['SUPABASE_DB_URL']\n"
    inv, _ = _run(tmp_path, _api(**PG_DEP, **{"api/main.py": code}))
    assert _datastores(inv) == {"ds-supabase-postgres": "ds:supabase/postgres/unspecified-plan"}
    cfg = "db:\n  url: postgres://postgres.abc:pw@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres\n"
    inv, _ = _run(tmp_path / "b", _api(**{"api/config.yaml": cfg}))
    assert _datastores(inv) == {"ds-supabase-postgres": "ds:supabase/postgres/unspecified-plan"}


def test_supabase_rest_url_alone_or_compose_postgres_is_not_absorbed(tmp_path):
    # REST URL만으로는 DB 사용 근거가 아니다
    inv, _ = _run(tmp_path, _api(**PG_DEP, **{"api/.env.example": "SUPABASE_URL=https://abcdefghijkl.supabase.co\n"
                                               "DATABASE_URL=postgresql://u:p@localhost/db\n"}))
    assert _datastores(inv) == {"ds-postgresql": "ds:unspecified/postgresql/default"}
    # compose가 Postgres 컨테이너를 띄우면 별개 저장소일 수 있어 합치지 않는다
    compose = "services:\n  api:\n    build: ./api\n    depends_on: [db]\n  db:\n    image: postgres:16\n"
    inv, _ = _run(tmp_path / "b", _api(**PG_DEP, **{"docker-compose.yml": compose,
                                                   "api/.env.example": "SUPABASE_DB_URL=\n"}))
    assert set(_datastores(inv)) == {"ds-postgresql", "ds-supabase-postgres"}


def test_batch_only_repo_is_flagged(tmp_path):
    cli = 'import sys\n\n\ndef main(): ...\n\n\nif __name__ == "__main__":\n    main()\n'
    inv, p = _run(tmp_path, {"tool/convert.py": cli})
    assert [w["kind"] for w in inv["workloads"]] == ["batch"]
    b = p["batch_only"]
    assert b["value"] is True and b["workloads"] == ["w-convert"] and "사람이 실행하는 도구" in b["reason"]
    assert b["evidence"] == [inv["workloads"][0]["entrypoint"]]
    assert _dim(p, "w-app", "A1")["value"] == ["일회성 실행"]


def test_consistency_flags_bad_scaling_and_batch_only():
    from infrafit.consistency import check_s1, check_s2
    w = {"id": "w-a", "kind": "web", "name": "a", "status": "confirmed",
         "entrypoint": {"path": "a", "line": None, "snippet": "a"},
         "scaling": {"min": 3, "max": 2, "autoscale": False, "evidence": []}}
    inv = {"workloads": [w], "endpoints": [], "datastores": [], "request_paths": [], "current_components": []}
    assert "workload w-a: scaling min 3 > max 2" in check_s1(inv, None)
    profile = {"dimensions": [], "assumptions": [], "llm_used": False,
               "batch_only": {"value": True, "workloads": ["w-x"], "evidence": []}}
    assert "batch_only: unknown workload w-x" in check_s2(profile, inv, None)
