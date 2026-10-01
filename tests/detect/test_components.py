from infrafit.detect.artifacts import ParsedArtifact
from infrafit.detect.components import find_unmapped, map_components
from infrafit.detect.manifests import parse_manifests
from infrafit.detect.signatures import Match
from infrafit.detect.workloads import WorkloadInfo
from infrafit.repo import open_snapshot

EV = ({"path": "db.py", "line": 1, "snippet": "x"},)


def _w(wid, kind="web", source="code", app_dir=""):
    return WorkloadInfo(id=wid, kind=kind, name=wid[2:], entrypoint={"path": "k8s/a.yaml", "line": 3, "snippet": "x"},
                        status="confirmed", source=source, app_dir=app_dir)


def test_scope_ids_and_merge(tmp_path):
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    matches = [
        Match("A", "ds:local/sqlite/wal", "primary-db", "confirmed", EV),
        Match("B", "fs:local/container-disk/default", "file-storage", "candidate", EV),
        Match("C", "ds:supabase/postgres/unspecified-plan", "primary-db", "confirmed", EV),
        Match("D", "ca:local/process-memory/default", "session", "candidate", EV),
        Match("E", "ca:local/process-memory/default", "session", "confirmed", EV),
    ]
    ds, comps, compute = map_components(snap, matches, [_w("w-web"), _w("w-static", "static-frontend")], [])
    assert [(d["id"], d["role"], d["used_by"]) for d in ds] == [
        ("ds-sqlite", "primary-db", ["w-web"]),
        ("ds-supabase-postgres", "primary-db", ["w-web"]),
        ("svc-container-disk", "file-storage", ["w-web"]),
        ("svc-process-memory", "session", ["w-web"]),
    ]
    by_scope = {c["scope"]: c for c in comps}
    assert by_scope["svc-process-memory"]["status"] == "confirmed"
    assert by_scope["w-web"]["component"] == "unmapped"
    assert by_scope["w-web"]["label"] == "no deployment config"
    assert compute == {"w-web": "unmapped", "w-static": "unmapped"}


def test_hosting_refinement_and_k8s_compute(tmp_path):
    (tmp_path / "main.tf").write_text("x\n")
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    tf = ParsedArtifact("terraform", "main.tf", True, objects=[
        ("aws_db_instance", "main", {"engine": "postgres", "multi_az": True}),
        ("aws_eks_cluster", "main", {}),
    ])
    matches = [Match("P", "ds:unspecified/postgresql/default", "primary-db", "confirmed", EV)]
    ds, comps, compute = map_components(snap, matches, [_w("w-api", source="k8s")], [tf])
    by_scope = {c["scope"]: c for c in comps}
    assert ds[0]["id"] == "ds-postgresql"
    assert by_scope["ds-postgresql"]["component"] == "ds:aws/rds-postgres/multi-az-instance"
    assert any(e["path"] == "main.tf" for e in by_scope["ds-postgresql"]["evidence"])
    assert compute["w-api"] == "cp:aws/eks/unspecified"


def test_used_by_follows_code_roots(tmp_path):
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    ev = ({"path": "apps/billing/requirements.txt", "line": 5, "snippet": "x"},
          {"path": "apps/catalog/requirements.txt", "line": 5, "snippet": "x"})
    ws = [
        WorkloadInfo(id="w-billing", kind="web", name="billing", entrypoint=EV[0], status="confirmed",
                     source="k8s", code_root="apps/billing"),
        WorkloadInfo(id="w-catalog-sync", kind="worker", name="catalog-sync", entrypoint=EV[0],
                     status="confirmed", source="k8s", code_root="apps/catalog"),
        WorkloadInfo(id="w-gateway", kind="web", name="gateway", entrypoint=EV[0], status="confirmed",
                     source="k8s", code_root="web"),
        WorkloadInfo(id="w-unknown", kind="web", name="unknown", entrypoint=EV[0], status="confirmed",
                     source="k8s", code_root=None),
    ]
    ds, _, _ = map_components(snap, [Match("P", "ds:unspecified/postgresql/default", "primary-db", "confirmed", ev)],
                              ws, [])
    assert ds[0]["used_by"] == ["w-billing", "w-catalog-sync"]


def test_platform_config_wins(tmp_path):
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    vercel = ParsedArtifact("platform-config", "vercel.json", True)
    _, comps, compute = map_components(snap, [], [_w("w-web")], [vercel])
    assert compute["w-web"] == "cp:vercel/functions/unspecified-plan"
    assert comps[0]["evidence"] == [{"path": "vercel.json", "line": None, "snippet": "vercel.json"}]


def test_malformed_terraform_and_entrypoint_do_not_crash(tmp_path):
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    tf = ParsedArtifact("terraform", "main.tf", True, objects=[
        ("aws_db_instance", "a", "oops"),
        ("google_sql_database_instance", "b", {"database_version": ["x"], "settings": "bad"}),
        ("aws_db_instance", "c", {"engine": ["postgres"], "multi_az": [1]}),
        "garbage",
        ("only", "two"),
    ])
    w = WorkloadInfo(id="w-k", kind="web", name="k", entrypoint={}, status="confirmed", source="k8s")
    matches = [Match("P", "ds:unspecified/postgresql/default", "primary-db", "confirmed", EV)]
    ds, comps, compute = map_components(snap, matches, [w], [tf])
    assert ds[0]["id"] == "ds-postgresql"
    assert compute["w-k"] == "cp:k8s/deployment/unspecified-cluster"


def test_platform_config_picks_first_by_path(tmp_path):
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    arts = [ParsedArtifact("platform-config", "z/fly.toml", True),
            ParsedArtifact("platform-config", "a/vercel.json", True)]
    _, _, compute = map_components(snap, [], [_w("w-web")], arts)
    assert compute["w-web"] == "cp:vercel/functions/unspecified-plan"


def _unmapped_snap(tmp_path, deps):
    (tmp_path / "package.json").write_text(
        '{\n  "dependencies": {\n' + ",\n".join(f'    "{d}": "1.0.0"' for d in deps) + "\n  }\n}\n")
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    return snap, parse_manifests(snap)


def test_find_unmapped_reports_watchlist_dep(tmp_path):
    snap, mf = _unmapped_snap(tmp_path, ["express", "kafkajs"])
    out = find_unmapped(snap, mf)
    assert [o["label"] for o in out] == ["kafkajs"]
    ev = out[0]["evidence"][0]
    assert ev["path"] == "package.json" and ev["line"] == 4


def test_find_unmapped_ignores_non_watchlist(tmp_path):
    snap, mf = _unmapped_snap(tmp_path, ["express"])
    assert find_unmapped(snap, mf) == []


def test_find_unmapped_skips_signature_known_dep(tmp_path, monkeypatch):
    snap, mf = _unmapped_snap(tmp_path, ["redis"])
    monkeypatch.setattr("infrafit.detect.components.kb.watchlist", lambda: ("redis",))
    assert find_unmapped(snap, mf) == []
