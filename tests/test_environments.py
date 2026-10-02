from infrafit.consistency import check_s1
from infrafit.detect.artifacts import ParsedArtifact
from infrafit.detect.environments import Environment, detect_environments, env_slug, workload_in
from infrafit.detect.paths import build_paths
from infrafit.detect.workloads import WorkloadInfo
from infrafit.repo import open_snapshot

EV = {"path": "app.py", "line": 1, "snippet": "x"}


def _w(wid, command="uvicorn main:app"):
    return WorkloadInfo(id=wid, kind="web", name=wid[2:], entrypoint=EV, status="confirmed",
                        source="k8s", command=command)


def _deploy(name):
    return {"kind": "Deployment", "metadata": {"name": name}}


def _ingress(cls, backend):
    return {"kind": "Ingress", "metadata": {"name": "i"},
            "spec": {"ingressClassName": cls, "defaultBackend": {"service": {"name": backend}}}}


def _build(leaf, objects, parsed=True):
    return ParsedArtifact("k8s", f"{leaf}/kustomization.yaml#build", parsed, objects=objects)


def _snap(tmp_path):
    return open_snapshot(str(tmp_path), tmp_path / "_w")


def test_environment_names_and_slug():
    arts = [_build("k8s/overlays/aws/prod", []), _build("deploy/staging", []), _build("k8s/overlays/dev", [])]
    envs = detect_environments(arts, [])
    assert [e.name for e in envs] == ["aws/prod", "deploy/staging", "dev"]
    assert envs[0].source == "k8s/overlays/aws/prod/kustomization.yaml"
    assert env_slug("aws/prod") == "aws-prod"


def test_two_overlays_each_use_own_ingress(tmp_path):
    arts = [_build("k8s/overlays/a", [_deploy("api"), _ingress("alb", "api")]),
            _build("k8s/overlays/b", [_deploy("api"), _ingress("nginx", "api")])]
    envs = detect_environments(arts, [])
    paths = build_paths(_snap(tmp_path), [_w("w-api")], arts, {}, envs)
    assert [(p["id"], p["environment"]) for p in paths] == [("path-api.a", "a"), ("path-api.b", "b")]
    assert [p["hops"][0]["component"] for p in paths] == ["nw:aws/alb/default", "nw:k8s/ingress-nginx/default"]


def test_workload_only_in_one_overlay(tmp_path):
    arts = [_build("k8s/overlays/a", [_deploy("api")]), _build("k8s/overlays/b", [_deploy("other")])]
    envs = detect_environments(arts, [])
    paths = build_paths(_snap(tmp_path), [_w("w-api")], arts, {}, envs)
    assert [p["environment"] for p in paths] == ["a"]


def test_workload_in_matches_label():
    env = Environment("a", "a/kustomization.yaml", True, [
        {"kind": "Deployment", "metadata": {"name": "x", "labels": {"app.kubernetes.io/name": "api"}}},
        {"kind": "Service", "metadata": {"name": "web"}}, "junk"])
    assert workload_in(env, _w("w-api")) and not workload_in(env, _w("w-web"))


def test_no_overlays_gives_null_environment(tmp_path):
    k8s = ParsedArtifact("k8s", "k8s/ing.yaml", True, objects=[_ingress("alb", "api")])
    assert detect_environments([k8s], []) == []
    paths = build_paths(_snap(tmp_path), [_w("w-api")], [k8s], {}, [])
    assert paths[0]["id"] == "path-api" and paths[0]["environment"] is None
    assert paths[0]["hops"][0]["component"] == "nw:aws/alb/default"


def test_render_failure_listed_but_no_path(tmp_path):
    arts = [_build("k8s/overlays/bad", [], parsed=False)]
    envs = detect_environments(arts, [])
    assert [(e.name, e.rendered, e.objects) for e in envs] == [("bad", False, [])]
    assert envs[0].to_dict(_snap(tmp_path))["rendered"] is False
    paths = build_paths(_snap(tmp_path), [_w("w-api")], arts, {}, envs)
    assert [p["environment"] for p in paths] == [None]


def _inv(env="prod", pid="path-web.prod"):
    return {
        "workloads": [{"id": "w-web", "kind": "web", "entrypoint": EV, "status": "confirmed"}],
        "endpoints": [], "datastores": [], "current_components": [],
        "environments": [{"name": "prod", "rendered": True, "source": EV}],
        "request_paths": [{"id": pid, "workload": "w-web", "environment": env, "hops": []}],
        "existing_artifacts": [], "unmapped": [],
    }


def test_consistency_environment_rules():
    assert check_s1(_inv(), None) == []
    assert any("does not match" in i for i in check_s1(_inv(pid="path-web"), None))
    assert any("unknown environment" in i for i in check_s1(_inv(env="nope", pid="path-web.nope"), None))
    inv = _inv()
    inv["environments"].append(dict(inv["environments"][0]))
    assert any("duplicate environment" in i for i in check_s1(inv, None))
    assert check_s1(_inv(env=None, pid="path-web"), None) == []


def test_consistency_exposure_environment_rules():
    def inv(*exposure):
        i = _inv()
        i["endpoints"] = [{"id": "ep-web-001", "workload": "w-web", "method": "GET", "route": "/", "handler": EV,
                           "status": "confirmed", "exposure": list(exposure)}]
        return i
    ok = {"environment": "prod", "value": "routed"}
    assert check_s1(inv(ok, {"environment": None, "value": "not-routed"}), None) == []
    assert any("unknown environment" in i for i in check_s1(inv({"environment": "x", "value": "routed"}), None))
    assert any("duplicate exposure" in i for i in check_s1(inv(ok, dict(ok)), None))
