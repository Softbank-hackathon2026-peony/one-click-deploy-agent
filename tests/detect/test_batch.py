import json

from infrafit.detect.artifacts import parse_artifacts
from infrafit.detect.manifests import parse_manifests
from infrafit.detect.workloads import GHA_SCHEDULE, detect_workloads, schedule_matches
from infrafit.repo import open_snapshot


def _run(tmp_path):
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    return detect_workloads(snap, parse_manifests(snap), parse_artifacts(snap))


def _write(tmp_path, rel, text):
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


MAIN = 'import sys\n\n\ndef main(): ...\n\n\nif __name__ == "__main__":\n    main()\n'


def test_python_main_becomes_worker_one_per_directory(tmp_path):
    _write(tmp_path, "jobs/collect.py", MAIN)
    _write(tmp_path, "jobs/report.py", MAIN)
    _write(tmp_path, "tests/test_x.py", MAIN)
    _write(tmp_path, "scripts/seed.py", MAIN)
    _write(tmp_path, "cli/__main__.py", "print('hi')\n")
    ws = _run(tmp_path)
    assert [(w.id, w.kind, w.status, w.code_root) for w in ws] == [
        ("w-cli", "worker", "candidate", "cli"), ("w-collect", "worker", "candidate", "jobs")]
    collect = next(w for w in ws if w.id == "w-collect")
    assert collect.entrypoint["line"] == 7 and collect.entrypoint["snippet"].startswith("if __name__")
    assert schedule_matches(ws) == []


def test_scheduled_workflow_makes_scheduled_workload_and_scheduler(tmp_path):
    _write(tmp_path, "crawler/main.py", MAIN)
    _write(tmp_path, ".github/workflows/crawl.yml", """name: crawl
on:
  schedule:
    - cron: "0 * * * *"
  workflow_dispatch:
jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python main.py
        working-directory: crawler
""")
    ws = _run(tmp_path)
    assert [(w.id, w.kind) for w in ws] == [("w-main", "scheduled")]
    assert ws[0].schedule_evidence["path"] == ".github/workflows/crawl.yml"
    assert ws[0].schedule_evidence["line"] == 4
    (m,) = schedule_matches(ws)
    assert m.component == GHA_SCHEDULE and m.role == "scheduler"


def test_package_bin_and_pyproject_scripts(tmp_path):
    _write(tmp_path, "tool/package.json", json.dumps({"name": "@acme/notify", "bin": "./cli.js"}, indent=2))
    _write(tmp_path, "pyproject.toml", '[project]\nname = "x"\n\n[project.scripts]\nsync-data = "x.cli:main"\n')
    _write(tmp_path, ".github/workflows/sync.yml",
           "on:\n  schedule:\n    - cron: '0 0 * * *'\njobs:\n  a:\n    steps:\n      - run: pip install . && sync-data\n")
    ws = _run(tmp_path)
    assert [(w.id, w.kind, w.entrypoint["path"], w.entrypoint["line"]) for w in ws] == [
        ("w-notify", "worker", "tool/package.json", 3), ("w-sync-data", "scheduled", "pyproject.toml", 5)]


def test_batch_rule_off_when_repo_has_workloads(tmp_path):
    _write(tmp_path, "requirements.txt", "fastapi\n")
    _write(tmp_path, "jobs/collect.py", MAIN)
    assert [w.id for w in _run(tmp_path)] == ["w-web"]


def test_malformed_workflow_and_manifests_do_not_crash(tmp_path):
    _write(tmp_path, "run.py", MAIN)
    _write(tmp_path, ".github/workflows/bad.yml", "on: [\n")
    _write(tmp_path, ".github/workflows/odd.yml", "on:\n  schedule: 3\njobs: [1, 2]\n")
    _write(tmp_path, "package.json", "{not json")
    _write(tmp_path, "pyproject.toml", "[project\n")
    assert [(w.id, w.kind) for w in _run(tmp_path)] == [("w-run", "worker")]
