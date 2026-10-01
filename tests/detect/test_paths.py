from infrafit.detect.artifacts import ParsedArtifact
from infrafit.detect.paths import app_server, build_paths
from infrafit.detect.workloads import WorkloadInfo
from infrafit.repo import open_snapshot


def _w(wid, command="", kind="web", source="k8s"):
    return WorkloadInfo(id=wid, kind=kind, name=wid[2:], entrypoint={"path": "x", "line": None, "snippet": "x"},
                        status="confirmed", source=source, command=command,
                        code_root="" if source == "code" else None)


def test_app_server_parsing():
    assert app_server("uvicorn main:app --timeout-keep-alive 75") == ("nw:app/uvicorn/default", {"timeout_keep_alive": 75})
    assert app_server("gunicorn -w 4 --keep-alive 5 app:app") == ("nw:app/gunicorn/default", {"keepalive": 5})
    assert app_server("flask run --host=0.0.0.0") == ("nw:app/flask-dev/default", {})
    assert app_server("node index.js") == ("nw:app/node-http/default", {})
    assert app_server("python -m board.worker") is None


def test_ingress_and_app_server_hops(tmp_path):
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    ingress = {"apiVersion": "networking.k8s.io/v1", "kind": "Ingress",
               "metadata": {"name": "web", "annotations": {
                   "alb.ingress.kubernetes.io/load-balancer-attributes": "idle_timeout.timeout_seconds=120"}},
               "spec": {"ingressClassName": "alb",
                        "rules": [{"http": {"paths": [{"backend": {"service": {"name": "api"}}}]}}]}}
    k8s = ParsedArtifact("k8s", "k8s/ingress.yaml", True, objects=[ingress])
    paths = build_paths(snap, [_w("w-api", "uvicorn main:app"), _w("w-worker", kind="worker")], [k8s],
                        {"w-api": "cp:k8s/deployment/unspecified-cluster"})
    assert [p["id"] for p in paths] == ["path-api"]
    hops = paths[0]["hops"]
    assert [(h["order"], h["kind"], h["component"]) for h in hops] == [
        (0, "load-balancer", "nw:aws/alb/default"), (1, "app-server", "nw:app/uvicorn/default")]
    assert hops[0]["settings"] == [{"key": "idle_timeout", "value": 120, "defaulted": False}]
    assert hops[1]["settings"][0]["defaulted"] is True


def test_managed_runtime_skips_app_server(tmp_path):
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    vercel = ParsedArtifact("platform-config", "vercel.json", True)
    paths = build_paths(snap, [_w("w-web", "next start", source="code")], [vercel],
                        {"w-web": "cp:vercel/functions/unspecified-plan"})
    assert [(h["kind"], h["component"]) for h in paths[0]["hops"]] == [("edge-proxy", "nw:vercel/edge-proxy/default")]


def test_kustomize_build_ingress_evidence_points_to_real_file(tmp_path):
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    ingress = {"kind": "Ingress", "metadata": {"name": "web"},
               "spec": {"ingressClassName": "nginx",
                        "defaultBackend": {"service": {"name": "api"}}}}
    built = ParsedArtifact("k8s", "deploy/kustomization.yaml#build", True, objects=[ingress])
    paths = build_paths(snap, [_w("w-api")], [built], {})
    hop = paths[0]["hops"][0]
    assert hop["component"] == "nw:k8s/ingress-nginx/default"
    assert hop["evidence"][0]["path"] == "deploy/kustomization.yaml"
    assert hop["evidence"][0]["line"] is None


def test_malformed_inputs_do_not_crash(tmp_path):
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    bad = ParsedArtifact("k8s", "k8s/bad.yaml", True, objects=[
        "str", None, 3, [],
        {"kind": "Ingress", "metadata": "x", "spec": ["y"]},
        {"kind": "Ingress", "metadata": {"annotations": ["a"]},
         "spec": {"ingressClassName": 5, "rules": "r", "defaultBackend": {"service": "s"}}}])
    paths = build_paths(snap, [_w("w-api", command=None)], [bad], {})
    assert paths[0]["hops"] == []
    assert app_server(None) is None
