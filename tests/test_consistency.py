from infrafit.consistency import check_s1

EV = {"path": "app.py", "line": 1, "snippet": "x"}


def _inv():
    return {
        "workloads": [{"id": "w-web", "kind": "web", "entrypoint": EV, "status": "confirmed"}],
        "endpoints": [{"id": "ep-web-001", "workload": "w-web", "method": "GET", "route": "/", "handler": EV, "status": "confirmed"}],
        "datastores": [{"id": "ds-sqlite", "role": "primary-db", "used_by": ["w-web"], "status": "confirmed"}],
        "current_components": [{"scope": "ds-sqlite", "component": "ds:local/sqlite/default", "evidence": [EV], "status": "confirmed"}],
        "request_paths": [{"id": "path-web", "workload": "w-web", "hops": [
            {"order": 0, "kind": "app-server", "component": "nw:app/uvicorn/default", "settings": []}]}],
        "existing_artifacts": [], "unmapped": [],
    }


def test_clean_inventory_has_no_issues(tmp_path):
    (tmp_path / "app.py").write_text("x\n")
    assert check_s1(_inv(), tmp_path) == []


def test_detects_broken_references(tmp_path):
    inv = _inv()
    inv["endpoints"][0]["workload"] = "w-nope"
    inv["current_components"][0]["component"] = "ds:made/up/thing"
    inv["request_paths"][0]["id"] = "path-other"
    inv["request_paths"][0]["hops"][0]["order"] = 3
    inv["workloads"].append(dict(inv["workloads"][0]))
    issues = check_s1(inv, None)
    assert any("duplicate" in i for i in issues)
    assert any("w-nope" in i for i in issues)
    assert any("ds:made/up/thing" in i for i in issues)
    assert any("path-other" in i for i in issues)
    assert any("order" in i for i in issues)


def test_detects_missing_evidence_file(tmp_path):
    issues = check_s1(_inv(), tmp_path)
    assert any("app.py" in i for i in issues)


def test_evidence_line_out_of_range_and_null_line(tmp_path):
    (tmp_path / "app.py").write_text("x\n")
    inv = _inv()
    inv["workloads"][0]["entrypoint"] = {"path": "app.py", "line": 9, "snippet": "x"}
    inv["endpoints"][0]["handler"] = {"path": "app.py", "line": None, "snippet": "x"}
    issues = check_s1(inv, tmp_path)
    assert issues == ["evidence line out of range: app.py:9"]


def test_duplicate_endpoint_in_same_workload(tmp_path):
    (tmp_path / "app.py").write_text("x\n")
    inv = _inv()
    inv["endpoints"].append(dict(inv["endpoints"][0], id="ep-web-002"))
    assert check_s1(inv, tmp_path) == ["endpoint ep-web-002: duplicate of another endpoint in w-web"]
    inv["endpoints"][1]["route"] = "/other"
    assert check_s1(inv, tmp_path) == []
